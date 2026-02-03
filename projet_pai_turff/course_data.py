"""
course_data.py - Accès aux données des courses
"""
from .db.connection import get_connection
from .cache import course_cache
from .constants import OP_SQL_MAP


def get_course_data(course_id):
    """
    Récupère les données d'une course depuis le cache.
    
    Args:
        course_id: ID de la course dans le cache
    
    Returns:
        dict: Données de la course ou dict vide si non trouvée
    """
    return course_cache.courses.get(course_id, {})


def get_course_prediction_data(course_id):
    """
    Récupère les données d'une course pour la prédiction.
    Alias de get_course_data.
    """
    return get_course_data(course_id)


def get_course_recentes_from_db(filtre_widget) -> list[int]:
    """
    Retourne les IDs des courses récentes en appliquant filtres et tri.
    
    Args:
        filtre_widget: Widget de filtre contenant l'état des filtres
    
    Returns:
        list[int]: Liste des IDs UI des courses
    """
    filtre_state = filtre_widget.get_state()
    filtres = filtre_state.get("filtres", [])
    tri = filtre_state.get("tri")
    nbr = filtre_state.get("nbr")

    # Mappings SQL
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

    # Construction WHERE
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

    # Construction ORDER BY
    order_sql = "r.DateReunion DESC"
    if tri is not None:
        cle_tri, ordre_croissant = tri
        colonne_tri = TRI_SQL_MAP.get(cle_tri, "r.DateReunion")
        sens = "ASC" if ordre_croissant else "DESC"
        order_sql = f"{colonne_tri} {sens}"

    # Requête
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

    # Remplissage cache
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

            # Clés techniques
            "_num_course": row["NumCourse"],
            "_num_reunion": row["NumReunion"],
            "_date_reunion": row["DateReunion"],
        }
        ui_id += 1

    return list(course_cache.courses.keys())


def get_course_prediction_id(filtre_widget) -> list[int]:
    """
    Retourne les IDs des courses pour la prédiction.
    Alias de get_course_recentes_from_db.
    """
    return get_course_recentes_from_db(filtre_widget)
