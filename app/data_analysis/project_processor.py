import sys
from database import fetch_project, update_project_status
from preprocess import validate_input_file, normalize_data
from output import generate_heatmap
from utils import log_message, set_uid_hash, clear_files
from kohonen import KohonenSOM
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

# vytahneme data z databaze podle uid
def get_project_detail(uid_hash: str) -> dict:
    project = fetch_project(uid_hash)
    if not project:
        log_message(f"Projekt s UID {uid_hash} nenalezen nebo analýza již byla dokončena.")
        sys.exit(1)
    return project

# vezmeme jen nastavení z detailu projektu
def load_project_settings(project: dict) -> dict:
    try:
        import json
        settings = json.loads(project["som_settings"])
        return settings
    except (KeyError, ValueError) as e:
        log_message(f"Chyba při načítání nastavení projektu: {e}")
        sys.exit(1)

#  doplnit budou zvlašť data pro csv soubor a pro mapu
#def load_som_settings(project: dict) -> dict:


def train_and_analyze_som(preprocess_file: str, settings: dict, output_path: str, uid_hash: str) -> None:
    """Trénuje SOM a generuje výstupy."""
    # Načtení předzpracovaných dat
    data = pd.read_csv(preprocess_file, delimiter=';').values

    # Inicializace SOM je zde kontrola existence konkrétních nastavení tak aby nedošlo k chybějícímu atributu
    som = KohonenSOM(
        m=settings["som_height"],
        n=settings["som_width"],
        dim=data.shape[1],
        radius=settings.get("initial_sigma", max(settings["som_height"], settings["som_width"]) / 2),
        learning_rate=settings.get("learning_rate", 0.9),
        min_learning_rate=settings.get("min_learning_rate", 0.1),
        num_batches=settings.get("num_batches", 10),
        min_batch_percent=settings.get("min_batch_percent", 0.1),
        max_batch_percent=settings.get("max_batch_percent", 10),
        lr_decay_type=settings.get("lr_decay_type", "exp-drop"),
        radius_decay_type=settings.get("radius_decay_type", "exp-drop"),
        batch_growth_type=settings.get("batch_growth_type", "exp-growth"),
        random_seed=settings.get("random_seed", 42),
        growth_g=settings.get("growth_g", 15.0)
    ) 


    # Trénování SOM
    som.train(data)

    # Uložení vstupních dat
    np.savetxt(f"/userfiles/{uid_hash}/data.csv", data, delimiter=",")

    # Uložení naučených vah
    np.save(f"/userfiles/{uid_hash}/weights.npy", som.weights)

    # Analýza clusterů
    clusters = {}
    for i, sample in enumerate(data):
        bmu = som.find_bmu(sample)
        cluster_key = f"{bmu[0]}_{bmu[1]}"
        if cluster_key not in clusters:
            clusters[cluster_key] = []
        clusters[cluster_key].append(i)  # Ukládáme indexy původních řádků
    
    # Uložení clusterů do JSON
    # with open(f"/userfiles/{uid_hash}/clusters.json", "w", encoding="utf-8") as f:
    #     json.dump(clusters, f, indent=4)

    # Generování heatmapy
    generate_heatmap(som, data, output_path)



# hlavní metoda co řídí všechno
def process_project(uid_hash: str) -> None:
    # Nastavení uid_hash pro logování
    set_uid_hash(uid_hash)
    
    log_message(f"Spouštím zpracování projektu s UID {uid_hash}...")

    # Načtení detailů projektu
    project = get_project_detail(uid_hash)
    settings = load_project_settings(project)

    # Kontrola vstupního souboru
    input_file = f"/userfiles/{uid_hash}/input.csv"
    if not validate_input_file(input_file, settings):
        log_message(f"Neplatný vstupní soubor pro projekt {uid_hash}.")
        sys.exit(1)

    # Předzpracování dat
    preprocess_file = f"/userfiles/{uid_hash}/preprocess.csv"
    normalize_data(input_file, preprocess_file, settings)

    output_path = f"/userfiles/{uid_hash}/"
    kohonen_settings = {
        "som_height": 30,
        "som_width": 30,
        "learning_rate": 0.5,
        "lr_decay": 0.995
    }

    train_and_analyze_som(preprocess_file, kohonen_settings, output_path, uid_hash)

    # Aktualizace stavu projektu v databázi
    # update_project_status(uid_hash) odkomentovat, v prubehu testovani by se nepoustela analyza znovu
    log_message(f"Zpracování projektu {uid_hash} bylo dokončeno.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Použití: python3 project_processor.py <uid_hash>")
        sys.exit(1)    


    uid_hash = sys.argv[1]
    clear_files(uid_hash)
    process_project(uid_hash)
