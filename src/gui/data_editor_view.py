# src/gui/data_editor_view.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QTextEdit, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import datetime
import json
from src.config.constants import (
    SUBSTANCES_MASTER, DUAL_USE_MASTER, MATERIALS_DB,
    TEXTS_PL, TEXTS_EN
)


class DataEditorView(QWidget):
    def __init__(self, data_loader):
        super().__init__()
        self.data_loader = data_loader
        self.master_substances = {}
        self.master_dual_use = {}
        self.materials_db = {}

        self._init_ui()
        self._load_all_data_from_server()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. TYP DANYCH (Duży i na górze)
        mode_layout = QVBoxLayout()
        mode_label = QLabel("TYP EDYTOWANYCH DANYCH:")
        mode_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Substancje SML", "Dual-Use", "Treść Deklaracji"])
        self.combo_mode.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px; height: 40px;")
        self.combo_mode.currentTextChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.combo_mode)
        layout.addLayout(mode_layout)

        # 2. OSTRZEŻENIE O ZMIANACH GLOBALNYCH
        self.warn_label = QLabel(
            "⚠️ UWAGA: Zmiany w nazwach substancji zostaną wprowadzone we WSZYSTKICH deklaracjach korzystających z tej bazy.")
        self.warn_label.setStyleSheet(
            "color: #c0392b; font-weight: bold; background-color: #f9ebea; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.warn_label)

        # 3. WYBÓR MATERIAŁU
        context_layout = QHBoxLayout()
        self.label_context = QLabel("Wybierz Materiał:")
        self.label_context.setFont(QFont("Arial", 10, QFont.Bold))
        self.combo_context = QComboBox()
        self.combo_context.setMinimumWidth(200)
        self.combo_context.currentTextChanged.connect(self._refresh_display)

        btn_add_context = QPushButton("➕ DODAJ NOWY MATERIAŁ")
        btn_add_context.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_add_context.clicked.connect(self._add_new_context)

        context_layout.addWidget(self.label_context)
        context_layout.addWidget(self.combo_context)
        context_layout.addWidget(btn_add_context)
        context_layout.addStretch()
        layout.addLayout(context_layout)

        # 4. TABELA (Skompresowana)
        self.table = QTableWidget()
        self.table.itemChanged.connect(self._on_cell_changed)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Edytor tekstowy (ukryty domyślnie)
        self.text_editor = QTextEdit()
        self.text_editor.hide()
        layout.addWidget(self.text_editor)

        # 5. PRZYCISKI DOLNE
        actions = QHBoxLayout()
        btn_add_row = QPushButton("➕ Dodaj wiersz")
        btn_add_row.clicked.connect(lambda: self.table.insertRow(self.table.rowCount()))

        btn_del_row = QPushButton("➖ Usuń wiersz")
        btn_del_row.clicked.connect(lambda: self.table.removeRow(self.table.currentRow()))

        btn_save = QPushButton("💾 ZAPISZ ZMIANY W BAZIE SIECIOWEJ")
        btn_save.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 12px 30px; font-size: 14px; }
            QPushButton:hover { background-color: #219150; }
        """)
        btn_save.clicked.connect(self._save_data_to_server)

        actions.addWidget(btn_add_row)
        actions.addWidget(btn_del_row)
        actions.addStretch()
        actions.addWidget(btn_save)
        layout.addLayout(actions)

    def _load_all_data_from_server(self):
        try:
            self.master_substances = self.data_loader.load_json(SUBSTANCES_MASTER)
            self.master_dual_use = self.data_loader.load_json(DUAL_USE_MASTER)
            self.materials_db = self.data_loader.load_json(MATERIALS_DB)
            self._on_mode_changed()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd ładowania: {e}")

    def _on_mode_changed(self):
        mode = self.combo_mode.currentText()
        self.combo_context.clear()

        if mode == "Treść Deklaracji":
            self.label_context.setText("Język:")
            self.combo_context.addItems(["PL", "EN"])
            self.table.hide()
            self.text_editor.show()
            self.warn_label.hide()
        else:
            self.label_context.setText("Wybierz Materiał:")
            self.combo_context.addItems(sorted(list(self.materials_db.keys())))
            self.table.show()
            self.text_editor.hide()
            self.warn_label.show()

        self._refresh_display()

    def _refresh_display(self):
        mode = self.combo_mode.currentText()
        context = self.combo_context.currentText()
        if not context: return

        self.table.blockSignals(True)
        self.table.setRowCount(0)

        if mode == "Substancje SML":
            self.table.setColumnCount(7)
            # Skompresowane pierwsze kolumny + Dostawca i Data
            self.table.setHorizontalHeaderLabels(
                ["Ref", "CAS", "Nazwa EN", "Nazwa PL", "Limit SML", "Dostawca", "Aktualizacja"])
            mat_data = self.materials_db.get(context, {})
            subs = mat_data.get('substances', [])

            self.table.setRowCount(len(subs))
            for i, item in enumerate(subs):
                ref = str(item.get('ref', ''))
                master = self.master_substances.get(ref, {})

                # Dane substancji
                self.table.setItem(i, 0, QTableWidgetItem(ref))
                self.table.setItem(i, 1, QTableWidgetItem(master.get('cas', '')))
                self.table.setItem(i, 2, QTableWidgetItem(master.get('name_en', '')))
                self.table.setItem(i, 3, QTableWidgetItem(master.get('name_pl', '')))
                self.table.setItem(i, 4, QTableWidgetItem(item.get('sml', '')))
                # Dane dostawcy (pobierane z nagłówka materiału)
                self.table.setItem(i, 5, QTableWidgetItem(mat_data.get('supplier', '')))
                self.table.setItem(i, 6, QTableWidgetItem(mat_data.get('last_updated', '')))

            # Szerokości kolumn
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Ref
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # CAS
            header.setSectionResizeMode(2, QHeaderView.Stretch)  # EN
            header.setSectionResizeMode(3, QHeaderView.Stretch)  # PL
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # SML
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Dostawca
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Data

        elif mode == "Treść Deklaracji":
            path = TEXTS_PL if context == "PL" else TEXTS_EN
            data = self.data_loader.load_json(path)
            self.text_editor.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))

        self.table.blockSignals(False)

    def _on_cell_changed(self, item):
        row, col = item.row(), item.column()
        val = item.text().strip()
        if not val or col > 3: return  # Tylko Ref, CAS, Nazwy EN/PL wyzwalają szukanie

        self.table.blockSignals(True)
        master_list = self.master_substances if self.combo_mode.currentText() == "Substancje SML" else self.master_dual_use

        found_data = None
        # Szukaj po wszystkim (Ref, CAS, Nazwy)
        if val in master_list:
            ref, found_data = val, master_list[val]
        else:
            for r, d in master_list.items():
                if d.get('cas') == val or d.get('name_en') == val or d.get('name_pl') == val:
                    ref, found_data = r, d
                    break

        if found_data:
            self.table.setItem(row, 0, QTableWidgetItem(ref))
            self.table.setItem(row, 1, QTableWidgetItem(found_data.get('cas', '')))
            self.table.setItem(row, 2, QTableWidgetItem(found_data.get('name_en', '')))
            self.table.setItem(row, 3, QTableWidgetItem(found_data.get('name_pl', '')))

        self.table.blockSignals(False)

    def _save_data_to_server(self):
        mode = self.combo_mode.currentText()
        context = self.combo_context.currentText()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            if mode == "Substancje SML":
                new_subs = []
                supplier_name = ""

                for r in range(self.table.rowCount()):
                    ref = self.table.item(r, 0).text() if self.table.item(r, 0) else ""
                    if not ref: continue

                    # 1. Aktualizuj Słownik Master (Globalny)
                    self.master_substances[ref] = {
                        "cas": self.table.item(r, 1).text() if self.table.item(r, 1) else "",
                        "name_en": self.table.item(r, 2).text() if self.table.item(r, 2) else "",
                        "name_pl": self.table.item(r, 3).text() if self.table.item(r, 3) else ""
                    }
                    # 2. Zbierz dane dla materiału
                    new_subs.append({
                        "ref": ref,
                        "sml": self.table.item(r, 4).text() if self.table.item(r, 4) else "ND"
                    })
                    # 3. Pobierz nazwę dostawcy z ostatnio zmienionego wiersza (lub dowolnego)
                    if self.table.item(r, 5): supplier_name = self.table.item(r, 5).text()

                self.materials_db[context] = {
                    "supplier": supplier_name,
                    "last_updated": now,
                    "substances": new_subs,
                    "dual_use": self.materials_db.get(context, {}).get('dual_use', [])
                }

                self.data_loader.save_json(MATERIALS_DB, self.materials_db)
                self.data_loader.save_json(SUBSTANCES_MASTER, self.master_substances)

            QMessageBox.information(self, "Sukces", f"Zapisano pomyślnie. Data aktualizacji: {now}")
            self._refresh_display()

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def _add_new_context(self):
        name, ok = QInputDialog.getText(self, "Nowy Materiał", "Podaj nazwę folii (np. OPA15):")
        if ok and name:
            name = name.upper()
            if name not in self.materials_db:
                self.materials_db[name] = {"supplier": "", "last_updated": "-", "substances": [], "dual_use": []}
                self.combo_context.addItem(name)
            self.combo_context.setCurrentText(name)