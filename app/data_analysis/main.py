import time
import sys
from database import get_next_project
from project_processor import process_project
import logging
import subprocess

# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def process_next_project():
    """
    Zpracuje nejstarší připravený projekt.
    """
    project = get_next_project()
    if not project:
        logging.info("Žádný projekt není připraven ke zpracování")
        return

    uid_hash = project['uid_hash']
    
    try:
        logging.info(f"Spouštím zpracování projektu {uid_hash}")
        
        # Spuštění procesu
        process = subprocess.Popen(
            ['python3', 'project_processor.py', uid_hash],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Nespouštíme process.communicate(), aby se proces spustil na pozadí
        logging.info(f"Projekt {uid_hash} byl spuštěn na pozadí")
            
    except Exception as e:
        logging.error(f"Neočekávaná chyba při spouštění projektu {uid_hash}: {str(e)}")

def main():
    """
    Hlavní smyčka programu, která každou minutu kontroluje a spouští projekty.
    """
    logging.info("Spouštím službu pro zpracování projektů...")
    
    while True:
        try:
            process_next_project()
        except Exception as e:
            logging.error(f"Neočekávaná chyba v hlavní smyčce: {str(e)}")
        
        # Počkáme 60 sekund před další kontrolou
        time.sleep(10)

if __name__ == "__main__":
    main()
