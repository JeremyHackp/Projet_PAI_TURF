from .Filtre import Filtre
from .Graphe import Graphe
import random


"""donnees_a_afficher_boutons_course: dictionnaire définissant quelles données afficher sur les boutons de course.
   donnees_a_afficher_bouton_particpant: dictionnaire définissant quelles données afficher sur les boutons de participants.
   donnees_a_afficher_detail_course: dictionnaire définissant quelles données afficher dans la fenêtre de détail d'une course.
   donnees_a_afficher_detail_participant: dictionnaire définissant quelles données afficher dans la fenêtre de détail d'un participant.

   chaque dictionnaire est de la forme {clé_dans_les_données: "Label à afficher"}.
"""


donnees_a_afficher_boutons_course = {
    "name": "Nom",
    "date": "Date",
    "place": "Lieu",
    "distance": "Distance",
}
donnees_a_afficher_bouton_particpant = {
    "name": "Nom",
    "jockey": "Jockey",
    "odds": "Cotes",
}
donnees_a_afficher_detail_course = {
    "name": "Nom",
    "date": "Date",
    "place": "Lieu",
    "distance": "Distance",
}
donnees_a_afficher_detail_participant = {
    "name": "Nom",
    "jockey": "Jockey",
    "odds": "Cotes",
}


"""
clés sur lesquels l'on peut filtrer et trier les courses et participants.
colonnes_filtrage est de la forme {clé_donnee: type_donnee}
colonnes_tri est de la forme {clé_donnee: "Label à afficher"}
"""

colonnes_filtrage_courses = {"name": str, "date": str, "distance": str, "place": str}
colonnes_tri_courses = {
    "name": "Nom",
    "date": "Date",
    "distance": "Distance",
    "place": "Lieu",
}
colonnes_filtrage_participants = {
    "name": str,
    "race": str,
    "jokey": str,
    "entraineur": str,
    "age": int,
    "odds": str,
}
colonnes_tri_participants = {
    "meilleurs toutes catégories": "Meilleurs toutes catégories",
    "meilleurs categorie1": "Meilleurs categorie1",
}


"""Fonctions a remplir pour l'accès aux données réelles.
   Les fonctions ci-dessous simulent l'accès à une base de données.
"""


# Fonctions de recupération de données
def get_course_data(course_id):
    """Simule la récupération des données d'une course depuis la base de données."""
    courses = {
        1: {
            "name": "Prix de l'Arc de Triomphe",
            "date": "2025-10-05",
            "place": "Hippodrome de Longchamp",
            "distance": "2400m",
            "horse_count": 18,
            "prize_pool": "1000000€",
            "surface": "Turf",
            "conditions": "Bon",
            "handicap": "Non",
            "category": "Groupe 1",
            "time": "15:00",
        },
        2: {
            "name": "Prix du Jockey Club",
            "date": "2025-06-01",
            "place": "Hippodrome de Chantilly",
            "distance": "2100m",
            "horse_count": 15,
            "prize_pool": "500000€",
            "surface": "Turf",
            "conditions": "Très bon",
            "handicap": "Non",
            "category": "Groupe 1",
            "time": "15:15",
        },
        3: {
            "name": "Grand Steeple-Chase de Paris",
            "date": "2025-05-18",
            "place": "Hippodrome d'Auteuil",
            "distance": "4500m",
            "horse_count": 20,
            "prize_pool": "200000€",
            "surface": "Obstacles",
            "conditions": "Bon",
            "handicap": "Oui",
            "category": "Groupe 2",
            "time": "14:45",
        },
    }
    return courses.get(course_id, {"error": f"Course {course_id} not found"})


def get_course_participants_id(course_id):
    """Simule la récupération des ids des participants d'une course depuis la base de données."""
    participants = [3, 4, 2, 1, 6, 5]
    return participants


def get_participants_data(participant_id):
    """Simule la récupération des données d'un participant depuis la base de données a partir de son id."""
    participants_info = {
        1: {
            "name": "Cheval A",
            "age": 4,
            "jockey": "Jockey 1",
            "trainer": "Trainer 1",
            "odds": "5/1",
        },
        2: {
            "name": "Cheval B",
            "age": 5,
            "jockey": "Jockey 2",
            "trainer": "Trainer 2",
            "odds": "3/1",
        },
        3: {
            "name": "Cheval C",
            "age": 3,
            "jockey": "Jockey 3",
            "trainer": "Trainer 3",
            "odds": "4/1",
        },
        4: {
            "name": "Cheval D",
            "age": 6,
            "jockey": "Jockey 4",
            "trainer": "Trainer 4",
            "odds": "6/1",
        },
        5: {
            "name": "Cheval E",
            "age": 4,
            "jockey": "Jockey 5",
            "trainer": "Trainer 5",
            "odds": "10/1",
        },
        6: {
            "name": "Cheval F",
            "age": 5,
            "jockey": "Jockey 6",
            "trainer": "Trainer 6",
            "odds": "8/1",
        },
    }
    return participants_info.get(
        participant_id, {"error": f"Participant {participant_id} not found"}
    )


# Fonction de récupération des IDs filtrés et triés


def get_course_recentes_id(filtre_widget: Filtre) -> list[int]:
    """Fonction simulée pour obtenir une liste d'IDs de course filtrée.

    Args:
        filtre_widget: Instance du widget Filtre contenant les critères de filtrage et de tri, si tri=aucun, trier du plus recent au moins recent.

    Returns:
        Liste des IDs de course correspondant aux critères, ordonnée selon le tri.
    """

    filtre = filtre_widget.get_state()
    """renvoie un dictionnaire de la forme {
    'filtres': List[
        Tuple[str(valeure filtrée), 
        OperateurComparaison(parmis EGAL,DIFFERENT, SUPERIEUR, INFERIEUR, SUPERIEUR_EGAL, INFERIEUR_EGAL, CONTIENT, NE_CONTIENT_PAS), 
        Any(valeure a comparer)]], 

    'tri': Optional[
        Tuple[str(valeure sur laquelle on tri), 
        bool(True : ordre_croissant, False : décroissant)]}]}
    """

    # Pour l'instant, retourne une liste aleatoire pour la démonstration
    i = random.randint(1, 3)
    return [1, 2, i]


def get_meilleurs_cheveaux_ids(filtre_widget):
    """Simule la récupération des IDs des meilleurs chevaux selon certains filtres (quipeuvent designer type de course, type de cheveaux, ect) et tri (dans quel type de courses ils exèlent)."""

    filtre = filtre_widget.get_state()
    """renvoie un dictionnaire de la forme {
    'filtres': List[
        Tuple[str(valeure filtrée), 
        OperateurComparaison(parmis EGAL,DIFFERENT, SUPERIEUR, INFERIEUR, SUPERIEUR_EGAL, INFERIEUR_EGAL, CONTIENT, NE_CONTIENT_PAS), 
        Any(valeure a comparer)]], 

    'tri': Optional[
        Tuple[str(valeure sur laquelle on tri), 
        bool(True : ordre_croissant, False : décroissant)]}]}
    """

    return [1, 2, 3, 4, 5, 6]


# Définition des types de graphiques et des colonnes de filtrage pour les participants

type_graphiques_participants = [
    "Performance au cours des courses",
    "Cotes au cours des courses",
]
colonnes_filtrage_types_de_courses_pour_participants = {
    "type_de_course": str,
    "surface": str,
    "distance": str,
    "condition_meteorologique": str,
}
type_graphiques_groupes = [
    "Performance au cours des courses",
    "Cotes au cours des courses",
]
colonnes_filtrage_groupes = {
    "type_de_course": str,
    "surface": str,
    "distance": str,
    "condition_meteorologique": str,
    "type_cheval": str,
}


def update_graphe_data(graph_type: str, filtre_widget: Filtre, graphe: Graphe):
    """Met à jour les données du graphe en fonction du type de graphe sélectionné et des filtres appliqués.

    Args:
        graph_type: Type de graphe sélectionné.
        filtre_widget: Widget Filtre contenant les critères de filtrage.
        graphe: Instance du graphe à mettre à jour.
    """
    # Simuler la récupération des données filtrées
    filtres = filtre_widget.get_filtres()

    # Pour l'instant, utilise des données aléatoires pour la démonstration
    if graph_type == "Performance au cours des courses":
        x_data = [1, 2, 3, 4, 5]
        y_data = [random.randint(1, 10) for _ in x_data]
        graphe.plot(
            x_data,
            y_data,
            title="Performance du cheval",
            xlabel="Courses",
            ylabel="Position",
            marker="o",
            linestyle="-",
        )  # .hist et .scatter sont egalement disponibles
    elif graph_type == "Cotes au cours des courses":
        x_data = [1, 2, 3, 4, 5]
        y_data = [random.uniform(1.0, 10.0) for _ in x_data]
        graphe.plot(
            x_data,
            y_data,
            title="Cotes du cheval",
            xlabel="Courses",
            ylabel="Cotes",
            marker="s",
            linestyle="--",
        )
