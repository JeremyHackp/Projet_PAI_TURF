# tests/test_fetch_insert_participants.py

import unittest
import os
import sys
import json
import tempfile
import sqlite3
import requests

# Ajouter le dossier parent pour que Python trouve le module principal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from get_participant_insert_into_data_base import fetch_and_insert_participants


class TestFetchAndInsertParticipants(unittest.TestCase):
    def setUp(self):
        # Crée une base SQLite temporaire
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Crée la table Participants (minimal pour le test) avec Age
        self.cursor.execute("""
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
            PRIMARY KEY (Nom, NumReunion, NumCourse, DateReunion)
        )
        """)
        self.conn.commit()

        # Charger le JSON de référence
        self.json_path = os.path.join(os.path.dirname(__file__), "01012020R1C1.json")
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.reference_data = json.load(f).get("participants", [])

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_path)

    def test_fetch_and_insert_matches_json(self):
        """Récupère les participants depuis l'API, compare au JSON, puis insère dans la base"""
        date_reunion = "01012020"
        num_reunion = 1
        num_course = 1

        # Vérifie d'abord la réponse API
        url = f"https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date_reunion}/R{num_reunion}/C{num_course}/participants"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        api_data = response.json().get("participants", [])

        # Vérifie que le nombre de participants correspond au JSON
        self.assertEqual(len(api_data), len(self.reference_data), "Nombre de participants différent de la référence")

        # Comparaison des champs clés : numPmu, nom, age
        for ref, api in zip(self.reference_data, api_data):
            self.assertEqual(ref.get("numPmu"), api.get("numPmu"))
            self.assertEqual(ref.get("nom"), api.get("nom"))
            # Age peut être absent dans certains cas
            self.assertEqual(ref.get("age"), api.get("age"))

        # Insertion dans la base
        fetch_and_insert_participants(date_reunion, num_reunion, num_course, db_path=self.db_path)

        # Vérifie que tous les participants ont été insérés
        self.cursor.execute("SELECT NumParticipant, Nom, Age FROM Participants ORDER BY NumParticipant")
        rows = self.cursor.fetchall()
        self.assertEqual(len(rows), len(self.reference_data))

        # Comparaison finale NumParticipant, Nom et Age
        for db_row, ref in zip(rows, self.reference_data):
            self.assertEqual(db_row[0], ref.get("numPmu"))
            self.assertEqual(db_row[1], ref.get("nom"))
            self.assertEqual(db_row[2], ref.get("age"))


if __name__ == "__main__":
    unittest.main()
