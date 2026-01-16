"""
PDFGenerator - Generuje HTML i PDF z szablonów Jinja2
"""
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import pdfkit
from datetime import datetime
from src.config.constants import (
    TEMPLATES_PATH, OUTPUT_PATH, PDF_OPTIONS,
    TEMPLATE_PL_TECH, TEMPLATE_EN_TECH,
    TEMPLATE_PL_BOK, TEMPLATE_EN_BOK
)
from src.models.declaration import Declaration

class PDFGenerator:
    """Generator dokumentów HTML i PDF"""

    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_PATH)),
            autoescape=True
        )
        OUTPUT_PATH.mkdir(exist_ok=True)

    def _get_template_path(self, declaration: Declaration) -> Path:
        """Zwraca odpowiednią ścieżkę szablonu"""
        if declaration.declaration_type == 'tech':
            return TEMPLATE_PL_TECH if declaration.language == 'pl' else TEMPLATE_EN_TECH
        else:
            return TEMPLATE_PL_BOK if declaration.language == 'pl' else TEMPLATE_EN_BOK

    def _prepare_context(self, declaration: Declaration) -> dict:
        """Przygotowuje kontekst dla szablonu (połączenie danych + teksty)"""
        texts = self.data_loader.get_texts(declaration.language)
        context = declaration.to_template_dict()
        context['texts'] = texts
        return context

    def generate_html(self, declaration: Declaration) -> Path:
        """Generuje HTML z szablonu"""
        template_path = self._get_template_path(declaration)
        template_name = template_path.name

        template = self.env.get_template(template_name)
        context = self._prepare_context(declaration)

        html_content = template.render(**context)

        # Zapisz HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_PATH / f"declaration_{timestamp}.html"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_file

    def generate_pdf(self, declaration: Declaration) -> Path:
        """Generuje PDF przez HTML"""
        html_path = self.generate_html(declaration)
        pdf_path = html_path.with_suffix('.pdf')

        try:
            # === WYŁĄCZONE - wymaga wkhtmltopdf ===
            # pdfkit.from_file(
            #     str(html_path),
            #     str(pdf_path),
            #     options=PDF_OPTIONS
            # )
            # return pdf_path

            # === TYMCZASOWO - zwracamy tylko HTML ===
            print(f"INFO: Generowanie PDF wyłączone. HTML dostępny: {html_path}")
            return html_path  # Zwracamy HTML zamiast PDF

        except Exception as e:
            raise Exception(f"Błąd generowania PDF: {e}\n"
                          "Sprawdź czy wkhtmltopdf jest zainstalowany.")