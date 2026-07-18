from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base

# Ścieżka do lokalnego pliku z bazą danych
SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/database.db"

# Tworzenie silnika - parametr check_same_thread jest wymagany dla SQLite w FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Tworzy plik database.db i wszystkie tabele z pliku models.py, jeśli jeszcze nie istnieją
    Base.metadata.create_all(bind=engine)