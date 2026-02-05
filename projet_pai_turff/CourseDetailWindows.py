from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .data_access import (
    donnees_a_afficher_bouton_particpant,
    donnees_a_afficher_detail_course,
    get_course_data,
    get_course_participants_id,
    get_participants_data,
)
from .List_container import List_container
from .ParticipantDetailWindow import ParticipantDetailWindow


class CourseDetailWindow(QDialog):
    """Fenetre de détail permettant d'afficher les données d'une course spécifique et contenant la liste des participants, clicables vers une fenêtre ParticipantDetailWindow."""

    def __init__(self, id: any, parent=None, get_data: callable = None):
        """
        Args:
            id (Any): ID de la course à afficher, type flexible pour s'adapter à différents formats d'ID (int, str, etc.)
            parent (QWidget, optional): Parent widget de la fenêtre de détail. Par défaut None.
            get_data (callable, optional): Fonction pour récupérer les données de la course. inutile dans cette fenetre CourseDetailWindows, sert uniquement a garder un appel similaire a la classe ParticipantDetailWindow. Par défaut None.
        """
        super().__init__(parent)

        self.course_id = id

        self.donnees_a_afficher = donnees_a_afficher_detail_course
        self.get_course_data = get_course_data
        self.course_data = self.get_course_data(self.course_id)
        self.participants_id = get_course_participants_id(self.course_id)
        self.setWindowTitle(f"Détails - {self.course_data.get('name', 'Course')}")
        self.setMinimumSize(600, 500)

        self._setup_ui()

    def _setup_ui(self):
        """met en place l'interface graphique, fonction appelée lors de l'initialisation de la classe"""
        main_layout = QVBoxLayout(self)

        # ===== Titre =====
        title = QLabel(self.course_data.get("name", "Course sans nom"))
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        main_layout.addWidget(title)

        # ===== Détails course =====
        scroll_detail = QScrollArea()
        scroll_detail.setWidgetResizable(True)

        content = QWidget()
        layout_detail = QVBoxLayout(content)

        if self.donnees_a_afficher:  # afficher toutes les données spécifiées dans le dictionnaire donnees_a_afficher
            fields = self.donnees_a_afficher
        else:  # si aucune donnée spécifiée, afficher toutes les données disponibles
            fields = {
                k: k.replace("_", " ").title()
                for k in self.course_data.keys()
                if k != "error"
            }

        for key, label in fields.items():
            if key in self.course_data:
                row = QHBoxLayout()

                key_label = QLabel(
                    f"<b>{label}:</b>"
                )  # L'utilisation de <b> permet de mettre le texte en gras
                key_label.setMinimumWidth(150)
                row.addWidget(key_label)

                value_label = QLabel(str(self.course_data[key]))
                value_label.setWordWrap(
                    True
                )  # Permet de gérer le retour à la ligne automatique si le texte est trop long
                row.addWidget(value_label, 1)

                layout_detail.addLayout(row)

        layout_detail.addStretch()
        scroll_detail.setWidget(content)
        main_layout.addWidget(scroll_detail)

        # ===== Participants =====

        donnees_a_afficher_participant = donnees_a_afficher_bouton_particpant

        participants_widget = QWidget()
        layout_participant = QVBoxLayout(participants_widget)
        layout_participant.addWidget(QLabel("Participants dans l'ordre d'arrivée"))
        List_container(
            None,
            id_a_afficher=self.participants_id,
            donnees_a_afficher=donnees_a_afficher_participant,
            get_data=get_participants_data,
            main_layout=layout_participant,
            detailWindow=ParticipantDetailWindow,
        )
        layout_participant.addStretch()
        main_layout.addWidget(participants_widget)

        # ===== Bouton fermer =====
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn)
