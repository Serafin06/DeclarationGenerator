# utils/material_matcher.py

"""
MaterialMatcher - Inteligentne dopasowywanie nazw materiałów
Obsługuje różnice w formatowaniu: spacje, myślniki, wielkość liter
"""
import re
from typing import Optional, List, Tuple


class MaterialMatcher:
    """Helper do normalizacji i dopasowywania nazw materiałów"""

    @staticmethod
    def normalize(name: str) -> str:
        """
        Normalizuje nazwę materiału do porównań:
        - Usuwa spacje, myślniki, podkreślenia
        - Zamienia na wielkie litery
        - Usuwa znaki specjalne

        Przykłady:
        'PE-EVOH' → 'PEEVOH'
        'PE EVOH' → 'PEEVOH'
        'pe_evoh' → 'PEEVOH'
        """
        if not name:
            return ""

        # Zamień na wielkie litery
        normalized = name.upper()

        # Usuń spacje, myślniki, podkreślenia
        normalized = re.sub(r'[\s\-_]', '', normalized)

        # Usuń inne znaki specjalne (zostaw tylko litery i cyfry)
        normalized = re.sub(r'[^A-Z0-9]', '', normalized)

        return normalized

    @staticmethod
    def find_best_match(query: str, available_materials: List[str]) -> Optional[str]:
        """
        Znajduje najlepsze dopasowanie dla query w liście materiałów.

        Args:
            query: Nazwa materiału do znalezienia (np. 'PE-EVOH')
            available_materials: Lista dostępnych materiałów (np. ['PE EVOH', 'OPA', ...])

        Returns:
            Znaleziony materiał lub None
        """
        query_norm = MaterialMatcher.normalize(query)

        # Dokładne dopasowanie (po normalizacji)
        for material in available_materials:
            if MaterialMatcher.normalize(material) == query_norm:
                return material

        # Nie znaleziono
        return None

    @staticmethod
    def parse_structure(structure_str: str, available_materials: List[str]) -> Tuple[List[str], bool]:
        """
        Parsuje string struktury i dopasowuje materiały.

        Args:
            structure_str: String struktury z bazy (np. 'PE-EVOH/BOPP' lub 'OPA / PE')
            available_materials: Lista dostępnych materiałów

        Returns:
            (matched_materials, all_found)
            matched_materials: Lista dopasowanych materiałów
            all_found: True jeśli wszystkie warstwy zostały znalezione
        """
        if not structure_str:
            return [], False

        # Podziel po '/' (może być z spacjami lub bez)
        parts = [p.strip() for p in structure_str.split('/')]

        matched = []
        all_found = True

        for part in parts:
            match = MaterialMatcher.find_best_match(part, available_materials)
            if match:
                matched.append(match)
            else:
                # Nie znaleziono - dodaj oryginalną nazwę i zaznacz błąd
                matched.append(part)
                all_found = False

        return matched, all_found
