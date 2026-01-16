"""
Entry point aplikacji Declaration Generator
Uruchamia główne okno GUI
"""
import sys
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