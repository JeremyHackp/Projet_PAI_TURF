"""
query_builder.py - Construction des requêtes SQL et clauses WHERE
"""
from .constants import OP_SQL_MAP


def build_where_clause_stats(filtres):
    """
    Construit une clause WHERE SQL à partir d'une liste de filtres.
    
    Args:
        filtres: Liste de tuples (champ, operateur, valeur)
    
    Returns:
        tuple: (clause_where_sql, liste_parametres)
    """
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
