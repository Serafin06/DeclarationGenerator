# config/constants.py

"""
Stałe konfiguracyjne aplikacji - wszystkie ścieżki i parametry w jednym miejscu
"""
import os
import sys
from pathlib import Path

# Funkcja do ścieżek w onefile
def resource_path(relative_path: str) -> Path:
    """
    Zwraca poprawną ścieżkę zarówno dla PyInstaller (onefile),
    jak i normalnego uruchomienia z Pythona
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(relative_path)


def _load_dotenv() -> None:
    """
    Wczytuje plik .env (format: KLUCZ=wartosc) do zmiennych srodowiskowych.
    Zmienne juz ustawione w systemie maja priorytet nad plikiem .env.
    Plik szukany obok exe (tryb PyInstaller) oraz w katalogu glownym projektu.
    """
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent)
    candidates.append(Path(__file__).resolve().parents[2])

    for directory in candidates:
        env_file = directory / ".env"
        if not env_file.is_file():
            continue
        try:
            for raw_line in env_file.read_text(encoding="utf-8-sig").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        except OSError:
            pass
        return


# Aplikacjaa
APP_NAME = "Generator Deklaracji Zgodności"
APP_VERSION = "1.0.0"

_load_dotenv()

# Konfiguracja DB (serwer) - dane z pliku .env / zmiennych srodowiskowych
# (sekrety NIE sa trzymane w kodzie - wzor: .env.example)
DB_CONFIG = {
    'server': os.environ.get('DB_SERVER', ''),
    'database': os.environ.get('DB_NAME', ''),
    'username': os.environ.get('DB_USER', ''),
    'password': os.environ.get('DB_PASSWORD', ''),
}

# Ścieżki serwera sieciowego (adres zasobu nie jest sekretem - zostaje fallback)
SERVER_BASE = Path(os.environ.get('NETWORK_SHARE', r"\\192.168.14.14\declarations"))
DATA_PATH = SERVER_BASE / "data"
TEMPLATES_PATH_SERVER = SERVER_BASE / "templates"

NETWORK_USER = os.environ.get('NETWORK_USER', '')
NETWORK_PASSWORD = os.environ.get('NETWORK_PASSWORD', '')

# Fallback na lokalne
try:
    if SERVER_BASE.exists():
        CONFIG_PATH = DATA_PATH
        TEMPLATES_PATH = TEMPLATES_PATH_SERVER
        USE_NETWORK = True
    else:
        CONFIG_PATH = resource_path("templates")
        TEMPLATES_PATH = resource_path("templates")
        USE_NETWORK = False
        print("[!] Serwer niedostepny - uzywam lokalnych sciezek")
except:
    CONFIG_PATH = resource_path("templates")
    TEMPLATES_PATH = resource_path("templates")
    USE_NETWORK = False
    print("[!] Blad dostepu do serwera - uzywam lokalnych sciezek")

# Pliki JSON
SUBSTANCES_MASTER = CONFIG_PATH / "substances_master.json"
DUAL_USE_MASTER = CONFIG_PATH / "dual_use_master.json"
MATERIALS_DB = CONFIG_PATH / "materials_db.json"
TEXTS_PL = CONFIG_PATH / "texts_pl.json"
TEXTS_EN = CONFIG_PATH / "texts_en.json"

# Szablony HTML
TEMPLATE_PL_TECH = TEMPLATES_PATH / "declaration_tech_pl.html"
TEMPLATE_EN_TECH = TEMPLATES_PATH / "declaration_tech_en.html"
TEMPLATE_PL_BOK = TEMPLATES_PATH / "declaration_bok_pl.html"
TEMPLATE_EN_BOK = TEMPLATES_PATH / "declaration_bok_en.html"

# Folder output (do zapisu)
OUTPUT_PATH = Path.home() / "GeneratorDeklaracji" / "output"
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

# PDF Options
PDF_OPTIONS = {
    'page-size': 'A4',
    'margin-top': '15mm',
    'margin-right': '15mm',
    'margin-bottom': '15mm',
    'margin-left': '15mm',
    'encoding': 'UTF-8',
    'enable-local-file-access': None
}
