# src/gui/data_editor_view.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QTextEdit, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import datetime
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
        self.materials_db = {"materials": {}}

        # Style kolorystyczne
        self.COLOR_ADD = "#2c3e50"  # Granatowy dla wszystkich "Dodaj"
        self.COLOR_DEL = "#d98880"  # Przygaszona czerwień dla "Usuń"
        self.COLOR_SAVE = "#27ae60"  # Zielony dla zapisu (zostawiam, bo to kluczowa akcja)
        self.COLOR_WARN = "#e74c3c"  # Intensywny czerwony dla ostrzeżenia

        self._init_ui()
        self._load_all_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. NAGŁÓWEK (Tryb edycji)
        header_container = QWidget()
        header_container.setStyleSheet(f"background-color: {self.COLOR_ADD}; border-radius: 5px;")
        header_layout = QHBoxLayout(header_container)

        header_title = QLabel("TRYB EDYCJI:")
        header_title.setStyleSheet("color: white; font-weight: bold; font-size: 14px; border: none;")

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Substancje SML", "Surowce Dual-Use", "Treść Deklaracji"])
        self.combo_mode.setStyleSheet("""
            QComboBox { 
                font-size: 16px; font-weight: bold; color: white; border: 1px solid white; 
                padding: 5px; background: transparent; min-width: 300px;
            }
            QComboBox QAbstractItemView { background-color: #34495e; color: white; }
        """)
        self.combo_mode.currentTextChanged.connect(self._on_mode_changed)

        header_layout.addWidget(header_title)
        header_layout.addWidget(self.combo_mode)
        header_layout.addStretch()
        layout.addWidget(header_container)

        # 2. WYBÓR MATERIAŁU I DOSTAWCY
        selection_layout = QHBoxLayout()

        self.combo_material = QComboBox()
        self.combo_material.setMinimumWidth(150)
        self.combo_material.currentTextChanged.connect(self._on_material_changed)

        self.combo_supplier = QComboBox()
        self.combo_supplier.setMinimumWidth(250)
        self.combo_supplier.currentTextChanged.connect(self._refresh_display)

        btn_style_add = f"background-color: {self.COLOR_ADD}; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;"
        btn_style_del = f"background-color: {self.COLOR_DEL}; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;"

        btn_add_mat = QPushButton("➕ NOWA FOLIA")
        btn_add_mat.setStyleSheet(btn_style_add)
        btn_add_mat.clicked.connect(self._add_new_material)

        btn_add_supp = QPushButton("➕ DODAJ DOSTAWCĘ")
        btn_add_supp.setStyleSheet(btn_style_add)
        btn_add_supp.clicked.connect(self._add_new_supplier_entry)

        btn_del_supp = QPushButton("🗑️ USUŃ DOSTAWCĘ")
        btn_del_supp.setStyleSheet(btn_style_del)
        btn_del_supp.clicked.connect(self._delete_current_supplier)

        selection_layout.addWidget(QLabel("Folia:"))
        selection_layout.addWidget(self.combo_material)
        selection_layout.addWidget(btn_add_mat)
        selection_layout.addWidget(QLabel("Dostawca:"))
        selection_layout.addWidget(self.combo_supplier)
        selection_layout.addWidget(btn_add_supp)
        selection_layout.addWidget(btn_del_supp)
        selection_layout.addStretch()
        layout.addLayout(selection_layout)

        # 3. OSTRZEŻENIE
        self.warn_label = QLabel("⚠️ ZMIANY W NAZWACH LUB CAS SĄ GLOBALNE I WPŁYWAJĄ NA WSZYSTKIE DEKLARACJE!")
        self.warn_label.setAlignment(Qt.AlignCenter)
        self.warn_label.setStyleSheet(f"""
            background-color: {self.COLOR_WARN}; color: white; padding: 10px; 
            font-weight: bold; border-radius: 4px;
        """)
        layout.addWidget(self.warn_label)

        # 4. TABELA
        self.table = QTableWidget()
        self.table.itemChanged.connect(self._on_cell_changed)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { gridline-color: #dcdde1; }")
        layout.addWidget(self.table)

        self.text_editor = QTextEdit()
        self.text_editor.hide()
        layout.addWidget(self.text_editor)

        # 5. STOPKA - PRZYCISKI AKCJI
        footer = QHBoxLayout()

        btn_add_row = QPushButton("➕ DODAJ NOWY WIERSZ")
        btn_add_row.setMinimumHeight(55)
        btn_add_row.setMinimumWidth(250)
        btn_add_row.setStyleSheet(btn_style_add + "font-size: 14px;")
        btn_add_row.clicked.connect(lambda: self.table.insertRow(self.table.rowCount()))

        btn_del_row = QPushButton("➖ USUŃ WIERSZ")
        btn_del_row.setMinimumHeight(55)
        btn_del_row.setStyleSheet(btn_style_del)
        btn_del_row.clicked.connect(lambda: self.table.removeRow(self.table.currentRow()))

        self.btn_save = QPushButton("💾 ZAPISZ ZMIANY W BAZIE")
        self.btn_save.setMinimumHeight(55)
        self.btn_save.setMinimumWidth(300)
        self.btn_save.setStyleSheet(
            f"background-color: {self.COLOR_SAVE}; color: white; font-weight: bold; font-size: 16px; border-radius: 4px;")
        self.btn_save.clicked.connect(self._save_all_data)

        footer.addWidget(btn_add_row)
        footer.addWidget(btn_del_row)
        footer.addStretch()
        footer.addWidget(self.btn_save)
        layout.addLayout(footer)

    def _load_all_data(self):
        self.master_substances = self.data_loader.load_json(SUBSTANCES_MASTER)
        self.master_dual_use = self.data_loader.load_json(DUAL_USE_MASTER)
        self.materials_db = self.data_loader.load_json(MATERIALS_DB)
        if "materials" not in self.materials_db: self.materials_db["materials"] = {}
        self._on_mode_changed()

    def _on_mode_changed(self):
        mode = self.combo_mode.currentText()
        if "Treść" in mode:
            self.combo_material.hide()
            self.combo_supplier.hide()
            self.table.hide()
            self.text_editor.show()
        else:
            self.combo_material.show()
            self.combo_supplier.show()
            self.table.show()
            self.text_editor.hide()
            self.combo_material.clear()
            self.combo_material.addItems(sorted(self.materials_db["materials"].keys()))
        self._refresh_display()

    def _on_material_changed(self, mat_name):
        self.combo_supplier.clear()
        if mat_name in self.materials_db["materials"]:
            entries = self.materials_db["materials"][mat_name]
            for i, entry in enumerate(entries):
                display = f"{entry.get('supplier', 'Dostawca')} ({entry.get('lastUpdated', '')[:10]})"
                self.combo_supplier.addItem(display, i)

    def _refresh_display(self):
        mode = self.combo_mode.currentText()
        mat_name = self.combo_material.currentText()
        supp_idx = self.combo_supplier.currentData()

        if "Treść" in mode or mat_name == "" or supp_idx is None:
            self.table.setRowCount(0)
            return

        self.table.blockSignals(True)
        self.table.setRowCount(0)

        mat_entry = self.materials_db["materials"][mat_name][supp_idx]
        is_sml = "Substancje" in mode

        headers = ["ID", "CAS", "NAZWA EN", "NAZWA PL", "WARTOŚĆ SML" if is_sml else "SYMBOL E"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        items = mat_entry.get('sml' if is_sml else 'dualUse', [])
        bold_font = QFont();
        bold_font.setBold(True)

        for i, item in enumerate(items):
            self.table.insertRow(i)
            s_id = str(item.get('substanceId') if is_sml else item)
            master = self.master_substances.get(s_id, {}) if is_sml else self.master_dual_use.get(s_id, {})

            cells = [
                s_id,
                master.get('cas', ''),
                master.get('name_en', ''),  # EN pierwsze
                master.get('name_pl', ''),  # PL drugie
                str(item.get('value', '')) if is_sml else master.get('e_symbol', '')
            ]

            for col, text in enumerate(cells):
                table_item = QTableWidgetItem(text)
                table_item.setTextAlignment(Qt.AlignCenter)
                if col == 4: table_item.setFont(bold_font)  # SML pogrubione
                self.table.setItem(i, col, table_item)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.blockSignals(False)

    def _on_cell_changed(self, item):
        if item.column() != 0: return
        self.table.blockSignals(True)
        val = item.text().strip()
        is_sml = "Substancje" in self.combo_mode.currentText()
        master = self.master_substances if is_sml else self.master_dual_use

        if val in master:
            d = master[val]
            self.table.setItem(item.row(), 1, QTableWidgetItem(d.get('cas', '')))
            self.table.setItem(item.row(), 2, QTableWidgetItem(d.get('name_en', '')))
            self.table.setItem(item.row(), 3, QTableWidgetItem(d.get('name_pl', '')))
            if not is_sml: self.table.setItem(item.row(), 4, QTableWidgetItem(d.get('e_symbol', '')))

            for col in range(1, 5):
                if self.table.item(item.row(), col):
                    self.table.item(item.row(), col).setTextAlignment(Qt.AlignCenter)
        self.table.blockSignals(False)

    def _delete_current_supplier(self):
        mat_name = self.combo_material.currentText()
        supp_idx = self.combo_supplier.currentData()
        if supp_idx is None: return

        if QMessageBox.question(self, "Usuń", f"Usunąć dostawcę z {mat_name}?") == QMessageBox.Yes:
            self.materials_db["materials"][mat_name].pop(supp_idx)
            self.data_loader.save_json(MATERIALS_DB, self.materials_db)
            self._on_material_changed(mat_name)

    def _save_all_data(self):
        mode = self.combo_mode.currentText()
        mat_name = self.combo_material.currentText()
        supp_idx = self.combo_supplier.currentData()
        if mat_name == "" or supp_idx is None: return

        try:
            is_sml = "Substancje" in mode
            new_list = []
            for r in range(self.table.rowCount()):
                row_id = self.table.item(r, 0).text() if self.table.item(r, 0) else ""
                if not row_id: continue

                master_data = {
                    "cas": self.table.item(r, 1).text() if self.table.item(r, 1) else "",
                    "name_en": self.table.item(r, 2).text() if self.table.item(r, 2) else "",
                    "name_pl": self.table.item(r, 3).text() if self.table.item(r, 3) else ""
                }

                if is_sml:
                    self.master_substances[row_id] = master_data
                    val = self.table.item(r, 4).text() if self.table.item(r, 4) else "0"
                    new_list.append({"substanceId": int(row_id), "value": float(val.replace(',', '.'))})
                else:
                    master_data["e_symbol"] = self.table.item(r, 4).text() if self.table.item(r, 4) else ""
                    self.master_dual_use[row_id] = master_data
                    new_list.append(int(row_id))

            target = self.materials_db["materials"][mat_name][supp_idx]
            target["lastUpdated"] = datetime.datetime.now().isoformat()
            if is_sml:
                target["sml"] = new_list
            else:
                target["dualUse"] = new_list

            self.data_loader.save_json(MATERIALS_DB, self.materials_db)
            self.data_loader.save_json(SUBSTANCES_MASTER, self.master_substances)
            self.data_loader.save_json(DUAL_USE_MASTER, self.master_dual_use)
            QMessageBox.information(self, "OK", "Baza zaktualizowana.")
            self._on_material_changed(mat_name)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def _add_new_material(self):
        name, ok = QInputDialog.getText(self, "Nowa Folia", "Nazwa:")
        if ok and name:
            name = name.upper()
            if name not in self.materials_db["materials"]:
                self.materials_db["materials"][name] = []
                self.combo_material.addItem(name)
            self.combo_material.setCurrentText(name)

    def _add_new_supplier_entry(self):
        mat_name = self.combo_material.currentText()
        if not mat_name: return
        supp, ok = QInputDialog.getText(self, "Nowy Dostawca", f"Nazwa dostawcy dla {mat_name}:")
        if ok and supp:
            self.materials_db["materials"][mat_name].append({
                "supplier": supp, "lastUpdated": datetime.datetime.now().isoformat(),
                "sml": [], "dualUse": []
            })
            self._on_material_changed(mat_name)
            self.combo_supplier.setCurrentIndex(self.combo_supplier.count() - 1)