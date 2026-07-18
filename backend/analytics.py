import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///./backend/database.db")

def get_dashboard_stats():
    # 1. Wyliczenie pozostałej raty
    query_all = """
        SELECT t.amount, c.name as category 
        FROM transactions t 
        JOIN categories c ON t.category_id = c.id
    """
    try:
        df_all = pd.read_sql(query_all, engine)
        paid_rata = df_all[df_all['category'] == 'Rata']['amount'].abs().sum() if not df_all.empty else 0.0
    except Exception:
        paid_rata = 0.0
        
    INITIAL_DEBT = 2047.52 
    remaining_debt = round(INITIAL_DEBT - float(paid_rata), 2)
    if remaining_debt < 0: remaining_debt = 0.0
        
    # 2. Znajdź aktywne ID cyklu
    cycle_df = pd.read_sql("SELECT id FROM cycles WHERE is_active = 1 LIMIT 1", engine)
    
    if cycle_df.empty:
        return {"total_income": 0, "total_expenses": 0, "daily_avg": 0, "by_date": {}, "remaining_debt": remaining_debt, "wants_budget": 0, "wants_spent": 0}
        
    active_cycle_id = cycle_df.iloc[0]['id']
    
    # 3. Pobierz transakcje z aktywnego cyklu WRAZ Z NAZWAMI KATEGORII
    query_cycle = f"""
        SELECT t.amount, t.date, c.name as category 
        FROM transactions t 
        JOIN categories c ON t.category_id = c.id
        WHERE t.cycle_id = {active_cycle_id}
    """
    df = pd.read_sql(query_cycle, engine)
    
    if df.empty:
        return {"total_income": 0, "total_expenses": 0, "daily_avg": 0, "by_date": {}, "remaining_debt": remaining_debt, "wants_budget": 0, "wants_spent": 0}

    # 4. Podział na wpływy i wydatki
    incomes = df[df['amount'] > 0]
    expenses = df[df['amount'] < 0].copy()
    expenses['amount'] = expenses['amount'].abs()

    total_income = float(incomes['amount'].sum()) if not incomes.empty else 0.0
    total_expenses = float(expenses['amount'].sum()) if not expenses.empty else 0.0
    
    unique_days = expenses['date'].nunique()
    daily_avg = round(total_expenses / unique_days, 2) if unique_days > 0 else 0.0

    by_date = {}
    if not expenses.empty:
        by_date = expenses.groupby('date')['amount'].sum().to_dict()

    # 5. Pula na zachcianki (Kategorie luźne)
    # ZAKTUALIZOWANA LISTA O TWOJE NOWE KATEGORIE
    wants_categories = [
        "Jedzenie na mieście", 
        "Rozrywka / Wyjścia", 
        "Uroda, higiena i ubrania", 
        "Zdrowie i uroda", 
        "Zakupy (spożywcze/chemia)", 
        "Inne",
        "Inne wydatki"
    ]
    
    wants_budget = total_income * 0.30
    wants_spent = float(expenses[expenses['category'].isin(wants_categories)]['amount'].sum()) if not expenses.empty else 0.0

    # 6. Oczekujące opłaty (koszty stałe)
    expected_fixed_costs = ["Rata", "Rachunki", "Catering dietetyczny", "Siłownia / Sport", "Subskrypcje"]
    paid_this_cycle = expenses['category'].unique().tolist() if not expenses.empty else []
    unpaid_fixed_costs = [cost for cost in expected_fixed_costs if cost not in paid_this_cycle]

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "daily_avg": daily_avg,
        "by_date": by_date,
        "remaining_debt": remaining_debt,
        "wants_budget": wants_budget,
        "wants_spent": wants_spent,
        "unpaid_costs": unpaid_fixed_costs
    }

def get_planning_suggestions():
    """Pobiera wydatki z poprzedniego cyklu jako propozycje do planowania."""
    try:
        # Szukamy ostatniego ZAMKNIĘTEGO cyklu
        closed_cycles = pd.read_sql("SELECT id FROM cycles WHERE is_active = 0 ORDER BY id DESC LIMIT 1", engine)
        
        if closed_cycles.empty:
            # Jeśli nie ma zamkniętego cyklu (dopiero zaczęłaś), bierzemy sumy z aktywnego
            query = "SELECT c.name, SUM(ABS(t.amount)) as total FROM transactions t JOIN categories c ON t.category_id = c.id WHERE t.amount < 0 GROUP BY c.name"
        else:
            last_cycle_id = closed_cycles.iloc[0]['id']
            query = f"SELECT c.name, SUM(ABS(t.amount)) as total FROM transactions t JOIN categories c ON t.category_id = c.id WHERE t.cycle_id = {last_cycle_id} AND t.amount < 0 GROUP BY c.name"
        
        df = pd.read_sql(query, engine)
        if df.empty:
            return {}
            
        return df.set_index('name')['total'].to_dict()
    except Exception as e:
        return {}

def get_advanced_stats():
    """Pobiera i grupuje dane do zaawansowanej analityki (8 wykresów)."""
    try:
        active_cycle_df = pd.read_sql("SELECT id FROM cycles WHERE is_active = 1 LIMIT 1", engine)
        if active_cycle_df.empty:
            return {"categories": {}, "weekdays": {}, "daily_trend": {}, "bubble": []}
            
        active_id = active_cycle_df.iloc[0]['id']
        
        query = f"""
            SELECT t.amount, t.date, c.name as category 
            FROM transactions t 
            JOIN categories c ON t.category_id = c.id
            WHERE t.cycle_id = {active_id} AND t.amount < 0
        """
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return {"categories": {}, "weekdays": {}, "daily_trend": {}, "bubble": []}

        df['amount'] = df['amount'].abs()
        df['date_obj'] = pd.to_datetime(df['date'])
        
        # 1. Suma per kategoria
        cat_dist = df.groupby('category')['amount'].sum().to_dict()
        
        # 2. Suma per dzień tygodnia
        day_map = {'Monday': 'Poniedziałek', 'Tuesday': 'Wtorek', 'Wednesday': 'Środa', 'Thursday': 'Czwartek', 'Friday': 'Piątek', 'Saturday': 'Sobota', 'Sunday': 'Niedziela'}
        df['weekday'] = df['date_obj'].dt.day_name().map(day_map)
        weekday_dist = df.groupby('weekday')['amount'].sum().to_dict()
        
        # 3. Dzienny trend (do wykresów skumulowanych i mieszanych)
        daily_sums = df.groupby('date')['amount'].sum().to_dict()
        
        # 4. Dane do wykresu bąbelkowego (dzień miesiąca, kwota)
        df['day'] = df['date_obj'].dt.day
        bubble = [{"x": int(row['day']), "y": float(row['amount']), "r": max(float(row['amount']) / 15, 5), "category": row['category']} for _, row in df.iterrows()]

        return {
            "categories": cat_dist,
            "weekdays": weekday_dist,
            "daily_trend": daily_sums,
            "bubble": bubble
        }
    except Exception as e:
        return {"categories": {}, "weekdays": {}, "daily_trend": {}, "bubble": []}