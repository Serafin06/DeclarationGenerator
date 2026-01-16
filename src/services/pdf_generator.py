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
        OUTPUT_PATH.mkdir(exist_ok=True, parents=True)

    def _get_template_path(self, declaration: Declaration) -> Path:
        """Zwraca odpowiednią ścieżkę szablonu"""
        if declaration.declaration_type == 'tech':
            return TEMPLATE_PL_TECH if declaration.language == 'pl' else TEMPLATE_EN_TECH
        else:
            return TEMPLATE_PL_BOK if declaration.language == 'pl' else TEMPLATE_EN_BOK

    def _prepare_context(self, declaration: Declaration) -> dict:
        """Przygotowuje kontekst dla szablonu"""
        texts = self.data_loader.get_texts(declaration.language)
        context = declaration.to_template_dict()
        context['texts'] = texts
        context['generation_date'] = declaration.generation_date.strftime("%d.%m.%Y")
        return context

    def generate_html_content(self, declaration: Declaration) -> str:
        """Renderuje szablon do stringa HTML"""
        template_path = self._get_template_path(declaration)
        template = self.env.get_template(template_path.name)
        context = self._prepare_context(declaration)
        return template.render(**context)

    def generate_html(self, declaration: Declaration) -> Path:
        """Zapisuje podgląd HTML i zwraca ŚCIEŻKĘ ABSOLUTNĄ (rozwiązuje błąd URI)"""
        html_content = self.generate_html_content(declaration)

        # .resolve() zamienia ścieżkę relatywną na absolutną (C:\Users\...)
        output_file = (OUTPUT_PATH / "preview_temp.html").resolve()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_file

    def generate_pdf_bytes(self, declaration: Declaration) -> bytes:
        """Generuje PDF i zwraca go jako bajty (naprawia błąd braku atrybutu)"""
        html_content = self.generate_html_content(declaration)
        try:
            # False oznacza, że pdfkit zwróci dane zamiast zapisywać do pliku
            return pdfkit.from_string(html_content, False, options=PDF_OPTIONS)
        except Exception as e:
            raise Exception(f"Błąd silnika wkhtmltopdf: {e}")