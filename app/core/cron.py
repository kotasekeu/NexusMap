# from database import get_db_connection
# import subprocess
#
#
# def fetch_one_pending_project():
#     """Načte jeden neanalyzovaný projekt z databáze."""
#     db = get_db_connection()
#     cursor = db.cursor(dictionary=True)
#
#     try:
#         query = "SELECT uid_hash FROM projects WHERE analysis_done = 0 ORDER BY added ASC LIMIT 1"
#         cursor.execute(query)
#         result = cursor.fetchone()
#     finally:
#         cursor.close()
#         db.close()
#
#     return result
#
#
# def run_analysis(uid_hash):
#     """Spustí analýzu pro konkrétní projekt."""
#     subprocess.run(["python3", "/app/core/analysis.py", uid_hash])
#
#
# if __name__ == "__main__":
#     project = fetch_one_pending_project()
#     if project:
#         print(f"Spouštím analýzu pro projekt {project['uid_hash']}")
#         run_analysis(project['uid_hash'])
#     else:
#         print("Žádné projekty k analýze.")

# spustím analysis