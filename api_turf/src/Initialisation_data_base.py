#!/usr/bin/env python3
"""
Module d'initialisation de la base de données SQLite pour les courses hippiques.

Ce module crée les tables principales nécessaires pour stocker les informations
des réunions, courses, participants et chevaux, si elles n'existent pas déjà.

Tables créées :
- Reunions : informations générales sur chaque réunion
- Courses : informations sur chaque course
- Participants : informations sur chaque cheval dans une course
- Cheval : informations stables sur chaque cheval (filiation, race, robe)

Fonction principale :
- create_database(db_path: str = "courses.db") -> None
    Crée la base SQLite et les tables si elles n'existent pas. Affiche un message de confirmation.
"""

import sqlite3


def create_database(db_path: str = "courses.db"):
    """Crée la base de données et les tables si elles n'existent pas."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Table Reunions
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

    # Table Courses avec pénétromètre
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
            TypePiste TEXT,
            CategorieParticularite TEXT,
            ConditionAge TEXT,
            PenetrometreValeur TEXT,
            PenetrometreIntitule TEXT,
            MontantOffert1er REAL,
            MontantOffert2eme REAL,
            MontantOffert3eme REAL,
            MontantOffert4eme REAL,
            MontantOffert5eme REAL,
            Conditions TEXT,
            PRIMARY KEY (NumCourse, NumReunion, DateReunion)
        )
        """
    )

    # ✅ Nouvelle table Cheval
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS Cheval (
        Nom TEXT PRIMARY KEY,
        NomDuPere TEXT,
        NomDeLaMere TEXT,
        Race TEXT,
        RobeCode TEXT,
        RobeLibelle TEXT
    )
    """
    )

    # Table Participants (modifiée)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Participants (
            NumParticipant INTEGER,
            NumReunion INTEGER,
            NumCourse INTEGER,
            DateReunion TEXT,
            Nom TEXT,
            Age INTEGER,
            Sexe TEXT,
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
            Incident TEXT,
            Eleveur TEXT,
            Musique TEXT,
            ReductionKilometrique REAL,
            PRIMARY KEY (Nom, NumReunion, NumCourse, DateReunion),
            FOREIGN KEY (NumReunion, DateReunion) REFERENCES Reunions(NumReunion, DateReunion),
            FOREIGN KEY (Nom) REFERENCES Cheval(Nom)
        )
        """
    )

    conn.commit()
    conn.close()
    print(f"Base de données '{db_path}' initialisée avec succès.")


if __name__ == "__main__":
    create_database()
