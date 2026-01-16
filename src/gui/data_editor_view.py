"""
DataEditorView - Interfejs do edycji plików JSON
Idiotoodporny edytor z walidacją
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QTextEdit, QMessageBox,
                             QGroupBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDialog, QFormLayout, QLineEdit,
                             QDialogButtonBox)
from PyQt5.QtCore import Qt
import json
from src.config.constants import (
    SUBSTANCES_TABLE, DUAL_USE_TABLE, LAMINATE_STRUCTURES
)


class DataEditorView(QWidget):
    """Widok edycji danych wejściowych"""

    def __init__(self, data_loader):
        super().__init__()
        self.data_loader = data_loader
        self.current_file = None
        self.current_data = None
        self._init_ui()

    def _init_ui(self):
        """Inicjalizuje interfejs"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Nagłówek
        title = QLabel("Edycja Danych Wejściowych")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        warning = QLabel("⚠️ Zmiany w tych danych wpływają na wszystkie generowane deklaracje!")
        warning.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(warning)

        # Wybór pliku do edycji
        file_group = self._create_file_selector()
        layout.addWidget(file_group)

        # Tabela edycji
        self.table_widget = QTableWidget()
        self.table_widget.setEnabled(False)
        layout.addWidget(self.table_widget)

        # Przyciski akcji
        buttons_layout = self._create_buttons()
        layout.addLayout(buttons_layout)

    def _create_file_selector(self) -> QGroupBox:
        """Tworzy sekcję wyboru pliku"""
        group = QGroupBox("Wybór pliku do edycji")
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Plik:"))

        self.file_combo = QComboBox()
        self.file_combo.addItems([
            "Tabela substancji (pkt 6)",
            "Tabela dual use (pkt 8)",
            "Struktury laminatów"
        ])
        self.file_combo.currentTextChanged.connect(self._load_file_data)
        layout.addWidget(self.file_combo)

        btn_load = QPushButton("Załaduj")
        btn_load.clicked.connect(self._load_file_data)
        layout.addWidget(btn_load)

        layout.addStretch()

        group.setLayout(layout)
        return group

    def _create_buttons(self) -> QHBoxLayout:
        """Tworzy przyciski akcji"""
        layout = QHBoxLayout()

        btn_add = QPushButton("➕ Dodaj wiersz")
        btn_add.clicked.connect(self._add_row)
        layout.addWidget(btn_add)

        btn_remove = QPushButton("➖ Usuń zaznaczony")
        btn_remove.clicked.connect(self._remove_row)
        layout.addWidget(btn_remove)

        layout.addStretch()

        btn_cancel = QPushButton("↩️ Anuluj zmiany")
        btn_cancel.clicked.connect(self._load_file_data)
        layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Zapisz")
        btn_save.clicked.connect(self._save_data)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 30px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        layout.addWidget(btn_save)

        return layout

    def _get_current_file_path(self):
        """Zwraca ścieżkę do aktualnie wybranego pliku"""
        index = self.file_combo.currentIndex()
        if index == 0:
            return SUBSTANCES_TABLE
        elif index == 1:
            return DUAL_USE_TABLE
        elif index == 2:
            return LAMINATE_STRUCTURES
        return None

    def _load_file_data(self):
        """Ładuje dane z wybranego pliku"""
        try:
            file_path = self._get_current_file_path()
            if not file_path:
                return

            self.current_file = file_path
            self.current_data = self.data_loader.reload(file_path)
            self._populate_table()
            self.table_widget.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się załadować pliku:\n{e}")

    def _populate_table(self):
        """Wypełnia tabelę danymi"""
        if not self.current_data:
            return

        index = self.file_combo.currentIndex()

        if index == 0:  # Substances table
            self._populate_substances_table()
        elif index == 1:  # Dual use table
            self._populate_dual_use_table()
        elif index == 2:  # Laminate structures
            self._populate_structures_table()

    def _populate_substances_table(self):
        """Wypełnia tabelę substancji"""
        substances = self.current_data.get('substances', [])

        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels([
            "Nr ref.", "Nr CAS", "Nazwa substancji", "Limit SML [mg/kg]"
        ])
        self.table_widget.setRowCount(len(substances))

        for i, sub in enumerate(substances):
            self.table_widget.setItem(i, 0, QTableWidgetItem(sub.get('nr_ref', '')))
            self.table_widget.setItem(i, 1, QTableWidgetItem(sub.get('nr_cas', '')))
            self.table_widget.setItem(i, 2, QTableWidgetItem(sub.get('name', '')))
            self.table_widget.setItem(i, 3, QTableWidgetItem(sub.get('sml_limit', '')))

        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def _populate_dual_use_table(self):
        """Wypełnia tabelę dual use"""
        items = self.current_data.get('items', [])

        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Nazwa", "Kod E"])
        self.table_widget.setRowCount(len(items))

        for i, item in enumerate(items):
            self.table_widget.setItem(i, 0, QTableWidgetItem(item.get('name', '')))
            self.table_widget.setItem(i, 1, QTableWidgetItem(item.get('e_code', '')))

        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def _populate_structures_table(self):
        """Wypełnia tabelę struktur laminatów"""
        structures = self.current_data.get('structures', {})

        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels([
            "Struktura", "Liczba substancji SML", "Liczba dual use"
        ])
        self.table_widget.setRowCount(len(structures))

        for i, (key, value) in enumerate(structures.items()):
            self.table_widget.setItem(i, 0, QTableWidgetItem(key))
            self.table_widget.setItem(i, 1, QTableWidgetItem(str(len(value.get('substances', [])))))
            self.table_widget.setItem(i, 2, QTableWidgetItem(str(len(value.get('dual_use', [])))))

        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def _add_row(self):
        """Dodaje nowy wiersz do tabeli"""
        row_count = self.table_widget.rowCount()
        self.table_widget.insertRow(row_count)

        # Wypełnij pustymi wartościami
        for col in range(self.table_widget.columnCount()):
            self.table_widget.setItem(row_count, col, QTableWidgetItem(""))

    def _remove_row(self):
        """Usuwa zaznaczony wiersz"""
        current_row = self.table_widget.currentRow()
        if current_row >= 0:
            confirm = QMessageBox.question(
                self,
                "Potwierdzenie",
                "Czy na pewno usunąć ten wiersz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.table_widget.removeRow(current_row)

    def _save_data(self):
        """Zapisuje dane do pliku JSON"""
        try:
            # Odczytaj dane z tabeli
            index = self.file_combo.currentIndex()

            if index == 0:  # Substances
                updated_data = self._extract_substances_data()
            elif index == 1:  # Dual use
                updated_data = self._extract_dual_use_data()
            elif index == 2:  # Structures
                QMessageBox.warning(
                    self,
                    "Info",
                    "Edycja struktur laminatów w zaawansowanej wersji.\n"
                    "Na razie edytuj plik JSON bezpośrednio."
                )
                return
            else:
                return

            # Zapisz do pliku
            self.data_loader.save_json(self.current_file, updated_data)

            QMessageBox.information(
                self,
                "Sukces",
                "Dane zostały zapisane na serwerze."
            )
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać:\n{e}")

    def _extract_substances_data(self) -> dict:
        """Wyciąga dane substancji z tabeli"""
        substances = []
        for row in range(self.table_widget.rowCount()):
            substances.append({
                'nr_ref': self.table_widget.item(row, 0).text() if self.table_widget.item(row, 0) else '',
                'nr_cas': self.table_widget.item(row, 1).text() if self.table_widget.item(row, 1) else '',
                'name': self.table_widget.item(row, 2).text() if self.table_widget.item(row, 2) else '',
                'sml_limit': self.table_widget.item(row, 3).text() if self.table_widget.item(row, 3) else ''
            })
        return {'substances': substances}

    def _extract_dual_use_data(self) -> dict:
        """Wyciąga dane dual use z tabeli"""
        items = []
        for row in range(self.table_widget.rowCount()):
            items.append({
                'name': self.table_widget.item(row, 0).text() if self.table_widget.item(row, 0) else '',
                'e_code': self.table_widget.item(row, 1).text() if self.table_widget.item(row, 1) else ''
            })
        return {'items': items}

    def refresh_data(self):
        """Odświeża dane"""
        if self.current_file:
            self._load_file_data()