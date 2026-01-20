# config/databasaConst.py

# Informacje dotyczące bazy danych produkcji

# === NAZWY TABEL ===
TABLE_NAMES = {
    'orders': 'ZO',  # Zamówienia - dane produktu
    # TODO: Dodaj nazwę tabeli kontrahentów
    'clients': 'NAZWA_TABELI_KONTRAHENTOW',  # Kontrahenci
}

# === KOLUMNY TABEL ===
ZO_COLUMNS = {
    'order_number': 'NUMER',  # Numer zlecenia
    'article_index': 'NAZWA_INDEKS1',
    'client_article_index': 'ART',
    'article_description': 'OPIS1',
    'product_structure': 'RECEPTURA_1',
    # TODO: Dodaj kolumny dla daty produkcji i ilości
    # 'production_date': 'NAZWA_KOLUMNY_DATA',
    # 'quantity': 'NAZWA_KOLUMNY_ILOSC',
}

# TODO: Uzupełnij kolumny tabeli kontrahentów
CLIENT_COLUMNS = {
    'client_number': 'NUMER_KONTRAHENTA',  # Numer kontrahenta
    'client_name': 'NAZWA',  # Nazwa firmy
    'client_address': 'ADRES',  # Adres (lub osobne kolumny)
}