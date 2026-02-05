"""
participant_data.py - Accès aux données des participants
"""

from .cache import course_cache, meilleurs_chevaux, participants_cache
from .constants import OP_SQL_MAP
from .db.connection import get_connection


def get_participants_data(participant_id):
    """
    Récupère les données d'un participant depuis le cache.

    Args:
        participant_id: ID du participant dans le cache

    Returns:
        dict: Données du participant ou dict vide si non trouvé
    """
    return participants_cache.participants.get(participant_id, {})


def get_cheveaux_data(cheval_id):
    """
    Récupère les données d'un cheval depuis le cache des meilleurs chevaux.

    Args:
        cheval_id: ID du cheval dans le cache

    Returns:
        dict: Données du cheval ou dict vide si non trouvé
    """
    return meilleurs_chevaux.participants.get(cheval_id, {})


def get_participant_predits_data(participant_id):
    """
    Récupère les données d'un participant prédit.
    Alias de get_participants_data.
    """
    return get_participants_data(participant_id)


def get_course_participants_id(course_ui_id):
    """
    Charge tous les participants de la course depuis la BDD
    et remplit le cache participants.

    Args:
        course_ui_id: ID UI de la course

    Returns:
        list[int]: Liste des IDs UI des participants (1..N)
    """
    course = course_cache.courses.get(course_ui_id)
    if not course:
        return []

    num_course = course["_num_course"]
    num_reunion = course["_num_reunion"]
    date_reunion = course["_date_reunion"]

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
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
        """,
            (num_course, num_reunion, date_reunion),
        )

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


def get_meilleurs_cheveaux_ids(filtre_widget):
    """
    Charge les meilleurs chevaux (1 par nom) avec toutes les infos participant,
    triés selon le filtre sélectionné.

    Args:
        filtre_widget: Widget de filtre contenant l'état des filtres

    Returns:
        list[int]: Liste des IDs UI des meilleurs chevaux
    """
    FILTRE_SQL_MAP = {
        "name": "p.Nom",
        "race": "p.Sexe",
        "jokey": "p.Driver",
        "entraineur": "p.Entraineur",
        "age": "p.Age",
        "odds": "p.Cote",
    }

    filtres = filtre_widget.get_state()
    tri = filtres.get("tri") or ("meilleurs toutes catégories", False)

    # Sécurité si format inattendu
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

        # Typage auto
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
