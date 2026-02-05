import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from projet_pai_turff.PredictionDetailWindows import (
    ParticipantVerificationWindow,
    PredictionDetailWindow,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def app():
    """Instance QApplication requise pour PySide6."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def disable_qt_dialogs(monkeypatch):
    """
    Désactive toutes les boîtes de dialogue Qt pendant les tests
    pour éviter les popups bloquantes.
    """
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: None)

    # Empêche les exec_() bloquants
    monkeypatch.setattr(ParticipantVerificationWindow, "exec_", lambda self: None)


# ============================================================================
# TESTS
# ============================================================================


def test_prediction_window_initialization(app):
    """
    Vérifie que la fenêtre s'initialise sans erreur.
    """
    window = PredictionDetailWindow(id=1)
    assert window is not None
    assert window.course_id == 1


def test_participants_loaded(app):
    """
    Vérifie que les participants sont bien chargés.
    """
    window = PredictionDetailWindow(id=1)
    assert isinstance(window.participants_data_list, list)


def test_model_loading(app):
    """
    Vérifie que le modèle DummyModel est chargé correctement.
    """
    window = PredictionDetailWindow(id=1)

    # Simule la sélection du modèle
    window._load_selected_model("DummyModel")

    assert window.model_module is not None
    assert hasattr(window.model_module, "predict_ranking")


def test_prediction_logic(app):
    """
    Vérifie que la prédiction réordonne les participants.
    """
    window = PredictionDetailWindow(id=1)
    window._load_selected_model("DummyModel")

    original_ids = [p["id"] for p in window.participants_data_list]

    window._predict()

    # DummyModel renvoie l'ordre inversé
    assert window.prediction_ids == list(reversed(original_ids))


def test_verification_window_creation(app, qtbot):
    """
    Vérifie que la fenêtre de vérification est appelée sans erreur.
    """
    window = PredictionDetailWindow(id=1)
    qtbot.addWidget(window)

    window._load_selected_model("DummyModel")
    window._predict()

    # Ne doit pas lever d'exception
    window._verify_prediction_order()


def test_model_combobox_filled(app):
    """
    Vérifie que le QComboBox des modèles contient au moins un modèle.
    """
    window = PredictionDetailWindow(id=1)

    # Vérifie que le combobox contient au moins DummyModel
    combo_texts = [
        window.model_selector.itemText(i) for i in range(window.model_selector.count())
    ]
    assert "DummyModel" in combo_texts
    assert window.model_selector.count() > 0


def test_predict_button_triggers_prediction(app, qtbot, monkeypatch):
    """
    Vérifie que cliquer sur le bouton 'Prédire' appelle bien _predict()
    et met à jour prediction_ids.
    """
    window = PredictionDetailWindow(id=1)
    qtbot.addWidget(window)

    window._load_selected_model("DummyModel")

    # Capture de l'ancien ordre
    original_ids = [p["id"] for p in window.participants_data_list]

    # Compter les appels à _predict
    call_counter = {"called": False}

    def fake_predict():
        call_counter["called"] = True
        window.prediction_ids = list(reversed(original_ids))

    monkeypatch.setattr(window, "_predict", fake_predict)

    # Cherche le bouton "Prédire" parmi les QPushButton
    predict_button = next(
        (w for w in window.findChildren(QPushButton) if w.text() == "Prédire"), None
    )
    assert predict_button is not None, "Bouton 'Prédire' introuvable"

    # Simule le clic sur le bouton
    qtbot.mouseClick(predict_button, Qt.LeftButton)

    # Vérifie que _predict a été appelé
    assert call_counter["called"] is True
    # Vérifie que prediction_ids a été mis à jour correctement
    assert window.prediction_ids == list(reversed(original_ids))
