# gui/bok_declaration_view.py

"""
BOKDeclarationView - Widok do generowania deklaracji BOK z danymi z bazy
"""
import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QGroupBox,
                             QMessageBox, QRadioButton, QButtonGroup,
                             QFormLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFileDialog, QDateEdit, QTextEdit)
from PyQt5.QtCore import QDate
from datetime import date, timedelta

from src.config.constants import MATERIALS_DB
from src.models.declaration import Declaration, Product, ClientData, ProductBatch
from src.services.pdf_generator import PDFGenerator
from src.services.database_service import DatabaseService


class BOKDeclarationView(QWidget):
    """Widok do generowania deklaracji BOK z danymi klienta"""

    def __init__(self, data_loader):
        super().__init__()
        self.data_loader = data_loader
        self.db_service = DatabaseService()
        self.products = []  # Lista obiektów ProductBatch
        self.pdf_generator = PDFGenerator(self.data_loader)

        self.available_materials = self.data_loader.get_materials_list()
        self._init_ui()
        self._test_db_connection()

    def _test_db_connection(self):
        """Testuje połączenie z bazą przy starcie"""
        if not self.db_service.testConnection():
            QMessageBox.warning(
                self,
                "Uwaga",
                "Nie można połączyć się z bazą danych.\n"
                "Funkcje pobierania danych będą niedostępne."
            )

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- SEKCJA 1: JĘZYK ---
        lang_group = QGroupBox("Język")
        lang_layout = QHBoxLayout()
        self.radio_pl = QRadioButton("Polski");
        self.radio_pl.setChecked(True)
        self.radio_en = QRadioButton("English")
        lang_layout.addWidget(self.radio_pl);
        lang_layout.addWidget(self.radio_en);
        lang_layout.addStretch()
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)

        # --- SEKCJA 2: KLIENT I FAKTURA ---
        client_group = QGroupBox("Dane Kontrahenta i Dokumentu")
        c_layout = QFormLayout()
        self.input_client_name = QLineEdit()
        self.input_client_id = QLineEdit();
        self.input_client_id.setFixedWidth(100)
        self.input_client_addr = QLineEdit()
        self.input_invoice = QLineEdit();
        self.input_invoice.setPlaceholderText("np. TSPRZ/...")

        c_layout.addRow("Klient:", self.input_client_name)
        c_layout.addRow("ID / Adres:", self.input_client_id)
        c_layout.addRow("", self.input_client_addr)
        c_layout.addRow("Nr faktury:", self.input_invoice)
        client_group.setLayout(c_layout)
        layout.addWidget(client_group)

        # --- SEKCJA 3: SPECYFIKACJA LAMINATU ---
        struct_group = QGroupBox("Specyfikacja Struktury")
        s_layout = QFormLayout()
        lam_layout = QHBoxLayout()
        self.combo_mat1 = QComboBox();
        self.combo_mat1.addItems(self.available_materials)
        self.combo_mat2 = QComboBox();
        self.combo_mat2.addItems(self.available_materials)
        self.combo_mat1.currentTextChanged.connect(self._update_laminate_info)
        self.combo_mat2.currentTextChanged.connect(self._update_laminate_info)

        lam_layout.addWidget(self.combo_mat1);
        lam_layout.addWidget(QLabel("/"));
        lam_layout.addWidget(self.combo_mat2)
        s_layout.addRow("Struktura:", lam_layout)

        self.preview_text = QTextEdit();
        self.preview_text.setReadOnly(True);
        self.preview_text.setMaximumHeight(60)
        s_layout.addRow("Info o substancjach:", self.preview_text)
        struct_group.setLayout(s_layout)
        layout.addWidget(struct_group)

        # --- SEKCJA 4: DODAWANIE WYROBU (ZLECENIA) ---
        add_group = QGroupBox("Dodaj Wyrób (Zlecenie)")
        a_layout = QFormLayout()
        search_layout = QHBoxLayout()
        self.input_zo = QLineEdit();
        self.input_zo.setPlaceholderText("Nr zlecenia...")
        btn_fetch = QPushButton("🔍 Pobierz");
        btn_fetch.clicked.connect(self._search_order)
        search_layout.addWidget(self.input_zo);
        search_layout.addWidget(btn_fetch)

        self.input_art_index = QLineEdit();
        self.input_art_index.setReadOnly(True)
        self.input_art_desc = QLineEdit()
        self.input_batch = QLineEdit()
        self.input_qty = QLineEdit()

        a_layout.addRow("Zlecenie:", search_layout)
        a_layout.addRow("Indeks artykułu:", self.input_art_index)
        a_layout.addRow("Opis produktu:", self.input_art_desc)
        a_layout.addRow("Nr partii:", self.input_batch)
        a_layout.addRow("Ilość:", self.input_qty)

        btn_add = QPushButton("➕ DODAJ WYRÓB DO LISTY")
        btn_add.clicked.connect(self._add_product_to_list)
        btn_add.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; height: 35px;")
        a_layout.addRow(btn_add)
        add_group.setLayout(a_layout)
        layout.addWidget(add_group)

        # --- SEKCJA 5: LISTA WPROWADZONYCH WYROBÓW (TABELA) ---
        table_group = QGroupBox("Wyroby w deklaracji")
        t_layout = QVBoxLayout()
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Indeks", "Nazwa", "Nr Partii", "Ilość", "Usuń"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t_layout.addWidget(self.table)
        table_group.setLayout(t_layout)
        layout.addWidget(table_group)

        # Przyciski Akcji
        layout.addLayout(self._create_action_buttons())

    def _search_order(self):
        """Pobiera dane z bazy i uzupełnia pola"""
        zo = self.input_zo.text().strip()
        data = self.db_service.get_order_data(zo)
        if data:
            if not self.products:  # Tylko przy pierwszym rekordzie
                self.input_client_id.setText(str(data['client_number']))
                self.input_client_name.setText(data['client_name'])
                self.input_client_addr.setText(data['client_address'])
                db_struct = data.get('product_structure', '')
                if "/" in db_struct:
                    m1, m2 = db_struct.split('/')[:2]
                    self.combo_mat1.setCurrentText(m1);
                    self.combo_mat2.setCurrentText(m2)

            self.input_art_index.setText(str(data['article_index']))
            self.input_art_desc.setText(data['article_description'])
            year = str(datetime.datetime.now().year)[2:]
            self.input_batch.setText(f"{zo}/{year}/ZK")
        else:
            QMessageBox.warning(self, "Błąd", "Nie znaleziono zlecenia.")

    def _add_product_to_list(self):
        """Przenosi dane z pól do tabeli i czyści pola zlecenia"""
        idx = self.input_art_index.text().strip()
        desc = self.input_art_desc.text().strip()
        batch = self.input_batch.text().strip()
        qty = self.input_qty.text().strip()

        if not all([idx, desc, batch, qty]):
            QMessageBox.warning(self, "Błąd", "Wypełnij dane wyrobu przed dodaniem.")
            return

        # Dodajemy do modelu
        product = ProductBatch(
            product_code=idx,
            product_name=desc,
            batch_number=batch,
            quantity=qty,
            production_date=date.today(),  # Możesz tu dodać QDateEdit jeśli potrzebna konkretna data
            expiry_date="12 miesięcy"
        )
        self.products.append(product)
        self._update_products_table()

        # Czyścimy pola zlecenia dla następnego wpisu
        self.input_zo.clear();
        self.input_art_index.clear()
        self.input_art_desc.clear();
        self.input_batch.clear();
        self.input_qty.clear()

    def _update_products_table(self):
        self.table.setRowCount(len(self.products))
        for i, p in enumerate(self.products):
            self.table.setItem(i, 0, QTableWidgetItem(p.product_code))
            self.table.setItem(i, 1, QTableWidgetItem(p.product_name))
            self.table.setItem(i, 2, QTableWidgetItem(p.batch_number))
            self.table.setItem(i, 3, QTableWidgetItem(p.quantity))
            btn_del = QPushButton("❌");
            btn_del.clicked.connect(lambda ch, idx=i: self._remove_product(idx))
            self.table.setCellWidget(i, 4, btn_del)

    def _remove_product(self, index):
        self.products.pop(index)
        self._update_products_table()

    def _update_laminate_info(self):
        m1, m2 = self.combo_mat1.currentText(), self.combo_mat2.currentText()
        data = self.data_loader.build_structure_data(m1, m2)
        self.preview_text.setPlainText(
            f"Struktura: {m1}/{m2}\nSML: {len(data['substances'])} | Dual: {len(data['dual_use'])}")

    def _create_action_buttons(self):
        layout = QHBoxLayout()

        btn_clear = QPushButton("🗑️ Wyczyść")
        btn_clear.clicked.connect(self._clear_all)

        # Przycisk DOCX
        btn_docx = QPushButton("W Word (DOCX)")
        btn_docx.clicked.connect(self._generate_docx)
        btn_docx.setStyleSheet("background-color: #2b579a; color: white; font-weight: bold; padding: 10px;")

        # Przycisk PDF
        btn_pdf = QPushButton("📄 GENERUJ PDF")
        btn_pdf.clicked.connect(self._generate_pdf)
        btn_pdf.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")

        layout.addStretch()
        layout.addWidget(btn_clear)
        layout.addWidget(btn_docx)
        layout.addWidget(btn_pdf)
        return layout

    def _clear_all(self):
        self.products.clear();
        self._update_products_table()
        self.input_client_name.clear();
        self.input_client_id.clear();
        self.input_client_addr.clear()

    def _create_declaration(self) -> Declaration:
        """Zbiera wszystkie dane z GUI do jednego obiektu modelu"""
        declaration = Declaration()
        declaration.language = 'pl' if self.radio_pl.isChecked() else 'en'
        declaration.declaration_type = 'bok'
        declaration.generation_date = date.today()

        # 1. Dane klienta i dokumentu
        declaration.client = ClientData(
            client_code=self.input_client_id.text().strip(),
            client_name=self.input_client_name.text().strip(),
            client_address=self.input_client_addr.text().strip(),
            invoice_number=self.input_invoice.text().strip()
        )

        # 2. Dane o strukturze laminatu (z Twoich ComboBoxów)
        m1 = self.combo_mat1.currentText()
        m2 = self.combo_mat2.currentText()
        structure_str = f"{m1}/{m2}"

        # Pobieramy pełne dane o substancjach dla tej struktury
        structure_details = self.data_loader.build_structure_data(m1, m2)

        declaration.product = Product(
            name=self.input_art_desc.text().strip() or "Laminat",
            structure=structure_str,
            substances=structure_details.get('substances', []),
            dual_use=structure_details.get('dual_use', [])
        )

        # 3. Lista wszystkich dodanych partii z tabeli
        declaration.batches = self.products.copy()

        return declaration

    def _generate_pdf(self):
        """Generuje PDF i pozwala go zapisać"""
        if not self._validate_input(): return

        try:
            decl = self._create_declaration()
            pdf_bytes = self.pdf_generator.generate_pdf_bytes(decl)

            path, _ = QFileDialog.getSaveFileName(self, "Zapisz PDF",
                                                  f"Deklaracja_{decl.client.client_name}.pdf", "PDF Files (*.pdf)")

            if path:
                with open(path, 'wb') as f:
                    f.write(pdf_bytes)
                QMessageBox.information(self, "Sukces", "Plik PDF został zapisany.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd PDF", f"Szczegóły: {str(e)}")

    def _generate_docx(self):
        """Generuje DOCX używając Twojej metody w PDFGenerator"""
        if not self._validate_input(): return

        try:
            decl = self._create_declaration()
            # Twoja metoda generate_docx zapisuje plik w OUTPUT_PATH
            output_path = self.pdf_generator.generate_docx(decl)

            QMessageBox.information(self, "Sukces", f"Plik DOCX został wygenerowany w:\n{output_path}")

            # Opcjonalnie: otwórz folder z plikiem
            import os
            os.startfile(output_path.parent)
        except Exception as e:
            QMessageBox.critical(self, "Błąd DOCX", f"Szczegóły: {str(e)}")
