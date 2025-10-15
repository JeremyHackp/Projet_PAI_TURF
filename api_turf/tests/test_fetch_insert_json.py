# tests/test_fetch_insert_json.py
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

# Import corrigé : enlever le préfixe src
from get_reunion_insert_into_data_base import fetch_and_insert_reunion


class TestFetchAndInsertFromJSON(unittest.TestCase):
    def setUp(self):
        # Crée une base SQLite temporaire
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Création des tables avec clés primaires composées
        self.cursor.execute(
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

        self.cursor.execute(
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
                PRIMARY KEY (NumReunion, NumCourse, DateReunion),
                FOREIGN KEY (NumReunion, DateReunion) REFERENCES Reunions(NumReunion, DateReunion)
            )
            """
        )
        self.conn.commit()

        # Charger les données de test depuis le fichier JSON
        json_path = os.path.join(os.path.dirname(__file__), "01012024.json")
        with open(json_path, "r", encoding="utf-8") as f:
            self.test_data: Dict[str, Any] = json.load(f)

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_path)

    def test_inserted_data_matches_json(self):
        # Appel de la fonction avec la base temporaire
        fetch_and_insert_reunion("01012024", self.db_path)

        # Vérification des réunions
        self.cursor.execute("SELECT * FROM Reunions ORDER BY NumReunion, DateReunion")
        rows_reunions = self.cursor.fetchall()
        json_reunions = self.test_data.get("programme", {}).get("reunions", [])
        self.assertEqual(len(rows_reunions), len(json_reunions))

        for i, reunion in enumerate(json_reunions):
            db_row = rows_reunions[i]
            self.assertEqual(str(db_row[0]), str(reunion.get("numOfficiel", "")))
            self.assertEqual(db_row[1], "01012024")  # DateReunion
            self.assertEqual(db_row[2], reunion.get("nature", ""))
            self.assertIsInstance(db_row[7], (int, float, type(None)))  # temperature
            self.assertIsInstance(db_row[8], (int, float, type(None)))  # forceVent

        # Vérification des courses
        self.cursor.execute(
            "SELECT * FROM Courses ORDER BY NumReunion, NumCourse, DateReunion"
        )
        rows_courses = self.cursor.fetchall()
        total_courses = sum(len(r.get("courses", [])) for r in json_reunions)
        self.assertEqual(len(rows_courses), total_courses)

        for db_row, course in zip(
            rows_courses, sum([r.get("courses", []) for r in json_reunions], [])
        ):
            self.assertIsInstance(db_row[4], (int, float, type(None)))  # distance
            self.assertIsInstance(db_row[10], (int, type(None)))  # nbr_participants

            # Vérification des nouveaux attributs
            self.assertEqual(db_row[13], course.get("typePiste", ""))
            self.assertEqual(db_row[14], course.get("categorieParticularite", ""))
            self.assertEqual(db_row[15], course.get("conditionAge", ""))

            # ✅ Vérification pénétromètre
            penetrometre = course.get("penetrometre", {})
            self.assertEqual(db_row[16], penetrometre.get("valeurMesure", ""))
            self.assertEqual(db_row[17], penetrometre.get("intitule", ""))



class TestMainBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Corrigé : ajout de 'src' dans le chemin
        cls.script_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "src", "get_reunion_insert_into_data_base.py"
            )
        )

    def test_help_flag(self):
        """Vérifie que le script affiche l'aide avec -h et --help"""
        for flag in ("-h", "--help"):
            result = subprocess.run(
                [sys.executable, self.script_path, flag],
                capture_output=True,
                text=True
            )
            output = result.stdout + result.stderr
            self.assertIn("Usage : python get.py <date_reunion>", output)
            self.assertIn("Exemple : python get.py 16022020", output)

    def test_no_argument(self):
        """Vérifie que le script affiche l'aide quand aucun argument n'est fourni"""
        result = subprocess.run(
            [sys.executable, self.script_path],
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr
        self.assertIn("Usage : python get.py <date_reunion>", output)
        self.assertIn("Exemple : python get.py 16022020", output)


if __name__ == "__main__":
    unittest.main()
