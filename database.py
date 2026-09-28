import mysql.connector
from config.settings import DB_CONFIG
import json

def get_db_connection():
    """
    Establishes and returns a connection to the database based on the DB_CONFIG settings.

    :return: A connection to the database
    :rtype: mysql.connector.connection.MySQLConnection
    """
    return mysql.connector.connect(**DB_CONFIG)

def fetch_project(uid_hash):
    """
    Retrieves project information from the database based on the provided uid_hash and analysis status.

    :param uid_hash: A unique identifier for the project
    :type uid_hash: str
    :return: Project information or None if the project was not found
    :rtype: dict or None
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Query to retrieve all project information where the uid_hash matches the provided value and the analysis is not yet done.
        query = "SELECT * FROM projects WHERE uid_hash = %s AND status = 0 AND ready_to_analyze = 1"
        cursor.execute(query, (uid_hash,))
        result = cursor.fetchone()
    finally:
        # Ensure all open resources are closed.
        cursor.close()
        db.close()
    return result

def update_project_status(uid_hash, status):
    """
    Aktualizuje stav projektu na základě zadaného uid_hash a statusu.

    :param uid_hash: Jedinečný identifikátor pro projekt
    :type uid_hash: str
    :param status: Nový stav projektu (1 - hotový, 2 - běžící)
    :type status: int
    :return: None
    """
    db = get_db_connection()
    cursor = db.cursor()

    try:
        # Query to update the project status based on the provided uid_hash and status.
        query = "UPDATE projects SET status = %s WHERE uid_hash = %s"
        cursor.execute(query, (status, uid_hash))
        db.commit()  # Uloží změny do databáze.
    finally:
        # Zajistí, že jsou všechny otevřené zdroje uzavřeny.
        cursor.close()
        db.close()

def update_project_settings(uid_hash, project_setting):
    db = get_db_connection()
    cursor = db.cursor()
    settings_string = json.dumps(project_setting)
    try:
        # Query to update the project som_setting based on the provided uid_hash and som_setting.
        query = "UPDATE projects SET project_settings = %s WHERE uid_hash = %s"
        cursor.execute(query, (settings_string, uid_hash))
        db.commit()  # Uloží změny do databáze.
    finally:
        # Zajistí, že jsou všechny otevřené zdroje uzavřeny.
        cursor.close()
        db.close()

def update_project_results(uid_hash, results):
    """
    Uloží výsledky (metriky) trénování do sloupce results v tabulce projects.

    :param uid_hash: Jedinečný identifikátor pro projekt
    :type uid_hash: str
    :param results: Slovník s výsledky/metrikami (uloží se jako JSON)
    :type results: dict
    :return: None
    """
    db = get_db_connection()
    cursor = db.cursor()
    results_string = json.dumps(results)
    try:
        query = "UPDATE projects SET results = %s WHERE uid_hash = %s"
        cursor.execute(query, (results_string, uid_hash))
        db.commit()
    finally:
        cursor.close()
        db.close()

def get_next_project():
    """
    Získá nejstarší projekt, který je připraven k analýze.
    
    :return: Informace o projektu nebo None, pokud není žádný projekt připraven
    :rtype: dict or None
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Získá nejstarší projekt, který je připraven k analýze (status = 0 a ready_to_analyze = 1)
        # změnit na order podle data spuštění na analýzu
        query = """
            SELECT * FROM projects 
            WHERE status = 0 AND ready_to_analyze = 1 
            ORDER BY project_id ASC  
            LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
    finally:
        cursor.close()
        db.close()
    return result