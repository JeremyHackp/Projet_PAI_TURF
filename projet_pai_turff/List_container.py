from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .OverviewButton import OverviewButton


class List_container(QWidget):
    def __init__(
        self,
        parent=None,
        id_a_afficher=[],
        donnees_a_afficher=None,
        get_data: Callable | None = None,
        main_layout=None,
        detailWindow=None,
    ):
        """

        Args:
            parent: Parent QWidget
            id_a_afficher: Liste des IDs des courses à afficher
            donnees_a_afficher: Dictionnaire optionnel spécifiant les champs à afficher
                              au format {cle_donnee: "Label à afficher"}
                              Ex: {'name': 'Nom', 'date': 'Date', 'place': 'Lieu'}
                              Si None, affiche tous les champs du dictionnaire retourné par get_data.
            get_data: Fonction de récupération des données de la course
            main_layout: Layout principal pour intégrer ce widget (optionnel)
        """

        super().__init__(parent)
        self.list_layout = QVBoxLayout(self)
        self.list_layout.setSpacing(16)
        self.list_layout.setContentsMargins(6, 6, 6, 6)
        self.get_data = get_data
        self.donnees_a_afficher = donnees_a_afficher
        self.detailWindow = detailWindow

        for i in id_a_afficher:
            # Create course overview buttons (enable auto_scale for responsive text)
            self.list_layout.addWidget(
                OverviewButton(
                    i,
                    self.get_data,
                    self.donnees_a_afficher,
                    self.detailWindow,
                    auto_scale=True,
                )
            )

        self.list_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        if main_layout is not None:
            main_layout.addWidget(scroll_area)

        QTimer.singleShot(50, self._refresh_card_sizes)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def update(self, id_a_afficher):
        """Met à jour les boutons de la liste des courses affichées.
        Args:
            id_a_afficher: Liste des IDs des courses à afficher
        """

        # 1. Vider l'affichage actuel
        self.clear_layout(self.list_layout)
        # 2. Recréer les boutons
        for i in id_a_afficher:
            # Create course overview buttons (enable auto_scale for responsive text)
            self.list_layout.addWidget(
                OverviewButton(
                    i,
                    self.get_data,
                    self.donnees_a_afficher,
                    self.detailWindow,
                    auto_scale=True,
                )
            )

        self.list_layout.addStretch()

    # After the UI is built, ensure each OverviewButton recalculates size
    def _refresh_card_sizes(self):
        for w in self.findChildren(OverviewButton):
            try:
                w._update_font_size()
            except Exception:
                pass
