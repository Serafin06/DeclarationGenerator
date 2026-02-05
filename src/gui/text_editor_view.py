"""
TextEditorView - Edytor szablonów HTML deklaracji
Pozwala edytować pełne szablony HTML dla PL i EN
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QMessageBox, QComboBox,
                             QGroupBox, QSplitter, QCheckBox, QStackedWidget)
from PyQt5.QtCore import Qt
from src.config.constants import TEXTS_PL, TEXTS_EN
from pathlib import Path


class TextEditorView(QWidget):
    """
    Widok do edycji szablonów HTML i JSONów tekstowych.
    Obsługuje:
    - Szablony HTML (tech_declaration_pl.html, tech_declaration_en.html)
    - JSONy tekstowe (texts_pl.json, texts_en.json)
    """

    def __init__(self, data_loader):
        super().__init__()
        self.data_loader = data_loader
        self.has_unsaved_changes = False

        # Import wszystkich potrzebnych stałych
        from src.config.constants import (
            TEMPLATES_PATH, TEXTS_PL, TEXTS_EN,
            TEMPLATE_PL_TECH, TEMPLATE_EN_TECH,
            TEMPLATE_PL_BOK, TEMPLATE_EN_BOK
        )

        self.templates_path = TEMPLATES_PATH
        self.texts_pl = TEXTS_PL
        self.texts_en = TEXTS_EN

        # Mapa plików
        self.file_map = {
            ('html_tech', 'pl'): TEMPLATE_PL_TECH,
            ('html_tech', 'en'): TEMPLATE_EN_TECH,
            ('html_bok', 'pl'): TEMPLATE_PL_BOK,
            ('html_bok', 'en'): TEMPLATE_EN_BOK,
            ('json', 'pl'): TEXTS_PL,
            ('json', 'en'): TEXTS_EN,
        }

        self.has_unsaved_changes = False

        self._init_ui()
        self._load_content()

    def _init_ui(self):
        """Inicjalizuje interfejs"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Nagłówek
        header = QLabel("📝 Edytor Tekstów Deklaracji")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        # Wybór pliku
        controls_group = QGroupBox("Wybierz plik do edycji")
        controls_layout = QVBoxLayout()

        # Rząd 1: Typ dokumentu
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Typ deklaracji:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems([
            "Teksty JSON (punkty deklaracji)",
            "Szablon HTML - Technologiczna",
            "Szablon HTML - BOK"
        ])
        self.combo_type.currentTextChanged.connect(self._on_type_changed)
        row1.addWidget(self.combo_type, stretch=1)
        controls_layout.addLayout(row1)

        # Rząd 2: Język + Info + Tryb
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Język:"))
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Polski", "English"])
        self.combo_lang.currentTextChanged.connect(self._on_type_changed)
        row2.addWidget(self.combo_lang)
        row2.addSpacing(20)

        self.label_file_info = QLabel()
        self.label_file_info.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        row2.addWidget(self.label_file_info, stretch=1)

        # Przełącznik trybu (tylko dla JSON)
        self.checkbox_visual_mode = QCheckBox("Tryb wizualny (sekcje)")
        self.checkbox_visual_mode.setChecked(True)
        self.checkbox_visual_mode.toggled.connect(self._toggle_editor_mode)
        row2.addWidget(self.checkbox_visual_mode)

        controls_layout.addLayout(row2)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # === STACKED WIDGET dla dwóch trybów ===
        self.editor_stack = QStackedWidget()

        # TRYB 1: Edytor surowy (dla HTML i JSON w trybie zaawansowanym)
        raw_widget = QWidget()
        raw_layout = QVBoxLayout(raw_widget)
        raw_layout.setContentsMargins(0, 0, 0, 0)

        raw_group = QGroupBox("Edytor (tryb surowy)")
        raw_editor_layout = QVBoxLayout()
        self.text_editor = QTextEdit()
        self.text_editor.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.5;
                padding: 10px;
                background-color: #fdfefe;
                border: 1px solid #bdc3c7;
            }
        """)
        self.text_editor.textChanged.connect(self._mark_as_modified)
        raw_editor_layout.addWidget(self.text_editor)
        raw_group.setLayout(raw_editor_layout)
        raw_layout.addWidget(raw_group)

        # TRYB 2: Edytor wizualny (tylko dla JSON)
        visual_widget = QWidget()
        visual_layout = QVBoxLayout(visual_widget)
        visual_layout.setContentsMargins(0, 0, 0, 0)

        visual_group = QGroupBox("Edytor (tryb wizualny - sekcje)")
        visual_editor_layout = QVBoxLayout()

        from PyQt5.QtWidgets import QScrollArea, QFormLayout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #bdc3c7; background: #fdfefe; }")

        scroll_content = QWidget()
        self.visual_form_layout = QFormLayout(scroll_content)
        self.visual_form_layout.setSpacing(10)
        self.visual_fields = {}  # Przechowuje QTextEdit dla każdego klucza

        scroll.setWidget(scroll_content)
        visual_editor_layout.addWidget(scroll)
        visual_group.setLayout(visual_editor_layout)
        visual_layout.addWidget(visual_group)

        # Dodaj oba tryby do stacka
        self.editor_stack.addWidget(raw_widget)  # index 0
        self.editor_stack.addWidget(visual_widget)  # index 1

        layout.addWidget(self.editor_stack, stretch=1)

        # Pomoc kontekstowa
        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        self.help_label.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                padding: 10px;
                border-left: 4px solid #3498db;
                color: #2c3e50;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.help_label)

        # Przyciski
        buttons_layout = QHBoxLayout()

        btn_reload = QPushButton("🔄 Cofnij zmiany")
        btn_reload.clicked.connect(self._reload_current)
        btn_reload.setStyleSheet("padding: 8px 15px;")

        btn_save = QPushButton("💾 ZAPISZ")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 30px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        btn_save.clicked.connect(self._save_content)

        buttons_layout.addWidget(btn_reload)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_save)
        layout.addLayout(buttons_layout)

        # Ustaw początkowy stan
        self._on_type_changed()

    def _on_type_changed(self):
        """Reaguje na zmianę wyboru pliku"""
        file_type = self._get_file_type()

        # Pokaż/ukryj checkbox trybu wizualnego
        is_json = (file_type == 'json')
        self.checkbox_visual_mode.setVisible(is_json)

        # Aktualizuj info o pliku
        file_path = self._get_current_file_path()
        exists = "✅" if file_path.exists() else "⚠️ (zostanie utworzony)"
        self.label_file_info.setText(f"Plik: {file_path.name} {exists}")

        # Aktualizuj pomoc
        if file_type == 'json':
            self.help_label.setText(
                "💡 TEKSTY JSON - Wybierz tryb:\n"
                "• Wizualny: Edytuj każdą sekcję osobno (łatwiejsze)\n"
                "• Surowy: Edytuj cały plik JSON (zaawansowane)"
            )
        elif file_type == 'html_tech':
            self.help_label.setText(
                "💡 SZABLON HTML - Edytujesz szablon deklaracji Technologicznej.\n"
                "Zmienne: {{ product.name }}, {{ texts.regulations.eu_10_2011 }}, itp."
            )
        else:  # html_bok
            self.help_label.setText(
                "💡 SZABLON HTML - Edytujesz szablon deklaracji BOK.\n"
                "Zmienne: {{ client.client_name }}, {{ batches }}, itp."
            )

        # Załaduj odpowiedni tryb
        self._toggle_editor_mode()

    def _get_file_type(self) -> str:
        """Zwraca typ pliku: 'json', 'html_tech', 'html_bok'"""
        selected = self.combo_type.currentText()
        if "JSON" in selected:
            return 'json'
        elif "Technologiczna" in selected:
            return 'html_tech'
        else:
            return 'html_bok'

    def _get_current_file_path(self) -> Path:
        """Zwraca ścieżkę do aktualnie wybranego pliku"""
        file_type = self._get_file_type()
        lang = 'pl' if 'Polski' in self.combo_lang.currentText() else 'en'
        return self.file_map.get((file_type, lang))

    def _load_content(self):
        """Ładuje zawartość wybranego pliku"""
        try:
            file_path = self._get_current_file_path()

            if not file_path.exists():
                self.text_editor.setPlainText(
                    f"# Plik jeszcze nie istnieje.\n"
                    f"# Lokalizacja: {file_path}\n"
                    f"# Zostanie utworzony po pierwszym zapisie.\n\n"
                )
                self.has_unsaved_changes = False
                return

            is_json = self._get_file_type() == 'json'

            if is_json:
                import json
                data = self.data_loader.load_json(file_path)
                content = json.dumps(data, ensure_ascii=False, indent=2)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            self.text_editor.setPlainText(content)
            self.has_unsaved_changes = False

        except Exception as e:
            QMessageBox.warning(self, "Błąd odczytu", f"Nie można załadować pliku:\n{e}")
            self.text_editor.setPlainText(f"# Błąd: {e}")

    def _reload_current(self):
        """Przeładowuje plik bez zapisywania"""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Cofnij zmiany",
                "Masz niezapisane zmiany.\n\nCzy na pewno chcesz je odrzucić?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        file_path = self._get_current_file_path()
        if self._get_file_type() == 'json':
            self.data_loader.reload(file_path)

        self._load_content()

    def _save_content(self):
        """Zapisuje zawartość do pliku"""
        try:
            file_path = self._get_current_file_path()
            is_json = self._get_file_type() == 'json'

            # Pobierz zawartość
            if is_json and self.checkbox_visual_mode.isChecked():
                # Tryb wizualny - zbierz dane z pól
                import json
                original_data = self.data_loader.load_json(file_path) if file_path.exists() else {}

                for full_key, field_widget in self.visual_fields.items():
                    value = field_widget.toPlainText().strip()

                    if '.' in full_key:
                        # Zagnieżdżony klucz (np. "regulations.eu_10_2011")
                        section, key = full_key.split('.', 1)
                        if section not in original_data:
                            original_data[section] = {}
                        original_data[section][key] = value
                    else:
                        # Klucz prosty (np. "final_note")
                        original_data[full_key] = value

                content = json.dumps(original_data, ensure_ascii=False, indent=2)
            else:
                # Tryb surowy
                content = self.text_editor.toPlainText()

            # Walidacja
            if not content.strip():
                QMessageBox.warning(self, "Błąd", "Plik nie może być pusty.")
                return

            if is_json:
                # Walidacja JSON
                import json
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    QMessageBox.critical(
                        self,
                        "Błędna składnia JSON",
                        f"Znaleziono błąd w linii {e.lineno}:\n{e.msg}\n\n"
                        "Popraw błędy przed zapisem."
                    )
                    return

                self.data_loader.save_json(file_path, data)
            else:
                # HTML - walidacja podstawowa
                if '{{' in content and '}}' not in content:
                    reply = QMessageBox.warning(
                        self,
                        "Ostrzeżenie",
                        "Znaleziono otwierający {{ bez zamknięcia }}.\n\n"
                        "Czy na pewno zapisać?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return

                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            self.has_unsaved_changes = False
            QMessageBox.information(
                self,
                "✅ Zapisano",
                f"Plik został zapisany:\n{file_path.name}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu", f"Nie udało się zapisać:\n{e}")

    def _mark_as_modified(self):
        """Oznacza dokument jako zmodyfikowany"""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True

    def _toggle_editor_mode(self):
        """Przełącza między trybem wizualnym a surowym"""
        file_type = self._get_file_type()

        if file_type == 'json' and self.checkbox_visual_mode.isChecked():
            # Przejdź do trybu wizualnego
            self.editor_stack.setCurrentIndex(1)
            self._load_visual_editor()
        else:
            # Przejdź do trybu surowego
            self.editor_stack.setCurrentIndex(0)
            self._load_content()


    def _load_visual_editor(self):
        """Ładuje JSON jako formularz z polami"""
        try:
            file_path = self._get_current_file_path()

            if not file_path.exists():
                return

            import json
            data = self.data_loader.load_json(file_path)

            # Wyczyść poprzednie pola
            for i in reversed(range(self.visual_form_layout.count())):
                widget = self.visual_form_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            self.visual_fields.clear()

            # Definicje przyjaznych nazw
            section_names = {
                'regulations': '📜 Regulacje prawne',
                'statements': '✅ Oświadczenia zgodności',
                'final_note': '📝 Notatka końcowa'
            }

            field_names = {
                'eu_10_2011': 'Rozporządzenie UE 10/2011',
                'eu_1935_2004': 'Rozporządzenie UE 1935/2004',
                'eu_2023_2006': 'Rozporządzenie UE 2023/2006',
                'eu_2022_1616': 'Rozporządzenie UE 2022/1616',
                'directive_94_62': 'Dyrektywa 94/62/WE',
                'eu_1895_2005': 'Rozporządzenie UE 1895/2005',
                'pl_product_safety': 'Ustawa o bezpieczeństwie produktów',
                'pl_food_safety': 'Ustawa o bezpieczeństwie żywności',
                'pl_waste': 'Ustawa o odpadach',
                'pl_packaging': 'Ustawa o opakowaniach',
                'materials_compliance': 'Zgodność materiałów',
                'allowed_substances': 'Dozwolone substancje',
                'migration_limits': 'Limity migracji',
                'migration_test': 'Test migracji globalnej',
                'nias_available': 'Dostępność NIAS',
                'printing_inks': 'Farby drukarskie',
                'no_bisphenol': 'Brak bisfenoli',
                'reach_compliance': 'Zgodność z REACH',
                'heavy_metals': 'Metale ciężkie',
                'food_contact_conditions': 'Warunki kontaktu z żywnością'
            }

            # Buduj formularz
            for section_key, section_value in data.items():
                # Nagłówek sekcji
                section_label = QLabel(f"<b>{section_names.get(section_key, section_key)}</b>")
                section_label.setStyleSheet("font-size: 12pt; color: #2c3e50; margin-top: 15px;")
                self.visual_form_layout.addRow(section_label)

                if isinstance(section_value, dict):
                    # Sekcja ze słownikiem (regulations, statements)
                    for field_key, field_value in section_value.items():
                        label_text = field_names.get(field_key, field_key)

                        field_editor = QTextEdit()
                        field_editor.setPlainText(str(field_value))
                        field_editor.setMaximumHeight(80)
                        field_editor.setStyleSheet("""
                            QTextEdit {
                                font-size: 10pt;
                                padding: 5px;
                                border: 1px solid #bdc3c7;
                                background: white;
                            }
                        """)
                        field_editor.textChanged.connect(self._mark_as_modified)

                        full_key = f"{section_key}.{field_key}"
                        self.visual_fields[full_key] = field_editor

                        self.visual_form_layout.addRow(f"{label_text}:", field_editor)
                else:
                    # Pole proste (final_note)
                    field_editor = QTextEdit()
                    field_editor.setPlainText(str(section_value))
                    field_editor.setMaximumHeight(100)
                    field_editor.setStyleSheet("""
                        QTextEdit {
                            font-size: 10pt;
                            padding: 5px;
                            border: 1px solid #bdc3c7;
                            background: white;
                        }
                    """)
                    field_editor.textChanged.connect(self._mark_as_modified)

                    self.visual_fields[section_key] = field_editor
                    self.visual_form_layout.addRow(field_editor)

            self.has_unsaved_changes = False

        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie można załadować trybu wizualnego:\n{e}")

    def refresh_data(self):
        """Odświeża dane z serwera"""
        self._load_content()

    def closeEvent(self, event):
        """Obsługuje zamknięcie widoku"""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Niezapisane zmiany",
                "Masz niezapisane zmiany.\n\nCzy chcesz je zapisać przed zamknięciem?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                self._save_content()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()