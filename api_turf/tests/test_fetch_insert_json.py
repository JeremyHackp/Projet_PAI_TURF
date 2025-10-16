import unittest
import os
import sys
import json
import tempfile
import sqlite3
import subprocess
from typing import Dict, Any

# Ajouter src/ au path pour que Python trouve le module principal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from get_reunion_insert_into_data_base import fetch_and_insert_reunion


class TestFetchAndInsertFromJSON(unittest.TestCase):
    def setUp(self):
        # Crée une base SQLite temporaire
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # --- Création des tables ---
        self.cursor.execute("""
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

        # ✅ Schéma corrigé avec tous les nouveaux champs
        self.cursor.execute("""
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
                PRIMARY KEY (NumReunion, NumCourse, DateReunion),
                FOREIGN KEY (NumReunion, DateReunion)
                    REFERENCES Reunions(NumReunion, DateReunion)
            )
        """)
        self.conn.commit()

        # --- Chargement du fichier JSON de test ---
        json_path = os.path.join(os.path.dirname(__file__), "01012024.json")
        with open(json_path, "r", encoding="utf-8") as f:
            self.test_data: Dict[str, Any] = json.load(f)

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_path)

    def test_inserted_data_matches_json(self):
        """Teste que les données insérées correspondent au JSON"""
        fetch_and_insert_reunion("01012024", self.db_path)

        # --- Vérification Reunions ---
        self.cursor.execute("SELECT * FROM Reunions ORDER BY NumReunion, DateReunion")
        rows_reunions = self.cursor.fetchall()
        json_reunions = self.test_data.get("programme", {}).get("reunions", [])
        self.assertEqual(len(rows_reunions), len(json_reunions))

        for i, reunion in enumerate(json_reunions):
            db_row = rows_reunions[i]
            self.assertEqual(str(db_row[0]), str(reunion.get("numOfficiel", "")))
            self.assertEqual(db_row[1], "01012024")  # Date
            self.assertEqual(db_row[2], reunion.get("nature", ""))
            self.assertIsInstance(db_row[7], (int, float, type(None)))  # Temperature
            self.assertIsInstance(db_row[8], (int, float, type(None)))  # ForceVent

        # --- Vérification Courses ---
        self.cursor.execute("SELECT * FROM Courses ORDER BY NumReunion, NumCourse, DateReunion")
        rows_courses = self.cursor.fetchall()
        total_courses = sum(len(r.get("courses", [])) for r in json_reunions)
        self.assertEqual(len(rows_courses), total_courses)

        for db_row, course in zip(
            rows_courses, sum([r.get("courses", []) for r in json_reunions], [])
        ):
            # Vérifications générales
            self.assertIsInstance(db_row[4], (int, float, type(None)))  # Distance
            self.assertIsInstance(db_row[10], (int, type(None)))        # NbrParticipants

            # Nouveaux attributs
            self.assertEqual(db_row[13], course.get("typePiste", ""))
            self.assertEqual(db_row[14], course.get("categorieParticularite", ""))
            self.assertEqual(db_row[15], course.get("conditionAge", ""))

            # Pénétromètre
            penetrometre = course.get("penetrometre", {})
            self.assertEqual(db_row[16], penetrometre.get("valeurMesure", ""))
            self.assertEqual(db_row[17], penetrometre.get("intitule", ""))

            # ✅ Vérifie les montants d’allocation
            self.assertEqual(db_row[18], course.get("montantOffert1er"))
            self.assertEqual(db_row[19], course.get("montantOffert2eme"))
            self.assertEqual(db_row[20], course.get("montantOffert3eme"))
            self.assertEqual(db_row[21], course.get("montantOffert4eme"))
            self.assertEqual(db_row[22], course.get("montantOffert5eme"))
            self.assertEqual(db_row[23], course.get("conditions", ""))


class TestMainBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "src", "get_reunion_insert_into_data_base.py")
        )

    def test_help_flag(self):
        """Vérifie que -h et --help affichent l'aide"""
        for flag in ("-h", "--help"):
            result = subprocess.run(
                [sys.executable, self.script_path, flag],
                capture_output=True,
                text=True,
            )
            output = result.stdout + result.stderr
            self.assertIn("Usage : python get.py <date_reunion>", output)
            self.assertIn("Exemple : python get.py 16022020", output)

    def test_no_argument(self):
        """Vérifie que l'aide s'affiche sans argument"""
        result = subprocess.run(
            [sys.executable, self.script_path],
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        self.assertIn("Usage : python get.py <date_reunion>", output)
        self.assertIn("Exemple : python get.py 16022020", output)


if __name__ == "__main__":
    unittest.main()
