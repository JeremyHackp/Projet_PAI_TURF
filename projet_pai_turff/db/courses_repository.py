from .connection import get_connection

def get_all_courses():
    """
    Récupère toutes les courses depuis la base de données
    et retourne une liste de dicts.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                c.NumCourse,
                c.NumReunion,
                c.DateReunion,
                c.LabelCourse,
                c.Distance,
                c.Unite,
                c.NbrParticipants,
                c.TypePiste,
                c.CategorieParticularite,
                r.NomHippodrome,
                r.DateReunion
            FROM Courses c
            JOIN Reunions r
              ON r.NumReunion = c.NumReunion
             AND r.DateReunion = c.DateReunion
            ORDER BY r.DateReunion DESC, c.NumCourse
        """)
        return cur.fetchall()