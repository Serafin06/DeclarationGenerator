# gui/support/client_search_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem


class ClientSearchDialog(QDialog):
    def __init__(self, clients_dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wyszukaj kontrahenta")
        self.setMinimumSize(500, 400)
        self.clients = clients_dict
        self.selected_client_id = None

        layout = QVBoxLayout(self)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Wpisz nazwę kontrahenta...")
        self.search_bar.textChanged.connect(self._filter_list)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._select_and_close)

        layout.addWidget(self.search_bar)
        layout.addWidget(self.list_widget)
        self._filter_list()

    def _filter_list(self):
        self.list_widget.clear()
        search_text = self.search_bar.text().lower()
        for c_id, data in self.clients.items():
            # --- KLUCZOWA POPRAWKA ---
            # Używamy 'or ''', aby zapewnić, że client_name nigdy nie będzie None,
            # nawet jeśli wartość w bazie danych to NULL.
            client_name = data.get('client_name') or ''

            # Sprawdzamy, czy tekst wyszukiwania znajduje się w nazwie klienta
            if search_text in client_name.lower():
                # Dla lepszej czytelności, jeśli nazwa jest pusta, wyświetlamy "Brak nazwy"
                display_name = client_name if client_name else 'Brak nazwy'
                item = QListWidgetItem(f"{display_name} (ID: {c_id})")
                item.setData(32, c_id)  # Zapisujemy ukryte ID
                self.list_widget.addItem(item)

    def _select_and_close(self, item):
        self.selected_client_id = item.data(32)
        self.accept()