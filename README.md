## projet_PAI_TURFF


Application d’analyse et de prédiction de courses hippiques développée dans le cadre du projet PAI.

Le logiciel exploite une base de données de courses afin d’étudier les performances des chevaux, les caractéristiques des épreuves et de produire des statistiques globales ainsi que des prédictions de résultats.
L’objectif est de fournir un outil d’exploration et d’aide à l’analyse dans le domaine du turfisme, en combinant données historiques, filtres dynamiques et visualisations graphiques.

Le projet repose sur une architecture modulaire séparant l’accès aux données, la construction des requêtes SQL, la logique métier, les visualisations et l’interface graphique.

L’application s’appuie sur une base SQLite contenant les principales entités du domaine hippique : les chevaux (identité, race, robe, parents, sexe), les courses (date, distance, discipline, surface) et les participants (engagements, résultats, cotes, informations associées).
Les requêtes SQL sont construites dynamiquement via un système de filtres paramétrables, permettant de produire des analyses conditionnelles (âge, race, type de course, surface, distance, etc.).
Un système de cache est utilisé afin de limiter les accès répétés à la base de données et d’améliorer les performances.

L’interface graphique est organisée en quatre onglets principaux : un onglet dédié aux courses, un onglet centré sur les chevaux et leurs performances individuelles, un onglet de statistiques globales permettant d’explorer les tendances agrégées, et un onglet de prédictions produisant un ordre d’arrivée estimé pour une course donnée à partir des données historiques.

This project was started with [supopo-pai-cookiecutter-template](https://github.com/ClementPinard/supop-pai-cookiecuttter-template/tree/main)

## How to run

⚠️ Chose one of the two method below, and remove the other one.

### How to run with NiceGUI

```bash
uv run main_ng
```

You can also run in development mode, which will reload the interface when it see code
changes.

```bash
uv run python projet_pai_turff/main_nicegui.py
```

### How to run with PySide

```bash
uv run main_qt
```

## Development

### How to run pre-commit

```bash
uvx pre-commit run -a
```

Alternatively, you can install it so that it runs before every commit :

```bash
uvx pre-commit install
```

### How to run tests

```bash
uv sync --group test
uv run pytest
```

### How to run type checking

```bash
uvx pyright projet_pai_turff --pythonpath .venv/bin/python
```

### How to build docs

```bash
uv sync --group docs
cd docs && uv run make html
```

#### How to run autobuild for docs

```bash
uv sync --group docs
cd docs && make livehtml
