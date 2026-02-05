"""
predictions.py - Fonctions de prédiction
"""


def prediction_ordre_participants(course_id):
    """
    Simule la prédiction de l'ordre des ids des participants d'une course.

    Args:
        course_id: ID de la course

    Returns:
        list[int]: Liste des IDs des participants dans l'ordre prédit
    """
    participants = [3, 6, 2, 1, 4, 5]
    return participants


def prediction_ordre_participants_verification(course_id):
    """
    Simule la récupération des ids des participants d'une course depuis la base de données
    pour vérification.

    Args:
        course_id: ID de la course

    Returns:
        list[int]: Liste des IDs des participants dans l'ordre réel
    """
    participants = [3, 4, 2, 1, 6, 5]
    return participants
