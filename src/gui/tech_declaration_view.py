"""
TechDeclarationView - Widok do generowania deklaracji technologicznej/BOK
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QGroupBox,
                             QTextEdit, QMessageBox, QRadioButton, QButtonGroup,
                             QFormLayout, QCheckBox, QFileDialog)
from datetime import date
from src.models.declaration import Declaration, Product
from src.services.pdf_generator import PDFGenerator

class TechDeclarationView(QWidget):
    """Widok do wprowadzania danych i generowania deklaracji"""

    def __init__(self, data_loader):
        super().__init__()
        self.data_loader = data_loader
        self.pdf_generator = PDFGenerator(data_loader)
        self._init_ui()
        self._load_initial_data()

    def _init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Nagłówek
        title = QLabel("Generator Deklaracji Zgodności")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Sekcja wyboru typu i języka
        options_group = self._create_options_section()
        layout.addWidget(options_group)

        # Sekcja danych produktu
        product_group = self._create_product_section()
        layout.addWidget(product_group)

        # Podgląd struktury
        preview_group = self._create_preview_section()
        layout.addWidget(preview_group)

        # Przyciski akcji
        buttons_layout = self._create_action_buttons()
        layout.addLayout(buttons_layout)

        layout.addStretch()

    def _create_options_section(self) -> QGroupBox:
        """Tworzy sekcję wyboru opcji"""
        group = QGroupBox("Opcje dokumentu")
        layout = QVBoxLayout()

        # Wybór języka
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Język:"))

        self.lang_group = QButtonGroup()
        self.radio_pl = QRadioButton("Polski")
        self.radio_en = QRadioButton("English")
        self.radio_pl.setChecked(True)

        self.lang_group.addButton(self.radio_pl, 1)
        self.lang_group.addButton(self.radio_en, 2)

        lang_layout.addWidget(self.radio_pl)
        lang_layout.addWidget(self.radio_en)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # Wybór typu deklaracji
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Typ:"))

        self.type_group = QButtonGroup()
        self.radio_tech = QRadioButton("Technologiczna")
        self.radio_bok = QRadioButton("BOK (z danymi klienta)")
        self.radio_tech.setChecked(True)
        self.radio_bok.setEnabled(False)  # Tymczasowo wyłączone

        self.type_group.addButton(self.radio_tech, 1)
        self.type_group.addButton(self.radio_bok, 2)

        type_layout.addWidget(self.radio_tech)
        type_layout.addWidget(self.radio_bok)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        group.setLayout(layout)
        return group

    def _create_product_section(self) -> QGroupBox:
        """Tworzy sekcję danych produktu"""
        group = QGroupBox("Dane produktu")
        layout = QFormLayout()

        # Nazwa produktu
        self.input_product_name = QLineEdit()
        self.input_product_name.setPlaceholderText("Np. Folia wielowarstwowa laminat OPA/PE...")
        layout.addRow("Nazwa produktu:", self.input_product_name)

        # Wybór materiału 1
        self.combo_material1 = QComboBox()
        self.combo_material1.currentTextChanged.connect(self._update_structure_preview)
        layout.addRow("Materiał 1:", self.combo_material1)

        # Wybór materiału 2
        self.combo_material2 = QComboBox()
        self.combo_material2.currentTextChanged.connect(self._update_structure_preview)
        layout.addRow("Materiał 2:", self.combo_material2)

        # Struktura (auto-generowana)
        self.label_structure = QLabel("")
        self.label_structure.setStyleSheet("font-weight: bold; color: #27ae60;")
        layout.addRow("Struktura:", self.label_structure)

        group.setLayout(layout)
        return group

    def _create_preview_section(self) -> QGroupBox:
        """Tworzy sekcję podglądu"""
        group = QGroupBox("Podgląd substancji dla wybranej struktury")
        layout = QVBoxLayout()

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        layout.addWidget(self.preview_text)

        group.setLayout(layout)
        return group

    def _create_action_buttons(self) -> QHBoxLayout:
        """Tworzy przyciski akcji"""
        layout = QHBoxLayout()
        layout.addStretch()

        btn_preview = QPushButton("👁️ Podgląd HTML")
        btn_preview.clicked.connect(self._preview_html)
        btn_preview.setStyleSheet("padding: 10px 20px; font-size: 14px;")
        layout.addWidget(btn_preview)

        btn_generate = QPushButton("📄 Generuj PDF")
        btn_generate.clicked.connect(self._generate_pdf)
        btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(btn_generate)

        return layout

    def _load_initial_data(self):
        """Ładuje początkowe dane z serwera"""
        try:
            structures = self.data_loader.get_laminate_structures()
            materials = structures.get('materials', [])

            self.combo_material1.addItems(materials)
            self.combo_material2.addItems(materials)

            if len(materials) > 1:
                self.combo_material2.setCurrentIndex(1)

            self._update_structure_preview()
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się załadować danych: {e}")

    def _update_structure_preview(self):
        """Aktualizuje podgląd struktury i substancji"""
        mat1 = self.combo_material1.currentText()
        mat2 = self.combo_material2.currentText()

        if mat1 and mat2:
            structure = f"{mat1}/{mat2}"
            self.label_structure.setText(structure)

            # Pobierz substancje dla tej struktury
            try:
                structures = self.data_loader.get_laminate_structures()
                structure_data = structures.get('structures', {}).get(structure, {})

                if structure_data:
                    substances = structure_data.get('substances', [])
                    dual_use = structure_data.get('dual_use', [])

                    preview = f"Substancje SML: {len(substances)}\n"
                    preview += f"Substancje dual use: {len(dual_use)}\n\n"
                    preview += "Struktura rozpoznana w bazie danych."
                    self.preview_text.setPlainText(preview)
                else:
                    self.preview_text.setPlainText("⚠️ Struktura nie została jeszcze zdefiniowana w bazie danych.")
            except Exception as e:
                self.preview_text.setPlainText(f"Błąd: {e}")

    def _validate_input(self) -> bool:
        """Waliduje dane wejściowe"""
        if not self.input_product_name.text().strip():
            QMessageBox.warning(self, "Błąd", "Wprowadź nazwę produktu.")
            return False

        if not self.label_structure.text():
            QMessageBox.warning(self, "Błąd", "Wybierz materiały struktury.")
            return False

        return True

    def _create_declaration(self) -> Declaration:
        """Tworzy obiekt Declaration z wprowadzonych danych"""
        declaration = Declaration()
        declaration.language = 'pl' if self.radio_pl.isChecked() else 'en'
        declaration.declaration_type = 'tech' if self.radio_tech.isChecked() else 'bok'
        declaration.generation_date = date.today()

        declaration.product = Product(
            name=self.input_product_name.text().strip(),
            structure=self.label_structure.text()
        )

        # Pobierz dane tabel dla struktury
        try:
            structures = self.data_loader.get_laminate_structures()
            structure_data = structures.get('structures', {}).get(declaration.product.structure, {})

            declaration.substances_table = structure_data.get('substances', [])
            declaration.dual_use_list = structure_data.get('dual_use', [])
        except Exception as e:
            QMessageBox.warning(self, "Ostrzeżenie", f"Nie udało się załadować danych struktury: {e}")

        return declaration

    def _preview_html(self):
        """Generuje i otwiera podgląd HTML"""
        if not self._validate_input():
            return

        try:
            declaration = self._create_declaration()
            html_path = self.pdf_generator.generate_html(declaration)

            import webbrowser
            webbrowser.open(html_path.as_uri())
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wygenerować podglądu:\n{e}")

    def _generate_pdf(self):
        """Generuje PDF z możliwością wyboru ścieżki zapisu"""
        if not self._validate_input():
            return

        try:
            declaration = self._create_declaration()

            # Generuj PDF w pamięci (jako bajty)
            pdf_data = self.pdf_generator.generate_pdf_bytes(declaration)

            # Otwórz okno dialogowe "Zapisz jako"
            default_filename = f"Deklaracja_zgodnosci_{declaration.product.name.replace(' ', '_')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Zapisz deklarację jako",
                default_filename,
                "Pliki PDF (*.pdf)"
            )

            # Jeśli użytkownik wybrał ścieżkę (nie kliknął "Anuluj")
            if file_path:
                with open(file_path, 'wb') as f:
                    f.write(pdf_data)
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Deklaracja została zapisana w:\n{file_path}"
                )
            else:
                QMessageBox.information(self, "Anulowano", "Zapisywanie deklaracji zostało anulowane.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wygenerować PDF:\n{e}")

    def refresh_data(self):
        """Odświeża dane z serwera"""
        self._load_initial_data()