# tests/test_initialisation_database.py

import unittest
import sqlite3
import tempfile
import os
import sys

# Ajouter src/ au path pour pouvoir importer depuis le package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Importer les fonctions existantes pour créer les tables
from get_reunion_insert_into_data_base import fetch_and_insert_reunion
from get_participant_insert_into_data_base import fetch_and_insert_participants

def create_database(db_path):
    """Crée toutes les tables nécessaires pour la base de test"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
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
    """)

    cursor.execute("""
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
    """)

    cursor.execute("""
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
        PRIMARY KEY (Nom, NumReunion, NumCourse, DateReunion)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Cheval (
        Nom TEXT PRIMARY KEY,
        NomDuPere TEXT,
        NomDeLaMere TEXT,
        Race TEXT,
        RobeCode TEXT,
        RobeLibelle TEXT
    )
    """)

    conn.commit()
    conn.close()


class TestInitialisationDatabase(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        create_database(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_path)

    def test_tables_exist(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in self.cursor.fetchall()]
        expected_tables = ["Reunions", "Courses", "Participants", "Cheval"]
        for table in expected_tables:
            self.assertIn(table, tables)

    def test_columns_and_types(self):
        expected_schema = {
            "Reunions": {
                "NumReunion": "INTEGER",
                "DateReunion": "TEXT",
                "Nature": "TEXT",
                "NomHippodrome": "TEXT",
                "NomPays": "TEXT",
                "CodeNebulosite": "TEXT",
                "LibelleNebulosite": "TEXT",
                "Temperature": "REAL",
                "ForceVent": "REAL",
                "DirectionVent": "TEXT"
            },
            "Courses": {
                "NumCourse": "INTEGER",
                "NumReunion": "INTEGER",
                "DateReunion": "TEXT",
                "LabelCourse": "TEXT",
                "Distance": "REAL",
                "Unite": "TEXT",
                "Corde": "TEXT",
                "Discipline": "TEXT",
                "Specialite": "TEXT",
                "CondSexe": "TEXT",
                "NbrParticipants": "INTEGER",
                "DureeCourse": "INTEGER",
                "OrdreArrivee": "TEXT"
            },
            "Cheval": {
                "Nom": "TEXT",
                "NomDuPere": "TEXT",
                "NomDeLaMere": "TEXT",
                "Race": "TEXT",
                "RobeCode": "TEXT",
                "RobeLibelle": "TEXT"
            },
            "Participants": {
                "NumParticipant": "INTEGER",
                "NumReunion": "INTEGER",
                "NumCourse": "INTEGER",
                "DateReunion": "TEXT",
                "Nom": "TEXT",
                "Age": "INTEGER",
                "Sexe": "TEXT",
                "Proprietaire": "TEXT",
                "Entraineur": "TEXT",
                "Driver": "TEXT",
                "Oeilleres": "TEXT",
                "NbrCourse": "INTEGER",
                "NbrVictoires": "INTEGER",
                "NbrPlaces": "INTEGER",
                "NbrSecond": "INTEGER",
                "NbrTroisieme": "INTEGER",
                "GainsCarriere": "REAL",
                "GainsVictoires": "REAL",
                "GainsAnneeEnCours": "REAL",
                "GainsAnneePrecedente": "REAL",
                "PositionArrivee": "TEXT",
                "HandicapDistance": "REAL",
                "HandicapPoids": "REAL",
                "TempsObtenu": "TEXT",
                "Cote": "TEXT",
                "Incident": "TEXT"
            }
        }

        for table, columns in expected_schema.items():
            self.cursor.execute(f"PRAGMA table_info({table})")
            col_info = {row[1]: row[2].upper() for row in self.cursor.fetchall()}
            for col_name, col_type in columns.items():
                self.assertIn(col_name, col_info)
                self.assertEqual(col_info[col_name], col_type)


if __name__ == "__main__":
    unittest.main()
