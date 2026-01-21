import random

from .Filtre import Filtre
from .Graphe import Graphe
import random
import sqlite3
from .db.connection import get_connection

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

class CourseCache:
    def __init__(self):
        self.courses = {}  # {ui_id: course_dict}

    def clear(self):
        self.courses.clear()


course_cache = CourseCache()


class ParticipantsCache:
    def __init__(self):
        self.participants = {}  # {ui_id: participant_dict}

    def clear(self):
        self.participants.clear()


participants_cache = ParticipantsCache()




def get_course_prediction_data(course_id):
    return get_course_data(course_id)


def get_course_data(course_id):
    return course_cache.courses.get(course_id, {})

def get_cheveaux_data(cheval_id):
    """Simule la récupération des données d'un cheval depuis la base de données a partir de son id. Utilisé pour trouver les données d'un cheval dans le podium des meilleurs chevaux."""
    return get_participants_data(cheval_id)

def get_participant_predits_data(participant_id):
    """Simule la récupération des données d'un participant prédit depuis la base de données a partir de son id. utilisé pour trouver les données d'un particpant d'une course dans la fenetre de prédiction."""
    return get_participants_data(participant_id)

def get_participants_data(participant_id):
    return participants_cache.participants.get(participant_id, {})


def get_course_participants_id(course_ui_id):
    """
    Charge tous les participants de la course depuis la BDD
    et remplit le cache participants.
    Retourne les IDs UI (1..N)
    """

    course = course_cache.courses.get(course_ui_id)
    if not course:
        return []

    num_course = course["_num_course"]
    num_reunion = course["_num_reunion"]
    date_reunion = course["_date_reunion"]

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                p.Nom,
                p.Age,
                p.Driver,
                p.Entraineur,
                p.Cote,
                p.PositionArrivee
            FROM Participants p
            WHERE p.NumCourse = ?
              AND p.NumReunion = ?
              AND p.DateReunion = ?
            ORDER BY
                CASE
                    WHEN p.PositionArrivee GLOB '[0-9]*'
                    THEN CAST(p.PositionArrivee AS INTEGER)
                    ELSE 999
                END
        """, (num_course, num_reunion, date_reunion))

        rows = cur.fetchall()

    participants_cache.clear()

    ui_id = 1
    for row in rows:
        participants_cache.participants[ui_id] = {
            "name": row["Nom"],
            "age": row["Age"],
            "jockey": row["Driver"],
            "trainer": row["Entraineur"],
            "odds": row["Cote"] if row["Cote"] else "N/A",
        }
        ui_id += 1

    return list(participants_cache.participants.keys())


# Fonction de récupération des IDs filtrés et triés

def get_course_prediction_id(filtre_widget: Filtre) -> list[int]:
    return get_course_recentes_from_db(filtre_widget)



def get_course_recentes_from_db(filtre_widget: Filtre) -> list[int]:
    """Fonction simulée pour obtenir une liste d'IDs de course filtrée.

    Args:
        filtre_widget: Instance du widget Filtre contenant les critères de filtrage et de tri, si tri=aucun, trier du plus recent au moins recent.

    Returns:
        Liste des IDs de course correspondant aux critères, ordonnée selon le tri.
    """

    filtre = filtre_widget.get_state()  # noqa: F841
    """renvoie un dictionnaire de la forme {
    'filtres': List[
        Tuple[str(valeure filtrée),
        OperateurComparaison(parmis EGAL,DIFFERENT, SUPERIEUR, INFERIEUR, SUPERIEUR_EGAL, INFERIEUR_EGAL, CONTIENT, NE_CONTIENT_PAS),
        Any(valeure a comparer)]],

    'tri': Optional[
        Tuple[str(valeure sur laquelle on tri),
        bool(True : ordre_croissant, False : décroissant)]}]}
    """

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
                SELECT
                    c.NumCourse,
                    c.NumReunion,
                    c.DateReunion,
                    c.LabelCourse,
                    r.NomHippodrome,
                    c.Distance,
                    c.Unite,
                    c.NbrParticipants,
                    (
                        c.MontantOffert1er +
                        IFNULL(c.MontantOffert2eme, 0) +
                        IFNULL(c.MontantOffert3eme, 0) +
                        IFNULL(c.MontantOffert4eme, 0) +
                        IFNULL(c.MontantOffert5eme, 0)
                    ) AS prize_pool,
                    c.TypePiste,
                    c.PenetrometreIntitule,
                    c.CategorieParticularite
                FROM Courses c
                JOIN Reunions r
                  ON r.NumReunion = c.NumReunion
                 AND r.DateReunion = c.DateReunion
                ORDER BY r.DateReunion DESC, c.NumCourse
                LIMIT 10
            """)

        rows = cur.fetchall()

    course_cache.clear()

    ui_id = 1
    for row in rows:
        course_cache.courses[ui_id] = {
            "name": row["LabelCourse"],
            "date": row["DateReunion"],
            "place": row["NomHippodrome"],
            "distance": f"{row['Distance']}{row['Unite']}",
            "horse_count": row["NbrParticipants"],
            "prize_pool": f"{row['prize_pool']}€",
            "surface": row["TypePiste"],
            "conditions": row["PenetrometreIntitule"],
            "handicap": "Non",
            "category": row["CategorieParticularite"],
            "time": None,

            # clés techniques
            "_num_course": row["NumCourse"],
            "_num_reunion": row["NumReunion"],
            "_date_reunion": row["DateReunion"],
        }
        ui_id += 1

    return list(course_cache.courses.keys())


def get_meilleurs_cheveaux_ids(filtre_widget):
    """
    Charge les meilleurs chevaux (1 par nom),
    avec toutes les infos participant disponibles.
    """
    participants_cache.clear()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                p.Nom,
                p.Age,
                p.Driver,
                p.Entraineur,
                p.Cote,
                p.GainsCarriere,
                p.Sexe
            FROM Participants p
            JOIN (
                SELECT
                    Nom,
                    MAX(GainsCarriere) AS max_gains
                FROM Participants
                WHERE GainsCarriere IS NOT NULL
                GROUP BY Nom
            ) best
              ON best.Nom = p.Nom
             AND best.max_gains = p.GainsCarriere
            ORDER BY p.GainsCarriere DESC
            LIMIT 20
        """)

        rows = cur.fetchall()

    for i, row in enumerate(rows, start=1):
        participants_cache.participants[i] = {
            "name": row["Nom"],
            "age": row["Age"],
            "jockey": row["Driver"],
            "trainer": row["Entraineur"],
            "odds": row["Cote"],
            "sex": row["Sexe"],
            "total_gains": f"{row['GainsCarriere']}€",
        }

    return list(participants_cache.participants.keys())





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


def update_graphe_data(
    graph_type: str,
    filtre_widget: Filtre,
    graphe: Graphe,
    participant_id: int | None = None,
    get_data=None
):
    if participant_id is None:
        return

    participant = participants_cache.participants.get(participant_id)
    if not participant:
        return
    """
    Args:
        graph_type: Type de graphe sélectionné.
        filtre_widget: Widget Filtre contenant les critères de filtrage.
        graphe: Instance du graphe à mettre à jour.
        id : ID du participant ou du sujet du graphe.
        get_data : Fonction de récupération des données du milieu dans lequel on a le graphe : get_cheveaux_data pour la fenetre podium des cheveaux, 
                get_participant_data pour la fenetre des participants de courses et None pour les stats générales.
    """
    # Simuler la récupération des données filtrées
    filtres = filtre_widget.get_filtres()  # noqa: F841
    participant_name = participant.get("name")
    if not participant_name:
        return

    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            if graph_type == "Performance au cours des courses":
                cur.execute(
                    """
                    SELECT
                        DateReunion,
                        CAST(PositionArrivee AS INTEGER) AS position
                    FROM Participants
                    WHERE Nom = ?
                      AND PositionArrivee GLOB '[0-9]*'
                    ORDER BY
                    SUBSTR(DateReunion, 5, 4) || '-' ||
                    SUBSTR(DateReunion, 3, 2) || '-' ||
                    SUBSTR(DateReunion, 1, 2) ASC
                    LIMIT 10
                    """,
                    (participant_name,),
                )

                rows = cur.fetchall()
                if not rows:
                    return


                x_data = [
                    f"{d[:2]}/{d[2:4]}/{d[4:]}"
                    for d in (row["DateReunion"] for row in rows)
                    if d and len(d) == 8
                ]

                y_data = [int(row["position"]) for row in rows]

                graphe.clear()
                graphe.plot(
                    x_data,
                    y_data,
                    title="Performance sur les dernières courses",
                    xlabel="Date de la course",
                    ylabel="Position d'arrivée",
                    marker="o",
                    linestyle="-",
                )

            elif graph_type == "Cotes au cours des courses":
                cur.execute(
                    """
                    SELECT
                    DateReunion,
                    Cote
                    FROM Participants
                    WHERE Nom = ?
                    AND Cote IS NOT NULL
                    ORDER BY
                    SUBSTR(DateReunion, 5, 4) || '-' ||
                    SUBSTR(DateReunion, 3, 2) || '-' ||
                    SUBSTR(DateReunion, 1, 2) ASC
                    LIMIT 10
                    """,
                    (participant_name,),
                )

                rows = cur.fetchall()
                if not rows:
                    return

                x_data = [
                    f"{d[:2]}/{d[2:4]}/{d[4:]}"
                    for d in (row["DateReunion"] for row in rows)
                    if d and len(d) == 8
                ]

                y_data = [float(row["cote"]) for row in rows]

                graphe.clear()
                graphe.plot(
                    x_data,
                    y_data,
                    title="Évolution des cotes",
                    xlabel="Date de la course",
                    ylabel="Cote",
                    marker="o",
                    linestyle="-",
                )

    except Exception as e:
        print(f"Erreur update_graphe_data: {e}")
