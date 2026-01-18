import sys
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from .CourseDetailWindows import CourseDetailWindow
from .data_access import (
    colonnes_filtrage_courses,
    colonnes_filtrage_groupes,
    colonnes_filtrage_participants,
    colonnes_tri_courses,
    colonnes_tri_participants,
    donnees_a_afficher_bouton_particpant,
    donnees_a_afficher_boutons_course,
    get_course_data,
    get_course_recentes_id,
    get_meilleurs_cheveaux_ids,
    get_participants_data,
    type_graphiques_groupes,
    update_graphe_data,
)
from .Filtre import Filtre
from .Graphe import Graphe

# from projet_pai_turff.my_module import typed_function
from .List_container import List_container
from .OngletButton import OngletButton
from .ParticipantDetailWindow import ParticipantDetailWindow


def run():
    app = QApplication(sys.argv)
    style = """
    QWidget { background: #f6f8fb; color: #222; }
    QLabel.title { font-size: 50px; font-weight: 600; color: #1b3b6f; }
    QPushButton { background: #c0d2f5; color: #0d2042; border-radius: 6px; padding: 8px 12px; }
    QPushButton.secondary { background: transparent; color: #2d6cdf; border: 1px solid #d9e4ff; }
    """
    app.setStyleSheet(style)

    # Fenêtre principale
    main_widget = QWidget()
    main_widget.setWindowTitle("Guide sur les paris hippiques")
    main_layout = QHBoxLayout()

    # Barre de navigation (toujours visible)
    nav_layout = QVBoxLayout()

    # Ajuster le style global des tooltips pour qu'ils soient lisibles
    QToolTip.setFont(QToolTip.font())
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    QToolTip.setPalette(palette)

    # Trouver le dossier assets par rapport à ce fichier (OngletButton peut aussi gérer les chemins)
    assets_dir = Path(__file__).resolve().parent / "assets"

    # Taille des icônes affichées sur les boutons
    ICON_SIZE = QSize(100, 100)

    # Liste (fichier, label) dans l'ordre des pages
    nav_keys = [
        (assets_dir / "courses.png", "Courses récentes"),
        (assets_dir / "podium.png", "Podium des chevaux"),
        (assets_dir / "stats.png", "Statistiques"),
        (assets_dir / "predictions.png", "Prédictions"),
    ]

    # Créer les boutons via la classe OngletButton
    nav_buttons = []
    for path, label in nav_keys:
        btn = OngletButton(path, label, icon_size=ICON_SIZE)
        nav_buttons.append(btn)
        nav_layout.addWidget(btn)

    nav_layout.addStretch()
    main_layout.addLayout(nav_layout)

    # QStackedWidget pour gérer les pages
    stacked = QStackedWidget()

    # --------Page 1 - Courses récentes-------
    page1 = QWidget()
    layout1 = QVBoxLayout()
    layout1.addWidget(QLabel("Courses récentes"))

    # Ajouter le widget Filtre
    colonnes_filtrage = colonnes_filtrage_courses
    colonnes_tri = colonnes_tri_courses
    filtre_widget1 = Filtre(
        colonnes_filtrage,
        colonnes_tri,
        tri_initial="date",
        ordre_croissant_initial=False,
    )
    layout1.addWidget(filtre_widget1)

    # Définir les données à afficher sur les boutons (même pour toutes les courses)
    donnees_a_afficher = donnees_a_afficher_boutons_course
    courses_recents_ids = get_course_recentes_id(filtre_widget1)

    # Put course cards inside a scrollable area
    list_container1 = List_container(
        None,
        id_a_afficher=courses_recents_ids,
        donnees_a_afficher=donnees_a_afficher,
        get_data=get_course_data,
        main_layout=layout1,
        CourseDetailWindow=CourseDetailWindow,
    )
    filtre_widget1.filtres_changes.connect(
        lambda: list_container1.update(get_course_recentes_id(filtre_widget1))
    )

    page1.setLayout(layout1)

    # --------Page 2 - Meilleurs cheveaux-------
    page2 = QWidget()
    layout2 = QVBoxLayout()
    layout2.addWidget(QLabel("Podium des chevaux"))

    # Ajouter le widget Filtre
    colonnes_filtrage = colonnes_filtrage_participants
    colonnes_tri = colonnes_tri_participants
    filtre_widget2 = Filtre(
        colonnes_filtrage,
        colonnes_tri,
        tri_initial="meilleurs toutes catégories",
        ordre_croissant_initial=False,
    )
    layout2.addWidget(filtre_widget2)

    # Définir les données à afficher sur les boutons (même pour toutes les courses)
    donnees_a_afficher_participant = donnees_a_afficher_bouton_particpant
    meilleurs_cheveaux_ids = get_meilleurs_cheveaux_ids(filtre_widget2)

    # Put course cards inside a scrollable area
    list_container2 = List_container(
        None,
        id_a_afficher=meilleurs_cheveaux_ids,
        donnees_a_afficher=donnees_a_afficher_participant,
        get_data=get_participants_data,
        main_layout=layout2,
        CourseDetailWindow=ParticipantDetailWindow,
    )
    filtre_widget2.filtres_changes.connect(
        lambda: list_container2.update(get_meilleurs_cheveaux_ids(filtre_widget2))
    )

    page2.setLayout(layout2)

    # --------Page 3 - Statistiques générales -------
    def _on_graph_type_changed3(graph_type: str):
        nonlocal current_graph_type3
        current_graph_type3 = graph_type
        update_graphe3()

    def update_graphe3():
        update_graphe_data(current_graph_type3, filtre_widget3, graphe3)

    current_graph_type3 = type_graphiques_groupes[0]
    page3 = QWidget()
    layout3 = QVBoxLayout()
    layout3.addWidget(QLabel("Statistiques générales"))
    layout3.addWidget(QLabel(" "))

    graph_layout3 = QHBoxLayout()
    param_layout3 = QVBoxLayout()

    combo_graph3 = QComboBox()
    combo_graph3.addItems(type_graphiques_groupes)

    combo_graph3.currentTextChanged.connect(_on_graph_type_changed3)

    param_layout3.addWidget(QLabel("Type de graphe :"))
    param_layout3.addWidget(combo_graph3)

    colonnes_filtrage = colonnes_filtrage_groupes
    filtre_widget3 = Filtre(colonnes_filtrage)

    param_layout3.addWidget(QLabel("Filtre sur les types de courses :"))
    param_layout3.addWidget(filtre_widget3)

    filtre_widget3.filtres_changes.connect(lambda: update_graphe3())

    param_layout3.addStretch()
    graph_layout3.addLayout(param_layout3, 1)

    graphe3 = Graphe(parent=page3, layout=graph_layout3)

    layout3.addLayout(graph_layout3)
    update_graphe3()

    layout3.addStretch()
    page3.setLayout(layout3)

    # --------Page 4 - Prédictions -------

    page4 = QWidget()
    layout4 = QVBoxLayout()
    layout4.addWidget(QLabel("Prédictions"))
    layout4.addStretch()
    page4.setLayout(layout4)

    # --------Principal ---------

    # Ajouter les pages au QStackedWidget
    stacked.addWidget(page1)  # index 0
    stacked.addWidget(page2)  # index 1
    stacked.addWidget(page3)  # index 2
    stacked.addWidget(page4)  # index 3

    # Lorsqu'on active une page, on demande au bouton de passer en mode actif
    def highlight_active(active_index: int):
        for i, b in enumerate(nav_buttons):
            # OngletButton expose set_active(active: bool)
            try:
                b.set_active(i == active_index)
            except Exception:
                # ignore if button doesn't implement set_active
                pass

    def set_active(index: int):
        # change la page et met à jour l'icône du bouton actif
        stacked.setCurrentIndex(index)
        highlight_active(index)

    # Connecter les boutons de navigation aux changements de page via set_active
    for i, b in enumerate(nav_buttons):
        b.clicked.connect(lambda _checked, idx=i: set_active(idx))

    # Marquer la première page comme active au démarrage
    set_active(0)

    main_layout.addWidget(stacked)
    main_widget.setLayout(main_layout)
    main_widget.show()

    app.exec()
    # typed_function(np.zeros(10), "")
    """This is the main function that gets run"""


if __name__ == "__main__":
    run()
