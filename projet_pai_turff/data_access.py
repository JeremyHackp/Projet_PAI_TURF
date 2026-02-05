"""
data_access.py - Point d'entrée principal pour l'accès aux données

Ce fichier ré-exporte toutes les fonctions des modules décomposés
pour maintenir la compatibilité avec le code existant.
"""

# Import des widgets et classes externes
# Import des caches
from .cache import (
    CourseCache,
    ParticipantsCache,
    course_cache,
    meilleurs_chevaux,
    participants_cache,
)

# Import des constantes
from .constants import (
    OP_SQL_MAP,
    colonnes_filtrage_courses,
    colonnes_filtrage_groupes,
    colonnes_filtrage_participants,
    colonnes_filtrage_types_de_courses_pour_participants,
    colonnes_tri_courses,
    colonnes_tri_participants,
    donnees_a_afficher_bouton_particpant,
    donnees_a_afficher_boutons_course,
    donnees_a_afficher_detail_course,
    donnees_a_afficher_detail_participant,
    type_graphiques_groupes,
    type_graphiques_participants,
)

# Import des fonctions d'accès aux données de courses
from .course_data import (
    get_course_data,
    get_course_prediction_data,
    get_course_prediction_id,
    get_course_recentes_from_db,
)
from .Filtre import Filtre

# Import des fonctions de mise à jour des graphiques
from .graph_updates import (
    update_graphe_data,
    update_graphe_individuel,
    update_graphe_stats_groupe,
)
from .Graphe import Graphe

# Import des fonctions d'accès aux données de participants
from .participant_data import (
    get_cheveaux_data,
    get_course_participants_id,
    get_meilleurs_cheveaux_ids,
    get_participant_predits_data,
    get_participants_data,
)

# Import des fonctions de prédiction
from .predictions import (
    prediction_ordre_participants,
    prediction_ordre_participants_verification,
)

# Import des fonctions de construction de requêtes
from .query_builder import build_where_clause_stats

# Ré-export pour compatibilité
__all__ = [
    # Widgets
    "Filtre",
    "Graphe",
    # Constantes
    "OP_SQL_MAP",
    "donnees_a_afficher_boutons_course",
    "donnees_a_afficher_bouton_particpant",
    "donnees_a_afficher_detail_course",
    "donnees_a_afficher_detail_participant",
    "colonnes_filtrage_courses",
    "colonnes_tri_courses",
    "colonnes_filtrage_participants",
    "colonnes_tri_participants",
    "type_graphiques_participants",
    "colonnes_filtrage_types_de_courses_pour_participants",
    "type_graphiques_groupes",
    "colonnes_filtrage_groupes",
    # Caches
    "CourseCache",
    "ParticipantsCache",
    "course_cache",
    "participants_cache",
    "meilleurs_chevaux",
    # Query builder
    "build_where_clause_stats",
    # Course data
    "get_course_data",
    "get_course_prediction_data",
    "get_course_recentes_from_db",
    "get_course_prediction_id",
    # Participant data
    "get_participants_data",
    "get_cheveaux_data",
    "get_participant_predits_data",
    "get_course_participants_id",
    "get_meilleurs_cheveaux_ids",
    # Predictions
    "prediction_ordre_participants",
    "prediction_ordre_participants_verification",
    # Graph updates
    "update_graphe_individuel",
    "update_graphe_stats_groupe",
    "update_graphe_data",
]
