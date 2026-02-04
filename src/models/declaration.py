# models/declaration.py

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
        context = {
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
            'substances_table': self.substances_table,
            'dual_use_list': self.dual_use_list
        }

        # Dane BOK
        if self.declaration_type == 'bok':
            context['client'] = {
                'code': self.client.client_code if self.client else '',
                'name': self.client.client_name if self.client else '',
                'address': self.client.client_address if self.client else '',
                'invoice': self.client.invoice_number if self.client else ''
            }

            # Przygotuj dane partii
            batches_data = []
            for b in self.batches:
                # Buduj strukturę z grubościami
                thickness_str = ""
                if b.show_thickness and b.thickness1 and b.thickness2:
                    if b.thickness3:
                        thickness_str = f"{b.thickness1}/{b.thickness2}/{b.thickness3} μm"
                    else:
                        thickness_str = f"{b.thickness1}/{b.thickness2} μm"

                batches_data.append({
                    'index': b.product_code,
                    'description': b.product_name if b.show_name else '',
                    'batch_no': b.batch_number if b.show_batch else '',
                    'qty': b.quantity if b.show_quantity else '',
                    'thickness': thickness_str,
                    'prod_date': b.production_date.strftime('%d.%m.%Y') if (
                                b.production_date and b.show_production_date) else ''
                })

            context['batches'] = batches_data

            # Wspólna struktura (z product.name która zawiera np. "PET/PE 12/40 μm")
            context['common_structure'] = self.product.name

            # Config dla tabeli - czy pokazywać kolumny
            any_has_description = any(b.show_name for b in self.batches)
            any_has_thickness = any(b.show_thickness for b in self.batches)

            context['config'] = {
                'show_description': any_has_description,
                'show_thickness': any_has_thickness
            }

        return context