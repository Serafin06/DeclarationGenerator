# gui/bok_declaration_view.py

"""
BOKDeclarationView - Widok do generowania deklaracji BOK z danymi z bazy
"""
import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QGroupBox,
                             QMessageBox, QRadioButton, QButtonGroup,
                             QFormLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFileDialog, QDateEdit, QTextEdit, QCheckBox)
from PyQt5.QtCore import QDate, Qt  # Dodano Qt do obsługi klawisza Enter
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
        self.products = []
        self.pdf_generator = PDFGenerator(self.data_loader)

        self.structure_locked = False
        self.available_materials = self.data_loader.get_materials_list()

        # Dane struktury z pierwszego zlecenia
        self.structure_from_db = None  # Słownik z danymi struktury

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

        # Wyszukiwanie klienta
        search_client_layout = QHBoxLayout()
        self.input_client_id = QLineEdit()
        self.input_client_id.setFixedWidth(100)
        btn_search_client = QPushButton("🔍 Wyszukaj")
        btn_search_client.clicked.connect(self._search_client_dialog)
        search_client_layout.addWidget(self.input_client_id)
        search_client_layout.addWidget(btn_search_client)
        search_client_layout.addStretch()

        self.input_client_name = QLineEdit()
        self.input_client_addr = QLineEdit()
        self.input_invoice = QLineEdit()
        self.input_invoice.setPlaceholderText("np. TSPRZ/...")

        c_layout.addRow("ID Klienta:", search_client_layout)
        c_layout.addRow("Klient:", self.input_client_name)
        c_layout.addRow("Adres:", self.input_client_addr)
        c_layout.addRow("Nr faktury:", self.input_invoice)
        client_group.setLayout(c_layout)
        layout.addWidget(client_group)

        # --- SEKCJA 3: SPECYFIKACJA LAMINATU ---
        struct_group = QGroupBox("Specyfikacja Struktury")
        s_layout = QFormLayout()

        # Checkbox trilayer
        self.checkbox_trilayer = QCheckBox("Struktura 3-warstwowa")
        self.checkbox_trilayer.toggled.connect(self._toggle_trilayer)
        s_layout.addRow("", self.checkbox_trilayer)

        # Materiały
        lam_layout = QHBoxLayout()
        self.combo_mat1 = QComboBox()
        self.combo_mat1.addItems(self.available_materials)
        self.combo_mat2 = QComboBox()
        self.combo_mat2.addItems(self.available_materials)
        self.combo_mat3 = QComboBox()
        self.combo_mat3.addItems(self.available_materials)

        self.combo_mat1.currentTextChanged.connect(self._update_laminate_info)
        self.combo_mat2.currentTextChanged.connect(self._update_laminate_info)
        self.combo_mat3.currentTextChanged.connect(self._update_laminate_info)

        self.label_mat3 = QLabel("/")
        self.label_mat3.setVisible(False)
        self.combo_mat3.setVisible(False)

        lam_layout.addWidget(self.combo_mat1)
        lam_layout.addWidget(QLabel("/"))
        lam_layout.addWidget(self.combo_mat2)
        lam_layout.addWidget(self.label_mat3)
        lam_layout.addWidget(self.combo_mat3)
        s_layout.addRow("Materiały:", lam_layout)

        # Grubości
        thick_layout = QHBoxLayout()
        self.input_thick1 = QLineEdit()
        self.input_thick1.setPlaceholderText("12")
        self.input_thick1.setFixedWidth(60)
        self.input_thick2 = QLineEdit()
        self.input_thick2.setPlaceholderText("40")
        self.input_thick2.setFixedWidth(60)
        self.input_thick3 = QLineEdit()
        self.input_thick3.setPlaceholderText("50")
        self.input_thick3.setFixedWidth(60)
        self.input_thick3.setVisible(False)

        thick_layout.addWidget(self.input_thick1)
        thick_layout.addWidget(QLabel("/"))
        thick_layout.addWidget(self.input_thick2)
        self.label_thick3 = QLabel("/")
        self.label_thick3.setVisible(False)
        thick_layout.addWidget(self.label_thick3)
        thick_layout.addWidget(self.input_thick3)
        thick_layout.addWidget(QLabel("μm"))
        thick_layout.addStretch()
        s_layout.addRow("Grubości warstw:", thick_layout)

        # Auto-uzupełnianie
        self.checkbox_auto_structure = QCheckBox("Auto-uzupełnij strukturę i grubości z pierwszego zlecenia")
        self.checkbox_auto_structure.setChecked(True)
        s_layout.addRow("", self.checkbox_auto_structure)

        # Podgląd substancji
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
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
        # ZMIANA 1: Dodanie obsługi klawisza Enter
        self.input_zo.returnPressed.connect(self._search_order)
        btn_fetch = QPushButton("🔍 Pobierz");
        btn_fetch.clicked.connect(self._search_order)
        search_layout.addWidget(self.input_zo);
        search_layout.addWidget(btn_fetch)

        self.input_art_index = QLineEdit();
        self.input_art_index.setReadOnly(True)
        self.input_art_desc = QLineEdit()
        self.input_batch = QLineEdit()
        qty_layout = QHBoxLayout()
        self.input_qty = QLineEdit()
        self.combo_unit = QComboBox()
        self.combo_unit.addItems(["mb", "kg"])
        self.combo_unit.setFixedWidth(60)
        qty_layout.addWidget(self.input_qty)
        qty_layout.addWidget(self.combo_unit)
        self.input_date = QDateEdit()
        self.input_date.setCalendarPopup(True)
        self.input_date.setDate(QDate.currentDate())

        a_layout.addRow("Zlecenie:", search_layout)
        a_layout.addRow("Indeks artykułu:", self.input_art_index)
        a_layout.addRow("Opis produktu:", self.input_art_desc)
        a_layout.addRow("Nr partii:", self.input_batch)
        a_layout.addRow("Data produkcji:", self.input_date)
        a_layout.addRow("Ilość:", qty_layout)

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

    def _clean_address(self, address):
        """Usuwa zbędne spacje z adresu"""
        if not address:
            return address
        # Zamień wiele spacji na jedną i usuń spacje na początku i końcu
        return ' '.join(address.split())

    def _search_order(self):
        """Pobiera dane z bazy i uzupełnia pola"""
        zo = self.input_zo.text().strip()
        data = self.db_service.get_order_data(zo)

        if not data:
            QMessageBox.warning(self, "Błąd", "Nie znaleziono zlecenia.")
            return

        # Data produkcji
        db_date = data.get('production_date')
        if db_date:
            self.input_date.setDate(QDate(db_date.year, db_date.month, db_date.day))

        # === PIERWSZY PRODUKT - uzupełnij klienta i strukturę ===
        if not self.products:
            self.input_client_id.setText(str(data['client_number']))
            self.input_client_name.setText(data['client_name'])
            self.input_client_addr.setText(self._clean_address(data['client_address']))

            # Parsuj strukturę z bazy
            db_struct = data.get('product_structure', '')  # TODO: zamień na właściwą nazwę kolumny

            # TODO: Dodaj nazwy kolumn z grubościami
            thick1 = data.get('COLUMN_NAME_THICK1')  # <- TUTAJ WPISZ NAZWĘ KOLUMNY
            thick2 = data.get('COLUMN_NAME_THICK2')  # <- TUTAJ WPISZ NAZWĘ KOLUMNY
            thick3 = data.get('COLUMN_NAME_THICK3')  # <- TUTAJ WPISZ NAZWĘ KOLUMNY (opcjonalnie)

            if db_struct and "/" in db_struct:
                parts = db_struct.split('/')

                # Sprawdź czy 2-laminat czy 3-laminat
                is_trilayer = len(parts) == 3

                if self.checkbox_auto_structure.isChecked():
                    # Ustaw materiały
                    self.combo_mat1.setCurrentText(parts[0].strip())
                    self.combo_mat2.setCurrentText(parts[1].strip())

                    if is_trilayer:
                        self.checkbox_trilayer.setChecked(True)
                        self.combo_mat3.setCurrentText(parts[2].strip())

                    # Ustaw grubości
                    if thick1:
                        self.input_thick1.setText(str(thick1))
                    if thick2:
                        self.input_thick2.setText(str(thick2))
                    if thick3 and is_trilayer:
                        self.input_thick3.setText(str(thick3))

                    self.structure_locked = True

                    struct_info = f"{db_struct} {thick1}/{thick2}"
                    if is_trilayer and thick3:
                        struct_info += f"/{thick3}"
                    struct_info += " μm"

                    QMessageBox.information(
                        self,
                        "Struktura ustawiona",
                        f"Struktura: {struct_info}\n\nKolejne zlecenia będą sprawdzane."
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Struktura w bazie",
                        f"W bazie: {db_struct}\n\nAuto-uzupełnianie wyłączone."
                    )

        # === KOLEJNE PRODUKTY - sprawdź strukturę ===
        else:
            db_struct = data.get('product_structure', '')

            if self.checkbox_trilayer.isChecked():
                current_struct = f"{self.combo_mat1.currentText()}/{self.combo_mat2.currentText()}/{self.combo_mat3.currentText()}"
            else:
                current_struct = f"{self.combo_mat1.currentText()}/{self.combo_mat2.currentText()}"

            if db_struct and db_struct.strip() != current_struct:
                reply = QMessageBox.warning(
                    self,
                    "⚠️ Niezgodność struktury",
                    f"Bieżąca: {current_struct}\nW bazie: {db_struct}\n\nKontynuować?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

        # Dane produktu
        self.input_art_index.setText(str(data['article_index']))
        self.input_art_desc.setText(data['article_description'])
        year = str(datetime.datetime.now().year)[2:]
        self.input_batch.setText(f"{zo}/{year}/ZK")

    def _add_product_to_list(self):
        """Przenosi dane z pól do tabeli i czyści pola zlecenia"""
        idx = self.input_art_index.text().strip()
        desc = self.input_art_desc.text().strip()
        batch = self.input_batch.text().strip()
        qty = self.input_qty.text().strip()
        unit = self.combo_unit.currentText()

        if not all([idx, desc, batch, qty]):
            QMessageBox.warning(self, "Błąd", "Wypełnij dane wyrobu przed dodaniem.")
            return

        product = ProductBatch(
            product_code=idx,
            product_name=desc,
            batch_number=batch,
            quantity=f"{qty} {unit}",
            production_date=self.input_date.date().toPyDate(),
            expiry_date="12 miesięcy"
        )
        self.products.append(product)
        self._update_products_table()

        # Czyścimy pola zlecenia
        self.input_zo.clear()
        self.input_art_index.clear()
        self.input_art_desc.clear()
        self.input_batch.clear()
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
        """Aktualizuje podgląd struktury"""
        m1 = self.combo_mat1.currentText()
        m2 = self.combo_mat2.currentText()

        if self.checkbox_trilayer.isChecked():
            m3 = self.combo_mat3.currentText()
            if not m3:
                return
            data = self.data_loader.build_structure_data_trilayer(m1, m2, m3)
            structure = f"{m1}/{m2}/{m3}"
        else:
            data = self.data_loader.build_structure_data(m1, m2)
            structure = f"{m1}/{m2}"

        self.preview_text.setPlainText(
            f"Struktura: {structure}\nSML: {len(data['substances'])} | Dual: {len(data['dual_use'])}"
        )

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
        self.input_client_addr.clear();

    def _create_declaration(self) -> Declaration:
        """Zbiera wszystkie dane z GUI do jednego obiektu modelu"""
        declaration = Declaration()
        declaration.language = 'pl' if self.radio_pl.isChecked() else 'en'
        declaration.declaration_type = 'bok'
        declaration.generation_date = date.today()

        # Dane klienta
        declaration.client = ClientData(
            client_code=self.input_client_id.text().strip(),
            client_name=self.input_client_name.text().strip(),
            client_address=self.input_client_addr.text().strip(),
            invoice_number=self.input_invoice.text().strip()
        )

        # Struktura z grubościami
        m1 = self.combo_mat1.currentText()
        m2 = self.combo_mat2.currentText()
        t1 = self.input_thick1.text().strip()
        t2 = self.input_thick2.text().strip()

        if self.checkbox_trilayer.isChecked():
            m3 = self.combo_mat3.currentText()
            t3 = self.input_thick3.text().strip()
            structure_str = f"{m1}/{m2}/{m3}"
            thickness_str = f"{t1}/{t2}/{t3} μm" if all([t1, t2, t3]) else ""
            structure_details = self.data_loader.build_structure_data_trilayer(m1, m2, m3)
        else:
            structure_str = f"{m1}/{m2}"
            thickness_str = f"{t1}/{t2} μm" if t1 and t2 else ""
            structure_details = self.data_loader.build_structure_data(m1, m2)

        # Pełna nazwa ze strukturą i grubościami
        full_structure = f"{structure_str} {thickness_str}".strip()

        declaration.product = Product(
            name=full_structure,  # np. "PET/PE 12/40 μm"
            structure=structure_str
        )

        declaration.substances_table = structure_details.get('substances', [])
        declaration.dual_use_list = structure_details.get('dual_use', [])
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
        """Generuje DOCX z możliwością wyboru lokalizacji zapisu"""
        if not self._validate_input():
            return

        try:
            decl = self._create_declaration()

            # Przygotuj domyślną nazwę pliku
            safe_name = "".join(c for c in decl.client.client_name if c.isalnum() or c in (' ', '-')).rstrip()
            default_filename = f"Deklaracja_BOK_{safe_name}.docx"

            # Dialog wyboru ścieżki
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Zapisz deklarację DOCX",
                default_filename,
                "Pliki Word (*.docx)"
            )

            if not file_path:
                return  # Użytkownik anulował

            # Generuj HTML
            html_content = self.pdf_generator.generate_html_content(decl)

            # Konwertuj na DOCX
            from bs4 import BeautifulSoup
            from docx import Document
            from docx.shared import Inches

            soup = BeautifulSoup(html_content, 'html.parser')
            doc = Document()

            # Ustaw marginesy
            for section in doc.sections:
                section.top_margin = Inches(0.59)
                section.bottom_margin = Inches(0.59)
                section.left_margin = Inches(0.59)
                section.right_margin = Inches(0.59)

            # Przetwórz HTML
            body = soup.find('body')
            if body:
                self.pdf_generator._process_html_to_docx(doc, body)

            # Zapisz w wybranej lokalizacji
            doc.save(file_path)

            QMessageBox.information(
                self,
                "Sukces",
                f"Plik DOCX został zapisany:\n{file_path}"
            )

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Błąd DOCX:\n{error_details}")
            QMessageBox.critical(self, "Błąd DOCX", f"Szczegóły: {str(e)}")

    def _search_client_dialog(self):
        """Otwiera dialog wyszukiwania klienta"""
        try:
            from PyQt5.QtWidgets import QDialog
            from src.gui.support.client_search_dialog import ClientSearchDialog

            clients_dict = self.db_service.getAllClients()

            if not clients_dict:
                QMessageBox.warning(self, "Brak danych", "Nie znaleziono klientów w bazie.")
                return

            dialog = ClientSearchDialog(clients_dict, self)

            if dialog.exec_() == QDialog.Accepted and dialog.selected_client_id:
                client_data = clients_dict[dialog.selected_client_id]
                self.input_client_id.setText(str(dialog.selected_client_id))
                # Zabezpieczamy się również tutaj na wypadek, gdyby dane w słowniku były None
                self.input_client_name.setText(client_data.get('client_name') or '')
                self.input_client_addr.setText(self._clean_address(client_data.get('client_address') or ''))

        except Exception as e:
            # W razie dalszych problemów, dodajemy pełny ślad błędu do konsoli
            import traceback
            print("Błąd w wyszukiwaniu klienta:")
            traceback.print_exc()
            QMessageBox.critical(self, "Błąd", f"Błąd wyszukiwania klienta:\n{e}")

    def _validate_input(self):
        """Sprawdza czy wszystkie wymagane dane są uzupełnione"""
        if not self.input_client_name.text().strip():
            QMessageBox.warning(self, "Błąd", "Wypełnij dane klienta.")
            return False

        if not self.input_invoice.text().strip():
            QMessageBox.warning(self, "Błąd", "Wpisz numer faktury.")
            return False

        if not self.products:
            QMessageBox.warning(self, "Błąd", "Dodaj przynajmniej jeden produkt.")
            return False

        return True

    def _toggle_trilayer(self, checked: bool):
        """Pokazuje/ukrywa trzecią warstwę"""
        self.label_mat3.setVisible(checked)
        self.combo_mat3.setVisible(checked)
        self.label_thick3.setVisible(checked)
        self.input_thick3.setVisible(checked)
        self._update_laminate_info()