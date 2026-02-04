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


from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFileDialog, QMessageBox, QComboBox
)

import os
import sys

# Import dynamique de ton module Model.py
import importlib.util


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
    """
    Fenêtre de détail d'une course avec :
    - Affichage des informations de la course
    - Liste des participants (chevaux)
    - Sélection d'un modèle ML
    - Prédiction de l'ordre d'arrivée
    - Vérification de l'ordre prédit par rapport à l'ordre réel
    """

    def __init__(self, id: Any, parent=None, get_data=None):
        super().__init__(parent)

        # =============================
        # Identité et données de la course
        # =============================
        self.course_id = id
        self.get_data = get_data
        self.donnees_a_afficher = donnees_a_afficher_detail_course
        self.get_course_data = get_course_prediction_data
        self.get_participant_predits_data = get_participant_predits_data

        # Chargement des données de la course
        self.course_data = self.get_course_data(self.course_id)

        # Chargement des participants
        self.participants_data_list = self.get_participant_predits_data_for_course(self.course_id)

        # =============================
        # Modèle ML
        # =============================
        self.model_path = None
        self.model_module = None
        self.prediction_ids = []

        # =============================
        # Paramètres de la fenêtre
        # =============================
        self.setWindowTitle(f"Détails - {self.course_data.get('name', 'Course')}")
        self.setMinimumSize(700, 500)  # Peut être ajusté dynamiquement si nécessaire

        # Construction de l'UI
        self._setup_ui()

        # Affichage initial des participants
        self._refresh_participant_list(self.participants_data_list)

    # ======================================================================
    # DONNÉES PARTICIPANTS
    # ======================================================================

    def get_participant_predits_data_for_course(self, course_id):
        """
        Récupère les participants d'une course avec leurs données nécessaires à la prédiction.
        Retourne une liste de dictionnaires contenant au minimum :
        - id : ID du participant
        - name : nom du participant
        - odds : cote
        """
        participants = []
        participant_ids = get_course_participants_id(course_id)

        if not participant_ids:
            return participants

        for pid in participant_ids:
            data = self.get_participant_predits_data(pid, course_id) or {}
            data["id"] = pid
            data.setdefault("name", f"Participant {pid}")
            data.setdefault("odds", 0.0)
            participants.append(data)

        return participants

    # ======================================================================
    # CONSTRUCTION UI
    # ======================================================================

    def _setup_ui(self):
        """Construit toute l'interface graphique de la fenêtre."""

        self.main_layout = QVBoxLayout(self)

        # ===== Titre =====
        title = QLabel(self.course_data.get("name", "Course sans nom"))
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        self.main_layout.addWidget(title)

        # ===== Détails de la course =====
        scroll_detail = QScrollArea()
        scroll_detail.setWidgetResizable(True)
        detail_widget = QWidget()
        layout_detail = QVBoxLayout(detail_widget)

        fields = self.donnees_a_afficher or {
            k: k.replace("_", " ").title() for k in self.course_data.keys() if k != "error"
        }

        for key, label in fields.items():
            if key in self.course_data:
                row = QHBoxLayout()
                row.addWidget(QLabel(f"<b>{label}:</b>"))
                value = QLabel(str(self.course_data[key]))
                value.setWordWrap(True)
                row.addWidget(value, 1)
                layout_detail.addLayout(row)

        layout_detail.addStretch()
        scroll_detail.setWidget(detail_widget)
        self.main_layout.addWidget(scroll_detail)

        # ===== Participants (scrollable) =====
        scroll_participants = QScrollArea()
        scroll_participants.setWidgetResizable(True)
        self.participants_widget = QWidget()
        self.participants_layout = QVBoxLayout(self.participants_widget)
        self.participants_layout.addWidget(QLabel("Participants"))
        scroll_participants.setWidget(self.participants_widget)
        self.main_layout.addWidget(scroll_participants)

        # ===== Sélecteur de modèle ML =====
        self._setup_model_selector()

        # ===== Boutons =====
        btn_predict = QPushButton("Prédire")
        btn_predict.clicked.connect(self._predict)
        self.main_layout.addWidget(btn_predict)

        btn_verify_order = QPushButton("Vérifier l'ordre de la prédiction")
        btn_verify_order.clicked.connect(self._verify_prediction_order)
        self.main_layout.addWidget(btn_verify_order)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.close)
        self.main_layout.addWidget(close_btn)

    # ======================================================================
    # VÉRIFICATION DE L'ORDRE PRÉDIT
    # ======================================================================

    def _verify_prediction_order(self):
        """
        Ouvre une fenêtre pour comparer l'ordre prédit et l'ordre réel des participants.
        Affiche en rouge les erreurs de prédiction.
        """
        if not self.prediction_ids:
            QMessageBox.warning(self, "Erreur", "Aucune prédiction à vérifier")
            return

        ordre_reel = [p["id"] for p in self.participants_data_list]

        dialog = ParticipantVerificationWindow(
            course_id=self.course_id,
            ordre_predit=self.prediction_ids,
            ordre_reel=ordre_reel,
            parent=self
        )
        dialog.exec_()

    # ======================================================================
    # LISTE DES PARTICIPANTS
    # ======================================================================

    def _refresh_participant_list(self, participants_list):
        """
        Rafraîchit l'affichage de la liste des participants.
        Crée les boutons cliquables vers les détails de chaque participant.
        """
        # Nettoyage complet du layout
        while self.participants_layout.count():
            item = self.participants_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.participants_layout.addWidget(QLabel("Participants"))

        # Création des boutons via List_container
        List_container(
            parent=self.participants_widget,
            id_a_afficher=[p["id"] for p in participants_list],
            donnees_a_afficher=donnees_a_afficher_bouton_particpant,
            get_data=get_participants_data,
            main_layout=self.participants_layout,
            detailWindow=ParticipantDetailWindow,
        )

        self.participants_layout.addStretch()

    # ======================================================================
    # SÉLECTEUR DE MODÈLE
    # ======================================================================

    def _setup_model_selector(self):
        """
        Initialise le combobox pour sélectionner le modèle ML à utiliser.
        Charge automatiquement le premier modèle disponible.
        """
        self.main_layout.addWidget(QLabel("Choisir un modèle :"))
        self.model_selector = QComboBox()
        self.main_layout.addWidget(self.model_selector)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        models_root = os.path.join(base_dir, "Models")
        if not os.path.exists(models_root):
            QMessageBox.warning(self, "Erreur", "Dossier Models introuvable")
            return

        subfolders = [f for f in os.listdir(models_root) if os.path.isdir(os.path.join(models_root, f))]
        if not subfolders:
            QMessageBox.warning(self, "Erreur", "Aucun modèle trouvé")
            return

        self.model_selector.addItems(subfolders)
        self.model_selector.currentTextChanged.connect(self._load_selected_model)
        self._load_selected_model(subfolders[0])

    def _load_selected_model(self, folder_name):
        """
        Charge dynamiquement le modèle ML depuis un dossier donné.
        Le dossier doit contenir Model.h5 et Model.py
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        folder = os.path.join(base_dir, "Models", folder_name)
        model_file = os.path.join(folder, "Model.h5")
        model_py = os.path.join(folder, "Model.py")

        if not os.path.exists(model_file) or not os.path.exists(model_py):
            QMessageBox.warning(self, "Erreur", "Model.h5 ou Model.py manquant")
            self.model_module = None
            self.model_path = None
            return

        try:
            spec = importlib.util.spec_from_file_location("Model", model_py)
            self.model_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.model_module)
            self.model_path = model_file
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            self.model_module = None

    # ======================================================================
    # PRÉDICTION
    # ======================================================================

    def _predict(self):
        """
        Effectue la prédiction de l'ordre d'arrivée des participants
        en utilisant le modèle ML sélectionné.
        Rafraîchit l'affichage avec l'ordre prédit.
        """
        if not self.model_module or not self.model_path:
            QMessageBox.warning(self, "Erreur", "Aucun modèle valide")
            return

        participant_ids = [p["id"] for p in self.participants_data_list]

        try:
            self.prediction_ids = self.model_module.predict_ranking(participant_ids)
            self.prediction_ids = [pid for pid in self.prediction_ids if pid is not None]

            # Réordonner les participants selon la prédiction
            predicted_participants = [
                p for pid in self.prediction_ids
                for p in self.participants_data_list
                if p['id'] == pid
            ]

            self._refresh_participant_list(predicted_participants)
            QMessageBox.information(self, "Succès", "Prédiction affichée")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
