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

        # Crée la table Participants (avec les nouveaux attributs)
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
            Eleveur TEXT,
            Musique TEXT,
            ReductionKilometrique REAL,
            PRIMARY KEY (Nom, NumReunion, NumCourse, DateReunion),
            FOREIGN KEY (Nom) REFERENCES Cheval(Nom)
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

    @patch("get_participant_insert_into_data_base.requests.get")
    def test_fetch_and_insert_matches_json(self, mock_get):
        """Teste la récupération, l'insertion et la cohérence des données Participants/Cheval"""

        # Mock de la réponse API avec le JSON de test
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"participants": self.reference_data}
        mock_get.return_value = mock_response

        date_reunion = "01012020"
        num_reunion = 1
        num_course = 1

        # Exécution de la fonction principale
        fetch_and_insert_participants(date_reunion, num_reunion, num_course, db_path=self.db_path)

        # Vérifie les insertions dans Participants
        self.cursor.execute("""
            SELECT NumParticipant, Nom, Age, Eleveur, Musique, ReductionKilometrique
            FROM Participants ORDER BY NumParticipant
        """)
        participants_rows = self.cursor.fetchall()
        self.assertEqual(len(participants_rows), len(self.reference_data), "Le nombre de participants insérés ne correspond pas au JSON.")

        # Vérifie que les chevaux ont bien été ajoutés
        self.cursor.execute("SELECT Nom FROM Cheval")
        chevaux_rows = self.cursor.fetchall()
        self.assertGreater(len(chevaux_rows), 0, "Aucun cheval inséré dans la table Cheval.")

        # Vérifie cohérence entre Participants et Cheval
        participant_noms = {row[1] for row in participants_rows}
        cheval_noms = {row[0] for row in chevaux_rows}
        self.assertTrue(participant_noms.issubset(cheval_noms), "Certains participants n'ont pas de cheval associé.")

        # Vérification individuelle des nouveaux attributs
        for db_row, ref in zip(participants_rows, self.reference_data):
            num_participant, nom, age, eleveur, musique, reduction = db_row

            self.assertEqual(num_participant, ref.get("numPmu"), f"NumParticipant incorrect pour {nom}")
            self.assertEqual(nom, ref.get("nom"), f"Nom incorrect pour le participant {num_participant}")
            self.assertEqual(age, ref.get("age"), f"Âge incorrect pour {nom}")

            # Nouveaux attributs
            self.assertEqual(eleveur, ref.get("eleveur"), f"Eleveur incorrect pour {nom}")
            self.assertEqual(musique, ref.get("musique"), f"Musique incorrecte pour {nom}")
            self.assertEqual(reduction, ref.get("reductionKilometrique"), f"Réduction kilométrique incorrecte pour {nom}")

            # Vérifie que les champs ne sont pas vides s'ils existent dans le JSON
            if ref.get("eleveur"):
                self.assertIsInstance(eleveur, str, f"Eleveur doit être une chaîne pour {nom}")
                self.assertGreater(len(eleveur.strip()), 0, f"Eleveur vide pour {nom}")

            if ref.get("musique"):
                self.assertIsInstance(musique, str, f"Musique doit être une chaîne pour {nom}")
                self.assertGreater(len(musique.strip()), 0, f"Musique vide pour {nom}")

            if ref.get("reductionKilometrique") is not None:
                self.assertIsInstance(reduction, (float, int), f"Réduction kilométrique doit être numérique pour {nom}")

if __name__ == "__main__":
    unittest.main()
