import sys
from database import fetch_project, update_project_status
from preprocess import validate_input_file, normalize_data
from som import initialize_som, train_som, analyze_clusters
from output import save_clusters, generate_log, generate_map, generate_html
from utils import log_message
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

def generate_heatmap(som, data, output_path: str) -> None:
    """Generuje heatmapu SOM a ukládá ji jako map.jpg."""
    plt.figure(figsize=(10, 10))
    for sample in data:
        bmu = som.find_bmu(sample)
        plt.scatter(bmu[0] + np.random.rand() * 0.8, bmu[1] + np.random.rand() * 0.8, c="blue", alpha=0.5)

    plt.title("SOM Heatmap")
    plt.savefig(f"{output_path}map.jpg")
    plt.close()

def train_and_analyze_som(preprocess_file: str, settings: dict, output_path: str) -> None:
    """Trénuje SOM a generuje výstupy."""
    # Načtení předzpracovaných dat
    data = pd.read_csv(preprocess_file, delimiter=';').values

    # Inicializace SOM
    som = KohonenSOM(
        m=settings["som_height"],
        n=settings["som_width"],
        dim=data.shape[1],
        learning_rate=settings.get("learning_rate", 0.1),
        radius=settings.get("initial_sigma", max(settings["som_height"], settings["som_width"]) / 2),
        radius_decay=settings.get("radius_decay", 0.99),
        lr_decay=settings.get("lr_decay", 0.99),
        min_learning_rate=settings.get("min_learning_rate", 0.01)
    )

    # Trénování SOM
    som.train(data)

    # Analýza clusterů
    clusters = {}
    for i, sample in enumerate(data):
        bmu = som.find_bmu(sample)
        cluster_key = f"{bmu[0]}_{bmu[1]}"
        if cluster_key not in clusters:
            clusters[cluster_key] = []
        clusters[cluster_key].append(i)  # Ukládáme indexy původních řádků

    # Uložení clusterů do JSON
    with open(f"{output_path}clusters.json", "w", encoding="utf-8") as f:
        json.dump(clusters, f, indent=4)

    # Generování heatmapy
    generate_heatmap(som, data, output_path)



# hlavní metoda co řídí všechno
def process_project(uid_hash: str) -> None:
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
        "som_height": 20,
        "som_width": 20
    }
    train_and_analyze_som(preprocess_file, kohonen_settings, output_path)

    sys.exit("KOnec")



    # # Inicializace a trénování SOM
    # som = initialize_som(settings)
    # train_som(som, preprocess_file, settings)
    #
    # # Analýza clusterů
    # clusters = analyze_clusters(som, preprocess_file)
    #
    # # Uložení výstupů
    # output_path = f"/userfiles/{uid_hash}/"
    # save_clusters(f"{output_path}clusters.txt", clusters)
    # generate_log(f"{output_path}log.txt", f"Zpracování projektu {uid_hash} bylo úspěšné.")
    # generate_map(f"{output_path}map.jpg", som)
    # generate_html(f"{output_path}output.html", clusters, "Log: Zpracování projektu bylo úspěšné.")

    # Aktualizace stavu projektu v databázi
    update_project_status(uid_hash, analysis_done=True)
    log_message(f"Zpracování projektu {uid_hash} bylo dokončeno.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Použití: python3 project_processor.py <uid_hash>")
        sys.exit(1)
    log_message(f"====Začínáme=====")

    uid_hash = sys.argv[1]
    process_project(uid_hash)
