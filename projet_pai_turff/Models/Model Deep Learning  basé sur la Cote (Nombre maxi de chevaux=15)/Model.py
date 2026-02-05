import os

import numpy as np
import tensorflow as tf

from projet_pai_turff.data_access import get_participants_data

# Nombre maximal de chevaux attendu par le modèle
MAX_CHEVAUX = 15


# =================================================
# Fonction utilitaire : transforme les cotes en probabilités implicites
# =================================================
def implicit_probabilities(odds, mask=None, eps=1e-12, verbose=False):
    """
    Convertit les cotes en probabilités implicites normalisées.

    Paramètres
    ----------
    odds : list ou np.ndarray, shape (N_chevaux,)
        Liste des cotes décimales pour une course.
    mask : list ou np.ndarray de 0/1, shape (N_chevaux,), optionnel
        Indique quels chevaux sont valides (1) ou padding (0).
        Si None, tous les chevaux sont considérés valides.
    eps : float
        Petite valeur pour éviter la division par zéro.
    verbose : bool
        Affiche les étapes de debug.

    Retour
    ------
    probs : np.ndarray, shape (N_chevaux,)
        Probabilités implicites normalisées.
        Chevaux masqués auront une probabilité 0.
    """
    odds = np.array(odds, dtype=np.float32)
    N = len(odds)

    if mask is None:
        mask = np.ones(N, dtype=bool)
    else:
        mask = np.array(mask, dtype=bool)

    probs = np.zeros(N, dtype=np.float32)
    valid_odds = odds[mask]

    # éviter division par 0
    valid_odds[valid_odds == 0] = eps

    inv = 1.0 / valid_odds
    probs[mask] = inv / np.sum(inv)

    if verbose:
        print("[DEBUG] odds :", odds)
        print("[DEBUG] mask :", mask)
        print("[DEBUG] probabilités implicites :", probs)

    return probs


# =================================================
# Fonction principale de prédiction
# =================================================
def predict_ranking(participant_ids, verbose=False):
    """
    Prédit l'ordre d'arrivée des chevaux pour une course.

    Parameters
    ----------
    participant_ids : list[int]
        Liste des IDs des chevaux participants.
    verbose : bool
        Si True, affiche des informations de debug.

    Returns
    -------
    list[int]
        Liste des IDs triés par ordre prédit (meilleur → pire).
    """
    if verbose:
        print("[INFO] participant_ids reçus :", participant_ids)

    # =========================
    # Charger les données des participants
    # =========================
    participants_data = []
    for pid in participant_ids:
        data = get_participants_data(pid)
        if not data:
            if verbose:
                print(
                    f"[WARNING] Pas de données pour le participant {pid}, valeurs par défaut utilisées"
                )
            data = {"odds": 0.0, "id": pid, "name": f"Participant {pid}"}
        participants_data.append(data)

    # Extraire les cotes
    odds_list = [float(p.get("odds", 0.0) or 0.0) for p in participants_data]

    # =========================
    # Padding pour atteindre MAX_CHEVAUX
    # =========================
    while len(odds_list) < MAX_CHEVAUX:
        odds_list.append(0.0)
        participant_ids.append(None)  # placeholder pour ID inexistant

    if verbose:
        print("[DEBUG] Odds après padding :", odds_list)
        print("[DEBUG] participant_ids après padding :", participant_ids)

    # Créer le masque : 1 pour vrai cheval, 0 pour padding
    mask = np.array([pid is not None for pid in participant_ids], dtype=np.float32)

    # =========================
    # Charger le modèle
    # =========================
    model_path = os.path.join(os.path.dirname(__file__), "Model.h5")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Impossible de trouver le modèle à {model_path}")

    model = tf.keras.models.load_model(model_path, compile=False)
    if verbose:
        print(f"[INFO] Modèle chargé depuis {model_path}")

    # =========================
    # Préparer l'entrée pour le modèle
    # =========================
    X = implicit_probabilities(odds_list, mask=mask, verbose=verbose)
    X = X.reshape(1, -1)  # modèle attend (1, MAX_CHEVAUX)
    if verbose:
        print("[DEBUG] Entrée pour le modèle (X) :", X)

    # =========================
    # Prédiction
    # =========================
    scores = model.predict(X, verbose=0)[0]  # shape = (MAX_CHEVAUX,)
    if verbose:
        print("[DEBUG] Scores prédits :", scores)

    # Tri par score décroissant
    ranking_indices = np.argsort(-scores)
    if verbose:
        print("[DEBUG] Indices triés :", ranking_indices)

    # Retourner uniquement les vrais IDs (ignorer padding)
    ranking = [
        participant_ids[i] for i in ranking_indices if participant_ids[i] is not None
    ]

    if verbose:
        print("[INFO] Ordre final prédit :", ranking)

    return ranking
