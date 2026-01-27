"""
TextEditorView - Edytor szablonów HTML deklaracji
Pozwala edytować pełne szablony HTML dla PL i EN
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QMessageBox, QComboBox,
                             QGroupBox, QSplitter)
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

        # Import stałych
        from src.config.constants import (
            TEMPLATES_PATH, TEXTS_PL, TEXTS_EN,
            TEMPLATE_PL_TECH, TEMPLATE_EN_TECH
        )

        self.templates_path = TEMPLATES_PATH
        self.template_pl_tech = TEMPLATE_PL_TECH
        self.template_en_tech = TEMPLATE_EN_TECH
        self.texts_pl = TEXTS_PL
        self.texts_en = TEXTS_EN

        self._init_ui()
        self._load_content()

    def _init_ui(self):
        """Inicjalizuje interfejs"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Nagłówek
        header = QLabel("Edytor Szablonów Deklaracji")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        # Wybór typu i języka
        controls_group = QGroupBox("Wybierz plik do edycji")
        controls_layout = QHBoxLayout()

        self.combo_type = QComboBox()
        self.combo_type.addItems(["Szablon HTML", "Teksty JSON"])
        self.combo_type.currentTextChanged.connect(self._on_type_changed)

        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Polski (PL)", "English (EN)"])
        self.combo_lang.currentTextChanged.connect(self._load_content)

        controls_layout.addWidget(QLabel("Typ pliku:"))
        controls_layout.addWidget(self.combo_type, stretch=1)
        controls_layout.addWidget(QLabel("Język:"))
        controls_layout.addWidget(self.combo_lang)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Splitter z edytorem i podglądem
        splitter = QSplitter(Qt.Horizontal)

        # Lewy panel - edytor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        editor_label = QLabel("Edytor")
        editor_label.setStyleSheet("font-weight: bold; padding: 5px;")
        editor_layout.addWidget(editor_label)

        self.text_editor = QTextEdit()
        self.text_editor.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.4;
                padding: 10px;
                background-color: #fdfefe;
            }
        """)
        editor_layout.addWidget(self.text_editor)

        # Prawy panel - podgląd bieżącego pliku
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)

        info_label = QLabel("Informacje")
        info_label.setStyleSheet("font-weight: bold; padding: 5px;")
        info_layout.addWidget(info_label)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumWidth(350)
        self.info_text.setStyleSheet("""
            QTextEdit {
                font-size: 10px;
                background-color: #ecf0f1;
                color: #2c3e50;
            }
        """)
        info_layout.addWidget(self.info_text)

        splitter.addWidget(editor_widget)
        splitter.addWidget(info_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, stretch=1)

        # Informacja o HTML
        info = QLabel(
            "💡 Edytujesz surowy kod HTML/JSON. Zachowaj ostrożność przy zmianach struktury."
        )
        info.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 5px;")
        layout.addWidget(info)

        # Przyciski akcji
        buttons_layout = QHBoxLayout()

        btn_reload = QPushButton("🔄 Cofnij zmiany")
        btn_reload.clicked.connect(self._reload_current)
        btn_reload.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)

        btn_save = QPushButton("💾 ZAPISZ ZMIANY")
        btn_save.clicked.connect(self._save_content)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)

        buttons_layout.addWidget(btn_reload)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_save)
        layout.addLayout(buttons_layout)

        # Ustaw początkowy stan
        self._on_type_changed()

    def _on_type_changed(self):
        """Zmiana między HTML a JSON"""
        is_html = "HTML" in self.combo_type.currentText()

        if is_html:
            self.info_text.setPlainText(
                "SZABLON HTML\n\n"
                "Obecnie edytujesz szablon\n"
                "deklaracji TECHNOLOGICZNEJ.\n\n"
                "Dostępne pliki:\n"
                "- declaration_tech_pl.html\n"
                "- declaration_tech_en.html\n"
                "- declaration_bok_pl.html (wkrótce)\n"
                "- declaration_bok_en.html (wkrótce)\n\n"
                "Dostępne zmienne:\n"
                "{{ product.name }}\n"
                "{{ product.structure }}\n"
                "{{ generation_date }}\n"
                "{{ texts.regulations.* }}\n"
                "{{ texts.statements.* }}\n"
                "{{ substances_table }}\n"
                "{{ dual_use_list }}\n\n"
                "Pętle:\n"
                "{% for item in list %}\n"
                "  {{ item.field }}\n"
                "{% endfor %}"
            )
        else:
            self.info_text.setPlainText(
                "TEKSTY JSON\n\n"
                "Struktura:\n"
                "{\n"
                "  \"regulations\": {...},\n"
                "  \"statements\": {...},\n"
                "  \"final_note\": \"...\"\n"
                "}\n\n"
                "Używane w szablonie HTML:\n"
                "{{ texts.regulations.eu_10_2011 }}\n"
                "{{ texts.statements.materials_compliance }}\n"
                "itd."
            )

        self._load_content()

    def _get_current_file_path(self) -> Path:
        """Zwraca ścieżkę do aktualnie wybranego pliku"""
        is_html = "HTML" in self.combo_type.currentText()
        is_pl = "Polski" in self.combo_lang.currentText()

        if is_html:
            return self.template_pl_tech if is_pl else self.template_en_tech
        else:
            return self.texts_pl if is_pl else self.texts_en

    def _load_content(self):
        """Ładuje zawartość wybranego pliku"""
        try:
            file_path = self._get_current_file_path()

            if not file_path.exists():
                self.text_editor.setPlainText(f"# Plik nie istnieje: {file_path}\n# Zostanie utworzony przy zapisie.")
                return

            is_html = "HTML" in self.combo_type.currentText()

            if is_html:
                # HTML - czytaj jako tekst
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_editor.setPlainText(content)
            else:
                # JSON - formatuj ładnie
                import json
                data = self.data_loader.load_json(file_path)
                content = json.dumps(data, ensure_ascii=False, indent=2)
                self.text_editor.setPlainText(content)

        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie można załadować pliku:\n{e}")
            self.text_editor.setPlainText(f"# Błąd ładowania: {e}")

    def _reload_current(self):
        """Przeładowuje plik bez zapisywania"""
        reply = QMessageBox.question(
            self,
            "Cofnij zmiany",
            "Czy na pewno chcesz cofnąć niezapisane zmiany?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Wymuś przeładowanie z dysku
            file_path = self._get_current_file_path()
            if not "HTML" in self.combo_type.currentText():
                self.data_loader.reload(file_path)
            self._load_content()

    def _save_content(self):
        """Zapisuje zawartość do pliku"""
        try:
            file_path = self._get_current_file_path()
            content = self.text_editor.toPlainText()
            is_html = "HTML" in self.combo_type.currentText()

            if is_html:
                # HTML - zapisz bezpośrednio
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                # JSON - sprawdź poprawność i zapisz
                import json
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    QMessageBox.critical(
                        self,
                        "Błąd składni JSON",
                        f"Nieprawidłowy format JSON:\n{e}\n\nPopraw błędy przed zapisem."
                    )
                    return

                self.data_loader.save_json(file_path, data)

            QMessageBox.information(
                self,
                "Sukces",
                f"Zapisano zmiany:\n{file_path.name}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu", f"Nie udało się zapisać:\n{e}")

    def refresh_data(self):
        """Odświeża dane z serwera"""
        self._load_content()