import uvicorn
import os
import webbrowser
import threading
import time
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.responses import Response
import pandas as pd
from sqlalchemy import create_engine, func
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, datetime
from backend.database import init_db, SessionLocal
from backend.models import Transaction, Cycle, Category
from backend.analytics import get_dashboard_stats, get_planning_suggestions, get_advanced_stats

init_db()

app = FastAPI()

frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Zależność bazy danych
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Model danych wejściowych z formularza
class TransactionCreate(BaseModel):
    amount: float
    date: date
    category: str
    description: str
    type: str
    counterparty: str = "" # <-- DODANE POLE


@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")

# Endpoint do zapisywania transakcji
@app.post("/api/transactions/")
def create_transaction(trans: TransactionCreate, db: Session = Depends(get_db)):
    # Kwota ujemna dla wydatków
    final_amount = -abs(trans.amount) if trans.type == "expense" else abs(trans.amount)
    
    # 1. Wyszukiwanie lub tworzenie nowej kategorii w bazie
    category_obj = db.query(Category).filter(Category.name == trans.category).first()
    if not category_obj:
        category_obj = Category(name=trans.category, type=trans.type)
        db.add(category_obj)
        db.commit()
        db.refresh(category_obj)

    # 2. Zarządzanie cyklami
    active_cycle = db.query(Cycle).filter(Cycle.is_active == True).first()

    # Jeśli nie ma żadnego cyklu (np. przy pierwszym uruchomieniu), twórz nowy
    if not active_cycle:
        active_cycle = Cycle(start_date=trans.date, is_active=True)
        db.add(active_cycle)
        db.commit()
        db.refresh(active_cycle)

    # Automatyczne zerowanie cyklu po dodaniu wypłaty
    if trans.category == "Wypłata (Główna)":
        if active_cycle:
            active_cycle.is_active = False
            active_cycle.end_date = trans.date
            db.add(active_cycle)
        
        # Tworzymy i aktywujemy nowy cykl
        new_cycle = Cycle(start_date=trans.date, is_active=True)
        db.add(new_cycle)
        db.commit()
        db.refresh(new_cycle)
        
        # Nowa wypłata zasila już nowo otwarty cykl
        active_cycle = new_cycle
        
    # 3. Zapis transakcji z przypisanym category_id oraz cycle_id
    new_trans = Transaction(
        amount=final_amount,
        date=trans.date,
        description=trans.description,
        counterparty=trans.counterparty, # <-- DODANE POLE
        category_id=category_obj.id,
        cycle_id=active_cycle.id
    )
    
    db.add(new_trans)
    db.commit()
    db.refresh(new_trans)
    
    # Zwracamy po prostu sukces, bez odwoływania się do new_trans.id
    return {"status": "success"}

@app.get("/api/stats/")
def get_stats():
    # Pobiera statystyki z pandas i wysyła do przeglądarki
    return get_dashboard_stats()

@app.get("/api/advanced-stats/")
def advanced_stats():
    return get_advanced_stats()

@app.get("/api/simulator/")
def get_simulation_data(db: Session = Depends(get_db)):
    incomes = db.query(func.sum(Transaction.amount)).filter(Transaction.type == 'income').scalar() or 0
    expenses = db.query(func.sum(Transaction.amount)).filter(Transaction.type == 'expense').scalar() or 0
    current_capital = incomes - expenses

    # Znajdujemy datę pierwszej transakcji, by ustalić liczbę "aktywnych" miesięcy
    min_date = db.query(func.min(Transaction.date)).scalar()
    
    if not min_date:
        return {"current_capital": current_capital, "monthly_avg": 0, "months_active": 1}

    try:
        # Konwersja daty z formatu string na obiekt datetime
        if isinstance(min_date, str):
            min_d = datetime.strptime(min_date, "%Y-%m-%d")
        else:
            min_d = min_date
            
        now = datetime.now()
        months_diff = (now.year - min_d.year) * 12 + now.month - min_d.month + 1
    except ValueError:
        months_diff = 1

    monthly_avg = current_capital / months_diff if months_diff > 0 else 0

    return {
        "current_capital": current_capital,
        "monthly_avg": monthly_avg,
        "months_active": months_diff
    }

@app.get("/api/history/")
def get_history(db: Session = Depends(get_db)):
    # Pobieranie wszystkich transakcji i łączenie ich z tabelą Category
    transactions = db.query(Transaction, Category).join(Category, Transaction.category_id == Category.id).order_by(Transaction.date.desc()).all()
    
    result = []
    for trans, cat in transactions:
        # Zabezpieczenie: jeśli data to zwykły tekst, po prostu zrób z niego stringa
        if hasattr(trans.date, 'isoformat'):
            safe_date = trans.date.isoformat()
        else:
            safe_date = str(trans.date)

        result.append({
            "id": trans.id,
            "date": safe_date,
            "amount": trans.amount or 0.0,
            "description": trans.description or "",
            "counterparty": trans.counterparty or "",
            "category": cat.name,
            "type": cat.type
        })
    return result

@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    trans = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if trans:
        db.delete(trans)
        db.commit()
        return {"status": "success"}
    return {"status": "not_found"}

@app.get("/api/export/csv/")
def export_csv():
    """Eksportuje całą historię transakcji do pliku CSV."""
    engine = create_engine("sqlite:///./backend/database.db")
    query = """
        SELECT t.date as Data, c.name as Kategoria, t.counterparty as 'Sklep / Osoba', 
               t.description as Opis, t.amount as Kwota
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        ORDER BY t.date DESC
    """
    try:
        df = pd.read_sql(query, engine)
        
        # separator ';' jest lepszy dla polskiego Excela, utf-8-sig naprawia polskie znaki
        csv_data = df.to_csv(index=False, sep=';', encoding='utf-8-sig') 
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=moja_historia_wydatkow.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def open_browser():
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == '__main__':
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)