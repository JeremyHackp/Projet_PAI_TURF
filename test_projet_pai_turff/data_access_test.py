import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sqlite3
import pytest
from unittest.mock import patch

import projet_pai_turff.data_access as da


# ==============================================================================
# CRÉATION DE LA BASE DE TEST
# ==============================================================================

def creer_ma_db_test():
    """
    Crée et retourne une DB de test avec des données connues
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Tables
    cur.execute("""
        CREATE TABLE Reunions (
            NumReunion INTEGER,
            DateReunion TEXT,
            NomHippodrome TEXT,
            PRIMARY KEY (NumReunion, DateReunion)
        )
    """)

    cur.execute("""
        CREATE TABLE Courses (
            NumCourse INTEGER,
            NumReunion INTEGER,
            DateReunion TEXT,
            LabelCourse TEXT,
            Distance REAL,
            Unite TEXT,
            Discipline TEXT,
            TypePiste TEXT,
            NbrParticipants INTEGER,
            MontantOffert1er REAL,
            MontantOffert2eme REAL,
            MontantOffert3eme REAL,
            MontantOffert4eme REAL,
            MontantOffert5eme REAL,
            CategorieParticularite TEXT,
            PenetrometreIntitule TEXT,
            PRIMARY KEY (NumCourse, NumReunion, DateReunion)
        )
    """)

    cur.execute("""
        CREATE TABLE Cheval (
            Nom TEXT PRIMARY KEY,
            NomDuPere TEXT,
            NomDeLaMere TEXT,
            Race TEXT,
            RobeLibelle TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE Participants (
            NumReunion INTEGER,
            NumCourse INTEGER,
            DateReunion TEXT,
            Nom TEXT,
            Age INTEGER,
            Sexe TEXT,
            Entraineur TEXT,
            Driver TEXT,
            NbrVictoires INTEGER,
            GainsCarriere REAL,
            PositionArrivee TEXT,
            Cote TEXT,
            PRIMARY KEY (Nom, NumReunion, NumCourse, DateReunion)
        )
    """)

    # MES DONNÉES DE TEST
    cur.execute("INSERT INTO Reunions VALUES (1, '03022025', 'Vincennes')")
    cur.execute("INSERT INTO Reunions VALUES (1, '04022025', 'Longchamp')")

    cur.execute("INSERT INTO Cheval VALUES ('Thunder', 'Papa', 'Maman', 'Pur-Sang', 'Bai')")
    cur.execute("INSERT INTO Cheval VALUES ('Spirit', 'Dad', 'Mom', 'Trotteur', 'Alezan')")

    cur.execute("""
        INSERT INTO Courses VALUES 
        (1, 1, '03022025', 'Course A', 2000, 'm', 'Plat', 'Gazon', 
         2, 1000, 500, 250, 100, 50, 'Groupe I', 'Bon')
    """)

    cur.execute("""
        INSERT INTO Courses VALUES 
        (1, 1, '04022025', 'Course B', 3000, 'm', 'Trot', 'Sable',
         1, 2000, 1000, 500, 200, 100, 'Groupe II', 'Souple')
    """)

    cur.execute("""
        INSERT INTO Participants VALUES
        (1, 1, '03022025', 'Thunder', 3, 'M', 'Trainer1', 'Jockey1', 10, 100000, '1', '2.5'),
        (1, 1, '03022025', 'Spirit', 4, 'F', 'Trainer2', 'Jockey2', 5, 50000, '2', '4.0'),
        (1, 1, '04022025', 'Thunder', 3, 'M', 'Trainer1', 'Jockey1', 10, 100000, '3', '3.0')
    """)

    conn.commit()
    return conn


class FakeFiltre:
    """Widget de filtre simulé"""

    def __init__(self, filtres=None, tri=None, nbr=100):
        self._state = {
            "filtres": filtres or [],
            "tri": tri,
            "nbr": nbr
        }

    def get_state(self):
        return self._state


# ==============================================================================
# TESTS (sans DB - juste logique)
# ==============================================================================

def test_build_where_clause_sans_filtre():
    """Entrée: [], Sortie: ('', [])"""
    where, params = da.build_where_clause_stats([])
    assert where == ""
    assert params == []


def test_build_where_clause_un_filtre():
    """Entrée: un filtre, Sortie: WHERE avec condition"""
    where, params = da.build_where_clause_stats([("race", "=", "Pur-Sang")])
    assert "WHERE" in where
    assert "c.Race = ?" in where
    assert params == ["Pur-Sang"]


def test_build_where_clause_plusieurs_filtres():
    """Entrée: plusieurs filtres, Sortie: WHERE avec AND"""
    where, params = da.build_where_clause_stats([
        ("race", "=", "Pur-Sang"),
        ("age", ">", 3)
    ])
    assert "WHERE" in where
    assert "AND" in where
    assert params == ["Pur-Sang", 3]


# ==============================================================================
# TESTS (avec DB de test)
# ==============================================================================

@patch('projet_pai_turff.course_data.get_connection')  # Patcher ICI où c'est utilisé
def test_recuperer_toutes_les_courses(mock_get_conn):
    """Entrée: pas de filtre, Sortie: 2 courses"""
    # Setup: utiliser MA DB de test
    ma_db = creer_ma_db_test()
    mock_get_conn.return_value = ma_db

    da.course_cache.clear()
    filtre = FakeFiltre()

    # Action
    ids = da.get_course_recentes_from_db(filtre)

    # Vérification
    assert len(ids) == 2, f"Je m'attends à 2 courses, j'ai {len(ids)}"

    course_1 = da.course_cache.courses[1]
    assert course_1["name"] == "Course B"
    assert course_1["place"] == "Longchamp"

    ma_db.close()


@patch('projet_pai_turff.course_data.get_connection')
def test_filtrer_courses_par_lieu(mock_get_conn):
    """Entrée: filtre Vincennes, Sortie: 1 course"""
    ma_db = creer_ma_db_test()
    mock_get_conn.return_value = ma_db

    da.course_cache.clear()
    filtre = FakeFiltre(filtres=[("place", "=", "Vincennes")])

    ids = da.get_course_recentes_from_db(filtre)

    assert len(ids) == 1, f"1 course à Vincennes, j'ai {len(ids)}"
    course = da.course_cache.courses[1]
    assert course["place"] == "Vincennes"

    ma_db.close()


@patch('projet_pai_turff.participant_data.get_connection')
def test_recuperer_participants_course_a(mock_get_conn):
    """Entrée: Course A, Sortie: 2 participants (Thunder et Spirit)"""
    ma_db = creer_ma_db_test()
    mock_get_conn.return_value = ma_db

    da.course_cache.clear()
    da.course_cache.courses[1] = {
        "_num_course": 1,
        "_num_reunion": 1,
        "_date_reunion": "03022025"
    }

    participant_ids = da.get_course_participants_id(1)

    assert len(participant_ids) == 2, f"2 participants attendus, j'ai {len(participant_ids)}"

    thunder = da.participants_cache.participants[1]
    assert thunder["name"] == "Thunder"
    assert thunder["age"] == 3
    assert thunder["jockey"] == "Jockey1"

    ma_db.close()


@patch('projet_pai_turff.participant_data.get_connection')
def test_recuperer_participants_course_b(mock_get_conn):
    """Entrée: Course B, Sortie: 1 participant (Thunder)"""
    ma_db = creer_ma_db_test()
    mock_get_conn.return_value = ma_db

    da.course_cache.clear()
    da.course_cache.courses[2] = {
        "_num_course": 1,
        "_num_reunion": 1,
        "_date_reunion": "04022025"
    }

    participant_ids = da.get_course_participants_id(2)

    assert len(participant_ids) == 1
    assert da.participants_cache.participants[1]["name"] == "Thunder"

    ma_db.close()


@patch('projet_pai_turff.participant_data.get_connection')
def test_meilleurs_chevaux_par_gains(mock_get_conn):
    """Entrée: tri par gains, Sortie: Thunder 1er (100k), Spirit 2ème (50k)"""
    ma_db = creer_ma_db_test()
    mock_get_conn.return_value = ma_db

    da.meilleurs_chevaux.clear()
    filtre = FakeFiltre(tri=("meilleurs toutes catégories", False), nbr=10)

    ids = da.get_meilleurs_cheveaux_ids(filtre)

    assert len(ids) == 2
    assert da.meilleurs_chevaux.participants[1]["name"] == "Thunder"
    assert "100000" in da.meilleurs_chevaux.participants[1]["total_gains"]

    ma_db.close()


@patch('projet_pai_turff.participant_data.get_connection')
def test_meilleurs_chevaux_filtrer_par_age(mock_get_conn):
    """Entrée: filtre age=3, Sortie: seulement Thunder"""
    ma_db = creer_ma_db_test()
    mock_get_conn.return_value = ma_db

    da.meilleurs_chevaux.clear()
    filtre = FakeFiltre(filtres=[("age", "=", 3)], tri=("meilleurs toutes catégories", False), nbr=10)

    ids = da.get_meilleurs_cheveaux_ids(filtre)

    assert len(ids) == 1
    assert da.meilleurs_chevaux.participants[1]["name"] == "Thunder"
    assert da.meilleurs_chevaux.participants[1]["age"] == 3

    ma_db.close()


# ==============================================================================
# TESTS Cache (pas besoin de DB)
# ==============================================================================

def test_cache_course_clear():
    """Vérifier que clear() vide le cache"""
    da.course_cache.clear()
    da.course_cache.courses[1] = {"name": "Test"}
    assert len(da.course_cache.courses) == 1

    da.course_cache.clear()
    assert len(da.course_cache.courses) == 0


def test_get_course_data_existante():
    """Entrée: ID existant, Sortie: données de la course"""
    da.course_cache.clear()
    da.course_cache.courses[1] = {"name": "Ma Course", "date": "01/01/2025"}

    course = da.get_course_data(1)
    assert course["name"] == "Ma Course"


def test_get_course_data_inexistante():
    """Entrée: ID inexistant, Sortie: {}"""
    da.course_cache.clear()
    course = da.get_course_data(999)
    assert course == {}


def test_get_participants_data_existant():
    """Entrée: ID existant, Sortie: données du participant"""
    da.participants_cache.clear()
    da.participants_cache.participants[1] = {"name": "Thunder", "age": 3}

    data = da.get_participants_data(1)
    assert data["name"] == "Thunder"


def test_get_participants_data_inexistant():
    """Entrée: ID inexistant, Sortie: {}"""
    da.participants_cache.clear()
    data = da.get_participants_data(999)
    assert data == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
