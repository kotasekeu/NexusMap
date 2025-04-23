import sys
import json
import os
from project_processor import process_project

def main():
    if len(sys.argv) != 5:
        print("Použití: python3 analyze.py <uid_hash> <input.csv> <project_config.json> <som_config.json>")
        sys.exit(1)

    uid_hash = sys.argv[1]
    input_file = sys.argv[2]
    project_config_file = sys.argv[3]
    som_config_file = sys.argv[4]

    # Kontrola existence souborů
    if not os.path.exists(input_file):
        print(f"Chyba: Vstupní soubor {input_file} neexistuje.")
        sys.exit(1)
    
    if not os.path.exists(project_config_file):
        print(f"Chyba: Konfigurační soubor {project_config_file} neexistuje.")
        sys.exit(1)
    
    if not os.path.exists(som_config_file):
        print(f"Chyba: Konfigurační soubor {som_config_file} neexistuje.")
        sys.exit(1)

    # Načtení konfiguračních souborů
    try:
        with open(project_config_file, 'r', encoding='utf-8') as f:
            project_config = json.load(f)
    except json.JSONDecodeError:
        print(f"Chyba: Konfigurační soubor {project_config_file} není platný JSON.")
        sys.exit(1)

    try:
        with open(som_config_file, 'r', encoding='utf-8') as f:
            som_config = json.load(f)
    except json.JSONDecodeError:
        print(f"Chyba: Konfigurační soubor {som_config_file} není platný JSON.")
        sys.exit(1)

    # Spuštění analýzy
    process_project(uid_hash, input_file, project_config, som_config)

if __name__ == "__main__":
    main() 