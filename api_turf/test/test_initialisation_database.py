# tests/test_initialisation_database.py

import unittest
import sqlite3
import tempfile
import os
import sys

# Ajouter le dossier parent pour trouver le module principal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Initialisation_data_base import create_database

class TestInitialisationDatabase(unittest.TestCase):
    def setUp(self):
        # Crée un fichier temporaire pour la base SQLite
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        # Initialise la base de données
        create_database(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_path)

    def test_tables_exist(self):
        """Vérifie que toutes les tables sont créées"""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in self.cursor.fetchall()]
        expected_tables = ["Reunions", "Courses", "Participants"]
        for table in expected_tables:
            self.assertIn(table, tables, f"La table {table} devrait exister")

    def test_columns_and_types(self):
        """Vérifie que chaque table a les colonnes attendues et le type correct"""
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
            "Participants": {
                "NumParticipant": "INTEGER",
                "NumReunion": "INTEGER",
                "NumCourse": "INTEGER",
                "DateReunion": "TEXT",
                "Nom": "TEXT",
                "Age": "INTEGER",
                "Race": "TEXT",
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
                "NomDuPere": "TEXT",
                "NomDeLaMere": "TEXT",
                "Incident": "TEXT"
            }
        }

        for table, columns in expected_schema.items():
            self.cursor.execute(f"PRAGMA table_info({table})")
            col_info = {row[1]: row[2].upper() for row in self.cursor.fetchall()}  # {nom_colonne: type}
            for col_name, col_type in columns.items():
                self.assertIn(col_name, col_info, f"Colonne {col_name} manquante dans {table}")
                self.assertEqual(col_info[col_name], col_type, f"Type de {col_name} dans {table} incorrect")

if __name__ == "__main__":
    unittest.main()
