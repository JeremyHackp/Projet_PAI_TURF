# api_turf/__init__.py
"""
Package pmu_library
==================

Ce package permet de :
- Créer et initialiser la base de données PMU (SQLite)
- Récupérer les réunions et les courses depuis l'API PMU
    https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date_reunion}
- Récupérer les participants d'une course
    https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date_reunion}/R{num_reunion}/C{num_course}/participants
- Compléter la base entre deux dates

Exemple d'utilisation :
-----------------------
from api_turf import create_database, complete_data_base_between_two_dates

create_database("courses.db")
complete_data_base_between_two_dates("01012020", "10012020", db_path="courses.db")
"""

# Import des fonctions principales pour les rendre accessibles directement depuis api_turf
from .Initialisation_data_base import create_database
from .get_reunion_insert_into_data_base import fetch_and_insert_reunion
from .get_participant_insert_into_data_base import fetch_and_insert_participants
from .complete_data_base_between_two_dates import complete_data_base_between_two_dates

# Liste des éléments exportés par défaut lors d'un `from api_turf import *`
__all__ = [
    "create_database",
    "fetch_and_insert_reunion",
    "fetch_and_insert_participants",
    "complete_data_base_between_two_dates",
]