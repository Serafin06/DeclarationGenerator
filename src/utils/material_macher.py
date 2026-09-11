# utils/material_matcher.py

"""
MaterialMatcher - Inteligentne dopasowywanie nazw materiałów
Obsługuje różnice w formatowaniu: spacje, myślniki, wielkość liter,
aliasy handlowe (np. 'PE o-c' == 'PE-O15') oraz dopasowanie rozmyte (fuzzy).
"""
import re
from difflib import SequenceMatcher
from typing import Optional, List, Tuple


class MaterialMatcher:
    """Helper do normalizacji i dopasowywania nazw materiałów"""

    # Aliasy handlowe - różne oznaczenia tego samego materiału w RECEPTURZE.
    # Porównywane po normalizacji (bez spacji/myślników, WIELKIE litery).
    # Klucz   = zakończenie znormalizowanej nazwy z bazy (np. 'PE o-c' -> 'PEOC'),
    # Wartość = zamiennik (np. 'O15' -> 'PEO15' -> dopasuje materiał 'PE-O15').
    # Rozszerzaj tę mapę, gdy pojawią się nowe oznaczenia w recepturach.
    ALIAS_MAP = {
        'OC': 'O15',  # PE o-c == PE-O15
    }

    # Minimalny próg podobieństwa dopasowania rozmytego (0.0 - 1.0)
    FUZZY_THRESHOLD = 0.6

    # Minimalna długość znormalizowanej nazwy dla dopasowania rozmytego
    # (krótkie kody, np. 'PA', NIE są dopasowywane rozmyto - zbyt ryzykowne)
    FUZZY_MIN_LENGTH = 3

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
    def apply_aliases(normalized: str) -> str:
        """
        Zamienia aliasy handlowe w znormalizowanej nazwie.
        Alias zastępuje końcówkę nazwy, np. 'PEOC' -> 'PEO15'.
        """
        for alias, target in MaterialMatcher.ALIAS_MAP.items():
            if normalized.endswith(alias) and len(normalized) > len(alias):
                return normalized[:-len(alias)] + target
        return normalized

    @staticmethod
    def match_with_info(query: str,
                        available_materials: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Znajduje najlepsze dopasowanie i podaje jakim mechanizmem.
        Kolejność prób: dokładne -> alias -> rozmyte (fuzzy).

        Args:
            query: Nazwa materiału do znalezienia (np. 'PE o-c')
            available_materials: Lista dostępnych materiałów

        Returns:
            (material, kind) gdzie kind: 'exact' | 'alias' | 'fuzzy' | None
        """
        if not query or not available_materials:
            return None, None

        query_norm = MaterialMatcher.normalize(query)

        # 1) Dokładne dopasowanie (po normalizacji)
        for material in available_materials:
            if MaterialMatcher.normalize(material) == query_norm:
                return material, 'exact'

        # 2) Dopasowanie po aliasach (np. 'PE o-c' -> 'PE-O15')
        query_alias = MaterialMatcher.apply_aliases(query_norm)
        if query_alias != query_norm:
            for material in available_materials:
                if MaterialMatcher.normalize(material) == query_alias:
                    return material, 'alias'

        # 3) Dopasowanie rozmyte (tylko dla wystarczająco długich nazw)
        if len(query_norm) >= MaterialMatcher.FUZZY_MIN_LENGTH:
            best_material = None
            best_key = (0.0, 0)
            for material in available_materials:
                m_norm = MaterialMatcher.normalize(material)
                if len(m_norm) < MaterialMatcher.FUZZY_MIN_LENGTH:
                    continue
                ratio = SequenceMatcher(None, query_norm, m_norm).ratio()
                if ratio < MaterialMatcher.FUZZY_THRESHOLD:
                    continue
                # Remis podobieństwa: preferuj bardziej szczegółową (dłuższą) nazwę
                key = (ratio, len(m_norm))
                if key > best_key:
                    best_material, best_key = material, key
            if best_material:
                return best_material, 'fuzzy'

        return None, None

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
        match, _ = MaterialMatcher.match_with_info(query, available_materials)
        return match

    @staticmethod
    def suggest_matches(query: str, available_materials: List[str]) -> List[str]:
        """
        Zwraca WSZYSTKIE materiały posortowane od najlepszego dopasowania.
        Używane do wypełnienia list wyboru w dialogu struktury -
        najbliższe podpowiedzi lądują na górze listy.
        """
        query_norm = MaterialMatcher.normalize(query)
        query_alias = MaterialMatcher.apply_aliases(query_norm)

        scored = []
        for material in available_materials:
            m_norm = MaterialMatcher.normalize(material)
            if not m_norm:
                continue
            if m_norm == query_norm or (query_alias != query_norm and m_norm == query_alias):
                score = 1.0
            else:
                score = max(
                    SequenceMatcher(None, query_norm, m_norm).ratio(),
                    SequenceMatcher(None, query_alias, m_norm).ratio()
                )
            scored.append((score, len(m_norm), material))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [material for _, _, material in scored]

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
