"""
PDFGenerator - Generuje HTML i PDF z szablonów Jinja2
"""
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime
from src.config.constants import (
    TEMPLATES_PATH, OUTPUT_PATH,
    TEMPLATE_PL_TECH, TEMPLATE_EN_TECH,
    TEMPLATE_PL_BOK, TEMPLATE_EN_BOK
)
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from bs4 import BeautifulSoup
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

        # Zabezpieczenie przed None w dacie
        if declaration.generation_date:
            context['generation_date'] = declaration.generation_date.strftime("%d.%m.%Y")
        else:
            context['generation_date'] = datetime.now().strftime("%d.%m.%Y")

        return context

    def generate_html_content(self, declaration: Declaration) -> str:
        """Renderuje szablon do stringa HTML"""
        template_path = self._get_template_path(declaration)
        template = self.env.get_template(template_path.name)
        context = self._prepare_context(declaration)
        return template.render(**context)

    def generate_html(self, declaration: Declaration) -> Path:
        """Zapisuje podgląd HTML i zwraca ścieżkę absolutną"""
        html_content = self.generate_html_content(declaration)
        output_file = (OUTPUT_PATH / "preview_temp.html").resolve()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_file

    def generate_pdf_bytes(self, declaration: Declaration) -> bytes:
        """Generuje PDF i zwraca jako bajty do zapisu przez użytkownika"""
        html_content = self.generate_html_content(declaration)

        try:
            # xhtml2pdf - czysto pythonowa biblioteka
            result = BytesIO()
            pisa_status = pisa.CreatePDF(
                src=html_content,
                dest=result,
                encoding='utf-8'
            )

            if pisa_status.err:
                raise Exception("xhtml2pdf zgłosił błędy podczas konwersji")

            return result.getvalue()

        except Exception as e:
            raise Exception(f"Błąd generowania PDF: {e}")

    def generate_docx(self, declaration: Declaration) -> Path:
        """
        Generuje plik DOCX z deklaracji.
        Zwraca ścieżkę do zapisanego pliku.
        """
        html_content = self.generate_html_content(declaration)
        soup = BeautifulSoup(html_content, 'html.parser')

        # Utwórz dokument Word
        doc = Document()

        # Ustaw marginesy (15mm)
        for section in doc.sections:
            section.top_margin = Inches(0.59)
            section.bottom_margin = Inches(0.59)
            section.left_margin = Inches(0.59)
            section.right_margin = Inches(0.59)

        # Przetwórz zawartość body
        body = soup.find('body')
        if body:
            self._process_html_to_docx(doc, body)

        # Zapisz
        safe_name = "".join(c for c in declaration.product.name if c.isalnum() or c in (' ', '-')).rstrip()
        filename = f"Deklaracja_{safe_name.replace(' ', '_')}.docx"
        output_file = OUTPUT_PATH / filename

        doc.save(str(output_file))
        return output_file

    def _process_html_to_docx(self, doc, element):
        """Przetwarza elementy HTML do DOCX (uproszczona konwersja)"""
        for child in element.children:
            if isinstance(child, str):
                text = child.strip()
                if text:
                    doc.add_paragraph(text)
            else:
                tag_name = child.name

                if tag_name == 'h1':
                    text = child.get_text().strip()
                    p = doc.add_paragraph(text)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.runs[0].font.size = Pt(14)
                    p.runs[0].font.bold = True
                    p.runs[0].font.underline = True

                elif tag_name in ['p', 'div']:
                    text = child.get_text().strip()
                    if text:
                        p = doc.add_paragraph(text)
                        # Sprawdź czy zawiera <b> lub class="bold"
                        if child.find('b') or child.find('span', class_='bold'):
                            p.runs[0].font.bold = True

                elif tag_name == 'table':
                    self._add_table_to_docx(doc, child)

                elif tag_name == 'ul':
                    for li in child.find_all('li', recursive=False):
                        text = li.get_text().strip()
                        if text:
                            doc.add_paragraph(text, style='List Bullet')

                elif tag_name == 'br':
                    doc.add_paragraph()

                else:
                    self._process_html_to_docx(doc, child)

    def _add_table_to_docx(self, doc, table_element):
        """Dodaje tabelę HTML do DOCX"""
        rows = table_element.find_all('tr')
        if not rows:
            return

        # Policz kolumny
        cols_count = len(rows[0].find_all(['th', 'td']))

        # Utwórz tabelę
        word_table = doc.add_table(rows=len(rows), cols=cols_count)
        word_table.style = 'Table Grid'

        # Wypełnij komórki
        for row_idx, row in enumerate(rows):
            cells = row.find_all(['th', 'td'])

            for col_idx, cell in enumerate(cells):
                if col_idx >= cols_count:
                    break

                word_cell = word_table.rows[row_idx].cells[col_idx]

                # Rowspan/colspan
                rowspan = int(cell.get('rowspan', 1))
                colspan = int(cell.get('colspan', 1))

                if colspan > 1 or rowspan > 1:
                    try:
                        end_cell = word_table.rows[row_idx + rowspan - 1].cells[col_idx + colspan - 1]
                        word_cell.merge(end_cell)
                    except:
                        pass

                # Tekst
                text = cell.get_text().strip()
                word_cell.text = text

                # Formatowanie nagłówków
                if cell.name == 'th':
                    for paragraph in word_cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.bold = True
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif 'text-align: center' in cell.get('style', ''):
                    for paragraph in word_cell.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()