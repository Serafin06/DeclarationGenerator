# gui/main_window.py

"""
MainWindow - Główne okno aplikacji z menu nawigacji
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QStackedWidget, QMessageBox,
                             QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from src.gui.tech_declaration_view import TechDeclarationView
from src.gui.bok_declaration_view import BOKDeclarationView
from src.gui.data_editor_view import DataEditorView
from src.gui.text_editor_view import TextEditorView
from src.services.data_loader import DataLoader


class MainWindow(QMainWindow):
    """Główne okno aplikacji z nawigacją między widokami"""

    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()
        self._check_server_connection()
        self._init_ui()

    def _check_server_connection(self):
        """Sprawdza połączenie z danymi przy starcie"""
        try:
            # Próba załadowania podstawowych danych
            self.data_loader.get_texts('pl')

            # Sprawdź status sieciowy
            network_status = self.data_loader.get_network_status()
            if network_status:
                if not network_status['connected']:
                    QMessageBox.warning(
                        self,
                        "Uwaga - tryb lokalny",
                        "Nie można połączyć się z serwerem sieciowym.\n"
                        "Program działa w trybie lokalnym.\n\n"
                        "Sprawdź:\n"
                        "- Połączenie sieciowe\n"
                        "- Dostępność serwera 192.168.14.14\n"
                        "- Uprawnienia użytkownika"
                    )
                elif not network_status['write_access']:
                    QMessageBox.warning(
                        self,
                        "Uwaga - brak uprawnień zapisu",
                        "Połączono z serwerem, ale brak uprawnień do zapisu.\n"
                        "Edycja danych będzie niemożliwa."
                    )

        except FileNotFoundError as e:
            QMessageBox.critical(
                self,
                "Błąd danych",
                f"Nie można załadować plików konfiguracyjnych:\n{e}\n\n"
                "Upewnij się że folder zawiera wszystkie pliki JSON."
            )

    def _init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        self.setWindowTitle("Generator Deklaracji Zgodności")
        self.setMinimumSize(1200, 800)

        # Główny widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout główny
        main_layout = QHBoxLayout(central_widget)

        # Panel boczny z menu
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Stacked widget dla różnych widoków
        self.stacked_widget = QStackedWidget()
        self.tech_view = TechDeclarationView(self.data_loader)
        self.bok_view = BOKDeclarationView(self.data_loader)
        self.data_editor_view = DataEditorView(self.data_loader)
        self.text_editor_view = TextEditorView(self.data_loader)

        self.stacked_widget.addWidget(self.tech_view)
        self.stacked_widget.addWidget(self.bok_view)
        self.stacked_widget.addWidget(self.data_editor_view)
        self.stacked_widget.addWidget(self.text_editor_view)

        main_layout.addWidget(self.stacked_widget, stretch=1)

    def _create_sidebar(self) -> QWidget:
        """Tworzy panel boczny z przyciskami nawigacji"""
        sidebar = QWidget()
        sidebar.setMaximumWidth(250)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
            }
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 15px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QLabel {
                color: white;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        # Nagłówek
        title = QLabel("MENU")
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Przyciski nawigacji
        btn_tech = QPushButton("📄 Deklaracja\nTechnologiczna")
        btn_tech.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(btn_tech)

        btn_bok = QPushButton("📋 Deklaracja BOK\n(z bazą danych)")
        btn_bok.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        layout.addWidget(btn_bok)

        btn_editor = QPushButton("⚙️ Edycja Danych\nWejściowych")
        btn_editor.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        layout.addWidget(btn_editor)

        btn_text_editor = QPushButton("📝 Edycja Tekstów\nDeklaracji")
        btn_text_editor.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        layout.addWidget(btn_text_editor)

        # Spacer
        layout.addStretch()

        # Przycisk statusu połączenia
        btn_status = QPushButton("📡 Status połączenia")
        btn_status.clicked.connect(self._show_network_status)
        btn_status.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        layout.addWidget(btn_status)

        # Przycisk odświeżania danych
        btn_refresh = QPushButton("🔄 Odśwież dane\nz serwera")
        btn_refresh.clicked.connect(self._refresh_data)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        layout.addWidget(btn_refresh)

        # Info o wersji
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #95a5a6; font-size: 10px;")
        layout.addWidget(version_label)

        return sidebar

    def _show_network_status(self):
        """Pokazuje status połączenia sieciowego"""
        network_status = self.data_loader.get_network_status()

        if network_status is None:
            msg = "Tryb lokalny\n\nProgram korzysta z plików lokalnych."
        else:
            status_icon = "✅" if network_status['connected'] else "❌"
            write_icon = "✅" if network_status['write_access'] else "❌"
            templates_icon = "✅" if network_status['templates_exists'] else "❌"
            data_icon = "✅" if network_status['data_exists'] else "❌"

            msg = f"Status połączenia sieciowego\n\n"
            msg += f"{status_icon} Połączenie: {'Aktywne' if network_status['connected'] else 'Brak'}\n"
            msg += f"{write_icon} Uprawnienia zapisu: {'Tak' if network_status['write_access'] else 'Nie'}\n"
            msg += f"📂 Ścieżka: {network_status['server_path']}\n\n"
            msg += f"{templates_icon} Folder templates/\n"
            msg += f"{data_icon} Folder data/\n"

        QMessageBox.information(self, "Status połączenia", msg)

    def _refresh_data(self):
        """Odświeża dane z serwera (czyści cache)"""
        try:
            self.data_loader.clear_cache()
            self.tech_view.refresh_data()
            self.bok_view.refresh_data()
            self.data_editor_view.refresh_data()
            self.text_editor_view.refresh_data()
            QMessageBox.information(
                self,
                "Sukces",
                "Dane zostały odświeżone z serwera."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Błąd",
                f"Nie udało się odświeżyć danych:\n{e}"
            )