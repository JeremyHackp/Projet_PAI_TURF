#!/usr/bin/env python3
"""
Module pour compléter la base de données PMU entre deux dates.

Ce module permet de récupérer automatiquement les réunions et les participants
d'une période donnée depuis l'API PMU, et de les insérer dans une base SQLite locale.

Fonctions principales :
- complete_data_base_between_two_dates(start_str: str, end_str: str, db_path: str = "courses.db") -> None
    Parcourt toutes les dates entre start_str et end_str incluses, appelle les scripts
    `get_reunion_insert_into_data_base.py` et `get_participant_insert_into_data_base.py`,
    et remplit la base SQLite spécifiée.

- process_date(date_reunion: str, db_path: str) -> None
    Traite une seule date : récupération des réunions et insertion des participants.

- count_reunions_and_courses(date_reunion: str, db_path: str) -> Tuple[int, Dict[int, int]]
    Compte le nombre de réunions et de courses pour une date donnée.

- daterange(start_date: datetime.date, end_date: datetime.date) -> datetime.date
    Générateur de toutes les dates entre start_date et end_date incluses.

- execute_command(command: List[str]) -> None
    Exécute une commande système et affiche sa sortie.

Usage depuis le terminal :
    python complete_data_base_between_two_dates.py <start_date> <end_date> [db_path]

    start_date / end_date : dates au format JJMMAAAA (ex. 01012024)
    db_path : chemin optionnel vers la base SQLite (par défaut 'courses.db')

Exemple :
    python complete_data_base_between_two_dates.py 01012020 10012020 /home/user/courses.db
"""

import subprocess
import sqlite3
import datetime
from typing import Tuple, Dict, List


def daterange(start_date: datetime.date, end_date: datetime.date) -> datetime.date:
    """
    Génère toutes les dates entre start_date et end_date incluses.

    Args:
        start_date (datetime.date) : date de début
        end_date (datetime.date) : date de fin

    Yields:
        datetime.date : chaque date de la plage
    """
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + datetime.timedelta(n)


def execute_command(command: List[str]) -> None:
    """
    Exécute une commande système et affiche la sortie en direct.
    """
    try:
        print(f"💻 Exécution : {' '.join(command)}")
        subprocess.run(command, check=True)  # <--- ici, la commande est déjà une liste
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Erreur lors de l'exécution de : {' '.join(command)}")
        print(e)



def count_reunions_and_courses(date_reunion: str, db_path: str) -> Tuple[int, Dict[int, int]]:
    """
    Compte le nombre de réunions et de courses pour une date donnée.

    Args:
        date_reunion (str) : date au format 'DDMMYYYY'
        db_path (str) : chemin vers la base SQLite

    Returns:
        Tuple[int, Dict[int, int]] :
            nb_reunions (int) : nombre de réunions trouvées
            course_counts (Dict[int, int]) : dictionnaire {NumReunion: nombre_de_courses}
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT NumReunion FROM Reunions WHERE DateReunion = ?", (date_reunion,)
    )
    reunions: List[int] = [r[0] for r in cursor.fetchall()]
    nb_reunions: int = len(reunions)

    course_counts: Dict[int, int] = {}
    for num_reunion in reunions:
        cursor.execute(
            "SELECT COUNT(*) FROM Courses WHERE NumReunion = ? AND DateReunion = ?",
            (num_reunion, date_reunion),
        )
        count: int = cursor.fetchone()[0]
        course_counts[num_reunion] = count

    conn.close()
    return nb_reunions, course_counts


def process_date(date_reunion: str, db_path: str) -> None:
    """
    Traite toutes les réunions et courses pour une date donnée.
    """
    print(f"===== {date_reunion} =====")

    # Vérifie que GR.py existe
    import os
    if not os.path.isfile("get_reunion_insert_into_data_base.py"):
        print("❌ Erreur : 'get_reunion_insert_into_data_base.py' introuvable !")
        return

    # Appel du script GR.py
    print("→ Récupération des réunions et courses...")
    execute_command([sys.executable, "get_reunion_insert_into_data_base.py", date_reunion])

    # Comptage des réunions et courses
    nb_reunions, course_counts = count_reunions_and_courses(date_reunion, db_path)
    print(f"{nb_reunions} réunions trouvées pour le {date_reunion} :")
    for num_r, nb_c in course_counts.items():
        print(f"  Réunion {num_r} → {nb_c} courses")

        # Vérifie que GP.py existe
        if not os.path.isfile("get_participant_insert_into_data_base.py"):
            print("❌ Erreur : 'get_participant_insert_into_data_base.py' introuvable !")
            continue

        for course_num in range(1, nb_c + 1):
            print(f"    → Traitement de la course {course_num} de la réunion {num_r}...")
            execute_command([
                sys.executable,
                "get_participant_insert_into_data_base.py",
                date_reunion,
                str(num_r),
                str(course_num)
            ])


def complete_data_base_between_two_dates(start_str: str, end_str: str, db_path: str = "courses.db") -> None:
    """
    Traite toutes les dates entre start_str et end_str incluses et remplit la base spécifiée.

    Args:
        start_str (str) : date de début au format 'DDMMYYYY'
        end_str (str) : date de fin au format 'DDMMYYYY'
        db_path (str) : chemin vers la base SQLite

    Raises:
        ValueError : si le format des dates est invalide ou si end < start
    """
    try:
        start_date: datetime.date = datetime.datetime.strptime(start_str, "%d%m%Y").date()
        end_date: datetime.date = datetime.datetime.strptime(end_str, "%d%m%Y").date()
    except ValueError:
        raise ValueError("Format de date invalide. Utilisez JJMMAAAA (ex : 01012024)")

    if end_date < start_date:
        raise ValueError("La date de fin doit être après la date de début.")

    print(f"\n📅 Traitement des dates du {start_str} au {end_str}\n")
    for current_date in daterange(start_date, end_date):
        process_date(current_date.strftime("%d%m%Y"), db_path)

    print("✅ Toutes les dates ont été traitées avec succès.")


# Point d'entrée pour le terminal
if __name__ == "__main__":
    import sys

    if len(sys.argv) not in (3, 4):
        print("Usage : python complete_data_base_between_two_dates.py <start_date> <end_date> [db_path]")
        print("Format des dates : JJMMAAAA (ex : 01012024)")
        print("db_path : optionnel, chemin vers la base SQLite (par défaut 'courses.db')")
        sys.exit(1)

    start_str: str = sys.argv[1]
    end_str: str = sys.argv[2]
    db_path: str = sys.argv[3] if len(sys.argv) == 4 else "courses.db"

    try:
        complete_data_base_between_two_dates(start_str, end_str, db_path)
    except Exception as e:
        print(f"❌ Erreur : {e}")
        sys.exit(1)
