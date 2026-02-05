"""
graph_updates.py - Fonctions de mise à jour des graphiques
"""

import sqlite3

from .cache import meilleurs_chevaux, participants_cache
from .db.connection import get_connection
from .participant_data import get_cheveaux_data, get_participants_data
from .query_builder import build_where_clause_stats


def update_graphe_individuel(
    graph_type, filtre_widget, graphe, participant_id, cache_dict
):
    """
    Met à jour un graphique individuel (performance ou cotes d'un participant).

    Args:
        graph_type: Type de graphique ("Performance au cours des courses" ou "Cotes au cours des courses")
        filtre_widget: Widget contenant les filtres
        graphe: Objet graphique à mettre à jour
        participant_id: ID du participant
        cache_dict: Dictionnaire de cache contenant les participants
    """
    participant = cache_dict.get(participant_id)
    if not participant:
        return

    participant_name = participant.get("name")
    if not participant_name:
        return

    state = filtre_widget.get_state()
    nbr = state.get("nbr", 20)
    filtres = state.get("filtres", [])

    where_sql, params = build_where_clause_stats(filtres)

    def add_condition(base_where, condition):
        if base_where:
            return base_where + " AND " + condition
        return "WHERE " + condition

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # ================= PERFORMANCE =================
        if graph_type == "Performance au cours des courses":
            print(filtres)
            where_full = add_condition(where_sql, "p.Nom = ?")
            where_full = add_condition(where_full, "p.PositionArrivee GLOB '[0-9]*'")

            query = f"""
                SELECT p.DateReunion,
                       CAST(p.PositionArrivee AS INTEGER) AS position
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_full}
                ORDER BY
                    SUBSTR(p.DateReunion,5,4)||'-'||SUBSTR(p.DateReunion,3,2)||'-'||SUBSTR(p.DateReunion,1,2)
                LIMIT ?
            """
            cur.execute(query, (*params, participant_name, nbr))

            rows = cur.fetchall()
            if not rows:
                return

            x_data = [
                f"{d[:2]}/{d[2:4]}/{d[4:]}" for d in (r["DateReunion"] for r in rows)
            ]
            y_data = [r["position"] for r in rows]

            graphe.clear()
            graphe.plot(
                x_data,
                y_data,
                title="Performance sur les courses",
                xlabel="Date",
                ylabel="Position",
                marker="o",
            )

        # ================= COTES =================
        elif graph_type == "Cotes au cours des courses":
            where_full = add_condition(where_sql, "p.Nom = ?")
            where_full = add_condition(where_full, "p.Cote IS NOT NULL")

            query = f"""
                SELECT p.DateReunion, p.Cote
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_full}
                ORDER BY
                    SUBSTR(p.DateReunion,5,4)||'-'||SUBSTR(p.DateReunion,3,2)||'-'||SUBSTR(p.DateReunion,1,2)
                LIMIT ?
            """
            cur.execute(query, (*params, participant_name, nbr))

            rows = cur.fetchall()
            if not rows:
                return

            x_data = [
                f"{d[:2]}/{d[2:4]}/{d[4:]}" for d in (r["DateReunion"] for r in rows)
            ]
            y_data = [float(r["Cote"]) for r in rows]

            graphe.clear()
            graphe.plot(
                x_data,
                y_data,
                title="Évolution des cotes",
                xlabel="Date",
                ylabel="Cote",
                marker="o",
            )

    graphe.ax.tick_params(axis="x", labelrotation=90)
    graphe.figure.tight_layout()


def update_graphe_stats_groupe(tri_nom, filtre_widget, graphe):
    """
    Met à jour un graphique de statistiques groupées.

    Args:
        tri_nom: Nom du type de statistique à afficher
        filtre_widget: Widget contenant les filtres
        graphe: Objet graphique à mettre à jour
    """
    state = filtre_widget.get_state()
    filtres = state.get("filtres", [])
    nbr = state.get("nbr")
    where_sql, params = build_where_clause_stats(filtres)

    def add_condition(base_where, condition):
        if base_where:
            return base_where + " AND " + condition
        return "WHERE " + condition

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # -------------------------------------------------------------
        # VICTOIRES PAR RACE
        # -------------------------------------------------------------
        if tri_nom == "Victoires par race":
            where_full = add_condition(where_sql, "p.PositionArrivee='1'")
            query = f"""
                SELECT c.Race AS categorie, COUNT(*) AS victoires
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_full}
                GROUP BY c.Race
                ORDER BY victoires DESC
                LIMIT ?
            """
            cur.execute(query, (*params, nbr))
            rows = cur.fetchall()
            ylabel = "Nombre de victoires"
            title = "Nombre de victoires par race"
            marker, linestyle = "s", ""
            x_data = [r["categorie"] for r in rows]
            y_data = [r["victoires"] for r in rows]

        # -------------------------------------------------------------
        # TAUX DE VICTOIRE PAR RACE
        # -------------------------------------------------------------
        elif tri_nom == "Taux de victoire par race":
            query = f"""
                SELECT c.Race AS categorie,
                       COUNT(*) AS courses,
                       SUM(CASE WHEN p.PositionArrivee='1' THEN 1 ELSE 0 END) AS victoires
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_sql}
                GROUP BY c.Race
                HAVING courses > 30
                ORDER BY (victoires*100.0/courses) DESC
                LIMIT ?
            """
            cur.execute(query, (*params, nbr))
            rows = cur.fetchall()
            ylabel = "% de victoires"
            title = "Taux de victoire par race"
            marker, linestyle = "s", ""
            x_data = [r["categorie"] for r in rows]
            y_data = [(r["victoires"] * 100.0 / r["courses"]) for r in rows]

        # -------------------------------------------------------------
        # TAUX DE VICTOIRE PAR ÂGE
        # -------------------------------------------------------------
        elif tri_nom == "Taux de victoire par âge":
            query = f"""
                SELECT p.Age AS categorie,
                       COUNT(*) AS courses,
                       SUM(CASE WHEN p.PositionArrivee='1' THEN 1 ELSE 0 END) AS victoires
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_sql}
                GROUP BY p.Age
                HAVING courses > 30
                ORDER BY p.Age
            """
            cur.execute(query, params)
            rows = cur.fetchall()
            ylabel = "% de victoires"
            title = "Taux de victoire par âge"
            marker, linestyle = "o", "-"
            x_data = [r["categorie"] for r in rows]
            y_data = [(r["victoires"] * 100.0 / r["courses"]) for r in rows]

        # -------------------------------------------------------------
        # COURSES PAR TYPE
        # -------------------------------------------------------------
        elif tri_nom == "Courses par type de course":
            query = f"""
                SELECT co.Discipline AS categorie, COUNT(*) AS nb
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_sql}
                GROUP BY co.Discipline
                ORDER BY nb DESC
            """
            cur.execute(query, params)
            rows = cur.fetchall()
            ylabel = "Nombre de courses"
            title = "Répartition des courses par type"
            marker, linestyle = "s", ""
            x_data = [r["categorie"] for r in rows]
            y_data = [r["nb"] for r in rows]

        # -------------------------------------------------------------
        # COURSES PAR SURFACE
        # -------------------------------------------------------------
        elif tri_nom == "Courses par surface":
            query = f"""
                SELECT co.TypePiste AS categorie, COUNT(*) AS nb
                FROM Participants p
                JOIN Cheval c ON c.Nom = p.Nom
                JOIN Courses co ON co.DateReunion = p.DateReunion
                               AND co.NumReunion = p.NumReunion
                               AND co.NumCourse = p.NumCourse
                {where_sql}
                GROUP BY co.TypePiste
                ORDER BY nb DESC
            """
            cur.execute(query, params)
            rows = cur.fetchall()
            ylabel = "Nombre de courses"
            title = "Répartition des courses par surface"
            marker, linestyle = "s", ""
            x_data = [r["categorie"] for r in rows]
            y_data = [r["nb"] for r in rows]

        else:
            return

    # -------------------------------------------------------------
    # Affichage graphique
    # -------------------------------------------------------------
    if not x_data:
        graphe.clear()
        graphe.ax.text(
            0.5,
            0.5,
            "Aucune donnée",
            ha="center",
            va="center",
            transform=graphe.ax.transAxes,
        )
        graphe.figure.tight_layout()
        return

    graphe.clear()
    graphe.plot(
        x_data,
        y_data,
        title=title,
        xlabel="Catégorie",
        ylabel=ylabel,
        marker=marker,
        linestyle=linestyle,
    )
    graphe.ax.tick_params(axis="x", rotation=90)
    graphe.figure.tight_layout()


def update_graphe_data(
    graph_type: str,
    filtre_widget,
    graphe,
    participant_id: int | None = None,
    get_data=None,
):
    """
    Fonction principale de mise à jour des graphiques (dispatcher).

    Args:
        graph_type: Type de graphique à afficher
        filtre_widget: Widget contenant les filtres
        graphe: Objet graphique à mettre à jour
        participant_id: ID du participant (pour graphiques individuels)
        get_data: Fonction de récupération de données (None pour stats groupées)
    """
    # MODE STATS GROUPE
    if get_data is None:
        update_graphe_stats_groupe(graph_type, filtre_widget, graphe)
        return

    # MODES INDIVIDUELS
    if participant_id is None:
        return

    if get_data is get_participants_data:
        update_graphe_individuel(
            graph_type,
            filtre_widget,
            graphe,
            participant_id,
            participants_cache.participants,
        )

    elif get_data is get_cheveaux_data:
        update_graphe_individuel(
            graph_type,
            filtre_widget,
            graphe,
            participant_id,
            meilleurs_chevaux.participants,
        )

    else:
        print("Source de données inconnue")
