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

    def _build_substances_list(self, sml_max: dict, substances_master: dict, language: str) -> list:
        """
        Buduje zdeduplikowaną listę substancji po CAS (lub nazwie jako fallback).
        Eliminuje duplikaty wynikające z wielu substanceId dla tej samej substancji.
        Dla duplikatów zachowuje najwyższą wartość SML.
        """
        seen = {}  # klucz: cas lub normalized_name -> entry dict

        for sid, max_val in sml_max.items():
            sid_str = str(sid)
            master_data = substances_master.get(sid_str, {})

            cas = master_data.get('cas', '').strip()

            if language == 'en':
                name = master_data.get('name_en', '') or master_data.get('name_pl', '')
            else:
                name = master_data.get('name_pl', '') or master_data.get('name_en', '')

            dedup_key = cas if cas else name.lower().strip()

            if not dedup_key:
                continue

            entry = {
                'nr_ref': master_data.get('ref_no', ''),
                'nr_cas': cas,
                'name': name,
                'sml_limit': max_val
            }

            if dedup_key not in seen or max_val > seen[dedup_key]['sml_limit']:
                seen[dedup_key] = entry

        return list(seen.values())

    def _build_dual_use_list(self, dual_use_ids: set, dual_use_master: dict, language: str) -> list:
        """
        Buduje listę substancji dual-use na podstawie zestawu ID.
        Zwraca listę słowników z name, cas, e_symbol.
        """
        dual_use_formatted = []
        for did in sorted(dual_use_ids):
            did_str = str(did)
            master_data = dual_use_master.get(did_str, {})

            if language == 'en':
                name = master_data.get('name_en', '') or master_data.get('name_pl', '')
            else:
                name = master_data.get('name_pl', '') or master_data.get('name_en', '')

            cas = master_data.get('cas', '')
            e_symbol = master_data.get('e_symbol', '')

            if name:
                dual_use_formatted.append({
                    'name': name,
                    'cas': cas,
                    'e_symbol': e_symbol
                })

        return dual_use_formatted

    def _collect_sml_max(self, suppliers_lists: list) -> dict:
        """
        Zbiera maksymalne wartości SML dla każdego substanceId
        ze wszystkich list dostawców.
        """
        sml_max = {}
        for supplier_data in suppliers_lists:
            for item in supplier_data.get('sml', []):
                sid = item['substanceId']
                val = item.get('value', 0)
                if sid not in sml_max or val > sml_max[sid]:
                    sml_max[sid] = val
        return sml_max

    def _collect_dual_use_ids(self, suppliers_lists: list) -> set:
        """
        Zbiera unikalne ID dual-use ze wszystkich list dostawców.
        """
        dual_use_ids = set()
        for supplier_data in suppliers_lists:
            for did in supplier_data.get('dualUse', []):
                dual_use_ids.add(did)
        return dual_use_ids

    def build_structure_data(self, mat1: str, mat2: str, language: str = 'pl') -> Dict:
        """
        Buduje dane struktury z dwóch materiałów (WSZYSCY dostawcy).
        - SML: maksymalna wartość, zdeduplikowana po CAS
        - Dual Use: unikalne ID bez duplikatów

        Returns: {
            'substances': [...],  # dla tabeli SML
            'dual_use': [...]     # lista dict {name, cas, e_symbol}
        }
        """
        from src.config.constants import MATERIALS_DB, SUBSTANCES_MASTER, DUAL_USE_MASTER

        materials_db = self.load_json(MATERIALS_DB)
        substances_master = self.load_json(SUBSTANCES_MASTER)
        dual_use_master = self.load_json(DUAL_USE_MASTER)

        mat1_suppliers = materials_db.get('materials', {}).get(mat1, [])
        mat2_suppliers = materials_db.get('materials', {}).get(mat2, [])
        all_suppliers = mat1_suppliers + mat2_suppliers

        sml_max = self._collect_sml_max(all_suppliers)
        dual_use_ids = self._collect_dual_use_ids(all_suppliers)

        return {
            'substances': self._build_substances_list(sml_max, substances_master, language),
            'dual_use': self._build_dual_use_list(dual_use_ids, dual_use_master, language)
        }

    def build_structure_data_trilayer(self, mat1: str, mat2: str, mat3: str, language: str = 'pl') -> Dict:
        """Jak build_structure_data ale dla 3 materiałów"""
        from src.config.constants import MATERIALS_DB, SUBSTANCES_MASTER, DUAL_USE_MASTER

        materials_db = self.load_json(MATERIALS_DB)
        substances_master = self.load_json(SUBSTANCES_MASTER)
        dual_use_master = self.load_json(DUAL_USE_MASTER)

        mat1_suppliers = materials_db.get('materials', {}).get(mat1, [])
        mat2_suppliers = materials_db.get('materials', {}).get(mat2, [])
        mat3_suppliers = materials_db.get('materials', {}).get(mat3, [])
        all_suppliers = mat1_suppliers + mat2_suppliers + mat3_suppliers

        sml_max = self._collect_sml_max(all_suppliers)
        dual_use_ids = self._collect_dual_use_ids(all_suppliers)

        return {
            'substances': self._build_substances_list(sml_max, substances_master, language),
            'dual_use': self._build_dual_use_list(dual_use_ids, dual_use_master, language)
        }

    def get_network_status(self) -> Optional[dict]:
        """Zwraca status połączenia sieciowego"""
        if self.network_service:
            return self.network_service.get_status()
        return None

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