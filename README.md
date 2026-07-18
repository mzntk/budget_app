# Mój Budżet 🏦📊

Osobista, pełnostackowa aplikacja internetowa stworzona do kompleksowego zarządzania finansami, planowania budżetu oraz analizy danych. Zbudowana w oparciu o nowoczesny backend w Pythonie (FastAPI) i interaktywny frontend (Vanilla JS/CSS).

## 🚀 Główne funkcje

*   **Inteligentny Kokpit:** Śledzenie aktualnego salda, średnich dziennych wydatków oraz pozostałych rat w czasie rzeczywistym. Wizualizacja za pomocą interaktywnych wykresów Chart.js.
*   **Rejestrowanie Transakcji:** Błyskawiczne dodawanie wydatków i wpływów z podziałem na kategorie, automatycznym zapisywaniem kontrahentów (Sklep/Osoba) i przypisywaniem do odpowiedniego filaru budżetu.
*   **Automatyczne Cykle Budżetowe:** Aplikacja automatycznie zamyka obecny i otwiera nowy miesiąc rozliczeniowy w momencie zaksięgowania głównej wypłaty.
*   **Planer 50/30/20:** Interaktywne narzędzie do podziału planowanych dochodów na „Potrzeby”, „Zachcianki” i „Oszczędności”, uwzględniające stałe koszty oraz tworzenie celowych buforów finansowych.
*   **Symulator Oszczędności:** Projekcja wzrostu kapitału na najbliższe 24 miesiące, oparta na obecnym saldzie, miesięcznych wpłatach i rocznym oprocentowaniu (mechanizm procentu składanego).
*   **Laboratorium Danych (Analityka):** 8 zaawansowanych wykresów wizualnych (m.in. Burn-up, Bubble Chart, Radar, Pareto) zaprojektowanych do odkrywania wzorców wydatkowych i analizy dynamiki zmian.
*   **Eksport Danych:** Funkcjonalność pobierania pełnej historii transakcji do pliku CSV (zgodnego z polskim Excelem) jednym kliknięciem.

## 🛠️ Stack Technologiczny

*   **Backend:** Python, FastAPI, Uvicorn (ASGI)
*   **Baza Danych:** SQLite, SQLAlchemy (ORM)
*   **Przetwarzanie Danych:** Pandas (do zaawansowanych zapytań analitycznych i agregacji)
*   **Frontend:** HTML5, Vanilla JavaScript (ES6+), CSS3 (Zmienne CSS, Flexbox, CSS Grid)
*   **Wizualizacja Danych:** Chart.js

## 📁 Struktura Projektu
```text
budget_app/
├── backend/
│   ├── analytics.py      # Logika oparta na Pandas do zaawansowanych statystyk
│   ├── database.py       # Konfiguracja silnika i sesji SQLAlchemy
│   └── models.py         # Schemat bazy danych (Cykle, Kategorie, Raty, Transakcje)
├── frontend/
│   ├── index.html        # Główny kokpit
│   ├── analityka.html    # Laboratorium Danych
│   ├── historia.html     # Historia transakcji i filtry
│   ├── oszczednosci.html # Symulator oszczędności
│   └── planowanie.html   # Planer budżetu
├── main.py               # Główny serwer FastAPI i endpointy API
├── requirements.txt      # Zależności Pythona
└── README.md
