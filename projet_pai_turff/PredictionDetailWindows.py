from typing import Any

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
from .OverviewButton import OverviewButton

from .data_access import (
    donnees_a_afficher_bouton_particpant,
    donnees_a_afficher_detail_course,
    get_course_data,
    get_course_participants_id,
    get_participants_data,
    get_course_prediction_data, 
    get_participant_predits_data,
    prediction_ordre_participants,
    prediction_ordre_participants_verification
)
from .List_container import List_container
from .ParticipantDetailWindow import ParticipantDetailWindow


from PySide6.QtCore import Qt, QTimer

class ParticipantVerificationWindow(QDialog):
    def __init__(self, course_id, ordre_predit, ordre_reel, parent=None):
        super().__init__(parent)

        self.course_id = course_id
        self.ordre_predit = ordre_predit
        self.ordre_reel = ordre_reel

        self.setWindowTitle("Véritable ordre d'arrivée des participants")
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        container = QWidget()
        list_layout = QVBoxLayout(container)
        list_layout.setSpacing(16)
        list_layout.setContentsMargins(6, 6, 6, 6)

        error_counter = 0

        for i in range(len(self.ordre_reel)):
            if self.ordre_reel[i] == self.ordre_predit[i]:
                list_layout.addWidget(
                    OverviewButton(
                        self.ordre_reel[i],
                        get_participant_predits_data,
                        donnees_a_afficher_bouton_particpant,
                        None,
                        auto_scale=True
                    )
                )
            else:
                error_counter += 1
                list_layout.addWidget(
                    OverviewButton(
                        self.ordre_reel[i],
                        get_participant_predits_data,
                        donnees_a_afficher_bouton_particpant,
                        None,
                        auto_scale=True,
                        bg_color="#FF8A8A",
                        shadow_color="#FF0000"
                    )
                )

        list_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container)

        main_layout.addWidget(scroll_area)
        main_layout.addWidget(QLabel(
            f"Nombre d'erreurs dans l'ordre prédit : {error_counter}"
        ))

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.reject)
        main_layout.addWidget(btn_close)

        QTimer.singleShot(50, self._refresh_card_sizes)

    def _refresh_card_sizes(self):
        for w in self.findChildren(OverviewButton):
            try:
                w._update_font_size()
            except Exception:
                pass





class PredictionDetailWindow(QDialog):
    """Fenetre de détail permettant d'afficher les données d'une course spécifique et ainsi que la liste des participants pour laquelle on prédit l'ordre, clicables vers une fenêtre ParticipantDetailWindow."""
    def __init__(self, id: Any, parent=None, get_data=None):
        super().__init__(parent)

        self.course_id = id

        self.donnees_a_afficher = donnees_a_afficher_detail_course
        self.get_course_data = get_course_prediction_data
        self.course_data = self.get_course_data(self.course_id)
        self.prediction_ids = prediction_ordre_participants(self.course_id)
        self.get_participant_predits_data = get_participant_predits_data
        self.setWindowTitle(f"Détails - {self.course_data.get('name', 'Course')}")
        self.setMinimumSize(600, 500)

        self._setup_ui()
    def _ouvrir_verification_window(self):
        window = ParticipantVerificationWindow(
            course_id=self.course_id,
            ordre_predit=self.prediction_ids,
            ordre_reel=prediction_ordre_participants_verification(self.course_id),
            parent=self
        )
        window.exec()

    def _setup_ui(self):
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

        if self.donnees_a_afficher: #afficher toutes les données spécifiées dans le dictionnaire donnees_a_afficher
            fields = self.donnees_a_afficher
        else: #si aucune donnée spécifiée, afficher toutes les données disponibles
            fields = {
                k: k.replace("_", " ").title()
                for k in self.course_data.keys()
                if k != "error"
            }

        for key, label in fields.items():
            if key in self.course_data:
                row = QHBoxLayout()

                key_label = QLabel(f"<b>{label}:</b>") #L'utilisation de <b> permet de mettre le texte en gras
                key_label.setMinimumWidth(150)
                row.addWidget(key_label)

                value_label = QLabel(str(self.course_data[key]))
                value_label.setWordWrap(True) #Permet de gérer le retour à la ligne automatique si le texte est trop long
                row.addWidget(value_label, 1)

                layout_detail.addLayout(row)

        layout_detail.addStretch()
        scroll_detail.setWidget(content)
        main_layout.addWidget(scroll_detail)

        # ===== Participants =====

        donnees_a_afficher_participant = donnees_a_afficher_bouton_particpant 
        participants_widget = QWidget()
        layout_participant = QVBoxLayout(participants_widget)
        layout_participant.addWidget(QLabel("Participants dans l'ordre d'arrivée prédite"))
        List_container(
            None,
            id_a_afficher=self.prediction_ids,
            donnees_a_afficher=donnees_a_afficher_participant,
            get_data=self.get_participant_predits_data,
            main_layout=layout_participant,
            detailWindow=ParticipantDetailWindow
        )
        layout_participant.addStretch()
        main_layout.addWidget(participants_widget)
        
        # ===== Bouton verifier =====
        verif_btn = QPushButton("Verifier l'ordre réel d'arrivée")
        verif_btn.clicked.connect(self._ouvrir_verification_window)
        main_layout.addWidget(verif_btn)

        # ===== Bouton fermer =====
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn)

