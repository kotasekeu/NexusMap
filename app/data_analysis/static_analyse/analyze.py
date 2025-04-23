import sys
import json
import os
import argparse
from project_processor import process_project

def validate_files(input_file: str, project_config_file: str, som_config_file: str = None, output_dir: str = None) -> tuple[dict, dict, str]:
    """
    Validuje vstupní soubory a načítá konfigurace.
    
    Args:
        input_file: Cesta k vstupnímu CSV souboru
        project_config_file: Cesta k konfiguračnímu souboru projektu
        som_config_file: Cesta k konfiguračnímu souboru SOM (volitelné)
        output_dir: Cesta k cílovému adresáři (volitelné)
        
    Returns:
        Tuple obsahující (project_config, som_config, output_dir)
        
    Raises:
        FileNotFoundError: Pokud některý ze souborů neexistuje
        json.JSONDecodeError: Pokud některý z konfiguračních souborů není platný JSON
    """
    # Kontrola existence souborů
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Vstupní soubor {input_file} neexistuje.")
    
    if not os.path.exists(project_config_file):
        raise FileNotFoundError(f"Konfigurační soubor {project_config_file} neexistuje.")
    
    # Načtení konfiguračních souborů
    with open(project_config_file, 'r', encoding='utf-8') as f:
        project_config = json.load(f)

    # Načtení SOM konfigurace, pokud je zadána
    som_config = None
    if som_config_file:
        if not os.path.exists(som_config_file):
            raise FileNotFoundError(f"Konfigurační soubor {som_config_file} neexistuje.")
        with open(som_config_file, 'r', encoding='utf-8') as f:
            som_config = json.load(f)

    # Určení cílového adresáře
    if not output_dir:
        output_dir = os.path.dirname(os.path.abspath(input_file))
    else:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    return project_config, som_config, output_dir

def parse_args():
    """Parsuje argumenty příkazové řádky."""
    parser = argparse.ArgumentParser(
        description='Analýza dat pomocí SOM sítě',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Příklady použití:
    # Základní použití
    python3 analyze.py -i data/input.csv -pc config/project.json
    
    # S SOM konfigurací
    python3 analyze.py -i data/input.csv -pc config/project.json -sc config/som.json
    
    # S výstupním adresářem
    python3 analyze.py -i data/input.csv -pc config/project.json -d output/results
    
    # Se všemi parametry
    python3 analyze.py -i data/input.csv -pc config/project.json -sc config/som.json -d output/results
        """
    )
    
    parser.add_argument('-i', '--input', required=True,
                      help='Cesta k vstupnímu CSV souboru')
    parser.add_argument('-pc', '--project-config', required=True,
                      help='Cesta k konfiguračnímu souboru projektu')
    parser.add_argument('-sc', '--som-config',
                      help='Cesta k konfiguračnímu souboru SOM (volitelné)')
    parser.add_argument('-d', '--output-dir',
                      help='Cesta k cílovému adresáři (volitelné)')
    
    return parser.parse_args()

def main():
    try:
        args = parse_args()
        
        project_config, som_config, output_dir = validate_files(
            args.input, args.project_config, args.som_config, args.output_dir
        )
        # process_project(args.input, project_config, som_config, output_dir)
        print("Spustíme analýzu")
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Chyba: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 