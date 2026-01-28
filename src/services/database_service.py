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

    def get_order_data(self, order_number: str) -> Optional[Dict]:
        """
        Pobiera dane zlecenia z tabeli ZO po numerze zlecenia
        Zwraca: dane produktu, klienta, daty produkcji
        """
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
                    k.{CLIENT_COLUMNS['client_address']} as client_address
                FROM {TABLE_NAMES['orders']} zo
                LEFT JOIN {TABLE_NAMES['clients']} k 
                    ON zo.{ZO_COLUMNS['client_number']} = k.{CLIENT_COLUMNS['client_number']}
                WHERE zo.{ZO_COLUMNS['order_number']} = :order_number
            """)

            with self.engine.connect() as conn:
                result = conn.execute(query, {"order_number": order_number}).fetchone()

                if result:
                    return {
                        'order_number': result.order_number,
                        'article_index': result.article_index,
                        'client_article_index': result.client_article_index,
                        'article_description': result.article_description,
                        'product_structure': result.product_structure,
                        'production_date': result.production_date,
                        'batch_number': result.order_number,  # Nr partii = Nr zlecenia
                        'client_number': result.client_number,
                        'client_name': result.client_name,
                        'client_address': result.client_address,
                        'quantity': None,  # TODO: będzie liczone z bazy lub ręcznie
                    }
                return None

        except Exception as e:
            print(f"Błąd pobierania zlecenia: {e}")
            raise

    def get_client_data(self, client_number: str) -> Optional[Dict]:
        """
        Pobiera dane kontrahenta z tabeli kontrahentów

        Args:
            client_number: Numer kontrahenta

        Returns:
            Dict z danymi kontrahenta lub None jeśli nie znaleziono
        """
        # TODO: Uzupełnij gdy będzie znana nazwa tabeli i kolumny
        try:
            query = text(f"""
                SELECT 
                    {CLIENT_COLUMNS['client_number']} as client_number,
                    {CLIENT_COLUMNS['client_name']} as client_name,
                    {CLIENT_COLUMNS['client_address']} as client_address
                FROM {TABLE_NAMES['clients']}
                WHERE {CLIENT_COLUMNS['client_number']} = :client_number
            """)

            with self.engine.connect() as conn:
                result = conn.execute(query, {"client_number": client_number}).fetchone()

                if result:
                    return {
                        'client_number': result.client_number,
                        'client_name': result.client_name,
                        'client_address': result.client_address,
                    }
                return None

        except Exception as e:
            print(f"Błąd pobierania kontrahenta: {e}")
            raise

    def test_connection(self) -> bool:
        """Testuje połączenie z bazą"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except:
            return False