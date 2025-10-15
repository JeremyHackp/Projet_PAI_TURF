# tests/test_fetch_insert_participants.py

import unittest
import os
import sys
import json
import tempfile
import sqlite3
from unittest.mock import patch, Mock

# Ajouter src/ au path pour que Python trouve le module principal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from get_participant_insert_into_data_base import fetch_and_insert_participants

class TestFetchAndInsertParticipants(unittest.TestCase):
    def setUp(self):
        # Crée une base SQLite temporaire
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Crée la table Cheval
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Cheval (
            Nom TEXT PRIMARY KEY,
            NomDuPere TEXT,
            NomDeLaMere TEXT,
            Race TEXT,
            RobeCode TEXT,
            RobeLibelle TEXT
        )
        """)

        # Crée la table Participants (nouvelle structure)
        self.cursor.execute("""
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
            PRIMARY KEY (Nom, NumReunion, NumCourse, DateReunion),
            FOREIGN KEY (Nom) REFERENCES Cheval(Nom)
        )
        """)
        self.conn.commit()

        # Charger le JSON de référence depuis le dossier tests
        self.json_path = os.path.join(os.path.dirname(__file__), "01012020R1C1.json")
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.reference_data = json.load(f).get("participants", [])

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_path)

    @patch("get_participant_insert_into_data_base.requests.get")
    def test_fetch_and_insert_matches_json(self, mock_get):
        """Teste la récupération, l'insertion et la cohérence des données Participants/Cheval"""

        # Mocker la réponse de l'API avec les données du JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"participants": self.reference_data}
        mock_get.return_value = mock_response

        date_reunion = "01012020"
        num_reunion = 1
        num_course = 1

        # Insertion via la fonction
        fetch_and_insert_participants(date_reunion, num_reunion, num_course, db_path=self.db_path)

        # Vérifie les insertions dans Participants
        self.cursor.execute("SELECT NumParticipant, Nom, Age FROM Participants ORDER BY NumParticipant")
        participants_rows = self.cursor.fetchall()
        self.assertEqual(len(participants_rows), len(self.reference_data))

        # Vérifie que les chevaux ont bien été ajoutés dans la table Cheval
        self.cursor.execute("SELECT Nom, Race, NomDuPere, NomDeLaMere FROM Cheval ORDER BY Nom")
        chevaux_rows = self.cursor.fetchall()
        self.assertGreater(len(chevaux_rows), 0, "Aucun cheval inséré dans la table Cheval")

        # Vérifie cohérence entre Participants et Cheval
        participant_noms = {row[1] for row in participants_rows}
        cheval_noms = {row[0] for row in chevaux_rows}
        self.assertTrue(participant_noms.issubset(cheval_noms), "Certains participants n'ont pas de cheval associé")

        # Comparaison finale NumParticipant, Nom, Age
        for db_row, ref in zip(participants_rows, self.reference_data):
            self.assertEqual(db_row[0], ref.get("numPmu"))
            self.assertEqual(db_row[1], ref.get("nom"))
            self.assertEqual(db_row[2], ref.get("age"))


if __name__ == "__main__":
    unittest.main()
