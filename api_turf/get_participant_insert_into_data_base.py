#!/usr/bin/env python3
"""
Module pour récupérer les participants d'une course via l'API PMU
et les insérer dans une base SQLite.

Fonctions principales :
- fetch_and_insert_participants(date_reunion: str, num_reunion: int, num_course: int, db_path: str = "courses.db") -> None
    Récupère et insère les participants d'une course spécifique.
- main(args: Optional[List[str]] = None) -> None
    Point d'entrée pour exécuter le script depuis le terminal.

Types utilisés :
- date_reunion : str au format 'DDMMYYYY'
- num_reunion : int numéro de la réunion
- num_course : int numéro de la course
- db_path : str chemin vers la base SQLite
"""

import requests
import sqlite3
import sys
from typing import Optional, Dict, Any, List


def fetch_and_insert_participants(
    date_reunion: str,
    num_reunion: int,
    num_course: int,
    db_path: str = "courses.db"
) -> None:
    """
    Récupère les participants d'une course via l'API PMU et les insère dans la base SQLite.

    Paramètres :
        date_reunion (str) : date au format 'DDMMYYYY'
        num_reunion (int) : numéro de la réunion (ex. 1 pour R1)
        num_course (int) : numéro de la course (ex. 1 pour C1)
        db_path (str) : chemin vers la base SQLite (par défaut 'courses.db')
    """
    print(f"Récupération des participants pour la réunion {num_reunion}, course {num_course}, date {date_reunion}...")

    url = f"https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date_reunion}/R{num_reunion}/C{num_course}/participants"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erreur lors de la requête API : {e}")
        return

    data: Dict[str, Any] = response.json()
    participants: List[Dict[str, Any]] = data.get("participants", [])
    print(f"{len(participants)} participants récupérés depuis l'API.")

    if not participants:
        print("Aucun participant trouvé, rien à insérer.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for p in participants:
        cursor.execute("""
            INSERT OR REPLACE INTO Participants (
                NumParticipant, NumReunion, NumCourse, DateReunion,
                Nom, Age, Race, Proprietaire, Entraineur, Driver, Oeilleres,
                NbrCourse, NbrVictoires, NbrPlaces, NbrSecond, NbrTroisieme,
                GainsCarriere, GainsVictoires, GainsAnneeEnCours, GainsAnneePrecedente,
                PositionArrivee, HandicapDistance, HandicapPoids, TempsObtenu, Cote,
                NomDuPere, NomDeLaMere, Incident
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p.get("numPmu"),
            num_reunion,
            num_course,
            date_reunion,
            p.get("nom"),
            p.get("age"),  # <-- ajout de l'age
            p.get("race"),
            p.get("proprietaire"),
            p.get("entraineur"),
            p.get("driver"),
            p.get("oeilleres"),
            p.get("nombreCourses"),
            p.get("nombreVictoires"),
            p.get("nombrePlaces"),
            p.get("nombrePlacesSecond"),
            p.get("nombrePlacesTroisieme"),
            p.get("gainsParticipant", {}).get("gainsCarriere", 0),
            p.get("gainsParticipant", {}).get("gainsVictoires", 0),
            p.get("gainsParticipant", {}).get("gainsAnneeEnCours", 0),
            p.get("gainsParticipant", {}).get("gainsAnneePrecedente", 0),
            p.get("ordreArrivee"),
            p.get("handicapDistance"),
            p.get("handicapPoids"),
            p.get("tempsObtenu"),
            p.get("dernierRapportDirect", {}).get("rapport"),
            p.get("nomPere"),
            p.get("nomMere"),
            p.get("incident")
        ))

    conn.commit()
    conn.close()
    print(f"{len(participants)} participants insérés ou mis à jour dans la base '{db_path}'.")


def main(args: Optional[List[str]] = None) -> None:
    """
    Point d'entrée pour exécuter le script depuis le terminal.

    Args:
        args (Optional[List[str]]): liste d'arguments. Par défaut sys.argv[1:].
    """
    if args is None:
        args = sys.argv[1:]

    if len(args) == 1 and args[0] in ("-h", "--help"):
        print("Usage : python get_participant_insert_into_data_base.py <date_reunion> <num_reunion> <num_course>")
        print("Exemple : python get_participant_insert_into_data_base.py 16022020 1 1")
        print("Récupère les participants d'une course spécifique et les insère dans la base SQLite 'courses.db'.")
        return

    if len(args) != 3:
        print("Erreur : mauvais nombre d'arguments.")
        print("Pour l'aide : python get_participant_insert_into_data_base.py -h")
        return

    date_param = args[0]
    try:
        num_reunion_param = int(args[1])
        num_course_param = int(args[2])
    except ValueError:
        print("Erreur : num_reunion et num_course doivent être des entiers.")
        return

    fetch_and_insert_participants(date_param, num_reunion_param, num_course_param)


if __name__ == "__main__":
    main()
