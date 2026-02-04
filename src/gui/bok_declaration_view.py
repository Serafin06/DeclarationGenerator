# gui/bok_declaration_view.py

"""
BOKDeclarationView - Widok do generowania deklaracji BOK z danymi z bazy
"""
import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QGroupBox,
                             QMessageBox, QRadioButton, QFormLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QFileDialog, QDateEdit, QCheckBox)
from PyQt5.QtCore import QDate, Qt
from src.models.declaration import Declaration, Product, ClientData, ProductBatch
from src.services.pdf_generator import PDFGenerator
from src.services.database_service import DatabaseService


class BOKDeclarationView(QWidget):
    def __init__(self, data_loader):
        super().__init__()
        self.data_loader = data_loader
        self.db_service = DatabaseService()
        self.products = []
        self.pdf_generator = PDFGenerator(self.data_loader)
        self.available_materials = self.data_loader.get_materials_list()

        self._init_ui()
        self._test_db_connection()
        self._update_laminate_info()  # Wywołanie na start, żeby pole nie było puste

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- SEKCA 1: STATUS I JĘZYK ---
        top_row = QHBoxLayout()
        db_group = QGroupBox("Status Systemu")
        db_l = QHBoxLayout()
        self.label_db_status = QLabel("Sprawdzanie...")
        self.btn_reconnect = QPushButton("🔄 Odśwież połączenie")
        self.btn_reconnect.setFixedWidth(160)  # Ustalona szerokość, żeby nie był za duży
        self.btn_reconnect.clicked.connect(self._reconnect_database)
        db_l.addWidget(self.label_db_status)
        db_l.addWidget(self.btn_reconnect)
        db_group.setLayout(db_l)

        lang_group = QGroupBox("Język Dokumentu")
        lang_l = QHBoxLayout();
        self.radio_pl = QRadioButton("Polski");
        self.radio_pl.setChecked(True);
        self.radio_en = QRadioButton("Angielski")
        lang_l.addWidget(self.radio_pl);
        lang_l.addWidget(self.radio_en);
        lang_group.setLayout(lang_l)
        top_row.addWidget(db_group);
        top_row.addWidget(lang_group);
        layout.addLayout(top_row)

        # --- SEKCJA 2: KLIENT ---
        client_group = QGroupBox("Dane Kontrahenta")
        c_form = QFormLayout()
        search_l = QHBoxLayout();
        self.input_client_id = QLineEdit();
        self.input_client_id.setFixedWidth(70)
        btn_s = QPushButton("🔍");
        btn_s.clicked.connect(self._search_client_dialog)
        search_l.addWidget(self.input_client_id);
        search_l.addWidget(btn_s);
        search_l.addStretch()
        self.input_client_name = QLineEdit();
        self.input_client_addr = QLineEdit();
        self.input_invoice = QLineEdit()
        c_form.addRow("ID / Szukaj:", search_l);
        c_form.addRow("Klient:", self.input_client_name)
        c_form.addRow("Adres:", self.input_client_addr);
        c_form.addRow("Faktura:", self.input_invoice)
        client_group.setLayout(c_form);
        layout.addWidget(client_group)

        # --- SEKCJA 3: STRUKTURA ---
        struct_group = QGroupBox("Specyfikacja Struktury")
        s_layout = QVBoxLayout()
        check_row = QHBoxLayout()
        self.checkbox_auto_structure = QCheckBox("Auto-pobieranie");
        self.checkbox_auto_structure.setChecked(True)
        self.checkbox_trilayer = QCheckBox("Struktura 3-warstwowa");
        self.checkbox_trilayer.toggled.connect(self._toggle_trilayer)
        check_row.addWidget(self.checkbox_auto_structure);
        check_row.addSpacing(20);
        check_row.addWidget(self.checkbox_trilayer);
        check_row.addStretch()
        s_layout.addLayout(check_row)

        mat_layout = QHBoxLayout()
        self.combo_mat1 = QComboBox();
        self.combo_mat2 = QComboBox();
        self.combo_mat3 = QComboBox()
        for c in [self.combo_mat1, self.combo_mat2, self.combo_mat3]:
            c.addItems(self.available_materials)
            c.currentIndexChanged.connect(self._update_laminate_info)  # Odświeżanie przy zmianie

        self.label_mat3 = QLabel("/");
        self.label_mat3.hide();
        self.combo_mat3.hide()
        mat_layout.addWidget(self.combo_mat1);
        mat_layout.addWidget(QLabel("/"));
        mat_layout.addWidget(self.combo_mat2)
        mat_layout.addWidget(self.label_mat3);
        mat_layout.addWidget(self.combo_mat3)
        s_layout.addLayout(mat_layout)

        self.preview_text = QLineEdit();
        self.preview_text.setReadOnly(True);
        self.preview_text.setStyleSheet("background: #f8f9fa; color: #495057;")
        s_layout.addWidget(self.preview_text);
        struct_group.setLayout(s_layout);
        layout.addWidget(struct_group)

        # --- SEKCJA 4: DODAWANIE WYROBU ---
        add_group = QGroupBox("Dodaj Wyrób")
        a_layout = QVBoxLayout()

        # Rząd 1: ZO i Indeks (ZMODYFIKOWANE)
        r1 = QHBoxLayout()

        self.input_zo = QLineEdit()
        self.input_zo.setPlaceholderText("ZO...")
        self.input_zo.setFixedWidth(180)  # Zmniejszone ze standardu, żeby zmieścić przycisk
        self.input_zo.returnPressed.connect(self._search_order)

        # Dodany przycisk wyszukiwania
        self.btn_search_zo = QPushButton("🔍")
        self.btn_search_zo.setFixedWidth(35)
        self.btn_search_zo.setToolTip("Pobierz dane zlecenia")
        self.btn_search_zo.clicked.connect(self._search_order)

        self.input_art_index = QLineEdit()
        self.input_art_index.setReadOnly(True)

        r1.addWidget(QLabel("Zlecenie:"))
        r1.addWidget(self.input_zo)
        r1.addWidget(self.btn_search_zo)  # Przycisk między ZO a Indeksem
        r1.addWidget(QLabel("Indeks:"))
        r1.addWidget(self.input_art_index)
        a_layout.addLayout(r1)

        # Rząd 2: Opis
        r2 = QHBoxLayout();
        self.chk_show_name = QCheckBox();
        self.chk_show_name.setChecked(True)
        self.input_art_desc = QLineEdit()
        r2.addWidget(self.chk_show_name);
        r2.addWidget(QLabel("Opis:"));
        r2.addWidget(self.input_art_desc);
        a_layout.addLayout(r2)

        # Rząd 3: Partia i Ilość
        r3 = QHBoxLayout();
        self.chk_show_batch = QCheckBox();
        self.chk_show_batch.setChecked(True)
        self.input_batch = QLineEdit();
        self.input_batch.setFixedWidth(120)
        self.chk_show_qty = QCheckBox();
        self.chk_show_qty.setChecked(True)
        self.input_qty = QLineEdit();
        self.input_qty.setFixedWidth(80);
        self.combo_unit = QComboBox()
        self.combo_unit.addItems(["mb", "kg"]);
        self.combo_unit.setFixedWidth(60)
        r3.addWidget(self.chk_show_batch);
        r3.addWidget(QLabel("Partia:"));
        r3.addWidget(self.input_batch);
        r3.addSpacing(15)
        r3.addWidget(self.chk_show_qty);
        r3.addWidget(QLabel("Ilość:"));
        r3.addWidget(self.input_qty);
        r3.addWidget(self.combo_unit);
        r3.addStretch()
        a_layout.addLayout(r3)

        # Rząd 4: Data i Grubości
        r4 = QHBoxLayout();
        self.chk_show_date = QCheckBox();
        self.chk_show_date.setChecked(True)
        self.input_date = QDateEdit();
        self.input_date.setCalendarPopup(True);
        self.input_date.setDate(QDate.currentDate())
        self.chk_show_thickness = QCheckBox();
        self.chk_show_thickness.setChecked(True)
        self.input_prod_thick1 = QLineEdit();
        self.input_prod_thick2 = QLineEdit();
        self.input_prod_thick3 = QLineEdit()
        self.label_prod_thick3 = QLabel("/");
        self.input_prod_thick3.hide();
        self.label_prod_thick3.hide()
        for f in [self.input_prod_thick1, self.input_prod_thick2, self.input_prod_thick3]: f.setFixedWidth(35)

        btn_add = QPushButton("➕ DODAJ");
        btn_add.clicked.connect(self._add_product_to_list)
        btn_add.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 5px 15px;")

        r4.addWidget(self.chk_show_date);
        r4.addWidget(QLabel("Data:"));
        r4.addWidget(self.input_date);
        r4.addSpacing(15)
        r4.addWidget(self.chk_show_thickness);
        r4.addWidget(QLabel("Grubości:"));
        r4.addWidget(self.input_prod_thick1);
        r4.addWidget(QLabel("/"))
        r4.addWidget(self.input_prod_thick2);
        r4.addWidget(self.label_prod_thick3);
        r4.addWidget(self.input_prod_thick3);
        r4.addStretch();
        r4.addWidget(btn_add)
        a_layout.addLayout(r4);
        add_group.setLayout(a_layout);
        layout.addWidget(add_group)

        # --- LOGIKA SZARZENIA POL (Bindowanie) ---
        self._setup_checkbox_logic()

        # --- TABELA ---
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Indeks", "Nazwa", "Nr Partii", "Ilość",
            "Struktura", "Grubości", "Data Prod.", "Usuń"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Nazwa niech się rozciąga
        layout.addWidget(self.table)

        # --- DOLNE PRZYCISKI (Poprawiony DOCX i Kosz) ---
        layout.addLayout(self._create_action_buttons())

    def _setup_checkbox_logic(self):
        """Ustawia logikę szarzenia i pamięci wartości dla pól wyrobu"""

        def bind(chk, widgets):
            if not isinstance(widgets, list): widgets = [widgets]

            def toggle(state):
                is_checked = (state == Qt.Checked)
                for w in widgets:
                    if not is_checked:
                        if hasattr(w, 'text'):
                            w._saved = w.text(); w.clear()
                        elif hasattr(w, 'date'):
                            w._saved = w.date()
                        w.setEnabled(False)
                    else:
                        w.setEnabled(True)
                        if hasattr(w, '_saved'):
                            if hasattr(w, 'setText'):
                                w.setText(w._saved)
                            elif hasattr(w, 'setDate'):
                                w.setDate(w._saved)

            chk.stateChanged.connect(toggle)

        bind(self.chk_show_name, self.input_art_desc)
        bind(self.chk_show_batch, self.input_batch)
        bind(self.chk_show_qty, [self.input_qty, self.combo_unit])
        bind(self.chk_show_date, self.input_date)
        bind(self.chk_show_thickness, [self.input_prod_thick1, self.input_prod_thick2, self.input_prod_thick3])

    def _update_laminate_info(self):
        m1, m2 = self.combo_mat1.currentText(), self.combo_mat2.currentText()
        if self.checkbox_trilayer.isChecked():
            m3 = self.combo_mat3.currentText()
            data = self.data_loader.build_structure_data_trilayer(m1, m2, m3)
            s = f"{m1}/{m2}/{m3}"
        else:
            data = self.data_loader.build_structure_data(m1, m2)
            s = f"{m1}/{m2}"

        sm = len(data.get('substances', []))
        du = len(data.get('dual_use', []))
        self.preview_text.setText(f"Struktura: {s} | Substancje SML: {sm} | Dual Use: {du}")

    def _toggle_trilayer(self, checked):
        for w in [self.label_mat3, self.combo_mat3, self.label_prod_thick3, self.input_prod_thick3]:
            w.setVisible(checked)
        self._update_laminate_info()

    def _search_order(self):
        zo = self.input_zo.text().strip()
        if not zo: return

        data = self.db_service.get_order_data(zo)
        if not data:
            QMessageBox.warning(self, "Błąd", f"Nie znaleziono zlecenia: {zo}")
            return

        # Dane produktu - zawsze
        self.input_art_index.setText(str(data.get('article_index', '')))
        self.input_art_desc.setText(data.get('article_description', ''))
        self.input_batch.setText(f"{zo}/{str(datetime.datetime.now().year)[2:]}/ZK")

        db_date = data.get('production_date')
        if db_date:
            self.input_date.setDate(QDate(db_date.year, db_date.month, db_date.day))

        # Grubości z bazy
        t1 = str(data.get('thickness1', '')).strip()
        t2 = str(data.get('thickness2', '')).strip()
        t3 = str(data.get('thickness3', '')).strip()

        # Usuń "0", "None", puste stringi
        if t1 in ["0", "None", ""]: t1 = ""
        if t2 in ["0", "None", ""]: t2 = ""
        if t3 in ["0", "None", ""]: t3 = ""

        # === PIERWSZY PRODUKT - ustaw strukturę i klienta ===
        if not self.products:
            self.input_client_id.setText(str(data.get('client_number', '')))
            self.input_client_name.setText(data.get('client_name', ''))
            self.input_client_addr.setText(" ".join((data.get('client_address') or "").split()))

            db_struct = data.get('product_structure', '').strip()

            if db_struct and self.checkbox_auto_structure.isChecked():
                parts = [p.strip() for p in db_struct.split('/')]

                # Wykryj czy 3-laminat (albo po strukturze albo po thickness3)
                is_trilayer = (len(parts) == 3) or (t3 and t3 not in ["0", "None", ""])

                if is_trilayer:
                    self.checkbox_trilayer.setChecked(True)
                    if len(parts) >= 3:
                        self.combo_mat1.setCurrentText(parts[0])
                        self.combo_mat2.setCurrentText(parts[1])
                        self.combo_mat3.setCurrentText(parts[2])
                    elif len(parts) == 2:
                        # Mamy tylko 2 materiały w strukturze ale thickness3 jest wypełniony
                        self.combo_mat1.setCurrentText(parts[0])
                        self.combo_mat2.setCurrentText(parts[1])
                        # combo_mat3 zostaje domyślny
                else:
                    self.checkbox_trilayer.setChecked(False)
                    if len(parts) >= 2:
                        self.combo_mat1.setCurrentText(parts[0])
                        self.combo_mat2.setCurrentText(parts[1])

                # Komunikat
                struct_info = f"Struktura: {db_struct}"
                if t1 and t2:
                    struct_info += f"\nGrubości: {t1}/{t2}"
                    if is_trilayer and t3:
                        struct_info += f"/{t3}"
                struct_info += "\n\nKolejne zlecenia będą sprawdzane pod kątem zgodności."

                QMessageBox.information(self, "✅ Struktura ustawiona", struct_info)

        # === KOLEJNE PRODUKTY - waliduj strukturę ===
        else:
            db_struct = data.get('product_structure', '').strip()

            # Zbuduj bieżącą strukturę z combo
            m1 = self.combo_mat1.currentText()
            m2 = self.combo_mat2.currentText()
            m3 = self.combo_mat3.currentText()

            if self.checkbox_trilayer.isChecked():
                current_struct = f"{m1}/{m2}/{m3}"
            else:
                current_struct = f"{m1}/{m2}"

            # Porównaj
            if db_struct and db_struct != current_struct:
                reply = QMessageBox.warning(
                    self,
                    "⚠️ Niezgodność struktury",
                    f"Bieżąca struktura: {current_struct}\n"
                    f"Struktura w zleceniu: {db_struct}\n\n"
                    f"Czy kontynuować dodawanie tego wyrobu?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

        # Ustaw grubości (dla każdego produktu osobno)
        self.input_prod_thick1.setText(t1)
        self.input_prod_thick2.setText(t2)
        if self.checkbox_trilayer.isChecked():
            self.input_prod_thick3.setText(t3)

        self._update_laminate_info()

    # --- POZOSTAŁE METODY POMOCNICZE ---
    def _add_product_to_list(self):
        """Dodaje produkt do listy z walidacją pól obowiązkowych"""

        # WALIDACJA - sprawdź czy wymagane pola są wypełnione
        idx = self.input_art_index.text().strip()

        if not idx:
            QMessageBox.warning(self, "Błąd", "Brak indeksu produktu.\nPobierz dane ze zlecenia.")
            return

        # Sprawdź pola z checkboxami
        if self.chk_show_name.isChecked() and not self.input_art_desc.text().strip():
            QMessageBox.warning(self, "Błąd", "Pole 'Opis' jest zaznaczone, ale puste.\nWypełnij lub odznacz checkbox.")
            return

        if self.chk_show_batch.isChecked() and not self.input_batch.text().strip():
            QMessageBox.warning(self, "Błąd",
                                "Pole 'Partia' jest zaznaczone, ale puste.\nWypełnij lub odznacz checkbox.")
            return

        if self.chk_show_qty.isChecked() and not self.input_qty.text().strip():
            QMessageBox.warning(self, "Błąd",
                                "Pole 'Ilość' jest zaznaczone, ale puste.\nWypełnij lub odznacz checkbox.")
            return

        if self.chk_show_thickness.isChecked():
            g1 = self.input_prod_thick1.text().strip()
            g2 = self.input_prod_thick2.text().strip()

            if not g1 or not g2:
                QMessageBox.warning(self, "Błąd",
                                    "Grubości są zaznaczone, ale pola 1 lub 2 są puste.\nWypełnij lub odznacz checkbox.")
                return

            # Sprawdź 3. warstwę tylko jeśli trilayer jest włączony
            if self.checkbox_trilayer.isChecked():
                g3 = self.input_prod_thick3.text().strip()
                if not g3:
                    QMessageBox.warning(self, "Błąd",
                                        "Struktura 3-warstwowa wymaga grubości warstwy 3.\nWypełnij lub odznacz trilayer.")
                    return

        # Pobieranie danych (teraz wiemy że są wypełnione)
        desc = self.input_art_desc.text().strip() if self.chk_show_name.isChecked() else ""
        batch = self.input_batch.text().strip() if self.chk_show_batch.isChecked() else ""
        qty = f"{self.input_qty.text()} {self.combo_unit.currentText()}" if self.chk_show_qty.isChecked() else ""
        date_str = self.input_date.date().toString("yyyy-MM-dd") if self.chk_show_date.isChecked() else ""

        # Budowanie stringu grubości
        g1 = self.input_prod_thick1.text().strip()
        g2 = self.input_prod_thick2.text().strip()
        g3 = self.input_prod_thick3.text().strip() if self.checkbox_trilayer.isChecked() else ""

        thickness_str = ""
        if self.chk_show_thickness.isChecked():
            if self.checkbox_trilayer.isChecked():
                thickness_str = f"{g1}/{g2}/{g3}"
            else:
                thickness_str = f"{g1}/{g2}"

        # Pobranie aktualnej struktury z combo
        m1, m2 = self.combo_mat1.currentText(), self.combo_mat2.currentText()
        struct_str = f"{m1}/{m2}"
        if self.checkbox_trilayer.isChecked():
            struct_str += f"/{self.combo_mat3.currentText()}"

        # Dodanie do listy obiektów
        p = ProductBatch(
            product_code=idx,
            product_name=desc,
            batch_number=batch,
            quantity=qty,
            production_date=self.input_date.date().toPyDate(),
            thickness1=g1,
            thickness2=g2,
            thickness3=g3,
            show_name=self.chk_show_name.isChecked(),
            show_batch=self.chk_show_batch.isChecked(),
            show_quantity=self.chk_show_qty.isChecked(),
            show_production_date=self.chk_show_date.isChecked(),
            show_thickness=self.chk_show_thickness.isChecked()
        )

        # Pola pomocnicze do wyświetlania w tabeli
        p._display_struct = struct_str
        p._display_thick = thickness_str
        p._display_date = date_str

        self.products.append(p)
        self._update_products_table()

        # Czyszczenie pól po dodaniu
        for f in [self.input_zo, self.input_art_index, self.input_art_desc,
                  self.input_batch, self.input_qty, self.input_prod_thick1,
                  self.input_prod_thick2, self.input_prod_thick3]:
            f.clear()

        # Komunikat sukcesu (opcjonalnie)
        self.statusBar().showMessage(f"✅ Dodano: {idx}", 2000) if hasattr(self, 'statusBar') else None

    def _update_products_table(self):
        self.table.setRowCount(len(self.products))
        for i, p in enumerate(self.products):
            self.table.setItem(i, 0, QTableWidgetItem(p.product_code))
            self.table.setItem(i, 1, QTableWidgetItem(p.product_name))
            self.table.setItem(i, 2, QTableWidgetItem(p.batch_number))
            self.table.setItem(i, 3, QTableWidgetItem(p.quantity))
            self.table.setItem(i, 4, QTableWidgetItem(getattr(p, '_display_struct', '')))
            self.table.setItem(i, 5, QTableWidgetItem(getattr(p, '_display_thick', '')))
            self.table.setItem(i, 6, QTableWidgetItem(getattr(p, '_display_date', '')))

            btn = QPushButton("❌")
            btn.setFixedWidth(40)
            btn.clicked.connect(lambda ch, idx=i: (self.products.pop(idx), self._update_products_table()))
            self.table.setCellWidget(i, 7, btn)

    def _create_action_buttons(self):
        l = QHBoxLayout()

        btn_clear = QPushButton("🗑️ WYCZYŚĆ FORMULARZ")
        btn_clear.setStyleSheet("color: #7f8c8d; padding: 8px;")
        btn_clear.clicked.connect(self._clear_all)

        btn_docx = QPushButton("📝 GENERUJ DOCX")
        btn_docx.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 10px 20px;")
        btn_docx.clicked.connect(self._generate_docx)

        btn_pdf = QPushButton("📄 GENERUJ PDF")
        btn_pdf.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px 20px;")
        btn_pdf.clicked.connect(self._generate_pdf)

        l.addWidget(btn_clear)
        l.addStretch()
        l.addWidget(btn_docx)
        l.addWidget(btn_pdf)
        return l

    def _clear_all(self):
        self.products.clear();
        self._update_products_table()
        for f in [self.input_client_name, self.input_client_id, self.input_client_addr, self.input_invoice]: f.clear()

    def _test_db_connection(self):
        res = self.db_service.testConnection()
        self.label_db_status.setText("✅ OK" if res else "❌ Brak")
        self.label_db_status.setStyleSheet(f"color: {'#27ae60' if res else '#e74c3c'}; font-weight: bold;")
        self.btn_reconnect.setEnabled(not res)

    def _reconnect_database(self):
        self.db_service = DatabaseService();
        self._test_db_connection()

    def _validate_input(self):
        """Walidacja przed generowaniem dokumentu"""

        # Sprawdź klienta
        if not self.input_client_name.text().strip():
            QMessageBox.warning(self, "Błąd", "Brak nazwy klienta.")
            return False

        # Sprawdź produkty
        if not self.products:
            QMessageBox.warning(self, "Błąd", "Brak wyrobów.\nDodaj przynajmniej jeden produkt.")
            return False

        # Sprawdź numer faktury
        if not self.input_invoice.text().strip():
            reply = QMessageBox.question(
                self,
                "Brak numeru faktury",
                "Nie podano numeru faktury.\n\nCzy kontynuować bez faktury?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return False

        return True

    def _create_declaration(self) -> Declaration:
        decl = Declaration()
        decl.declaration_type = 'bok'
        decl.language = 'pl' if self.radio_pl.isChecked() else 'en'

        # Dane klienta
        decl.client = ClientData(
            client_code=self.input_client_id.text(),
            client_name=self.input_client_name.text(),
            client_address=self.input_client_addr.text(),
            invoice_number=self.input_invoice.text()
        )

        # Struktura produktu
        m1, m2 = self.combo_mat1.currentText(), self.combo_mat2.currentText()

        if self.checkbox_trilayer.isChecked():
            m3 = self.combo_mat3.currentText()
            decl.product = Product(name=f"{m1}/{m2}/{m3}", structure=f"{m1}/{m2}/{m3}")
            details = self.data_loader.build_structure_data_trilayer(m1, m2, m3)
        else:
            decl.product = Product(name=f"{m1}/{m2}", structure=f"{m1}/{m2}")
            details = self.data_loader.build_structure_data(m1, m2)

        # ✅ NOWY KOD (POPRAWNY):
        decl.substances_table = details.get('substances', [])
        decl.dual_use_list = details.get('dual_use', [])
        decl.batches = self.products.copy()  # <-- To jest lista ProductBatch!

        # === DEBUG (opcjonalnie - możesz usunąć po sprawdzeniu) ===
        print(f"\n=== DEBUG _create_declaration ===")
        print(f"Liczba batches: {len(decl.batches)}")
        print(f"Liczba substances: {len(decl.substances_table)}")
        print(f"Liczba dual_use: {len(decl.dual_use_list)}")
        if decl.batches:
            for i, b in enumerate(decl.batches):
                print(f"  Batch {i}: {b.product_code} | {b.product_name} | {b.batch_number}")
        # === KONIEC DEBUG ===

        return decl

    def _generate_pdf(self):
        if not self._validate_input():
            return

        try:
            decl = self._create_declaration()
            path, _ = QFileDialog.getSaveFileName(self, "Zapisz", f"Deklaracja_{decl.client.client_name}.pdf", "*.pdf")
            if path:
                with open(path, 'wb') as f:
                    f.write(self.pdf_generator.generate_pdf_bytes(decl))
                QMessageBox.information(self, "OK", "Zapisano PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def _generate_docx(self):
        # DODAJ WALIDACJĘ (było tylko: if not self.products: return)
        if not self._validate_input():
            return

        decl = self._create_declaration()
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz DOCX", "", "*.docx")
        if path:
            self.pdf_generator.generate_docx(decl, path)
            QMessageBox.information(self, "Sukces", "Plik DOCX został wygenerowany.")

    def _search_client_dialog(self):
        try:
            from src.gui.support.client_search_dialog import ClientSearchDialog
            from PyQt5.QtWidgets import QDialog
            cls = self.db_service.getAllClients()
            d = ClientSearchDialog(cls, self)
            if d.exec_() == QDialog.Accepted and d.selected_client_id:
                c = cls[d.selected_client_id]
                self.input_client_id.setText(str(d.selected_client_id))
                self.input_client_name.setText(c.get('client_name', ''))
                self.input_client_addr.setText(" ".join((c.get('client_address') or "").split()))
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))
