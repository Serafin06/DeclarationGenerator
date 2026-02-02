"""
Declaration - Model przechowujący dane deklaracji zgodności
Używa wzorca Builder do konstrukcji
"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict


@dataclass
class Product:
    """Dane produktu (pkt 1)"""
    name: str = ""
    structure: str = ""  # np. "OPA/PE"


@dataclass
class Producer:
    """Dane producenta (pkt 2)"""
    name: str = "MARPOL Sp. z o.o."
    address_line1: str = "Ignatki 40/1"
    address_line2: str = "16-001 Kleosin"
    phone: str = "0048 85 7474397"
    fax: str = "0048 85 6631150"
    plant_name: str = "Zakład Produkcyjny Marpol Sp. z o.o. w Tychach"
    plant_address: str = "43-100 Tychy, ul. Składowa 2"


@dataclass
class ClientData:
    """Dane klienta (tylko dla wersji BOK)"""
    client_code: str = ""
    client_name: str = ""
    client_address: str = ""
    invoice_number: str = ""


@dataclass
class ProductBatch:
    """Dane partii produktu (tylko dla wersji BOK)"""

    product_code: str = ""
    product_name: str = ""
    production_date: Optional[date] = None
    quantity: str = ""
    batch_number: str = ""
    expiry_date: str = ""

    # NOWE POLA — indywidualne grubości
    thickness1: str = ""
    thickness2: str = ""
    thickness3: str = ""

    # NOWE POLA — checkboxy widoczności
    show_name: bool = True
    show_batch: bool = True
    show_quantity: bool = True
    show_production_date: bool = True
    show_thickness: bool = True




@dataclass
class Declaration:
    """Główny model deklaracji zgodności"""
    language: str = "pl"  # 'pl' lub 'en'
    declaration_type: str = "tech"  # 'tech' lub 'bok'
    generation_date: date = field(default_factory=date.today)

    product: Product = field(default_factory=Product)
    producer: Producer = field(default_factory=Producer)

    # Tylko dla wersji BOK
    client: Optional[ClientData] = None
    batches: List[ProductBatch] = field(default_factory=list)

    # Dane do tabel - generowane na podstawie struktury laminatu
    substances_table: List[Dict] = field(default_factory=list)
    dual_use_list: List[str] = field(default_factory=list)

    def to_template_dict(self) -> Dict:
        """Konwertuje model do słownika dla szablonu Jinja2"""
        return {
            'generation_date': self.generation_date.strftime('%d.%m.%Y'),
            'product': {
                'name': self.product.name,
                'structure': self.product.structure
            },
            'producer': {
                'name': self.producer.name,
                'address_line1': self.producer.address_line1,
                'address_line2': self.producer.address_line2,
                'phone': self.producer.phone,
                'fax': self.producer.fax,
                'plant_name': self.producer.plant_name,
                'plant_address': self.producer.plant_address
            },
            'client': {
                'code': self.client.client_code if self.client else '',
                'name': self.client.client_name if self.client else '',
                'address': self.client.client_address if self.client else '',
                'invoice': self.client.invoice_number if self.client else ''
            } if self.declaration_type == 'bok' else None,
            'batches': [
                {
                    'code': b.product_code,
                    'name': b.product_name if b.show_name else '',
                    'production_date': b.production_date.strftime('%d.%m.%Y') if (b.production_date and b.show_production_date) else '',
                    'quantity': b.quantity if b.show_quantity else '',
                    'batch_number': b.batch_number if b.show_batch else '',
                    'expiry_date': b.expiry_date,
                    'thickness': f"{b.thickness1}/{b.thickness2}/{b.thickness3} μm" if b.show_thickness else ''
                } for b in self.batches
            ] if self.declaration_type == 'bok' else [],
            'substances_table': self.substances_table,
            'dual_use_list': self.dual_use_list
        }