"""
Entry point aplikacji Declaration Generator
Uruchamia główne okno GUI
"""
import sys
import io
import os

# Obsługa lokalizacji GTK po spakowaniu w PyInstallerze
if getattr(sys, 'frozen', False):
    # Katalog roboczy wygenerowany tymczasowo przez PyInstaller
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    gtk_bin = os.path.join(base_dir, 'gtk_bin')
else:
    # Lokalna ścieżka deweloperska
    gtk_bin = r"C:\Users\grabowski\GTK3\gtk-nsis-pack\bin"

if os.path.exists(gtk_bin):
    os.add_dll_directory(gtk_bin)
    os.environ['PATH'] = gtk_bin + os.path.pathsep + os.environ.get('PATH', '')

import weasyprint

# Odpornosc konsoli Windows (cp1250) na znaki spoza tej strony kodowej (np. emoji)
# - zapobiega UnicodeEncodeError przy print() z emoji
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=sys.stdout.encoding, errors="replace")
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding=sys.stderr.encoding, errors="replace")

from PyQt5.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.config.constants import APP_NAME, APP_VERSION

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(f"{APP_NAME} v{APP_VERSION}")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()