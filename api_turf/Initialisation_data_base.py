#!/usr/bin/env python3
"""
Module d'initialisation de la base de données SQLite pour les courses hippiques.

Ce module crée les tables principales nécessaires pour stocker les informations
des réunions, courses et participants, si elles n'existent pas déjà.

Tables créées :
- Reunions : informations générales sur chaque réunion (NumReunion, DateReunion, Hippodrome, météo, etc.)
- Courses : informations sur chaque course (NumCourse, Distance, Discipline, Nombre de participants, etc.)
- Participants : informations sur chaque cheval participant (Nom, Age, Gains, Positions, etc.)

Fonction principale :
- create_database(db_path: str = "courses.db") -> None
    Crée la base SQLite et les tables si elles n'existent pas. Affiche un message de confirmation.

Usage depuis le terminal :
    python create_database.py

Exemple pour l’importation dans une bibliothèque Python :
    from create_database import create_database
    create_database("chemin/vers/ma_base.db")
"""

import sqlite3


def create_database(db_path: str = "courses.db"):
    """Crée la base de données et les tables si elles n'existent pas."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Création de la table Reunions
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS Reunions (
        NumReunion INTEGER,
        DateReunion TEXT,
        Nature TEXT,
        NomHippodrome TEXT,
        NomPays TEXT,
        CodeNebulosite TEXT,
        LibelleNebulosite TEXT,
        Temperature REAL,
        ForceVent REAL,
        DirectionVent TEXT,
        PRIMARY KEY (NumReunion, DateReunion)
    )
    """
    )

    # Création de la table Courses
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS Courses (
        NumCourse INTEGER,
        NumReunion INTEGER,
        DateReunion TEXT,
        LabelCourse TEXT,
        Distance REAL,
        Unite TEXT,
        Corde TEXT,
        Discipline TEXT,
        Specialite TEXT,
        CondSexe TEXT,
        NbrParticipants INTEGER,
        DureeCourse INTEGER,
        OrdreArrivee TEXT,
        PRIMARY KEY (NumReunion, NumCourse, DateReunion),
        FOREIGN KEY (NumReunion, DateReunion) REFERENCES Reunions(NumReunion, DateReunion)
    )
    """
    )

    # Création de la table Participants
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS Participants (
        NumParticipant INTEGER,
        NumReunion INTEGER,
        NumCourse INTEGER,
        DateReunion TEXT,
        Nom TEXT,
        Age INTEGER,
        Race TEXT,
        Proprietaire TEXT,
        Entraineur TEXT,
        Driver TEXT,
        Oeilleres TEXT,
        NbrCourse INTEGER,
        NbrVictoires INTEGER,
        NbrPlaces INTEGER,
        NbrSecond INTEGER,
        NbrTroisieme INTEGER,
        GainsCarriere REAL,
        GainsVictoires REAL,
        GainsAnneeEnCours REAL,
        GainsAnneePrecedente REAL,
        PositionArrivee TEXT,
        HandicapDistance REAL,
        HandicapPoids REAL,
        TempsObtenu TEXT,
        Cote TEXT,
        NomDuPere TEXT,
        NomDeLaMere TEXT,
        Incident TEXT,
        PRIMARY KEY (Nom, NumReunion, NumCourse, DateReunion),
        FOREIGN KEY (NumReunion, DateReunion) REFERENCES Reunions(NumReunion, DateReunion)
    )
    """
    )

    # Valider les changements et fermer la connexion
    conn.commit()
    conn.close()
    print(f"Base de données '{db_path}' initialisée avec succès.")


if __name__ == "__main__":
    create_database()
