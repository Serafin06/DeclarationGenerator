# gui/support/structure_select_dialog.py

"""
StructureSelectDialog - Dialog ręcznego wyboru struktury laminatu.
Pokazywany, gdy automatyczne dopasowanie struktury z bazy (RECEPTURA_1)
nie znalazło wszystkich materiałów. Użytkownik wybiera materiał każdej
warstwy z listy - najbliższe podpowiedzi znajdują się na górze.
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QCheckBox, QDialogButtonBox,
                             QGroupBox, QWidget)
from src.utils.material_macher import MaterialMatcher


class StructureSelectDialog(QDialog):
    """
    Dialog wyboru struktury, gdy automatyczne dopasowanie nie powiodło się.

    Args:
        db_structure: Oryginalna struktura z bazy (np. 'OPA/PE o-c')
        layer_parts: Lista warstw (po podziale przez '/'), np. ['OPA', 'PE o-c']
        materials: Dostępne materiały (combo do wyboru)
        suggestions: Lista podpowiedzi (najlepsze dopasowanie lub None) dla każdej warstwy
    """

    def __init__(self, db_structure: str, layer_parts: list, materials: list,
                 suggestions: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wybór struktury laminatu")
        self.setMinimumWidth(480)
        self.materials = materials
        self.layer_parts = layer_parts
        self.selected_materials = []

        layout = QVBoxLayout(self)

        info = QLabel(
            f"<b>Struktura z bazy:</b> {db_structure}<br><br>"
            "Nie udało się automatycznie dopasować struktury.<br>"
            "Wybierz materiał dla każdej warstwy - na górze listy<br>"
            "znajdują się najbliższe dopasowania:")
        info.setWordWrap(True)
        layout.addWidget(info)

        layers_box = QGroupBox("Warstwy laminatu")
        layers_layout = QVBoxLayout()
        self.combos = []

        for i, part in enumerate(layer_parts):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"Warstwa {i + 1} [{part}]:"))
            combo = QComboBox()
            for material in MaterialMatcher.suggest_matches(part, materials):
                combo.addItem(material)
            suggestion = suggestions[i] if i < len(suggestions) else None
            if suggestion:
                idx = combo.findText(suggestion)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            row.addWidget(combo, 1)
            layers_layout.addLayout(row)
            self.combos.append(combo)

        # Opcjonalna trzecia warstwa (gdy w bazie są 2 warstwy,
        # a użytkownik potrzebuje struktury 3-warstwowej)
        self.chk_third_layer = None
        self.combo_third_layer = None
        self.third_layer_row = None
        if len(layer_parts) == 2:
            self.chk_third_layer = QCheckBox("Struktura 3-warstwowa (dodaj warstwę)")
            layers_layout.addWidget(self.chk_third_layer)

            self.third_layer_row = QWidget()
            third_layout = QHBoxLayout()
            third_layout.addWidget(QLabel("Warstwa 3:"))
            self.combo_third_layer = QComboBox()
            self.combo_third_layer.addItems(self.materials)
            third_layout.addWidget(self.combo_third_layer, 1)
            self.third_layer_row.setLayout(third_layout)
            self.third_layer_row.setVisible(False)
            layers_layout.addWidget(self.third_layer_row)

            self.chk_third_layer.toggled.connect(self.third_layer_row.setVisible)

        layers_box.setLayout(layers_layout)
        layout.addWidget(layers_box)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        if not materials:
            buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        layout.addWidget(buttons)

    def _on_accept(self):
        """Zbiera wybrane materiały i zamyka dialog z akceptacją."""
        self.selected_materials = [combo.currentText() for combo in self.combos]
        if self.chk_third_layer is not None and self.chk_third_layer.isChecked():
            self.selected_materials.append(self.combo_third_layer.currentText())
        self.accept()
