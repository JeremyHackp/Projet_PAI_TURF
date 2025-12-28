from typing import Any, Dict, Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QComboBox,
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureWidget
from matplotlib.figure import Figure
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from .data_access import get_participants_data

from .List_container import List_container

from .data_access import donnees_a_afficher_detail_participant
from .Graphe import Graphe
from .data_access import type_graphiques_participants
from .data_access import colonnes_filtrage_types_de_courses_pour_participants
from .Filtre import Filtre
from .data_access import update_graphe_data


class ParticipantDetailWindow(QDialog):

    def __init__(self, id: Any, parent=None):
        super().__init__(parent)

        self.participant_id = id

        self.donnees_a_afficher = donnees_a_afficher_detail_participant
        self.get_participants_data = get_participants_data
        self.particpant_data = self.get_participants_data(self.participant_id)

        self.setWindowTitle(f"Détails - {self.particpant_data.get('name', 'Cheval')}")
        self.setMinimumSize(600, 500)
        self.current_graph_type = type_graphiques_participants[0]

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # ===== Titre =====
        title = QLabel(self.particpant_data.get("name", "Cheval sans nom"))
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        main_layout.addWidget(title)

        # ===== Détails =====
        scroll_detail = QScrollArea()
        scroll_detail.setWidgetResizable(True)

        content = QWidget()
        layout_detail = QVBoxLayout(content)

        if self.donnees_a_afficher:
            fields = self.donnees_a_afficher
        else:
            fields = {
                k: k.replace("_", " ").title()
                for k in self.particpant_data.keys()
                if k != "error"
            }

        for key, label in fields.items():
            if key in self.particpant_data:
                row = QHBoxLayout()

                key_label = QLabel(f"<b>{label}:</b>")
                key_label.setMinimumWidth(150)

                row.addWidget(key_label)

                value_label = QLabel(str(self.particpant_data[key]))
                value_label.setWordWrap(True)
                row.addWidget(value_label, 1)

                layout_detail.addLayout(row)

        layout_detail.addStretch()
        scroll_detail.setWidget(content)
        main_layout.addWidget(scroll_detail)

        # ===== Graphique =====

        graph_layout = QHBoxLayout()
        param_layout = QVBoxLayout()

        self.combo_graph = QComboBox()
        self.combo_graph.addItems(type_graphiques_participants)

        self.combo_graph.currentTextChanged.connect(self._on_graph_type_changed)

        param_layout.addWidget(QLabel("Type de graphe :"))
        param_layout.addWidget(self.combo_graph)

        colonnes_filtrage = colonnes_filtrage_types_de_courses_pour_participants
        self.filtre_widget = Filtre(colonnes_filtrage)

        param_layout.addWidget(QLabel("Filtre sur les types de courses :"))
        param_layout.addWidget(self.filtre_widget)

        self.filtre_widget.filtres_changes.connect(lambda: self.update_graphe())

        param_layout.addStretch()
        graph_layout.addLayout(param_layout)

        self.graphe = Graphe(parent=self, layout=graph_layout)

        graph_layout.addStretch()
        main_layout.addLayout(graph_layout)
        self.update_graphe()

        # ===== Bouton fermer =====
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn, alignment=Qt.AlignRight)

    def _on_graph_type_changed(self, graph_type: str):
        self.current_graph_type = graph_type
        self.update_graphe()

    def update_graphe(self):
        update_graphe_data(self.current_graph_type, self.filtre_widget, self.graphe)
