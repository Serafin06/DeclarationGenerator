# services/database_service.py

"""
DatabaseService - Serwis do komunikacji z bazą danych produkcji
Pobiera dane kontrahentów i zleceń
"""
from sqlalchemy import text
from src.dataBase.connection import getEngine
from src.config.databasaConst import TABLE_NAMES, ZO_COLUMNS, CLIENT_COLUMNS
from typing import Optional, Dict


class DatabaseService:
    """Serwis do pobierania danych z bazy produkcji"""

    def __init__(self):
        self.engine = getEngine()

    def testConnection(self):
        """Testuje połączenie z bazą danych, wykonując proste zapytanie."""
        engine = self.engine
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("✅ Połączono z bazą danych! Wynik testu:", result.scalar())
                return True
        except Exception as e:
            print("❌ Błąd połączenia:")
            print(e)
            return False

    def get_order_data(self, order_number: str) -> Optional[Dict]:
        try:
            query = text(f"""
                SELECT 
                    zo.{ZO_COLUMNS['order_number']} as order_number,
                    zo.{ZO_COLUMNS['article_index']} as article_index,
                    zo.{ZO_COLUMNS['client_article_index']} as client_article_index,
                    zo.{ZO_COLUMNS['article_description']} as article_description,
                    zo.{ZO_COLUMNS['product_structure']} as product_structure,
                    zo.{ZO_COLUMNS['production_date']} as production_date,
                    zo.{ZO_COLUMNS['client_number']} as client_number,
                    k.{CLIENT_COLUMNS['client_name']} as client_name,
                    k.{CLIENT_COLUMNS['ulica']} as street,
                    k.{CLIENT_COLUMNS['kod_pocztowy']} as zip_code,
                    k.{CLIENT_COLUMNS['miasto']} as city
                FROM {TABLE_NAMES['orders']} zo
                LEFT JOIN {TABLE_NAMES['clients']} k 
                    ON zo.{ZO_COLUMNS['client_number']} = k.{CLIENT_COLUMNS['client_number']}
                WHERE zo.{ZO_COLUMNS['order_number']} = :order_number
            """)

            with self.engine.connect() as conn:
                result = conn.execute(query, {"order_number": order_number}).fetchone()

                if result:
                    # Składanie adresu w jeden czytelny string
                    full_address = f"{result.street}, {result.zip_code} {result.city}"

                    return {
                        'order_number': result.order_number,
                        'article_index': result.article_index,
                        'client_article_index': result.client_article_index,
                        'article_description': result.article_description,
                        'product_structure': result.product_structure,
                        'production_date': result.production_date,
                        'batch_number': result.order_number,
                        'client_number': result.client_number,
                        'client_name': result.client_name,
                        'client_address': full_address,
                    }
                return None
        except Exception as e:
            print(f"❌ Database Error: {e}")
            raise

    def getAllClients(self) -> Dict[str, Dict]:
        """Pobiera listę wszystkich kontrahentów do wyszukiwarki"""
        try:
            query = text(f"""
                SELECT 
                    {CLIENT_COLUMNS['client_number']} as id,
                    {CLIENT_COLUMNS['client_name']} as name,
                    {CLIENT_COLUMNS['ulica']} as street,
                    {CLIENT_COLUMNS['kod_pocztowy']} as zip,
                    {CLIENT_COLUMNS['miasto']} as city
                FROM {TABLE_NAMES['clients']}
                ORDER BY {CLIENT_COLUMNS['client_name']} ASC
            """)

            clients = {}
            with self.engine.connect() as conn:
                result = conn.execute(query)
                for row in result:
                    clients[str(row.id)] = {
                        'client_name': row.name,
                        'client_address': f"{row.street}, {row.zip} {row.city}"
                    }
            return clients
        except Exception as e:
            print(f"Błąd pobierania listy kontrahentów: {e}")
            return {}