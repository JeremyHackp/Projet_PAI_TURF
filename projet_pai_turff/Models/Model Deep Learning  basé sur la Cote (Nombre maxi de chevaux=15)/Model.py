import numpy as np
import tensorflow as tf
from typing import List, Optional, Sequence
import os
from projet_pai_turff.data_access import get_participants_data

# Nombre maximal de chevaux attendu par le modèle
MAX_CHEVAUX = 15

# =================================================
# Fonction utilitaire : transforme les cotes en probabilités implicites
# =================================================
def implicit_probabilities(
    odds: Sequence[float],
    mask: Optional[Sequence[int | bool]] = None,
    eps: float = 1e-12,
    verbose: bool = False
) -> np.ndarray:
    """
    Convertit des cotes décimales en probabilités implicites normalisées.

    Cette fonction calcule l'inverse des cotes, applique un masque
    optionnel pour ignorer les chevaux de padding, puis normalise
    les probabilités afin que leur somme soit égale à 1.

    Parameters
    ----------
    odds : Sequence[float]
        Liste ou tableau des cotes décimales pour les chevaux
        (longueur N).
    mask : Optional[Sequence[int | bool]]
        Masque indiquant quels chevaux sont valides (1 / True)
        ou issus du padding (0 / False).
        Si None, tous les chevaux sont considérés valides.
    eps : float, default=1e-12
        Valeur minimale utilisée pour éviter une division par zéro.
    verbose : bool, default=False
        Active l'affichage des informations de debug.

    Returns
    -------
    np.ndarray
        Tableau des probabilités implicites normalisées,
        de shape (N,). Les chevaux masqués ont une probabilité nulle.

    Notes
    -----
    Les probabilités sont calculées comme :

    .. math::

        p_i = \\frac{1 / \\text{odds}_i}{\\sum_j (1 / \\text{odds}_j)}

    Raises
    ------
    ValueError
        Si la somme des probabilités est nulle.
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
def predict_ranking(
    participant_ids: List[int],
    verbose: bool = False
) -> List[int]:
    """
    Prédit l'ordre d'arrivée des participants d'une course hippique.

    Cette fonction :
    - charge les données des participants
    - transforme les cotes en probabilités implicites
    - applique un padding jusqu'à ``MAX_CHEVAUX``
    - utilise un modèle TensorFlow pour prédire un score par cheval
    - retourne les identifiants triés du meilleur au pire

    Parameters
    ----------
    participant_ids : List[int]
        Liste des identifiants des chevaux participants.
    verbose : bool, default=False
        Active l'affichage des informations de debug.

    Returns
    -------
    List[int]
        Liste des identifiants des chevaux triés selon
        l'ordre d'arrivée prédit (meilleur → pire).

    Raises
    ------
    FileNotFoundError
        Si le fichier ``Model.h5`` est introuvable.
    RuntimeError
        Si la prédiction du modèle échoue.

    Notes
    -----
    Le modèle doit :
    - accepter une entrée de shape ``(1, MAX_CHEVAUX)``
    - produire un vecteur de scores de shape ``(MAX_CHEVAUX,)``

    Les chevaux ajoutés par padding sont automatiquement ignorés
    dans le classement final.
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
                print(f"[WARNING] Pas de données pour le participant {pid}, valeurs par défaut utilisées")
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
    ranking = [participant_ids[i] for i in ranking_indices if participant_ids[i] is not None]

    if verbose:
        print("[INFO] Ordre final prédit :", ranking)

    return ranking