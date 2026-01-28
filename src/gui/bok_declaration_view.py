# gui/bok_declaration_view.py

"""
BOKDeclarationView - Widok do generowania deklaracji BOK z danymi z bazy
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QGroupBox,
                             QMessageBox, QRadioButton, QButtonGroup,
                             QFormLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFileDialog, QDateEdit)
from PyQt5.QtCore import QDate
from datetime import date, timedelta
from src.models.declaration import Declaration, Product, ClientData, ProductBatch
from src.services.pdf_generator import PDFGenerator
from src.services.database_service import DatabaseService


class BOKDeclarationView(QWidget):
    """Widok do generowania deklaracji BOK z danymi klienta"""

    def __init__(self, data_loader):
        super().__init__()
        self.data_loader = data_loader
        self.pdf_generator = PDFGenerator(data_loader)
        self.db_service = DatabaseService()

        # Lista produktów (partie)
        self.products = []

        self._init_ui()
        self._test_db_connection()

    def _test_db_connection(self):
        """Testuje połączenie z bazą przy starcie"""
        if not self.db_service.test_connection():
            QMessageBox.warning(
                self,
                "Uwaga",
                "Nie można połączyć się z bazą danych.\n"
                "Funkcje pobierania danych będą niedostępne."
            )

    def _init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Nagłówek
        title = QLabel("Generator Deklaracji BOK (z bazą danych)")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Wybór języka
        lang_group = self._create_language_section()
        layout.addWidget(lang_group)

        # Dane klienta (automatycznie z zlecenia) - ZMIENIONA KOLEJNOŚĆ
        client_group = self._create_client_section()
        layout.addWidget(client_group)

        # Dane zlecenia/produktu
        order_group = self._create_order_section()
        layout.addWidget(order_group)

        # Tabela produktów
        products_group = self._create_products_table()
        layout.addWidget(products_group)

        # Przyciski akcji
        buttons = self._create_action_buttons()
        layout.addLayout(buttons)

        layout.addStretch()

    def _create_language_section(self) -> QGroupBox:
        """Sekcja wyboru języka"""
        group = QGroupBox("Język dokumentu")
        layout = QHBoxLayout()

        self.lang_group = QButtonGroup()
        self.radio_pl = QRadioButton("Polski")
        self.radio_en = QRadioButton("English")
        self.radio_pl.setChecked(True)

        self.lang_group.addButton(self.radio_pl, 1)
        self.lang_group.addButton(self.radio_en, 2)

        layout.addWidget(self.radio_pl)
        layout.addWidget(self.radio_en)
        layout.addStretch()

        group.setLayout(layout)
        return group

    def _create_client_section(self) -> QGroupBox:
        """Sekcja danych klienta - automatycznie wypełniana z zlecenia"""
        group = QGroupBox("Dane klienta (automatycznie z zlecenia)")
        layout = QFormLayout()

        # Numer klienta (tylko do odczytu, z bazy)
        self.input_client_number = QLineEdit()
        self.input_client_number.setReadOnly(True)
        self.input_client_number.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("Numer klienta:", self.input_client_number)

        # Nazwa klienta (edytowalne)
        self.input_client_name = QLineEdit()
        layout.addRow("Nazwa:", self.input_client_name)

        # Adres klienta (edytowalne)
        self.input_client_address = QLineEdit()
        layout.addRow("Adres:", self.input_client_address)

        # Numer faktury (ręcznie)
        self.input_invoice_number = QLineEdit()
        self.input_invoice_number.setPlaceholderText("np. TSPRZ/151/2025")
        layout.addRow("Nr faktury:", self.input_invoice_number)

        group.setLayout(layout)
        return group

    def _create_order_section(self) -> QGroupBox:
        """Sekcja danych zlecenia/produktu"""
        group = QGroupBox("Dodawanie produktu")
        layout = QFormLayout()

        # Numer zlecenia + przycisk wyszukaj
        order_layout = QHBoxLayout()
        self.input_order_number = QLineEdit()
        self.input_order_number.setPlaceholderText("Numer zlecenia")
        btn_search_order = QPushButton("🔍 Pobierz z bazy")
        btn_search_order.clicked.connect(self._search_order)
        order_layout.addWidget(self.input_order_number)
        order_layout.addWidget(btn_search_order)
        layout.addRow("Numer zlecenia:", order_layout)

        # Kod produktu (edytowalny)
        self.input_product_code = QLineEdit()
        layout.addRow("Kod produktu:", self.input_product_code)

        # Nazwa produktu (edytowalna)
        self.input_product_name = QLineEdit()
        layout.addRow("Nazwa produktu:", self.input_product_name)

        # Data produkcji (edytowalna)
        self.input_production_date = QDateEdit()
        self.input_production_date.setDate(QDate.currentDate())
        self.input_production_date.setCalendarPopup(True)
        layout.addRow("Data produkcji:", self.input_production_date)

        # Ilość (edytowalna)
        self.input_quantity = QLineEdit()
        self.input_quantity.setPlaceholderText("np. 35.400 TMB")
        layout.addRow("Ilość:", self.input_quantity)

        # Nr partii (auto z numeru zlecenia, edytowalny)
        self.input_batch_number = QLineEdit()
        layout.addRow("Nr partii:", self.input_batch_number)

        # Data ważności (auto 12 miesięcy, edytowalna)
        self.input_expiry_date = QLineEdit()
        self.input_expiry_date.setText("12 miesięcy od daty produkcji")
        layout.addRow("Data ważności:", self.input_expiry_date)

        # Przycisk dodaj produkt
        btn_add_product = QPushButton("➕ Dodaj produkt do listy")
        btn_add_product.clicked.connect(self._add_product)
        btn_add_product.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addRow("", btn_add_product)

        group.setLayout(layout)
        return group

    def _create_products_table(self) -> QGroupBox:
        """Tabela z listą produktów"""
        group = QGroupBox("Lista produktów w deklaracji")
        layout = QVBoxLayout()

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels([
            "Kod", "Nazwa", "Data prod.", "Ilość", "Nr partii", "Data ważności", ""
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.products_table)

        group.setLayout(layout)
        return group

    def _create_action_buttons(self) -> QHBoxLayout:
        """Przyciski akcji"""
        layout = QHBoxLayout()
        layout.addStretch()

        btn_clear = QPushButton("🗑️ Wyczyść listę")
        btn_clear.clicked.connect(self._clear_products)
        layout.addWidget(btn_clear)

        btn_preview = QPushButton("👁️ Podgląd HTML")
        btn_preview.clicked.connect(self._preview_html)
        layout.addWidget(btn_preview)

        btn_generate = QPushButton("📄 Generuj PDF")
        btn_generate.clicked.connect(self._generate_pdf)
        btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219150;
            }
        """)
        layout.addWidget(btn_generate)

        return layout

    def _search_order(self):
        """Wyszukuje dane zlecenia w bazie i uzupełnia WSZYSTKIE pola"""
        order_number = self.input_order_number.text().strip()
        if not order_number:
            QMessageBox.warning(self, "Błąd", "Wprowadź numer zlecenia.")
            return

        try:
            order_data = self.db_service.get_order_data(order_number)
            if order_data:
                # === DANE KLIENTA (automatycznie z zlecenia) ===
                self.input_client_number.setText(order_data.get('client_number', ''))
                self.input_client_name.setText(order_data.get('client_name', ''))
                self.input_client_address.setText(order_data.get('client_address', ''))

                # === DANE PRODUKTU ===
                self.input_product_code.setText(order_data['article_index'])
                self.input_product_name.setText(order_data['article_description'])
                self.input_batch_number.setText(order_data['batch_number'])

                # === DATA PRODUKCJI (z bazy, edytowalna) ===
                if order_data.get('production_date'):
                    prod_date = order_data['production_date']
                    # Jeśli to string, konwertuj
                    if isinstance(prod_date, str):
                        from datetime import datetime
                        prod_date = datetime.strptime(prod_date, '%Y-%m-%d').date()
                    self.input_production_date.setDate(QDate(prod_date))

                # === STRUKTURA (do późniejszego użycia) ===
                self.current_product_structure = order_data.get('product_structure', '')

                # === ILOŚĆ - ręcznie, ale można policzyć z bazy (TODO) ===
                if order_data.get('quantity'):
                    self.input_quantity.setText(str(order_data['quantity']))

                QMessageBox.information(
                    self,
                    "Sukces",
                    f"✅ Dane zlecenia załadowane:\n\n"
                    f"Klient: {order_data.get('client_name', 'brak')}\n"
                    f"Produkt: {order_data['article_description']}\n"
                    f"Struktura: {self.current_product_structure}\n"
                    f"Nr partii: {order_data['batch_number']}"
                )
            else:
                QMessageBox.warning(self, "Nie znaleziono", "Brak zlecenia o tym numerze w bazie.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd pobierania danych zlecenia:\n{e}")

    def _add_product(self):
        """Dodaje produkt do listy"""
        # Walidacja
        if not all([
            self.input_product_code.text().strip(),
            self.input_product_name.text().strip(),
            self.input_quantity.text().strip(),
            self.input_batch_number.text().strip()
        ]):
            QMessageBox.warning(self, "Błąd", "Wypełnij wszystkie pola produktu.")
            return

        # Tworzenie ProductBatch
        product = ProductBatch(
            product_code=self.input_product_code.text().strip(),
            product_name=self.input_product_name.text().strip(),
            production_date=self.input_production_date.date().toPyDate(),
            quantity=self.input_quantity.text().strip(),
            batch_number=self.input_batch_number.text().strip(),
            expiry_date=self.input_expiry_date.text().strip()
        )

        self.products.append(product)
        self._update_products_table()

        # Wyczyść pola
        self.input_order_number.clear()
        self.input_product_code.clear()
        self.input_product_name.clear()
        self.input_quantity.clear()
        self.input_batch_number.clear()
        self.input_production_date.setDate(QDate.currentDate())
        self.input_expiry_date.setText("12 miesięcy od daty produkcji")

    def _update_products_table(self):
        """Odświeża tabelę produktów"""
        self.products_table.setRowCount(len(self.products))

        for i, product in enumerate(self.products):
            self.products_table.setItem(i, 0, QTableWidgetItem(product.product_code))
            self.products_table.setItem(i, 1, QTableWidgetItem(product.product_name))
            self.products_table.setItem(i, 2, QTableWidgetItem(product.production_date.strftime("%d.%m.%Y")))
            self.products_table.setItem(i, 3, QTableWidgetItem(product.quantity))
            self.products_table.setItem(i, 4, QTableWidgetItem(product.batch_number))
            self.products_table.setItem(i, 5, QTableWidgetItem(product.expiry_date))

            # Przycisk usuń
            btn_remove = QPushButton("❌")
            btn_remove.clicked.connect(lambda checked, idx=i: self._remove_product(idx))
            self.products_table.setCellWidget(i, 6, btn_remove)

    def _remove_product(self, index: int):
        """Usuwa produkt z listy"""
        if 0 <= index < len(self.products):
            self.products.pop(index)
            self._update_products_table()

    def _clear_products(self):
        """Czyści listę produktów"""
        if self.products:
            reply = QMessageBox.question(
                self, "Potwierdzenie",
                "Czy na pewno wyczyścić całą listę produktów?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.products.clear()
                self._update_products_table()

    def _validate_input(self) -> bool:
        """Waliduje dane przed generowaniem"""
        if not self.input_client_name.text().strip():
            QMessageBox.warning(self, "Błąd", "Wprowadź dane klienta.")
            return False

        if not self.input_invoice_number.text().strip():
            QMessageBox.warning(self, "Błąd", "Wprowadź numer faktury.")
            return False

        if not self.products:
            QMessageBox.warning(self, "Błąd", "Dodaj przynajmniej jeden produkt.")
            return False

        return True

    def _create_declaration(self) -> Declaration:
        """Tworzy obiekt Declaration z danych formularza"""
        declaration = Declaration()
        declaration.language = 'pl' if self.radio_pl.isChecked() else 'en'
        declaration.declaration_type = 'bok'
        declaration.generation_date = date.today()

        # Dane klienta
        declaration.client = ClientData(
            client_code=self.input_client_number.text().strip(),
            client_name=self.input_client_name.text().strip(),
            client_address=self.input_client_address.text().strip(),
            invoice_number=self.input_invoice_number.text().strip()
        )

        # Lista produktów
        declaration.batches = self.products.copy()

        # Dane struktury z pierwszego produktu (jeśli jest)
        if self.products:
            first_product = self.products[0]
            # TODO: Wyciągnij strukturę z product_name lub z bazy
            declaration.product = Product(
                name=first_product.product_name,
                structure=""  # TODO: parsuj ze struktury lub pobierz z bazy
            )

        return declaration

    def _preview_html(self):
        """Podgląd HTML"""
        if not self._validate_input():
            return

        try:
            declaration = self._create_declaration()
            html_path = self.pdf_generator.generate_html(declaration)

            import webbrowser
            webbrowser.open(html_path.as_uri())
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd podglądu:\n{e}")

    def _generate_pdf(self):
        """Generuje PDF"""
        if not self._validate_input():
            return

        try:
            declaration = self._create_declaration()
            pdf_data = self.pdf_generator.generate_pdf_bytes(declaration)

            # Dialog zapisu
            default_filename = f"Deklaracja_BOK_{declaration.client.client_code}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Zapisz deklarację", default_filename, "Pliki PDF (*.pdf)"
            )

            if file_path:
                with open(file_path, 'wb') as f:
                    f.write(pdf_data)

                QMessageBox.information(self, "Sukces", f"Zapisano:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd generowania PDF:\n{e}")

    def refresh_data(self):
        """Odświeża dane (na przyszłość)"""
        pass