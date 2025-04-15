import mysql.connector
from config.settings import DB_CONFIG

def get_db_connection():
    """Vytvoří a vrátí připojení k databázi."""
    return mysql.connector.connect(**DB_CONFIG)

def fetch_project(uid_hash):
    """Načte informace o projektu z databáze podle uid_hash."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        query = "SELECT * FROM projects WHERE uid_hash = %s AND analysis_done = 0"
        cursor.execute(query, (uid_hash,))
        result = cursor.fetchone()
    finally:
        cursor.close()
        db.close()

    return result

def update_project_status(uid_hash):
    db = get_db_connection()
    cursor = db.cursor()

    try:
        query = "UPDATE projects SET analysis_done = 1 WHERE uid_hash = %s"
        cursor.execute(query, (uid_hash,))
        db.commit()
    finally:
        cursor.close()
        db.close()