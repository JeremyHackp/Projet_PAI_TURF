import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sqlite3

import pytest

import projet_pai_turff.data_access as da
from unittest.mock import patch, MagicMock
# ======================================================================
# FIXTURE DB TEST
# ======================================================================


@pytest.fixture
def test_db(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE Cheval (
            Nom TEXT PRIMARY KEY,
            Race TEXT,
            RobeLibelle TEXT,
            NomDuPere TEXT,
            NomDeLaMere TEXT,
            Sexe TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE Courses (
            DateReunion TEXT,
            NumReunion INTEGER,
            NumCourse INTEGER,
            Distance INTEGER,
            Discipline TEXT,
            TypePiste TEXT,
            PRIMARY KEY (DateReunion, NumReunion, NumCourse)
        )
    """)

    cur.execute("""
        CREATE TABLE Participants (
            DateReunion TEXT,
            NumReunion INTEGER,
            NumCourse INTEGER,
            Nom TEXT,
            Age INTEGER,
            PositionArrivee TEXT,
            Cote REAL,
            Driver TEXT,
            Entraineur TEXT,
            PRIMARY KEY (DateReunion, NumReunion, NumCourse, Nom)
        )
    """)

    cur.execute(
        "INSERT INTO Cheval VALUES ('Thunder','Pur-Sang','Bai','Lightning','Storm','M')"
    )
    cur.execute("INSERT INTO Courses VALUES ('03022025',1,1,2000,'Plat','Gazon')")
    cur.execute(
        "INSERT INTO Participants VALUES ('03022025',1,1,'Thunder',3,'1',3.5,'Dupont','Martin')"
    )

    conn.commit()

    monkeypatch.setattr("data_access.get_connection", lambda: conn)

    yield conn
    conn.close()


# ======================================================================
# TEST QUERY BUILDER
# ======================================================================


def test_build_where_clause_stats():
    where, params = da.build_where_clause_stats(
        [("race", "=", "Pur-Sang"), ("age", ">", 2)]
    )

    assert "c.Race" in where
    assert "p.Age" in where
    assert params == ["Pur-Sang", 2]


# ======================================================================
# TEST CACHE
# ======================================================================


def test_participants_cache():
    da.participants_cache.clear()
    da.participants_cache.participants[1] = {"Nom": "Thunder"}

    assert 1 in da.participants_cache.participants

    da.participants_cache.clear()
    assert len(da.participants_cache.participants) == 0


# ======================================================================
# TEST PARTICIPANTS DATA
# ======================================================================

def test_get_participants_data():
    # Vider le cache avant le test
    da.participants_cache.clear()

    da.participants_cache.participants[1] = {
        "Nom": "Thunder",
        "Age": 3
    }

    data = da.get_participants_data(1)

    assert data["Nom"] == "Thunder"
    assert data["Age"] == 3

    data_vide = da.get_participants_data(999)
    assert data_vide == {}

# ======================================================================
# FAKE GRAPH CLASSES
# ======================================================================


class FakeAx:
    def __init__(self):
        self.plotted = False

    def tick_params(self, **kwargs):
        pass

    def text(self, *args, **kwargs):
        pass

    @property
    def transAxes(self):
        return None


class FakeGraph:
    def __init__(self):
        self.ax = MagicMock()
        self.figure = MagicMock()
        self.plotted = False

    def clear(self):
        pass

    def plot(self, x, y, **kwargs):
        self.plotted = True


class FakeFiltre:
    def get_state(self):
        return {"filtres": []}  # tu peux ajouter des filtres si besoin


# ======================================================================
# TEST EXPORTS
# ======================================================================


def test_exports():
    assert hasattr(da, "build_where_clause_stats")
    assert hasattr(da, "get_participants_data")
    assert hasattr(da, "update_graphe_stats_groupe")
