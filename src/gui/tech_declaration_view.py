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

        # Prefiksy nazw produktów dla języków
        self.product_prefixes = {
            'pl': "Folia wielowarstwowa laminat",
            'en': "Multilayer foil laminate"
        }

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

        # Podgląd substancji
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

        # Połącz zmianę języka z aktualizacją nazwy produktu
        self.radio_pl.toggled.connect(self._update_structure_preview)
        self.radio_en.toggled.connect(self._update_structure_preview)

        self.lang_group.addButton(self.radio_pl, 1)
        self.lang_group.addButton(self.radio_en, 2)

        lang_layout.addWidget(self.radio_pl)
        lang_layout.addWidget(self.radio_en)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        group.setLayout(layout)
        return group

    def _create_product_section(self) -> QGroupBox:
        """Tworzy sekcję danych produktu"""
        group = QGroupBox("Dane produktu")
        layout = QFormLayout()

        # Wybór materiału 1
        self.combo_material1 = QComboBox()
        self.combo_material1.currentTextChanged.connect(self._update_structure_preview)
        layout.addRow("Materiał 1 (zewnętrzny):", self.combo_material1)

        # Wybór materiału 2
        self.combo_material2 = QComboBox()
        self.combo_material2.currentTextChanged.connect(self._update_structure_preview)
        layout.addRow("Materiał 2 (wewnętrzny):", self.combo_material2)

        # Struktura (wyświetlana dla pewności)
        self.label_structure = QLabel("")
        self.label_structure.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        layout.addRow("Zidentyfikowana struktura:", self.label_structure)

        # Nazwa produktu (Auto-generowana, ale edytowalna w razie potrzeby)
        self.input_product_name = QLineEdit()
        self.input_product_name.setStyleSheet("font-weight: bold; color: #2980b9; background-color: #f8f9fa;")
        layout.addRow("Pełna nazwa produktu (pkt 1):", self.input_product_name)

        group.setLayout(layout)
        return group

    def _create_preview_section(self) -> QGroupBox:
        """Tworzy sekcję podglądu substancji"""
        group = QGroupBox("Weryfikacja bazy danych dla struktury")
        layout = QVBoxLayout()

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(120)
        self.preview_text.setStyleSheet("background-color: #fdfefe;")
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

        btn_generate_pdf = QPushButton("📄 Generuj PDF")
        btn_generate_pdf.clicked.connect(self._generate_pdf)
        btn_generate_pdf.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #219150;
            }
        """)
        layout.addWidget(btn_generate_pdf)

        btn_generate_docx = QPushButton("📝 Generuj DOCX")
        btn_generate_docx.clicked.connect(self._generate_docx)
        btn_generate_docx.setStyleSheet("""
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
        layout.addWidget(btn_generate_docx)

        return layout

    def _load_initial_data(self):
        """Ładuje listę materiałów"""
        try:
            materials = self.data_loader.get_materials_list()

            self.combo_material1.clear()
            self.combo_material2.clear()
            self.combo_material1.addItems(materials)
            self.combo_material2.addItems(materials)

            # Ustaw domyślne wartości
            if "PET" in materials:
                self.combo_material1.setCurrentText("PET")
            if "PE" in materials:
                self.combo_material2.setCurrentText("PE")

            self._update_structure_preview()
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie udało się załadować danych: {e}")

    def _update_structure_preview(self):
        """
        Automatycznie aktualizuje nazwę produktu (pkt 1) oraz
        weryfikuje dane struktury w bazie danych.
        """
        try:
            mat1 = self.combo_material1.currentText()
            mat2 = self.combo_material2.currentText()

            if not mat1 or not mat2:
                return

            # Składanie struktury
            structure = f"{mat1}/{mat2}"
            self.label_structure.setText(structure)

            # Automatyczne generowanie nazwy
            lang = 'pl' if self.radio_pl.isChecked() else 'en'
            prefix = self.product_prefixes.get(lang, self.product_prefixes['pl'])
            full_name = f"{prefix} {structure}"
            self.input_product_name.setText(full_name)

            # Pobierz dane struktury (budowane dynamicznie)
            structure_data = self.data_loader.build_structure_data(mat1, mat2)

            substances_count = len(structure_data.get('substances', []))
            dual_use_count = len(structure_data.get('dual_use', []))

            preview = f"✅ Struktura zbudowana: {structure}\n"
            preview += f"Liczba substancji SML (tabela pkt 3): {substances_count}\n"
            preview += f"Substancje Dual Use (pkt 4): {dual_use_count}"
            self.preview_text.setPlainText(preview)

        except Exception as e:
            self.preview_text.setPlainText(f"⚠️ Błąd budowania struktury: {e}")

    def _validate_input(self) -> bool:
        """Waliduje dane przed generowaniem"""
        if not self.input_product_name.text().strip():
            QMessageBox.warning(self, "Błąd", "Nazwa produktu nie może być pusta.")
            return False
        return True

    def _create_declaration(self) -> Declaration:
        """Tworzy model danych dokumentu"""
        declaration = Declaration()
        declaration.language = 'pl' if self.radio_pl.isChecked() else 'en'
        declaration.declaration_type = 'tech'
        declaration.generation_date = date.today()

        # Punkt 1: Nazwa i struktura
        declaration.product = Product(
            name=self.input_product_name.text().strip(),
            structure=self.label_structure.text()
        )

        # Dane tabelaryczne - budowane dynamicznie
        try:
            mat1 = self.combo_material1.currentText()
            mat2 = self.combo_material2.currentText()
            structure_data = self.data_loader.build_structure_data(mat1, mat2)

            declaration.substances_table = structure_data.get('substances', [])
            declaration.dual_use_list = structure_data.get('dual_use', [])
        except Exception as e:
            print(f"Błąd ładowania danych struktury: {e}")
            declaration.substances_table = []
            declaration.dual_use_list = []

        return declaration

    def _preview_html(self):
        if not self._validate_input(): return
        try:
            declaration = self._create_declaration()
            html_path = self.pdf_generator.generate_html(declaration)
            import webbrowser
            webbrowser.open(html_path.as_uri())
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd podglądu: {e}")

    def _generate_pdf(self):
        """Generuje PDF z możliwością wyboru ścieżki zapisu przez użytkownika."""
        if not self._validate_input():
            return

        try:
            declaration = self._create_declaration()
            pdf_data = self.pdf_generator.generate_pdf_bytes(declaration)

            safe_product_name = "".join(c for c in declaration.product.name if c.isalnum() or c in (' ', '-')).rstrip()
            default_filename = f"Deklaracja_{safe_product_name.replace(' ', '_')}.pdf"

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Zapisz deklarację jako",
                default_filename,
                "Pliki PDF (*.pdf)"
            )

            if file_path:
                with open(file_path, 'wb') as f:
                    f.write(pdf_data)

                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Plik PDF został zapisany:\n{file_path}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Błąd generowania PDF",
                f"Nie udało się wygenerować pliku PDF.\n\n"
                f"Szczegóły błędu: {e}"
            )

    def _generate_docx(self):
        """Generuje DOCX z możliwością wyboru ścieżki zapisu przez użytkownika."""
        if not self._validate_input():
            return

        try:
            declaration = self._create_declaration()

            # Przygotuj domyślną nazwę pliku
            safe_product_name = "".join(c for c in declaration.product.name if c.isalnum() or c in (' ', '-')).rstrip()
            default_filename = f"Deklaracja_{safe_product_name.replace(' ', '_')}.docx"

            # Otwórz dialog "Zapisz jako"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Zapisz deklarację jako",
                default_filename,
                "Pliki Word (*.docx)"
            )

            # Jeśli użytkownik wybrał ścieżkę
            if file_path:
                # Wygeneruj DOCX w pamięci
                html_content = self.pdf_generator.generate_html_content(declaration)

                from bs4 import BeautifulSoup
                from docx import Document
                from docx.shared import Inches, Pt
                from docx.enum.text import WD_ALIGN_PARAGRAPH

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
            QMessageBox.critical(
                self,
                "Błąd generowania DOCX",
                f"Nie udało się wygenerować pliku DOCX.\n\n"
                f"Szczegóły błędu: {e}"
            )

    def refresh_data(self):
        self._load_initial_data()