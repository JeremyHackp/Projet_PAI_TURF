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

OP_SQL_MAP = {
    "=": lambda col, v: (f"{col} = ?", v),
    "!=": lambda col, v: (f"{col} != ?", v),
    ">": lambda col, v: (f"{col} > ?", v),
    "<": lambda col, v: (f"{col} < ?", v),
    ">=": lambda col, v: (f"{col} >= ?", v),
    "<=": lambda col, v: (f"{col} <= ?", v),
    "contient": lambda col, v: (f"{col} LIKE ?", f"%{v}%"),
    "ne contient pas": lambda col, v: (f"{col} NOT LIKE ?", f"%{v}%"),
}

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
    "horse_count": "NbrParticipants",
    "prize_pool": "Récompenses",
    "surface": "Type Piste",
    "conditions": "Penetrometre Intitule",
    "handicap": "Non",
    "category": "Categorie Particularite"
}
donnees_a_afficher_detail_participant = {
    "name": "Nom",
    "jockey": "Jockey",
    "odds": "Cotes",
    "age": "Age",
    "trainer": "Entraineur",
    "victories": "NbrVictoires",
    "total_gains": "GainsCarriere",
    "robe": "RobeLibelle" ,
    "race": "Race",
    "father": "NomDuPere",
    "mother": "NomDeLaMere" ,
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
    "meilleurs toutes catégories": "Meilleurs Gains Totaux",
    "meilleurs categorie1": "Meilleur nombre de Victoires",
}

"""Fonctions a remplir pour l'accès aux données réelles.
   Les fonctions ci-dessous effectuent l'accès à une base de données.
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

meilleurs_chevaux = ParticipantsCache()




def get_course_prediction_data(course_id):
    return get_course_data(course_id)

def prediction_ordre_participants(course_id):
    """Simule la prédiction de l'ordre des ids des participants d'une course."""
    participants = [3, 6, 2, 1, 4, 5]
    return participants
def prediction_ordre_participants_verification(course_id):
    """Simule la récupération des ids des participants d'une course depuis la base de données."""
    participants = [3, 4, 2, 1, 6, 5]
    return participants


def get_course_data(course_id):
    return course_cache.courses.get(course_id, {})

def get_cheveaux_data(cheval_id):
    """Simule la récupération des données d'un cheval depuis la base de données a partir de son id. Utilisé pour trouver les données d'un cheval dans le podium des meilleurs chevaux."""
    return meilleurs_chevaux.participants.get(cheval_id, {})

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
                p.PositionArrivee,
                p.NbrVictoires,
                p.GainsCarriere,

                c.RobeLibelle,
                c.Race,
                c.NomDuPere,
                c.NomDeLaMere

            FROM Participants p
            LEFT JOIN Cheval c
                ON c.Nom = p.Nom

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
            "victories": row["NbrVictoires"],
            "total_gains": f"{row['GainsCarriere']}€",

            "robe": row["RobeLibelle"] or "Inconnue",
            "race": row["Race"] or "Inconnue",
            "father": row["NomDuPere"] or "—",
            "mother": row["NomDeLaMere"] or "—",
        }
        ui_id += 1

    return list(participants_cache.participants.keys())


# Fonction de récupération des IDs filtrés et triés

def get_course_prediction_id(filtre_widget: Filtre) -> list[int]:
    return get_course_recentes_from_db(filtre_widget)



def get_course_recentes_from_db(filtre_widget: Filtre) -> list[int]:
    """
    Retourne les IDs des courses récentes en appliquant filtres et tri.
    """
    filtre_state = filtre_widget.get_state()
    filtres = filtre_state.get("filtres", [])
    tri = filtre_state.get("tri")
    nbr = filtre_state.get("nbr")

    # --- mappings SQL ---
    FILTRE_SQL_MAP = {
        "date": "r.DateReunion",
        "name": "c.LabelCourse",
        "distance": "c.Distance",
        "place": "r.NomHippodrome",
    }


    TRI_SQL_MAP = {
        "date": "r.DateReunion",
        "name": "c.LabelCourse",
        "distance": "c.Distance",
        "place": "r.NomHippodrome",
    }

    # --- construction WHERE ---
    where_clauses = []
    params = []

    for champ, operateur, valeur in filtres:
        colonne = FILTRE_SQL_MAP.get(champ)
        if not colonne:
            continue

        handler = OP_SQL_MAP.get(operateur)
        if not handler:
            continue

        clause, param = handler(colonne, valeur)
        where_clauses.append(clause)
        params.append(param)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    # --- construction ORDER BY ---
    order_sql = "r.DateReunion DESC"
    if tri is not None:
        cle_tri, ordre_croissant = tri
        colonne_tri = TRI_SQL_MAP.get(cle_tri, "r.DateReunion")
        sens = "ASC" if ordre_croissant else "DESC"
        order_sql = f"{colonne_tri} {sens}"

    # --- requête ---
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
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
            {where_sql}
            ORDER BY {order_sql}, c.NumCourse
            LIMIT {nbr}
            """,
            params,
        )

        rows = cur.fetchall()

    # --- remplissage cache ---
    course_cache.clear()
    ui_id = 1

    for row in rows:
        d = row["DateReunion"]

        course_cache.courses[ui_id] = {
            "name": row["LabelCourse"],
            "date": f"{d[:2]}/{d[2:4]}/{d[4:]}" if d and len(d) == 8 else d,
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
    Charge les meilleurs chevaux (1 par nom), avec toutes les infos participant disponibles,
    triés selon le filtre sélectionné.


    """

    FILTRE_SQL_MAP = {
        "name": "p.Nom",
        "race": "p.Sexe",
        "jokey": "p.Driver",
        "entraineur": "p.Entraineur",
        "age": "p.Age",
        "odds": "p.Cote"
    }


    filtres = filtre_widget.get_state()
    tri = filtres.get("tri") or ("meilleurs toutes catégories", False)

    # sécurité si format inattendu
    if not isinstance(tri, (list, tuple)) or len(tri) != 2:
        tri = ("meilleurs toutes catégories", False)

    tri_nom, ordre_croissant = tri
    nbr = filtres.get("nbr")
    filtre = filtres.get("filtres") or []

    # Map du tri vers les colonnes SQL
    TRI_SQL_MAP = {
        "meilleurs toutes catégories": "p.GainsCarriere",
        "meilleurs categorie1": "p.NbrVictoires",
    }
    order_column = TRI_SQL_MAP.get(tri_nom, "p.GainsCarriere")
    order_sql = "ASC" if ordre_croissant else "DESC"

    where_clauses = []
    params = []

    for champ, operateur, valeur in filtre:
        col_sql = FILTRE_SQL_MAP.get(champ)
        op_func = OP_SQL_MAP.get(operateur)

        if not col_sql or not op_func or valeur in (None, ""):
            continue

        # typage auto
        if champ == "age":
            valeur = int(valeur)

        sql_snippet, param = op_func(col_sql, valeur)
        where_clauses.append(sql_snippet)
        params.append(param)

    where_sql = ""
    if where_clauses:
        where_sql = "AND " + " AND ".join(where_clauses)

    query = f"""
        SELECT 
            p.Nom,
            p.Age,
            p.Driver,
            p.Entraineur,
            p.Cote,
            p.GainsCarriere,
            p.Sexe,
            p.NbrVictoires,
            c.NomDuPere,
            c.NomDeLaMere,
            c.RobeLibelle,
            c.Race
        FROM Participants p
        JOIN (
            SELECT Nom, MAX(DateReunion || printf('%03d', NumCourse)) AS last_participation
            FROM Participants
            GROUP BY Nom
        ) last
          ON last.Nom = p.Nom
         AND (p.DateReunion || printf('%03d', p.NumCourse)) = last.last_participation
        JOIN Cheval c ON c.Nom = p.Nom
        WHERE 1=1
        {where_sql}
        ORDER BY {order_column} {order_sql}
        LIMIT ?
    """

    params.append(nbr)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()

    meilleurs_chevaux.participants.clear()

    for i, row in enumerate(rows, start=1):
        meilleurs_chevaux.participants[i] = {
            "name": row["Nom"],
            "age": row["Age"],
            "jockey": row["Driver"],
            "trainer": row["Entraineur"],
            "odds": row["Cote"],
            "sex": row["Sexe"],
            "total_gains": f"{row['GainsCarriere']}€",
            "victories": row["NbrVictoires"] or 0,

            "robe": row["RobeLibelle"] or "Inconnue",
            "race": row["Race"] or "Inconnue",
            "father": row["NomDuPere"] or "—",
            "mother": row["NomDeLaMere"] or "—",
        }

    return list(meilleurs_chevaux.participants.keys())


# Définition des types de graphiques et des colonnes de filtrage pour les participants

type_graphiques_participants = [
    "Performance au cours des courses",
    "Cotes au cours des courses",
]
colonnes_filtrage_types_de_courses_pour_participants = {
    "type_de_course": str,
    "surface": str,
    "distance": str
}
type_graphiques_groupes = [
    "Victoires par race",
    "Taux de victoire par race",
    "Taux de victoire par âge",
    "Courses par surface",
    "Courses par type de course"
]
colonnes_filtrage_groupes = {
    "race": str,          # c.Race
    "age": int,           # p.Age
    "type_course": str,   # co.Discipline
    "surface": str,       # co.TypePiste
    "distance": int,      # co.Distance
}


def build_where_clause_stats(filtres):
    COL_SQL_MAP = {
        "race": "c.Race",
        "robe": "c.Robe",
        "pere": "c.NomPere",
        "mere": "c.NomMere",
        "age": "p.Age",
        "jockey": "p.Driver",
        "entraineur": "p.Entraineur",
        "type_course": "co.Discipline",
        "surface": "co.TypePiste",
        "distance": "co.Distance",
    }

    OP_SQL_MAP = {
        "=": lambda col, v: (f"{col} = ?", v),
        "!=": lambda col, v: (f"{col} != ?", v),
        ">": lambda col, v: (f"{col} > ?", v),
        "<": lambda col, v: (f"{col} < ?", v),
        ">=": lambda col, v: (f"{col} >= ?", v),
        "<=": lambda col, v: (f"{col} <= ?", v),
        "contient": lambda col, v: (f"{col} LIKE ?", f"%{v}%"),
        "ne contient pas": lambda col, v: (f"{col} NOT LIKE ?", f"%{v}%"),
    }

    clauses, params = [], []

    for f in filtres:
        if not f or len(f) != 3:
            continue
        champ, op, val = f
        col = COL_SQL_MAP.get(champ)
        func = OP_SQL_MAP.get(op)
        if not col or not func:
            continue
        sql, param = func(col, val)
        clauses.append(sql)
        params.append(param)

    if not clauses:
        return "", []

    return "WHERE " + " AND ".join(clauses), params


def update_graphe_individuel(graph_type, filtre_widget, graphe,
                             participant_id, cache_dict):
    participant = cache_dict.get(participant_id)
    if not participant:
        return

    participant_name = participant.get("name")
    if not participant_name:
        return

    state = filtre_widget.get_state()
    nbr = state.get("nbr", 20)
    filtres = state.get("filtres", [])

    where_sql, params = build_where_clause_stats(filtres)

    def add_condition(base_where, condition):
        if base_where:
            return base_where + " AND " + condition
        return "WHERE " + condition

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # ================= PERFORMANCE =================
        if graph_type == "Performance au cours des courses":
            print(filtres)
            where_full = add_condition(where_sql, "p.Nom = ?")
            where_full = add_condition(where_full, "p.PositionArrivee GLOB '[0-9]*'")

            query = f"""
                SELECT p.DateReunion,
                       CAST(p.PositionArrivee AS INTEGER) AS position
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_full}
                ORDER BY
                    SUBSTR(p.DateReunion,5,4)||'-'||SUBSTR(p.DateReunion,3,2)||'-'||SUBSTR(p.DateReunion,1,2)
                LIMIT ?
            """
            cur.execute(query, (*params, participant_name, nbr))

            rows = cur.fetchall()
            if not rows:
                return

            x_data = [f"{d[:2]}/{d[2:4]}/{d[4:]}" for d in (r["DateReunion"] for r in rows)]
            y_data = [r["position"] for r in rows]

            graphe.clear()
            graphe.plot(x_data, y_data,
                        title="Performance sur les courses",
                        xlabel="Date", ylabel="Position",
                        marker="o")

        # ================= COTES =================
        elif graph_type == "Cotes au cours des courses":
            where_full = add_condition(where_sql, "p.Nom = ?")
            where_full = add_condition(where_full, "p.Cote IS NOT NULL")

            query = f"""
                SELECT p.DateReunion, p.Cote
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_full}
                ORDER BY
                    SUBSTR(p.DateReunion,5,4)||'-'||SUBSTR(p.DateReunion,3,2)||'-'||SUBSTR(p.DateReunion,1,2)
                LIMIT ?
            """
            cur.execute(query, (*params, participant_name, nbr))

            rows = cur.fetchall()
            if not rows:
                return

            x_data = [f"{d[:2]}/{d[2:4]}/{d[4:]}" for d in (r["DateReunion"] for r in rows)]
            y_data = [float(r["Cote"]) for r in rows]

            graphe.clear()
            graphe.plot(x_data, y_data,
                        title="Évolution des cotes",
                        xlabel="Date", ylabel="Cote",
                        marker="o")

    graphe.ax.tick_params(axis="x", labelrotation=90)
    graphe.figure.tight_layout()


def update_graphe_stats_groupe(tri_nom, filtre_widget, graphe):

    state = filtre_widget.get_state()
    filtres = state.get("filtres", [])
    nbr = state.get("nbr")
    where_sql, params = build_where_clause_stats(filtres)

    def add_condition(base_where, condition):
        if base_where:
            return base_where + " AND " + condition
        return "WHERE " + condition

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # -------------------------------------------------------------
        # VICTOIRES PAR RACE
        # -------------------------------------------------------------
        if tri_nom == "Victoires par race":
            where_full = add_condition(where_sql, "p.PositionArrivee='1'")
            query = f"""
                SELECT c.Race AS categorie, COUNT(*) AS victoires
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_full}
                GROUP BY c.Race
                ORDER BY victoires DESC
                LIMIT ?
            """
            cur.execute(query, (*params, nbr))
            rows = cur.fetchall()
            ylabel = "Nombre de victoires"
            title = "Nombre de victoires par race"
            marker, linestyle = "s", ""
            x_data = [r["categorie"] for r in rows]
            y_data = [r["victoires"] for r in rows]

        # -------------------------------------------------------------
        # TAUX DE VICTOIRE PAR RACE
        # -------------------------------------------------------------
        elif tri_nom == "Taux de victoire par race":
            query = f"""
                SELECT c.Race AS categorie,
                       COUNT(*) AS courses,
                       SUM(CASE WHEN p.PositionArrivee='1' THEN 1 ELSE 0 END) AS victoires
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_sql}
                GROUP BY c.Race
                HAVING courses > 30
                ORDER BY (victoires*100.0/courses) DESC
                LIMIT ?
            """
            cur.execute(query, (*params, nbr))
            rows = cur.fetchall()
            ylabel = "% de victoires"
            title = "Taux de victoire par race"
            marker, linestyle = "s", ""
            x_data = [r["categorie"] for r in rows]
            y_data = [(r["victoires"]*100.0/r["courses"]) for r in rows]

        # -------------------------------------------------------------
        # TAUX DE VICTOIRE PAR ÂGE
        # -------------------------------------------------------------
        elif tri_nom == "Taux de victoire par âge":
            query = f"""
                SELECT p.Age AS categorie,
                       COUNT(*) AS courses,
                       SUM(CASE WHEN p.PositionArrivee='1' THEN 1 ELSE 0 END) AS victoires
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_sql}
                GROUP BY p.Age
                HAVING courses > 30
                ORDER BY p.Age
            """
            cur.execute(query, params)
            rows = cur.fetchall()
            ylabel = "% de victoires"
            title = "Taux de victoire par âge"
            marker, linestyle = "o", "-"
            x_data = [r["categorie"] for r in rows]
            y_data = [(r["victoires"]*100.0/r["courses"]) for r in rows]

        # -------------------------------------------------------------
        # COURSES PAR TYPE
        # -------------------------------------------------------------
        elif tri_nom == "Courses par type de course":
            query = f"""
                SELECT co.Discipline AS categorie, COUNT(*) AS nb
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_sql}
                GROUP BY co.Discipline
                ORDER BY nb DESC
            """
            cur.execute(query, params)
            rows = cur.fetchall()
            ylabel = "Nombre de courses"
            title = "Répartition des courses par type"
            marker, linestyle = "s", ""
            x_data = [r["categorie"] for r in rows]
            y_data = [r["nb"] for r in rows]

        # -------------------------------------------------------------
        # COURSES PAR SURFACE
        # -------------------------------------------------------------
        elif tri_nom == "Courses par surface":
            query = f"""
                SELECT co.TypePiste AS categorie, COUNT(*) AS nb
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_sql}
                GROUP BY co.TypePiste
                ORDER BY nb DESC
            """
            cur.execute(query, params)
            rows = cur.fetchall()
            ylabel = "Nombre de courses"
            title = "Répartition des courses par surface"
            marker, linestyle = "s", ""
            x_data = [r["categorie"] for r in rows]
            y_data = [r["nb"] for r in rows]

        else:
            return

    # -------------------------------------------------------------
    # Affichage graphique
    # -------------------------------------------------------------
    if not x_data:
        graphe.clear()
        graphe.ax.text(0.5, 0.5, "Aucune donnée",
                       ha='center', va='center',
                       transform=graphe.ax.transAxes)
        graphe.figure.tight_layout()
        return

    graphe.clear()
    graphe.plot(x_data, y_data, title=title,
                xlabel="Catégorie", ylabel=ylabel,
                marker=marker, linestyle=linestyle)
    graphe.ax.tick_params(axis="x", rotation=90)
    graphe.figure.tight_layout()


def update_graphe_data(
    graph_type: str,
    filtre_widget: Filtre,
    graphe: Graphe,
    participant_id: int | None = None,
    get_data=None
):
    # MODE STATS GROUPE
    if get_data is None:
        update_graphe_stats_groupe(graph_type, filtre_widget, graphe)
        return

    # MODES INDIVIDUELS
    if participant_id is None:
        return

    if get_data is get_participants_data:
        update_graphe_individuel(graph_type, filtre_widget, graphe,
                                 participant_id, participants_cache.participants)

    elif get_data is get_cheveaux_data:
        update_graphe_individuel(graph_type, filtre_widget, graphe,
                                 participant_id, meilleurs_chevaux.participants)

    else:
        print("Source de données inconnue")

