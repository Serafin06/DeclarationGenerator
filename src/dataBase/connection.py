#dataBase/connection.py

"""
Moduł odpowiedzialny za nawiązywanie i testowanie połączenia z bazą danych.
"""

from sqlalchemy import create_engine, text
from src.config.constants import DB_CONFIG


def getEngine():
    """Zwraca engine do bazy danych MSSQL za pomocą SQLAlchemy."""
    connection_url = (f"mssql+pytds://{DB_CONFIG['username']}:{DB_CONFIG['password']}"
                      f"@{DB_CONFIG['server']}/{DB_CONFIG['database']}")
    return create_engine(connection_url)


def testConnection():
    """Testuje połączenie z bazą danych, wykonując proste zapytanie."""
    engine = getEngine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Połączono z bazą danych! Wynik testu:", result.scalar())
            return True
    except Exception as e:
        print("❌ Błąd połączenia:")
        print(e)
        return False