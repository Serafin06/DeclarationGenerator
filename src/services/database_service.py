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

        Args:
            order_number: Numer zlecenia

        Returns:
            Dict z danymi zlecenia lub None jeśli nie znaleziono
        """
        try:
            query = text(f"""
                SELECT 
                    {ZO_COLUMNS['order_number']} as order_number,
                    {ZO_COLUMNS['article_index']} as article_index,
                    {ZO_COLUMNS['client_article_index']} as client_article_index,
                    {ZO_COLUMNS['article_description']} as article_description,
                    {ZO_COLUMNS['product_structure']} as product_structure
                    -- TODO: Dodaj kolumny daty produkcji i ilości
                    -- {ZO_COLUMNS['production_date']} as production_date,
                    -- {ZO_COLUMNS['quantity']} as quantity
                FROM {TABLE_NAMES['orders']}
                WHERE {ZO_COLUMNS['order_number']} = :order_number
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
                        # TODO: Uzupełnij gdy będą dostępne kolumny
                        'production_date': None,  # result.production_date
                        'quantity': None,  # result.quantity
                        'batch_number': order_number,  # Nr partii = Nr zlecenia
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