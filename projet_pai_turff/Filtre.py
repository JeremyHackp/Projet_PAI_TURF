"""
Module pour le widget de filtrage et tri de la base de données.

Le signal filtres_changes de la class Filtre est émis à chaque modification des filtres ou du tri.

Les dictionnaires colonnes_filtrage: Dict[str, type], colonnes_tri: Dict[str, str] doivent être fournis lors de l'instanciation du widget Filtre et permettent de definir les catégories élligibles au tri ou au filtre.

"""

from enum import Enum

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class OperateurComparaison(Enum):
    EGAL = "="
    DIFFERENT = "!="
    SUPERIEUR = ">"
    INFERIEUR = "<"
    SUPERIEUR_EGAL = ">="
    INFERIEUR_EGAL = "<="
    CONTIENT = "contient"
    NE_CONTIENT_PAS = "ne contient pas"


class DialogAjouterFiltre(QDialog):
    def __init__(self, colonnes_filtrage: dict[str, type], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un filtre")
        self.setMinimumWidth(400)

        self.colonnes_filtrage = colonnes_filtrage
        self.resultat = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Colonne
        row_col = QHBoxLayout()
        row_col.addWidget(QLabel("Colonne:"))
        self.combo_colonne = QComboBox()
        self.combo_colonne.addItems(self.colonnes_filtrage.keys())
        self.combo_colonne.currentTextChanged.connect(self._on_colonne_changed)
        row_col.addWidget(self.combo_colonne)
        layout.addLayout(row_col)

        # Opérateur
        row_op = QHBoxLayout()
        row_op.addWidget(QLabel("Opérateur:"))
        self.combo_operateur = QComboBox()
        self.combo_operateur.addItems([op.value for op in OperateurComparaison])
        row_op.addWidget(self.combo_operateur)
        layout.addLayout(row_op)

        # Valeur
        self.row_valeur = QHBoxLayout()
        self.row_valeur.addWidget(QLabel("Valeur:"))
        self._create_value_widget()
        self.row_valeur.addWidget(self.widget_valeur)
        layout.addLayout(self.row_valeur)

        # Boutons
        row_btn = QHBoxLayout()
        btn_ok = QPushButton("Valider")
        btn_cancel = QPushButton("Annuler")
        btn_ok.clicked.connect(self._valider)
        btn_cancel.clicked.connect(self.reject)
        row_btn.addWidget(btn_ok)
        row_btn.addWidget(btn_cancel)
        layout.addLayout(row_btn)

    def _create_value_widget(self):
        type_colonne = self.colonnes_filtrage.get(self.combo_colonne.currentText(), str)

        if type_colonne is int:
            self.widget_valeur = QSpinBox()
            self.widget_valeur.setRange(-999999, 999999)
        else:
            self.widget_valeur = QLineEdit()
            self.widget_valeur.setPlaceholderText("Entrer une valeur")

    def _on_colonne_changed(self):
        old = self.widget_valeur
        self._create_value_widget()
        self.row_valeur.replaceWidget(old, self.widget_valeur)
        old.deleteLater()

    def _valider(self):
        colonne = self.combo_colonne.currentText()
        operateur = self.combo_operateur.currentText()

        if isinstance(self.widget_valeur, QLineEdit):
            valeur = self.widget_valeur.text()
            if not valeur:
                QMessageBox.warning(self, "Erreur", "Valeur requise")
                return
        else:
            valeur = self.widget_valeur.value()

        self.resultat = (colonne, operateur, valeur)
        self.accept()

    def get_filtre(self):
        return self.resultat


class Filtre(QWidget):
    """
    Widget UI de filtrage et tri.
    Ne fait AUCUN filtrage réel.
    Stocke et expose uniquement l’état sélectionné par l’utilisateur.
    """

    filtres_changes = Signal()

    def __init__(
        self,
        colonnes_filtrage: dict[str, type],
        colonnes_tri: dict[str, str] = None,
        parent=None,
        tri_initial: str | None = None,  # clé de colonne
        ordre_croissant_initial: bool = True,
    ):
        super().__init__(parent)
        self.tri = colonnes_tri is not None
        self.colonnes_filtrage = colonnes_filtrage
        self.colonnes_tri = colonnes_tri

        # État interne
        self.filtres_actifs = []
        self.colonne_tri = tri_initial
        self.ordre_croissant = ordre_croissant_initial

        self._setup_ui()
        if self.tri:
            self._appliquer_tri_initial()

    def _appliquer_tri_initial(self):
        """Synchronise l'état interne avec l'UI."""
        if self.colonne_tri and self.colonne_tri in self.colonnes_tri:
            label = self.colonnes_tri[self.colonne_tri]
            index = self.combo_tri.findText(label)
            if index != -1:
                self.combo_tri.setCurrentIndex(index)

        self.combo_ordre.setCurrentIndex(0 if self.ordre_croissant else 1)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Filtres ---
        filtres_group = QGroupBox("Filtres")
        filtres_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.scroll_widget = QWidget()
        self.filtres_layout = QVBoxLayout(self.scroll_widget)
        self.filtres_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.scroll_widget)

        filtres_layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_add = QPushButton("+")
        btn_add.setMaximumWidth(40)
        btn_add.clicked.connect(self._ouvrir_dialog_filtre)
        btn_row.addWidget(btn_add)

        filtres_layout.addLayout(btn_row)
        filtres_group.setLayout(filtres_layout)
        main_layout.addWidget(filtres_group)

        # --- Tri ---
        if self.tri:
            tri_group = QGroupBox("Tri")
            tri_layout = QHBoxLayout()

            tri_layout.addWidget(QLabel("Trier par:"))
            self.combo_tri = QComboBox()
            self.combo_tri.addItem("Aucun")
            self.combo_tri.addItems(self.colonnes_tri.values())
            self.combo_tri.currentTextChanged.connect(self._on_tri_changed)
            tri_layout.addWidget(self.combo_tri)

            tri_layout.addWidget(QLabel("Ordre:"))
            self.combo_ordre = QComboBox()
            self.combo_ordre.addItems(["Croissant", "Décroissant"])
            self.combo_ordre.currentTextChanged.connect(self._on_ordre_changed)
            tri_layout.addWidget(self.combo_ordre)

            tri_group.setLayout(tri_layout)
            main_layout.addWidget(tri_group)

        # Reset
        btn_reset = QPushButton("Réinitialiser")
        btn_reset.clicked.connect(self.reinitialiser)
        main_layout.addWidget(btn_reset)

        self.setMinimumWidth(400)

    def _ouvrir_dialog_filtre(self):
        dialog = DialogAjouterFiltre(self.colonnes_filtrage, self)
        if dialog.exec() == QDialog.Accepted:
            filtre = dialog.get_filtre()
            if filtre:
                self._ajouter_filtre(filtre)

    def _ajouter_filtre(self, filtre: tuple):
        self.filtres_actifs.append(filtre)

        row = QHBoxLayout()
        label = QLabel(f"{filtre[0]} {filtre[1]} {filtre[2]}")
        row.addWidget(label)

        btn_del = QPushButton("✕")
        btn_del.setMaximumWidth(30)
        btn_del.clicked.connect(lambda: self._supprimer_filtre(filtre, row))
        row.addWidget(btn_del)

        self.filtres_layout.addLayout(row)
        self.filtres_changes.emit()

    def _supprimer_filtre(self, filtre: tuple, row: QHBoxLayout):
        if filtre in self.filtres_actifs:
            self.filtres_actifs.remove(filtre)

        while row.count():
            item = row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.filtres_layout.removeItem(row)
        self.filtres_changes.emit()

    def _on_tri_changed(self, text: str):
        self.colonne_tri = None
        for cle, label in self.colonnes_tri.items():
            if label == text:
                self.colonne_tri = cle
                break
        self.filtres_changes.emit()

    def _on_ordre_changed(self, text: str):
        self.ordre_croissant = text == "Croissant"
        self.filtres_changes.emit()

    def get_filtres(self) -> list[tuple]:
        return self.filtres_actifs.copy()

    def get_tri(self) -> tuple | None:
        if self.colonne_tri and self.tri:
            return (self.colonne_tri, self.ordre_croissant)
        return None

    def get_state(self) -> dict:
        """renvoie un dictionnaire de la forme {
        'filtres': List[
            Tuple[str(valeure filtrée),
            OperateurComparaison(parmis EGAL,DIFFERENT, SUPERIEUR, INFERIEUR, SUPERIEUR_EGAL, INFERIEUR_EGAL, CONTIENT, NE_CONTIENT_PAS),
            Any(valeure a comparer)]],

        'tri': Optional[
            Tuple[str(valeure sur laquelle on tri),
            bool(True : ordre_croissant, False : décroissant)]}]}
        """
        return {"filtres": self.get_filtres(), "tri": self.get_tri()}

    def reinitialiser(self):
        self.filtres_actifs.clear()

        while self.filtres_layout.count():
            item = self.filtres_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        self.combo_tri.setCurrentIndex(0)
        self.combo_ordre.setCurrentIndex(0)

        self.colonne_tri = None
        self.ordre_croissant = True

        self.filtres_changes.emit()
