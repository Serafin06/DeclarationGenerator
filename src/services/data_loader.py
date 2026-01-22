# services/data_loader.py

"""
DataLoader - Singleton do ładowania i cache'owania danych z serwera
Obsługuje wszystkie pliki JSON z walidacją i obsługą błędów
Używa NetworkService do dostępu do folderu sieciowego
"""
import json
from pathlib import Path
from typing import Dict, Optional
from src.config.constants import (
    TEXTS_PL, TEXTS_EN, USE_NETWORK
)
from src.services.network_service import NetworkService

class DataLoader:
    """Singleton zarządzający danymi z serwera"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._cache = {}
        self._initialized = True

        # Inicjalizuj NetworkService jeśli używamy serwera
        if USE_NETWORK:
            self.network_service = NetworkService()
            self.network_service.ensure_connection()
        else:
            self.network_service = None

    def _ensure_network_access(self) -> bool:
        """Upewnia się że mamy dostęp do serwera"""
        if self.network_service:
            return self.network_service.ensure_connection()
        return True  # Tryb lokalny - zawsze dostępny

    def load_json(self, file_path: Path) -> Dict:
        """Ładuje JSON z cache lub z pliku"""
        # Upewnij się że mamy dostęp do serwera
        if not self._ensure_network_access():
            raise ConnectionError("Brak dostępu do serwera sieciowego")

        cache_key = str(file_path)

        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[cache_key] = data
                return data
        except FileNotFoundError:
            raise FileNotFoundError(f"Brak pliku: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Błąd parsowania JSON w {file_path}: {e}")

    def save_json(self, file_path: Path, data: Dict) -> None:
        """Zapisuje JSON i aktualizuje cache"""
        # Upewnij się że mamy dostęp do zapisu
        if not self._ensure_network_access():
            raise ConnectionError("Brak dostępu do serwera sieciowego")

        if self.network_service and not self.network_service.check_write_access():
            raise PermissionError("Brak uprawnień do zapisu na serwerze")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._cache[str(file_path)] = data
        except Exception as e:
            raise IOError(f"Błąd zapisu do {file_path}: {e}")

    def reload(self, file_path: Path) -> Dict:
        """Wymusza przeładowanie pliku (usuwa z cache)"""
        cache_key = str(file_path)
        if cache_key in self._cache:
            del self._cache[cache_key]
        return self.load_json(file_path)

    def get_texts(self, language: str = 'pl') -> Dict:
        """Pobiera teksty dla języka"""
        file_path = TEXTS_PL if language == 'pl' else TEXTS_EN
        return self.load_json(file_path)

    def clear_cache(self):
        """Czyści cały cache - wymusza przeładowanie wszystkich plików"""
        self._cache.clear()

    def get_network_status(self) -> Optional[dict]:
        """Zwraca status połączenia sieciowego"""
        if self.network_service:
            return self.network_service.get_status()
        return None