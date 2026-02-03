"""
constants.py - Constantes et configurations du projet
"""

# Opérateurs SQL pour les filtres
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

# Données à afficher sur les boutons de course
donnees_a_afficher_boutons_course = {
    "name": "Nom",
    "date": "Date",
    "place": "Lieu",
    "distance": "Distance",
}

# Données à afficher sur les boutons de participant
donnees_a_afficher_bouton_particpant = {
    "name": "Nom",
    "jockey": "Jockey",
    "odds": "Cotes",
}

# Données à afficher dans la fenêtre de détail d'une course
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

# Données à afficher dans la fenêtre de détail d'un participant
donnees_a_afficher_detail_participant = {
    "name": "Nom",
    "jockey": "Jockey",
    "odds": "Cotes",
    "age": "Age",
    "trainer": "Entraineur",
    "victories": "NbrVictoires",
    "total_gains": "GainsCarriere",
    "robe": "RobeLibelle",
    "race": "Race",
    "father": "NomDuPere",
    "mother": "NomDeLaMere",
}

# Colonnes de filtrage pour les courses
colonnes_filtrage_courses = {
    "name": str,
    "date": str,
    "distance": str,
    "place": str
}

# Colonnes de tri pour les courses
colonnes_tri_courses = {
    "name": "Nom",
    "date": "Date",
    "distance": "Distance",
    "place": "Lieu",
}

# Colonnes de filtrage pour les participants
colonnes_filtrage_participants = {
    "name": str,
    "race": str,
    "jokey": str,
    "entraineur": str,
    "age": int,
    "odds": str,
}

# Colonnes de tri pour les participants
colonnes_tri_participants = {
    "meilleurs toutes catégories": "Meilleurs Gains Totaux",
    "meilleurs categorie1": "Meilleur nombre de Victoires",
}

# Types de graphiques pour les participants individuels
type_graphiques_participants = [
    "Performance au cours des courses",
    "Cotes au cours des courses",
]

# Colonnes de filtrage pour les types de courses (graphiques participants)
colonnes_filtrage_types_de_courses_pour_participants = {
    "type_de_course": str,
    "surface": str,
    "distance": str
}

# Types de graphiques pour les groupes/statistiques
type_graphiques_groupes = [
    "Victoires par race",
    "Taux de victoire par race",
    "Taux de victoire par âge",
    "Courses par surface",
    "Courses par type de course"
]

# Colonnes de filtrage pour les statistiques groupées
colonnes_filtrage_groupes = {
    "race": str,
    "age": int,
    "type_course": str,
    "surface": str,
    "distance": int,
}
