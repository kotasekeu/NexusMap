import mysql.connector
from config.settings import DB_CONFIG

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
        query = "SELECT * FROM projects WHERE uid_hash = %s AND status = 0"
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