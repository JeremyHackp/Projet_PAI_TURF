import sys
import numpy as np
import matplotlib
import pytest
from pathlib import Path

matplotlib.use("Agg")  # backend non-GUI pour matplotlib

from PySide6.QtWidgets import QApplication

from projet_pai_turff.my_module import typed_function, other_function
from projet_pai_turff.OngletButton import load_icon_pair
from projet_pai_turff.Graphe import Graphe
from projet_pai_turff.Filtre import Filtre
from projet_pai_turff.data_access import (
    colonnes_filtrage_courses,
    colonnes_tri_courses,
)


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


# -------------------------
# Tests non graphiques
# -------------------------


def test_typed_function():
    assert not typed_function(np.zeros(10), "")
    assert not typed_function(np.zeros(10), "hello")
    assert not typed_function(np.ones(5))


def test_other_function():
    other_function()


# -------------------------
# Tests Qt (avec qapp), graphiques
# -------------------------


def test_load_icon_pair_existing(qapp):
    icon_path = Path("projet_pai_turff/assets/courses.png")
    normal, dark = load_icon_pair(icon_path)

    assert normal is not None
    assert dark is not None


def test_load_icon_pair_missing(qapp):
    non_exist = Path("non_exist.png")
    normal, dark = load_icon_pair(non_exist)

    assert normal is None
    assert dark is None


def test_graphe(qapp):
    graphe = Graphe()
    assert graphe is not None

    graphe.clear()
    graphe.plot([1, 2, 3], [4, 5, 6], title="Test")
    graphe.hist([1, 2, 3, 4, 5])
    graphe.bar([1, 2, 3], [4, 5, 6])
    graphe.scatter([1, 2, 3], [4, 5, 6])


def test_filtre_widget(qapp):
    filtre = Filtre(colonnes_filtrage_courses, colonnes_tri_courses)
    assert filtre is not None

    filtres = filtre.get_filtres()
    assert isinstance(filtres, list)

    tri = filtre.get_tri()
    assert tri is None or isinstance(tri, tuple)

    state = filtre.get_state()
    assert isinstance(state, dict)

    filtre.reinitialiser()
    assert filtre.get_filtres() == []
