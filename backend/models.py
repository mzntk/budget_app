from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import date

Base = declarative_base()

class Cycle(Base):
    """Tabela przechowująca Twoje cykle 'od wypłaty do wypłaty'"""
    __tablename__ = 'cycles'

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(Date, default=date.today)
    end_date = Column(Date, nullable=True)
    expected_income = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

    transactions = relationship("Transaction", back_populates="cycle")


class Category(Base):
    """Kategorie z podziałem na stałe i zmienne"""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String) 
    is_recurring = Column(Boolean, default=False) 

    transactions = relationship("Transaction", back_populates="category")


class Debt(Base):
    """NOWE: Tabela do śledzenia rat z możliwością nadpłacania"""
    __tablename__ = 'debts'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)                         # np. 'Rata 1'
    remaining_amount = Column(Float, default=0.0) # Startowe 2047.52
    minimum_payment = Column(Float, default=0.0)  # Startowe 241.62
    is_active = Column(Boolean, default=True)     # Zmieni się na False, gdy spłacisz do zera

    transactions = relationship("Transaction", back_populates="debt")


class Transaction(Base):
    """Tabela z konkretnymi wpisami (Twoje ręczne wprowadzanie)"""
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True) # <-- TUTAJ DODAJESZ "i"
    amount = Column(Float, nullable=False)
    date = Column(Date, default=date.today)
    description = Column(String)
    counterparty = Column(String, nullable=True) 
    
    # Klucze obce
    category_id = Column(Integer, ForeignKey('categories.id'))
    cycle_id = Column(Integer, ForeignKey('cycles.id'))
    debt_id = Column(Integer, ForeignKey('debts.id'), nullable=True) 

    # Relacje
    category = relationship("Category", back_populates="transactions")
    cycle = relationship("Cycle", back_populates="transactions")
    debt = relationship("Debt", back_populates="transactions")