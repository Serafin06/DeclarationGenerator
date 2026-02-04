# services/data_loader.py

"""
DataLoader - Singleton do ładowania i cache'owania danych z serwera
Obsługuje wszystkie pliki JSON z walidacją i obsługą błędów
Używa NetworkService do dostępu do folderu sieciowego
"""
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from src.config.constants import (
    TEXTS_PL, TEXTS_EN, USE_NETWORK
)
from src.services.network_service import NetworkService
from src.utils.material_macher import MaterialMatcher


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

    # Dodaj na końcu klasy DataLoader, przed get_network_status():

    def get_materials_list(self) -> list:
        """Zwraca listę dostępnych materiałów"""
        from src.config.constants import MATERIALS_DB
        materials_db = self.load_json(MATERIALS_DB)
        return sorted(materials_db.get('materials', {}).keys())

    def get_material_data(self, material_name: str, supplier_index: int = 0) -> Optional[Dict]:
        """
        Pobiera dane materiału dla konkretnego dostawcy.
        supplier_index=0 -> pierwszy dostawca (domyślnie)
        """
        from src.config.constants import MATERIALS_DB
        materials_db = self.load_json(MATERIALS_DB)

        material_entries = materials_db.get('materials', {}).get(material_name, [])
        if not material_entries or supplier_index >= len(material_entries):
            return None

        return material_entries[supplier_index]

    def build_structure_data(self, mat1: str, mat2: str) -> Dict:
        """
        Buduje dane struktury z dwóch materiałów (WSZYSCY dostawcy).
        - SML: maksymalna wartość dla każdego substanceId
        - Dual Use: unikalne ID bez duplikatów

        Returns: {
            'substances': [...],  # dla tabeli SML - KLUCZE: nr_ref, nr_cas, name, sml_limit
            'dual_use': [...]     # lista stringów "Nazwa (E-symbol)"
        }
        """
        from src.config.constants import MATERIALS_DB, SUBSTANCES_MASTER, DUAL_USE_MASTER

        materials_db = self.load_json(MATERIALS_DB)
        substances_master = self.load_json(SUBSTANCES_MASTER)
        dual_use_master = self.load_json(DUAL_USE_MASTER)

        # Pobierz WSZYSTKICH dostawców dla obu materiałów
        mat1_suppliers = materials_db.get('materials', {}).get(mat1, [])
        mat2_suppliers = materials_db.get('materials', {}).get(mat2, [])

        # === SML - maksymalna wartość dla każdego substanceId ===
        sml_max = {}  # {substanceId: max_value}

        for supplier_data in mat1_suppliers + mat2_suppliers:
            for item in supplier_data.get('sml', []):
                sid = item['substanceId']
                val = item.get('value', 0)

                if sid not in sml_max or val > sml_max[sid]:
                    sml_max[sid] = val

        # Buduj listę substancji dla tabeli
        substances_list = []
        for sid, max_val in sml_max.items():
            sid_str = str(sid)
            master_data = substances_master.get(sid_str, {})

            # Użyj name_pl dla PL, name_en jako fallback
            name = master_data.get('name_pl', '') or master_data.get('name_en', '')

            substances_list.append({
                'nr_ref': master_data.get('ref_no', ''),
                'nr_cas': master_data.get('cas', ''),
                'name': name,
                'sml_limit': max_val
            })

        # === Dual Use - unikalne ID ===
        dual_use_ids = set()

        for supplier_data in mat1_suppliers + mat2_suppliers:
            for did in supplier_data.get('dualUse', []):
                dual_use_ids.add(did)

        # Formatuj jako stringi "Nazwa (E-symbol)"
        dual_use_list = []
        for did in sorted(dual_use_ids):
            did_str = str(did)
            master_data = dual_use_master.get(did_str, {})

            name = master_data.get('name_pl', '') or master_data.get('name_en', '')
            e_symbol = master_data.get('e_symbol', '')

            if name and e_symbol:
                dual_use_list.append(f"{name} ({e_symbol})")
            elif name:
                dual_use_list.append(name)

        return {
            'substances': substances_list,
            'dual_use': dual_use_list
        }

    def get_network_status(self) -> Optional[dict]:
        """Zwraca status połączenia sieciowego"""
        if self.network_service:
            return self.network_service.get_status()
        return None

    def build_structure_data_trilayer(self, mat1: str, mat2: str, mat3: str) -> Dict:
        """Jak build_structure_data ale dla 3 materiałów"""
        from src.config.constants import MATERIALS_DB, SUBSTANCES_MASTER, DUAL_USE_MASTER

        materials_db = self.load_json(MATERIALS_DB)
        substances_master = self.load_json(SUBSTANCES_MASTER)
        dual_use_master = self.load_json(DUAL_USE_MASTER)

        # Pobierz WSZYSTKICH dostawców dla trzech materiałów
        mat1_suppliers = materials_db.get('materials', {}).get(mat1, [])
        mat2_suppliers = materials_db.get('materials', {}).get(mat2, [])
        mat3_suppliers = materials_db.get('materials', {}).get(mat3, [])

        # SML - maksymalna wartość
        sml_max = {}

        for supplier_data in mat1_suppliers + mat2_suppliers + mat3_suppliers:
            for item in supplier_data.get('sml', []):
                sid = item['substanceId']
                val = item.get('value', 0)

                if sid not in sml_max or val > sml_max[sid]:
                    sml_max[sid] = val

        # Buduj listę substancji
        substances_list = []
        for sid, max_val in sml_max.items():
            sid_str = str(sid)
            master_data = substances_master.get(sid_str, {})

            name = master_data.get('name_pl', '') or master_data.get('name_en', '')

            substances_list.append({
                'nr_ref': master_data.get('ref_no', ''),
                'nr_cas': master_data.get('cas', ''),
                'name': name,
                'sml_limit': max_val
            })

        # Dual Use - unikalne ID
        dual_use_ids = set()

        for supplier_data in mat1_suppliers + mat2_suppliers + mat3_suppliers:
            for did in supplier_data.get('dualUse', []):
                dual_use_ids.add(did)

        # Formatuj jako stringi
        dual_use_list = []
        for did in sorted(dual_use_ids):
            did_str = str(did)
            master_data = dual_use_master.get(did_str, {})

            name = master_data.get('name_pl', '') or master_data.get('name_en', '')
            e_symbol = master_data.get('e_symbol', '')

            if name and e_symbol:
                dual_use_list.append(f"{name} ({e_symbol})")
            elif name:
                dual_use_list.append(name)

        return {
            'substances': substances_list,
            'dual_use': dual_use_list
        }

    def find_material_match(self, material_name: str) -> Optional[str]:
        """
        Znajduje dopasowanie dla nazwy materiału z tolerancją na formatowanie.

        Args:
            material_name: Nazwa z bazy (np. 'PE-EVOH')

        Returns:
            Dopasowana nazwa z materials.json lub None
        """
        available = self.get_materials_list()
        return MaterialMatcher.find_best_match(material_name, available)

    def parse_and_match_structure(self, structure_str: str) -> Tuple[List[str], bool]:
        """
        Parsuje strukturę z bazy i dopasowuje materiały.

        Returns:
            (matched_materials, all_found)
        """
        available = self.get_materials_list()
        return MaterialMatcher.parse_structure(structure_str, available)