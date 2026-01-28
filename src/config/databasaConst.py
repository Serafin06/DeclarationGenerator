# config/databasaConst.py

# Informacje dotyczące bazy danych produkcji

# === NAZWY TABEL ===
TABLE_NAMES = {
    'orders': 'ZO',  # Zamówienia - dane produktu
    'clients': 'View_Kontrahent',  # Kontrahenci
}

# === KOLUMNY TABEL ===
ZO_COLUMNS = {
    'order_number': 'NUMER',  # Numer zlecenia
    'article_index': 'NAZWA_INDEKS1',
    'client_article_index': 'ART',
    'article_description': 'OPIS1',
    'product_structure': 'RECEPTURA_1',
    'production_date': 'TERMIN_ZAK',  # PLANOWANA Data produkcji
    'client_number': 'ID_KONTRAHENTA',
}

CLIENT_COLUMNS = {
    'client_number': 'ID_KONTRAHENTA',  # Numer kontrahenta
    'client_name': 'NAZWA_PELNA',  # Nazwa firmy
    'ulica': 'ULICA_LOKAL',
    'kod_pocztowy': 'KOD_POCZTOWY',
    'miasto': 'MIEJSCOWOSC',
    'clients':'NAZWA'
}