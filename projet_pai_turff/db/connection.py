import sqlite3
import os

# chemin ABSOLU vers le dossier du projet (1 niveau au-dessus de db/)
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

DB_PATH = os.path.join(PROJECT_ROOT, "db", "courses.db")
if not os.path.isfile(DB_PATH):
    raise RuntimeError(f"DB introuvable : {DB_PATH}")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn