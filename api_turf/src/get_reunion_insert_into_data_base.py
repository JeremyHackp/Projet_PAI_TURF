#!/usr/bin/env python3

"""
Module pour récupérer toutes les réunions et courses d'une date donnée via l'API PMU
et les insérer dans une base de données SQLite locale.

Fonctions principales :
- fetch_and_insert_reunion(date_reunion: str, db_path: str = "courses.db") -> None
    Récupère les réunions et courses pour une date et les insère dans la base.
- main() -> None
    Point d'entrée du script lorsqu'il est exécuté depuis le terminal.

Types utilisés :
- date_reunion : str au format 'DDMMYYYY'
- db_path : str chemin vers la base SQLite
"""

import requests
import sqlite3
import sys
from typing import Dict, Any, List, Optional


def fetch_and_insert_reunion(date_reunion: str, db_path: str = "courses.db") -> None:
    """
    Récupère toutes les réunions et courses pour une date donnée via l'API PMU
    et les insère dans la base SQLite.

    Args:
        date_reunion (str): date au format 'DDMMYYYY'
        db_path (str): chemin complet vers la base SQLite
    """
    print(f"Récupération des données pour la date {date_reunion}...")

    url = f"https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date_reunion}"

    try:
        response: requests.Response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erreur lors de la requête API : {e}")
        return

    data: Dict[str, Any] = response.json()
    programme: Dict[str, Any] = data.get("programme", {})
    reunions: List[Dict[str, Any]] = programme.get("reunions", [])

    if not reunions:
        print("Aucune réunion trouvée pour cette date.")
        return

    conn: sqlite3.Connection = sqlite3.connect(db_path)
    cursor: sqlite3.Cursor = conn.cursor()

    for reunion in reunions:
        num_reunion: str = reunion.get("numOfficiel", "")
        nature: str = reunion.get("nature", "")
        hippodrome: str = reunion.get("hippodrome", {}).get("libelleLong", "")
        pays: str = reunion.get("pays", {}).get("libelle", "")
        meteo: Dict[str, Any] = reunion.get("meteo", {})
        nebulosite_code: str = meteo.get("nebulositeCode", "")
        nebulosite_lib: str = meteo.get("nebulositeLibelleCourt", "")
        temperature: Optional[float] = meteo.get("temperature")
        force_vent: Optional[float] = meteo.get("forceVent")
        direction_vent: str = meteo.get("directionVent", "")

        cursor.execute(
            """
            INSERT OR IGNORE INTO Reunions 
            (NumReunion, DateReunion, Nature, NomHippodrome, NomPays, CodeNebulosite, LibelleNebulosite, Temperature, ForceVent, DirectionVent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                num_reunion,
                date_reunion,
                nature,
                hippodrome,
                pays,
                nebulosite_code,
                nebulosite_lib,
                temperature,
                force_vent,
                direction_vent,
            ),
        )
        print(f"Réunion {num_reunion} ({hippodrome}) ajoutée.")

        for course in reunion.get("courses", []):
            num_course: str = course.get("numOrdre", "")
            label_course: str = course.get("libelle", "")
            distance: Optional[float] = course.get("distance")
            unite: str = course.get("distanceUnit", "")
            corde: str = course.get("corde", "")
            discipline: str = course.get("discipline", "")
            specialite: str = course.get("specialite", "")
            cond_sexe: str = course.get("conditionSexe", "")
            nbr_participants: Optional[int] = course.get("nombreDeclaresPartants")
            duree_course: Optional[int] = course.get("dureeCourse")
            ordre_arrivee: List[List[Any]] = course.get("ordreArrivee", [])
            ordre_arrivee_str: str = ";".join([",".join(map(str, o)) for o in ordre_arrivee])
        
            # Nouveaux attributs
            type_piste: str = course.get("typePiste", "")
            categorie_particularite: str = course.get("categorieParticularite", "")
            condition_age: str = course.get("conditionAge", "")
        
            # Valeurs du pénétromètre
            penetrometre: dict = course.get("penetrometre", {})
            penetrometre_valeur: str = penetrometre.get("valeurMesure", "")
            penetrometre_intitule: str = penetrometre.get("intitule", "")
        
            cursor.execute(
                """
                INSERT OR IGNORE INTO Courses 
                (NumCourse, NumReunion, DateReunion, LabelCourse, Distance, Unite, Corde,
                 Discipline, Specialite, CondSexe, NbrParticipants, DureeCourse, OrdreArrivee,
                 TypePiste, CategorieParticularite, ConditionAge, PenetrometreValeur, PenetrometreIntitule)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    num_course,
                    num_reunion,
                    date_reunion,
                    label_course,
                    distance,
                    unite,
                    corde,
                    discipline,
                    specialite,
                    cond_sexe,
                    nbr_participants,
                    duree_course,
                    ordre_arrivee_str,
                    type_piste,
                    categorie_particularite,
                    condition_age,
                    penetrometre_valeur,
                    penetrometre_intitule,
                ),
            )
        
            print(
                f"  Course {num_course} ({label_course}) ajoutée avec {nbr_participants} participants, type piste '{type_piste}', catégorie '{categorie_particularite}', condition âge '{condition_age}'."
            )

    conn.commit()
    conn.close()
    print(
        f"Toutes les données pour la date {date_reunion} ont été insérées dans la base '{db_path}'."
    )


def main():
    """
    Point d'entrée principal du script.

    Ce script récupère toutes les réunions et courses pour une date donnée
    depuis l'API Turf et les insère dans une base SQLite locale.

    Utilisation :
        python get_reunion_insert_into_data_base.py <date_reunion>

    Paramètres :
        sys.argv[1] : date de la réunion au format JJMMYYYY

    Cas spéciaux :
        - Si aucun argument ou si -h/--help est fourni, affiche l'aide et quitte.
    """
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage : python get.py <date_reunion>")
        print("Exemple : python get.py 16022020")
        sys.exit(0)

    date_param = sys.argv[1]
    fetch_and_insert_reunion(date_param)


if __name__ == "__main__":
    main()
