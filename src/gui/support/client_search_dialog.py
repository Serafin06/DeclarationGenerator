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
            if search_text in data['client_name'].lower():
                item = QListWidgetItem(f"{data['client_name']} (ID: {c_id})")
                item.setData(32, c_id)  # Zapisujemy ukryte ID
                self.list_widget.addItem(item)

    def _select_and_close(self, item):
        self.selected_client_id = item.data(32)
        self.accept()