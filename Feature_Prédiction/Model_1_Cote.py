"""
========================================================================
Script de préparation, d'entraînement et de sauvegarde d'un modèle
de classement de chevaux basé sur les cotes des bookmakers.

Ce script effectue les étapes suivantes :

1 Extraction et préparation du dataset
   - Connexion à la base SQLite contenant la table Participants.
   - Sélection aléatoire de N courses valides.
   - Construction de trois matrices :
       * M : cotes brutes des chevaux (features)
       * L : rangs d'arrivée réels (labels)
       * m : masque indiquant quels chevaux sont présents
   - Application de padding pour les courses avec moins de chevaux
   - Vérification que les rangs forment une séquence naturelle (1..N)
   - Transformation des cotes en probabilités implicites normalisées
   - Normalisation des rangs en scores [0,1] pour la régression
   - Sanity check pour garantir la cohérence du dataset
   - Sauvegarde des matrices M, L et m dans des fichiers .txt

2️ Définition du réseau de neurones
   - Réseau fully-connected feed-forward
   - Input : vecteur de probabilités implicites par cheval
   - Couches intermédiaires : ReLU, définies par `hidden_units`
   - Sortie : scores latents par cheval (non normalisés, pas de softmax)
   - Fonction de loss : MSE masquée (ignore le padding)

3️ Split train / test
   - Séparation au niveau des courses (pas de mélange au sein d'une course)
   - Paramètres :
       * test_ratio = 0.1 par défaut
       * shuffle = True pour mélanger les courses avant split

4️ Entraînement
   - Optimiseur : Adam avec learning_rate=0.001
   - Batch size : 16 courses par batch
   - Nombre d'époques : 50
   - Validation : 10% du train pour suivi de loss

5️ Visualisation
   - Affichage de l'évolution de la loss sur le train et la validation
   - Graphique avec matplotlib

6️ Sauvegarde du modèle
   - Le modèle entraîné est sauvegardé au format HDF5 (`mon_modele.h5`)
   - Permet de le recharger ultérieurement sans réentraîner

7️ Évaluation des performances
   - Calcul des métriques sur le jeu test pour le modèle entraîné :
       * 'proportion_exact' : proportion de chevaux exactement classés
       * 'proportion_top3' : proportion des chevaux du top 3 correctement identifiés
       * 'best_in_top3'   : proportion de courses où le meilleur cheval
                             prédit est bien dans le top 3 réel
   - Comparaison avec un estimateur naïf basé sur les cotes :
       * Plus la cote est faible, meilleur est le cheval
       * Même métriques calculées pour juger de la performance naïve
   - Résultats affichés pour le modèle et l'estimateur naïf


========================================================================
Modules utilisés :
- sqlite3      : accès à la base SQLite
- numpy        : manipulation des matrices et vecteurs
- matplotlib   : visualisation des courbes
- tensorflow   : construction et entraînement du réseau
- tqdm         : barre de progression pour le traitement des courses

========================================================================
Notes importantes :
- Les cotes sont converties en probabilités implicites inversées,
  normalisées par course.
- Les rangs normalisés ne sont PAS des probabilités : ce sont des
  scores continus pour la régression, préservant l'ordre.
- Les fonctions de sanity check garantissent l'alignement
  des matrices et la validité des valeurs.
- Le padding est utilisé pour uniformiser la taille des courses
  avec moins de chevaux que `n_max_chevaux`.
========================================================================
"""

from tensorflow.keras.models import load_model
import sqlite3
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tqdm import tqdm


def evaluate_performance(Y_true, Y_pred, m):
    """
    Évalue les performances d'un modèle sur un jeu de test.

    Trois métriques sont calculées par course :
        1️ Proportion de chevaux exactement classés.
        2️ Proportion des chevaux du top 3 correctement identifiés.
        3️ Fraction de courses où le meilleur cheval prédit est dans le top 3 réel.

    Les calculs prennent en compte uniquement les chevaux présents
    (mask=1) pour ignorer le padding.

    Paramètres
    ----------
    Y_true : np.ndarray, shape (N_courses, max_chevaux)
        Scores réels normalisés (labels).
    Y_pred : np.ndarray, shape (N_courses, max_chevaux)
        Scores prédits par le modèle.
    m : np.ndarray, shape (N_courses, max_chevaux)
        Masque indiquant les chevaux présents (1) ou padding (0).

    Retour
    ------
    results : dict
        Dictionnaire contenant les trois métriques :
            - 'proportion_exact' : proportion de chevaux exactement classés.
            - 'proportion_top3' : proportion des chevaux du top 3 correctement identifiés.
            - 'best_in_top3'   : proportion de courses où le meilleur cheval prédit
                                  est bien dans le top 3 réel.
    """
    n_courses = Y_true.shape[0]
    total_chevaux = 0
    total_correct = 0
    top3_correct = 0
    best_in_top3_count = 0

    for i in range(n_courses):
        mask = m[i] == 1
        n_chevaux = np.sum(mask)
        if n_chevaux == 0:
            continue  # ignore les courses vides
        total_chevaux += n_chevaux

        # 🔹 Indices triés du meilleur au pire
        real_order = np.argsort(-Y_true[i][mask])
        pred_order = np.argsort(-Y_pred[i][mask])

        # 1️⃣ Exact : comparaison position par position
        total_correct += np.sum(real_order == pred_order)

        # 2️⃣ Top 3 proportionnel
        top3_real = set(real_order[:3])
        top3_pred = set(pred_order[:3])
        common = len(top3_real & top3_pred)
        top3_correct += common / 3

        # 3️⃣ Meilleur cheval prédit dans le top 3 réel
        best_pred = pred_order[0]
        if best_pred in real_order[:3]:
            best_in_top3_count += 1

    proportion_exact = total_correct / total_chevaux
    proportion_top3 = top3_correct / n_courses
    best_in_top3 = best_in_top3_count / n_courses

    results = {
        "proportion_exact": proportion_exact,
        "proportion_top3": proportion_top3,
        "best_in_top3": best_in_top3,
    }

    return results


def evaluate_performance_with_odds(Y_true, Y_pred, m, X):
    """
    Évalue la performance du modèle et d'un estimateur naïf basé sur les cotes.

    Paramètres :
    -----------
    Y_true : np.array, shape (N_courses, max_chevaux)
        Scores réels normalisés
    Y_pred : np.array, shape (N_courses, max_chevaux)
        Scores prédits par le modèle
    m : np.array, shape (N_courses, max_chevaux)
        Masque des chevaux présents (1 = présent, 0 = padding)
    X : np.array, shape (N_courses, max_chevaux)
        Features utilisées pour l'odds (probabilités ou cotes)

    Retour :
    -------
    results : dict
        Contient les 3 métriques pour le modèle et pour l'estimateur naïf
    """

    def compute_metrics(Y_pred_local):
        """Calcule les métriques pour un jeu de prédictions donné"""
        n_courses = Y_true.shape[0]
        total_chevaux = 0
        total_correct = 0
        top3_correct = 0
        best_in_top3_count = 0

        for i in range(n_courses):
            mask = m[i] == 1
            n_chevaux = np.sum(mask)
            if n_chevaux == 0:
                continue
            total_chevaux += n_chevaux

            # Tri décroissant pour obtenir l'ordre des chevaux (indice du meilleur au pire)
            real_order = np.argsort(-Y_true[i][mask])
            pred_order = np.argsort(-Y_pred_local[i][mask])

            # 1️⃣ Proportion exact : combien de chevaux sont exactement à la même place
            total_correct += np.sum(real_order == pred_order)

            # 2️⃣ Top 3 proportionnel : fraction de chevau correspondant dans le top3
            top3_real = set(real_order[:3])
            top3_pred = set(pred_order[:3])
            top3_correct += len(top3_real & top3_pred) / 3

            # 3️⃣ Meilleur cheval prédit dans le top 3 réel
            best_pred = pred_order[0]
            if best_pred in real_order[:3]:
                best_in_top3_count += 1

        return {
            "proportion_exact": total_correct / total_chevaux,
            "proportion_top3": top3_correct / n_courses,
            "best_in_top3": best_in_top3_count / n_courses,
        }

    # 1️ Métriques pour le modèle
    metrics_model = compute_metrics(Y_pred)

    # 2️ Métriques pour l'estimateur naïf basé sur les cotes
    Y_pred_naive = np.array(X)
    metrics_naive = compute_metrics(Y_pred_naive)

    # ========================================================
    # 3️⃣ Résultats combinés
    # ========================================================
    results = {"model": metrics_model, "naive_odds": metrics_naive}

    return results


def masked_mse(y_true, y_pred):
    """
    Mean Squared Error (MSE) masquée, calculée uniquement
    sur les chevaux effectivement présents dans chaque course.

    Cette fonction est conçue pour des données avec padding :
    - y_true = 0  → cheval absent (padding)
    - y_true > 0  → cheval présent

    La loss est calculée course par course, puis moyennée
    sur le batch.

    Paramètres
    ----------
    y_true : tf.Tensor, shape (batch_size, max_chevaux)
        Scores cibles normalisés (ex: rangs normalisés).
        Les valeurs à 0 correspondent au padding.

    y_pred : tf.Tensor, shape (batch_size, max_chevaux)
        Scores prédits par le modèle (scores latents).

    Retour
    ------
    tf.Tensor (scalaire)
        Valeur moyenne de la MSE masquée sur le batch.
    """

    # 1️⃣ Création du masque :
    # mask = 1 pour les chevaux présents, 0 pour le padding
    # On utilise y_true car le padding y est strictement à 0
    mask = tf.cast(tf.not_equal(y_true, 0), tf.float32)

    # 2️⃣ Nombre de chevaux valides par course
    # shape : (batch_size, 1)
    n = tf.reduce_sum(mask, axis=1, keepdims=True)

    # 3️⃣ Erreur quadratique masquée
    # - (y_true - y_pred)^2 : erreur par cheval
    # - multiplication par mask : ignore le padding
    squared_error = mask * tf.square(y_true - y_pred)

    # 4️⃣ MSE par course :
    # somme des erreurs / nombre de chevaux présents
    loss_per_course = tf.reduce_sum(squared_error, axis=1, keepdims=True) / (
        n + 1e-8
    )  # epsilon pour éviter division par zéro

    # 5️⃣ Moyenne sur le batch
    return tf.reduce_mean(loss_per_course)


def build_model(max_chevaux, hidden_units=[64, 32]):
    """
    Construit un réseau de neurones feed-forward pour prédire
    des scores latents de performance par cheval, course par course.

    Le modèle prend en entrée un vecteur de taille `max_chevaux`
    représentant les probabilités implicites (dérivées des cotes),
    et produit un score latent pour chaque cheval.

    Les sorties NE sont PAS des probabilités :
    - pas de softmax
    - pas de normalisation
    - l'ordre relatif des scores est utilisé pour le classement

    Paramètres
    ----------
    max_chevaux : int
        Nombre maximal de chevaux par course.
        Définit la dimension d'entrée et de sortie du réseau.

    hidden_units : list of int, optionnel (défaut = [64, 32])
        Liste définissant la taille des couches denses intermédiaires.
        Chaque couche utilise une activation ReLU.

    Retour
    ------
    model : tf.keras.Model
        Modèle Keras prêt à être compilé.
        Entrée : (batch_size, max_chevaux)
        Sortie : (batch_size, max_chevaux)
    """

    # Entrée : probabilités implicites par cheval (padding = 0)
    inputs = layers.Input(shape=(max_chevaux,), name="input_prob")

    # Couche de masquage :
    # - ignore les chevaux padding (valeur 0)
    # - utile si certaines couches futures exploitent le mask
    # - ici surtout une sécurité conceptuelle
    x = layers.Masking(mask_value=0.0)(inputs)

    # Couches denses fully-connected
    # Ces couches modélisent des interactions globales entre chevaux
    # (le modèle "voit" la course comme un tout)
    for units in hidden_units:
        x = layers.Dense(units, activation="relu")(x)

    # Sortie : score latent par cheval
    # Activation linéaire car on cherche un score ordinal, pas une proba
    outputs = layers.Dense(max_chevaux, activation="linear", name="latent_scores")(x)

    # Construction du modèle Keras
    model = models.Model(inputs=inputs, outputs=outputs, name="horse_ranking_model")

    return model


def train_test_split_masked(X, Y, m, test_ratio=0.1, shuffle=True, seed=None):
    """
    Sépare le dataset en jeux d'entraînement et de test en conservant
    la structure par course et le masque associé.

    La séparation se fait au niveau des courses (ligne par ligne),
    garantissant qu'une course complète ne se retrouve que dans un seul
    des deux ensembles.

    Paramètres
    ----------
    X : np.ndarray, shape = (n_courses, max_chevaux)
        Entrées du modèle.
        Ici : probabilités implicites normalisées par course.

    Y : np.ndarray, shape = (n_courses, max_chevaux)
        Labels cibles.
        Scores de rang normalisés dérivés du classement réel.
        ⚠️ Ce ne sont pas des probabilités.

    m : np.ndarray, shape = (n_courses, max_chevaux)
        Masque binaire des chevaux présents.
        - 1 → cheval présent
        - 0 → padding

    test_ratio : float, optionnel (défaut = 0.1)
        Proportion des courses placées dans le jeu de test.
        Doit vérifier : 0 < test_ratio < 1.

    shuffle : bool, optionnel (défaut = True)
        Si True, mélange aléatoirement les courses avant la séparation.

    seed : int ou None, optionnel
        Graine du générateur aléatoire pour garantir la reproductibilité
        lorsque shuffle=True.

    Retour
    ------
    X_train : np.ndarray, shape = (n_train, max_chevaux)
        Entrées du jeu d'entraînement.

    Y_train : np.ndarray, shape = (n_train, max_chevaux)
        Labels du jeu d'entraînement.

    m_train : np.ndarray, shape = (n_train, max_chevaux)
        Masque du jeu d'entraînement.

    X_test : np.ndarray, shape = (n_test, max_chevaux)
        Entrées du jeu de test.

    Y_test : np.ndarray, shape = (n_test, max_chevaux)
        Labels du jeu de test.

    m_test : np.ndarray, shape = (n_test, max_chevaux)
        Masque du jeu de test.
    """

    # Nombre total de courses
    N = X.shape[0]

    # Indices des courses
    indices = np.arange(N)

    # Mélange optionnel pour éviter tout biais temporel ou structurel
    if shuffle:
        rng = np.random.default_rng(seed)
        rng.shuffle(indices)

    # Taille du jeu de test
    test_size = int(N * test_ratio)

    # Séparation des indices
    test_idx = indices[:test_size]
    train_idx = indices[test_size:]

    # Construction des ensembles
    X_train = X[train_idx]
    Y_train = Y[train_idx]
    m_train = m[train_idx]

    X_test = X[test_idx]
    Y_test = Y[test_idx]
    m_test = m[test_idx]

    return X_train, Y_train, m_train, X_test, Y_test, m_test


def sanity_check_dataset(X, Y, m, tol=1e-6, verbose=True):
    """
    Vérifie la cohérence mathématique et structurelle du dataset course par course.

    Cette fonction agit comme un garde-fou avant l'entraînement du modèle.
    Elle vérifie que :
        - les shapes sont cohérentes
        - le padding est correctement appliqué
        - les valeurs sont dans les bornes attendues
        - les normalisations sont valides
        - l'ordre induit par les labels est cohérent

    En cas d'erreur, une AssertionError est levée avec un message explicite.
    Si verbose=True, un résumé est affiché pour chaque course.

    Paramètres
    ----------
    X : np.ndarray, shape = (n_courses, max_chevaux)
        Features d'entrée du modèle.
        Ici : probabilités implicites dérivées des cotes.
        - X[i, j] ∈ [0, 1]
        - ∑_j X[i, j] = 1 pour les chevaux présents
        - X[i, j] = 0 pour le padding

    Y : np.ndarray, shape = (n_courses, max_chevaux)
        Labels cibles du modèle.
        Scores de rang normalisés dérivés du classement réel.
        - Y[i, j] ∈ [0, 1]
        - max(Y[i]) = 1 (vainqueur)
        - min(Y[i]) = 0 (dernier)
        ⚠️ Ce ne sont PAS des probabilités.

    m : np.ndarray, shape = (n_courses, max_chevaux)
        Masque binaire indiquant la présence des chevaux.
        - 1 → cheval présent
        - 0 → padding / cheval absent

    tol : float, optionnel (défaut = 1e-6)
        Tolérance numérique utilisée pour les tests de normalisation
        (sommes, max, min).

    verbose : bool, optionnel (défaut = True)
        Si True, affiche un message de validation pour chaque course
        ainsi qu'un résumé final.

    Retour
    ------
    None
        La fonction ne retourne rien.
        Elle lève une AssertionError si une incohérence est détectée.
    """

    N, max_c = X.shape

    # 1️⃣ Vérification des dimensions globales
    assert Y.shape == (N, max_c), "Shape incohérent entre X et Y"
    assert m.shape == (N, max_c), "Shape incohérent entre X et m"

    # Vérification course par course
    for i in range(N):
        mask = m[i] == 1
        n = mask.sum()

        # Une course doit contenir au minimum 2 chevaux
        assert n >= 2, f"Course {i}: moins de 2 chevaux"

        # 2️⃣ Vérification du padding
        # Les positions masquées doivent être strictement nulles
        assert np.all(X[i][~mask] == 0), f"Course {i}: padding X non nul"
        assert np.all(Y[i][~mask] == 0), f"Course {i}: padding Y non nul"

        # 3️⃣ Vérification des bornes numériques
        # Les probabilités implicites et scores normalisés sont bornés dans [0, 1]
        assert np.all(
            (X[i][mask] >= 0) & (X[i][mask] <= 1)
        ), f"Course {i}: X hors [0,1]"
        assert np.all(
            (Y[i][mask] >= 0) & (Y[i][mask] <= 1)
        ), f"Course {i}: Y hors [0,1]"

        # 4️⃣ Vérification de la normalisation de X
        # Les probabilités implicites doivent sommer à 1
        s = X[i][mask].sum()
        assert abs(s - 1.0) < tol, f"Course {i}: somme X = {s:.6f} ≠ 1"

        # 5️⃣ Vérification des extrêmes de Y
        # Par construction :
        #   - le meilleur cheval a un score de 1
        #   - le dernier cheval a un score de 0
        y_valid = Y[i][mask]
        assert abs(y_valid.max() - 1.0) < tol, f"Course {i}: max(Y) ≠ 1"
        assert abs(y_valid.min() - 0.0) < tol, f"Course {i}: min(Y) ≠ 0"

        # 6️⃣ Vérification de la cohérence de l'ordre
        # Le tri des scores Y doit induire un ordre strict et cohérent
        order_Y = np.argsort(-y_valid)

        # Cette ligne est redondante par construction mais sert de garde-fou
        order_pos = np.argsort(-Y[i][mask])

        assert np.all(order_Y == order_pos), f"Course {i}: ordre incohérent"

        if verbose:
            print(f"✓ Course {i} OK ({n} chevaux)")

    if verbose:
        print("\n✅ Dataset cohérent et prêt pour l'apprentissage")


def normalized_rank(L, mask):
    """
    Transforme un rang d'arrivée en score ordinal normalisé compris entre 0 et 1.

    IMPORTANT :
    ----------------
    Les valeurs retournées NE SONT PAS des probabilités.
    Il s'agit d'une transformation déterministe du rang visant à :
        - préserver l'ordre relatif entre les chevaux
        - fournir une cible numérique continue adaptée à une régression (MSE)

    Principe de la normalisation
    ----------------------------
    Pour une course contenant n chevaux valides :
        - Rang 1 (vainqueur)        → score = 1
        - Rang n (dernier)          → score = 0
        - Rangs intermédiaires      → scores linéairement interpolés

    Formule utilisée :
        score = (n - rang) / (n - 1)

    Cette transformation :
        - conserve strictement l'ordre des classements
        - est invariante au nombre de chevaux par course
        - ne représente ni une probabilité, ni une fréquence
        - ne vérifie pas ∑ score = 1

    Paramètres
    ----------
    L : np.ndarray, shape = (n_courses, n_max_chevaux)
        Matrice des rangs d'arrivée bruts.
        - L[i, j] est le rang du cheval j dans la course i
        - Les chevaux absents ou padding ont une valeur arbitraire (ex : 0)

    mask : np.ndarray, shape = (n_courses, n_max_chevaux)
        Masque binaire indiquant les chevaux réellement présents.
        - 1 → cheval présent
        - 0 → padding / cheval absent

    Retour
    ------
    Y : np.ndarray, shape = (n_courses, n_max_chevaux)
        Matrice des scores de rang normalisés.
        - Valeurs dans [0, 1]
        - 1 correspond au meilleur cheval de la course
        - 0 correspond au dernier cheval de la course
        - Les positions masquées valent 0

    """
    Y = np.zeros_like(L, dtype=float)

    for i in range(L.shape[0]):
        # Sélection des chevaux réellement présents dans la course
        valid = mask[i] == 1
        n = valid.sum()

        # Normalisation linéaire du rang
        # Rang 1 -> 1.0
        # Rang n -> 0.0
        Y[i, valid] = (n - L[i, valid]) / (n - 1)

    return Y


def implicit_probabilities(M, mask, eps=1e-12):
    """
    Convertit les cotes en probabilités implicites normalisées, course par course.

    La probabilité implicite associée à une cote c est définie par :
        p_i = (1 / c_i) / Σ_j (1 / c_j)

    Cette mesure correspond à l'inverse de la cote, puis à une normalisation
    afin que la somme des probabilités des chevaux d'une même course soit égale à 1.
    Elle ignore explicitement la marge du bookmaker (overround).

    Paramètres
    ----------
    M : np.ndarray, shape (N_courses, N_max_chevaux)
        Matrice des cotes.
        - M[i, j] = cote du cheval j dans la course i
        - Les entrées correspondant à des chevaux inexistants peuvent être quelconques
          (généralement 0), mais seront ignorées via le masque.

    mask : np.ndarray, shape (N_courses, N_max_chevaux)
        Masque binaire indiquant les chevaux valides.
        - mask[i, j] = 1 si le cheval j participe à la course i
        - mask[i, j] = 0 sinon

    eps : float, optionnel (par défaut 1e-12)
        Terme de régularisation ajouté au dénominateur pour éviter toute division
        par zéro lorsque la cote est très faible ou nulle.

    Retour
    ------
    P : np.ndarray, shape (N_courses, N_max_chevaux)
        Matrice des probabilités implicites normalisées.
        - P[i, j] ∈ [0, 1]
        - Σ_j P[i, j] = 1 pour chaque course i (sur les chevaux valides)
        - P[i, j] = 0 pour les chevaux masqués

    Notes
    -----
    - Cette transformation suppose que les cotes sont décimales.
    - La normalisation supprime implicitement l'overround du bookmaker.
    - La sortie est directement exploitable comme distribution de probabilité
      conditionnelle par course.
    """
    P = np.zeros_like(M, dtype=float)

    for i in range(M.shape[0]):
        valid = mask[i] == 1
        inv = 1.0 / (M[i, valid] + eps)
        P[i, valid] = inv / inv.sum()

    return P


def check_natural_sequence(lst):
    """
    Vérifie si une liste représente une permutation exacte de la suite naturelle
    {1, 2, ..., N}, sans doublon ni valeur manquante.

    Cette fonction est typiquement utilisée pour valider un classement d'arrivée
    dans une course (positions finales), où chaque cheval doit occuper une place
    unique comprise entre 1 et N.

    Paramètres
    ----------
    lst : list[int] ou list[float]
        Liste des positions d'arrivée.
        - La liste doit contenir exactement N éléments
        - Les valeurs doivent représenter les entiers 1, 2, ..., N
        - Les floats sont acceptés s'ils représentent des entiers exacts

    Retour
    ------
    bool
        True si :
            - aucune position n'est dupliquée
            - aucune position n'est manquante
            - l'ensemble des valeurs est exactement {1, 2, ..., N}
        False sinon.

    Notes
    -----
    - L'ordre de la liste n'a pas d'importance (ex : [2, 1, 3] est valide).
    - Toute valeur hors de l'intervalle [1, N] invalide la séquence.
    - Cette vérification est essentielle avant toute normalisation ou
      apprentissage supervisé basé sur le rang.
    """
    # Conversion en ensemble pour supprimer les doublons
    s = set(lst)

    # Vérifie simultanément :
    # 1) absence de doublons        -> len(s) == len(lst)
    # 2) aucune valeur manquante    -> s == {1, 2, ..., N}
    return len(s) == len(lst) and s == set(range(1, len(lst) + 1))


def save_dataset_txt(M, L, m, M_filename, L_filename, m_filename):
    """
    Enregistre les matrices M, L et m dans des fichiers .txt.

    Paramètres
    ----------
    M : np.array
        Matrice des features (probabilités ou cotes).
    L : np.array
        Matrice des labels normalisés.
    m : np.array
        Masque des chevaux présents.
    M_filename : str
        Nom du fichier pour M (ex: 'M.txt').
    L_filename : str
        Nom du fichier pour L (ex: 'L.txt').
    m_filename : str
        Nom du fichier pour m (ex: 'mask.txt').
    """
    np.savetxt(M_filename, M, fmt="%.6f", delimiter=",")
    np.savetxt(L_filename, L, fmt="%.6f", delimiter=",")
    np.savetxt(m_filename, m, fmt="%d", delimiter=",")
    print(
        f"✅ Dataset enregistré :\n- M -> {M_filename}\n- L -> {L_filename}\n- m -> {m_filename}"
    )


def Creation_de_la_matrice_feature(db_path, n_course, n_max_chevaux=15):
    """
    Construit les matrices d'entrée, de labels et de masque à partir
    d'une base de données de courses hippiques.

    Chaque course est représentée par :
    - un vecteur de cotes (features)
    - un vecteur de positions d'arrivée (labels)
    - un vecteur masque indiquant quels chevaux sont présents

    Les courses sont échantillonnées aléatoirement dans la base.

    Paramètres
    ----------
    db_path : str
        Chemin vers la base de données SQLite contenant la table Participants.

    n_course : int
        Nombre de courses à extraire aléatoirement.

    n_max_chevaux : int, optionnel (par défaut = 15)
        Nombre maximal de chevaux par course.
        Les courses ayant moins de chevaux sont complétées par padding (0).

    Hypothèses / Filtres
    -------------------
    - Seules les courses dont toutes les positions d'arrivée forment
      une permutation exacte de [1, 2, ..., N] sont conservées. Pour
      éviter les courses ou il maque des chevaux
    - Les courses avec N >= n_max_chevaux sont ignorées.
    - Les chevaux sont ordonnés selon NumParticipant.

    Retour
    ------
    Matrice_feat_np : np.ndarray, shape (N_valid_courses, n_max_chevaux)
        Matrice des features.
        - Matrice_feat_np[i, j] = cote du cheval j de la course i
        - 0 si le cheval n'existe pas (padding)

    Label_vect_np : np.ndarray, shape (N_valid_courses, n_max_chevaux)
        Matrice des labels.
        - Label_vect_np[i, j] = position d'arrivée réelle du cheval j
        - 0 si le cheval n'existe pas (padding)

    Matrix_Masque_np : np.ndarray, shape (N_valid_courses, n_max_chevaux)
        Matrice masque.
        - 1 si le cheval est présent dans la course
        - 0 si padding

    Remarque
    --------
    Les trois matrices sont alignées :
        - ligne i correspond à la même course dans les trois matrices.
    """

    # --------------------------------------------------------
    # Connexion à la base SQLite
    # --------------------------------------------------------
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Sélection aléatoire de courses valides
    # --------------------------------------------------------
    cursor.execute(
        """
        SELECT DISTINCT DateReunion, NumReunion, NumCourse
        FROM Participants
        WHERE PositionArrivee IS NOT NULL
          AND Cote IS NOT NULL
        ORDER BY RANDOM()
        LIMIT ?
        """,
        (n_course,),
    )

    courses = cursor.fetchall()

    # --------------------------------------------------------
    # Listes de stockage (avant conversion en numpy)
    # --------------------------------------------------------
    Matrice_feat = []  # features (cotes)
    Label_vect = []  # labels (positions)
    Matrix_Masque = []  # masque de présence

    # --------------------------------------------------------
    # Boucle sur chaque course sélectionnée
    # --------------------------------------------------------
    for idx in tqdm(range(len(courses)), desc="Traitement des courses"):
        DateReunion, NumReunion, NumCourse = courses[idx]

        # Récupération des chevaux de la course
        cursor.execute(
            """
            SELECT Cote, PositionArrivee
            FROM Participants
            WHERE DateReunion = ?
              AND NumReunion = ?
              AND NumCourse = ?
              AND PositionArrivee IS NOT NULL
              AND Cote IS NOT NULL
            ORDER BY NumParticipant
            """,
            (DateReunion, NumReunion, NumCourse),
        )

        Rows = cursor.fetchall()

        # Extraction des cotes et positions
        Cotes = [float(row[0]) for row in Rows]
        PositionArivee = [float(row[1]) for row in Rows]

        N = len(Cotes)

        # ----------------------------------------------------
        # Construction des vecteurs paddés
        # ----------------------------------------------------
        Ligne_feature = []
        Ligne_label = []
        Masque_participants = []

        # On ne garde que les courses propres et de taille acceptable
        if N < n_max_chevaux and check_natural_sequence(PositionArivee):

            for j in range(n_max_chevaux):
                if j < N:
                    # Cheval réel
                    Ligne_feature.append(Cotes[j])
                    Ligne_label.append(PositionArivee[j])
                    Masque_participants.append(1)
                else:
                    # Padding
                    Ligne_feature.append(0)
                    Ligne_label.append(0)
                    Masque_participants.append(0)

            # Ajout au dataset final
            Matrice_feat.append(Ligne_feature)
            Label_vect.append(Ligne_label)
            Matrix_Masque.append(Masque_participants)

    # --------------------------------------------------------
    # Conversion finale en numpy arrays
    # --------------------------------------------------------
    Matrice_feat_np = np.array(Matrice_feat, dtype=float)
    Label_vect_np = np.array(Label_vect, dtype=float)
    Matrix_Masque_np = np.array(Matrix_Masque, dtype=float)

    return Matrice_feat_np, Label_vect_np, Matrix_Masque_np


# ============================================================
# Lancement du script
# ============================================================
if __name__ == "__main__":
    # ========================================================
    # 1️ Préparation du dataset
    # ========================================================
    # M : matrice des features (ex : cotes brutes)
    # L : labels (classement réel / positions d’arrivée)
    # m : masque (1 = cheval présent, 0 = padding)
    M, L, m = Creation_de_la_matrice_feature("courses.db", 3000)

    # Sauvegarde des données d'études
    save_dataset_txt(
        M, L, m, M_filename="M.txt", L_filename="L.txt", m_filename="mask.txt"
    )

    # Transformation des cotes en probabilités implicites
    X = implicit_probabilities(M, m)

    # Normalisation du classement réel (scores entre 0 et 1)
    Y = normalized_rank(L, m)

    # Vérifications de cohérence du dataset
    sanity_check_dataset(X, Y, m)

    # ========================================================
    # 2️ Définition du nombre maximum de chevaux par course
    # ========================================================
    # Correspond à la largeur des entrées du réseau
    max_chevaux = X.shape[1]

    # ========================================================
    # 3️ Séparation train / test
    # ========================================================
    X_train, Y_train, m_train, X_test, Y_test, m_test = train_test_split_masked(X, Y, m)

    # ========================================================
    # 4️ Création du modèle
    # ========================================================
    model = build_model(max_chevaux)

    # Affiche un résumé de l’architecture
    model.summary()

    # ========================================================
    # 5️ Compilation du modèle
    # ========================================================
    # Adam : optimiseur adaptatif robuste
    # masked_mse : loss personnalisée qui ignore le padding
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss=masked_mse
    )

    # ========================================================
    # 6️ Entraînement
    # ========================================================
    history = model.fit(
        X_train,
        Y_train,
        batch_size=16,  # nombre de courses par batch
        epochs=50,  # nombre de passages sur le dataset
        verbose=1,
        validation_split=0.1,  # 10% du train utilisé pour la validation
    )

    # ========================================================
    # 7️ Visualisation de l’évolution de la loss
    # ========================================================
    plt.figure(figsize=(8, 5))
    plt.plot(history.history["loss"], label="Train Loss")
    plt.plot(history.history["val_loss"], label="Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Masked MSE")
    plt.title("Évolution de la perte pendant l'entraînement")
    plt.legend()
    plt.grid(True)
    plt.show()

    # ========================================================
    # 8️ Sauvegarde du modèle entraîné
    # ========================================================
    # Permet de recharger le modèle sans réentraîner
    model.save("mon_modele.h5")
    print("✅ Modèle sauvegardé dans mon_modele.h5")

    # ========================================================
    # 9️ Évaluation des performances sur le jeu de test
    # ========================================================
    # Prédictions du modèle
    Y_pred = model.predict(X_test)

    # Évaluation selon les métriques définies
    # Ici, evaluate_performance compare les rangs exacts et top3
    results_model = evaluate_performance(Y_test, Y_pred, m_test)

    # Comparaison avec l'estimateur naïf basé sur les cotes
    # evaluate_performance_with_odds utilise Y_test, Y_pred et X_test
    results_odds = evaluate_performance_with_odds(Y_test, Y_pred, m_test, X_test)

    # --------------------------------------------------------
    # Affichage des résultats du modèle
    # --------------------------------------------------------
    print("===== Performance du modèle =====")
    print(
        "Proportion de chevaux exactement classés :",
        results_odds["model"]["proportion_exact"],
    )
    print(
        "Proportion des 3 meilleurs correctement identifiés :",
        results_odds["model"]["proportion_top3"],
    )
    print(
        "Proportion des courses où le meilleur cheval prédit est dans le top 3 réel :",
        results_odds["model"]["best_in_top3"],
    )

    # --------------------------------------------------------
    # Affichage des résultats de l'estimateur naïf (cotes)
    # --------------------------------------------------------
    print("\n===== Performance de l'estimateur naïf (cotes) =====")
    print(
        "Proportion de chevaux exactement classés :",
        results_odds["naive_odds"]["proportion_exact"],
    )
    print(
        "Proportion des 3 meilleurs correctement identifiés :",
        results_odds["naive_odds"]["proportion_top3"],
    )
    print(
        "Proportion des courses où le meilleur cheval prédit est dans le top 3 réel :",
        results_odds["naive_odds"]["best_in_top3"],
    )
