"""
Hlavní modul pro zpracování projektů analýzy dat.

Tento modul zajišťuje:
- Načítání a validaci projektových dat z databáze
- Předzpracování vstupních dat
- Trénování Kohonenovy SOM sítě
- Analýzu a detekci extrémů v datech
- Generování výstupních souborů a vizualizací
- Správu stavu projektu v databázi
"""

import sys
from database import fetch_project, update_project_status, update_project_results
from preprocess import validate_input_file, normalize_data
from utils import log_message, set_uid_hash
from kohonen import KohonenSOM
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from matplotlib.lines import Line2D
from visualization import generate_maps
import os
from collections import defaultdict, Counter, OrderedDict
import time
import psutil

def get_project_detail(uid_hash: str) -> dict:
    """Načte detail projektu z databáze podle UID.
    
    Args:
        uid_hash (str): Unikátní identifikátor projektu
        
    Returns:
        dict: Slovník s detaily projektu
        
    Raises:
        SystemExit: Pokud projekt není nalezen nebo analýza již byla dokončena
    """
    project = fetch_project(uid_hash)
    if not project:
        log_message(f"Projekt s UID {uid_hash} nenalezen nebo analýza již byla dokončena.")
        sys.exit(1)
    return project

def load_project_settings(project: dict) -> dict:
    """Načte nastavení projektu z JSON řetězce.
    
    Args:
        project (dict): Slovník s detaily projektu
        
    Returns:
        dict: Nastavení projektu
        
    Raises:
        SystemExit: Pokud nastavení nelze načíst nebo je neplatné
    """
    try:
        settings = json.loads(project["project_settings"])
        return settings
    except (KeyError, ValueError) as e:
        log_message(f"Chyba při načítání nastavení projektu: {e}")
        sys.exit(1)

def load_som_settings(project: dict) -> dict:
    """Načte nastavení SOM sítě z JSON řetězce.
    
    Args:
        project (dict): Slovník s detaily projektu
        
    Returns:
        dict: Nastavení SOM sítě
        
    Raises:
        SystemExit: Pokud nastavení nelze načíst nebo je neplatné
    """
    try:
        settings = json.loads(project["som_settings"])
        return settings
    except (KeyError, ValueError) as e:
        log_message(f"Chyba při načítání nastavení SOM: {e}")
        sys.exit(1)

def train_and_analyze_som(preprocess_file: str, som_settings: dict, project_settings: dict, output_path: str, uid_hash: str) -> None:
    """Trénuje SOM síť a generuje výstupy analýzy.
    
    Args:
        preprocess_file (str): Cesta k předzpracovanému souboru
        som_settings (dict): Nastavení SOM sítě
        project_settings (dict): Nastavení projektu
        output_path (str): Cesta pro výstupní soubory
        uid_hash (str): Unikátní identifikátor projektu
        
    Note:
        Funkce provádí:
        1. Trénování SOM sítě
        2. Uložení vstupních dat a naučených vah
        3. Extrakci a uložení shluků
        4. Generování dat pro koláčové grafy
        5. Výpočet statistik a detekci extrémů
        6. Generování vizualizací
    """
    # Načtení předzpracovaných dat
    data = pd.read_csv(preprocess_file, delimiter=',').values

    # Inicializace a trénování SOM
    max_memory = psutil.virtual_memory().used // (1024 ** 2)  # v MB před trénováním
    start_time = time.time()
    som = KohonenSOM(dim=data.shape[1], **som_settings)
    som.train(data)
    duration = time.time() - start_time
    # Změříme paměť po trénování
    max_memory = max(max_memory, psutil.virtual_memory().used // (1024 ** 2))
    # Uložení metrik do databáze
    metrics = {
        "duration": duration,
        "total_weight_updates": som.total_weight_updates,
        "best_mqe": som.best_mqe,
        "epochs": getattr(som, 'epochs_run', None),
        "map_size": [som.m, som.n],
        "max_memory_mb": max_memory
    }
    update_project_results(uid_hash, metrics)

    # Uložení vstupních dat a vah
    np.savetxt(f"{output_path}csv/data.csv", data, delimiter=",")
    np.save(f"{output_path}weights.npy", som.weights)

    # Načtení původních dat
    df_orig = pd.read_csv(f"{output_path}csv/input.csv", delimiter=',')

    # Extrakce a uložení shluků
    cluster_file = f"{output_path}json/clusters.json"
    extract_and_save_clusters(som, data, df_orig, cluster_file, project_settings["primary_id"])

    # Generování dat pro koláčové grafy
    extract_and_save_pie_data(som, data, df_orig, project_settings["categorical_column"], output_path)

    # Načtení dat pro analýzu
    clusters = json.load(open(cluster_file))

    # Výpočet statistik a detekce extrémů
    stats = compute_group_statistics(df_orig,
                                   project_settings["segmentation_column"],
                                   project_settings["selected_columns"],
                                   project_settings)

    detect_extremes(df_orig,
                   output_path,
                   clusters,
                   stats,
                   threshold=project_settings.get("std_threshold", 2),
                   segmentation_column=project_settings["segmentation_column"],
                   selected_columns=project_settings["selected_columns"],
                   primary_id=project_settings["primary_id"],
                   project_settings=project_settings)

    # Generování koláčových grafů pro shluky
    extract_and_save_pie_data_from_clusters(
        df_orig,
        f"{output_path}json/clusters.json",
        project_settings['categorical_column'],
        f"{output_path}",
        project_settings['primary_id']
    )

    # Generování vizualizací
    generate_maps(som, data, preprocess_file, output_path, som_settings, project_settings)

def extract_and_save_clusters(som, data: np.ndarray, df_orig: pd.DataFrame, cluster_filename: str, primary_id: str) -> None:
    """Extrahuje a ukládá shluky dat do JSON souboru.
    
    Args:
        som: Trénovaná SOM síť
        data (np.ndarray): Předzpracovaná data
        df_orig (pd.DataFrame): Původní data
        cluster_filename (str): Cesta k výstupnímu JSON souboru
        primary_id (str): Název sloupce s primárním klíčem
        
    Note:
        Vytváří JSON ve formátu: {"i_j": [pid1, pid2, ...], ...}
        kde i_j jsou souřadnice neuronu a pid jsou primární ID vzorků
    """
    clusters = {}
    for idx, sample in enumerate(data):
        i, j = som.find_bmu(sample)
        key = f"{i}_{j}"
        
        pid_raw = df_orig.iloc[idx][primary_id]
        if isinstance(pid_raw, (np.integer, np.floating)):
            pid_raw = pid_raw.item()
        clusters.setdefault(key, []).append(pid_raw)
    
    os.makedirs(os.path.dirname(cluster_filename), exist_ok=True)
    with open(cluster_filename, 'w', encoding='utf-8') as f:
        json.dump(clusters, f, indent=4)

def process_project(uid_hash: str) -> None:
    """Hlavní funkce pro zpracování projektu.
    
    Args:
        uid_hash (str): Unikátní identifikátor projektu
        
    Note:
        Proces zpracování:
        1. Načtení a validace dat
        2. Předzpracování dat
        3. Trénování a analýza SOM
        4. Aktualizace stavu projektu
    """
    set_uid_hash(uid_hash)
    output_path = f"/userfiles/{uid_hash}/"
    
    log_message(f"Spouštím zpracování projektu s UID {uid_hash}...")

    # Načtení a validace dat
    project = get_project_detail(uid_hash)
    update_project_status(uid_hash, 2)  # Stav: běžící

    project_settings = load_project_settings(project)
    som_settings = load_som_settings(project)

    # Kontrola vstupního souboru
    input_file = f"{output_path}csv/input.csv"
    if not validate_input_file(input_file, project_settings):
        log_message(f"Neplatný vstupní soubor pro projekt {uid_hash}.")
        sys.exit(1)

    # Předzpracování a analýza
    preprocess_file = normalize_data(input_file, uid_hash, project_settings)
    train_and_analyze_som(preprocess_file, som_settings, project_settings, output_path, uid_hash)

    # Dokončení
    update_project_status(uid_hash, 1)  # Stav: dokončeno
    log_message(f"Zpracování projektu {uid_hash} bylo dokončeno.")

def compute_group_statistics(df_orig: pd.DataFrame,
                           segmentation_column: str,
                           selected_columns: list[str],
                           project_settings: dict) -> dict[str, dict[str, tuple[float, float]]]:
    """Vypočítá statistiky pro skupiny dat.
    
    Args:
        df_orig (pd.DataFrame): Původní data
        segmentation_column (str): Sloupec pro segmentaci
        selected_columns (list[str]): Seznam vybraných sloupců pro analýzu
        project_settings (dict): Nastavení projektu
        
    Returns:
        dict: Statistiky ve formátu {skupina: {sloupec: (průměr, směrodatná odchylka)}}
    """
    stats = {}
    
    # Výběr numerických sloupců
    if 'numerical_column' in project_settings:
        numeric_columns = [col for col in project_settings['numerical_column'] if col in df_orig.columns]
    else:
        numeric_columns = df_orig[selected_columns].select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        log_message("Varování: Žádné numerické sloupce pro analýzu.")
        return stats

    if segmentation_column not in df_orig.columns:
        log_message(f"Varování: Sloupec {segmentation_column} nenalezen v datech.")
        return stats

    # Výpočet statistik
    grouped = df_orig.groupby(segmentation_column)[numeric_columns]
    agg = grouped.agg(['mean', 'std'])

    for key, row in agg.iterrows():
        stats[key] = {col: (row[(col, 'mean')], row[(col, 'std')]) for col in numeric_columns}
    return stats

def detect_extremes(df_orig: pd.DataFrame,
                   output_path: str,
                   clusters: dict[str, list[int]],
                   stats_by_group: dict[str, dict[str, tuple[float, float]]],
                   threshold: float,
                   segmentation_column: str,
                   selected_columns: list[str],
                   primary_id: str,
                   project_settings: dict) -> dict:
    """Detekuje extrémní hodnoty v datech.
    
    Args:
        df_orig (pd.DataFrame): Původní data
        output_path (str): Cesta pro výstupní soubory
        clusters (dict): Slovník shluků
        stats_by_group (dict): Statistiky pro skupiny
        threshold (float): Prahová hodnota pro detekci extrémů
        segmentation_column (str): Sloupec pro segmentaci
        selected_columns (list[str]): Seznam vybraných sloupců pro analýzu
        primary_id (str): Název sloupce s primárním klíčem
        project_settings (dict): Nastavení projektu
        
    Returns:
        dict: Extrémní hodnoty ve formátu {'by_group': {...}, 'by_cluster': {...}}
    """
    extremes = {'by_group': {}, 'by_cluster': {}}

    # Výběr numerických sloupců
    if 'numerical_column' in project_settings:
        numeric_columns = [col for col in project_settings['numerical_column'] if col in df_orig.columns]
    else:
        numeric_columns = df_orig[selected_columns].select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        log_message("Varování: Žádné numerické sloupce pro detekci extrémů.")
        return extremes

    # Detekce extrémů podle skupin
    unique_groups = df_orig[segmentation_column].unique()
    for group_val in unique_groups:
        mask = (df_orig[segmentation_column] == group_val)
        df_group = df_orig[mask]
        # Přeskočíme, pokud je skupina prázdná nebo obsahuje pouze NaN hodnoty v numerických sloupcích
        if df_group.shape[0] == 0 or df_group[numeric_columns].isnull().all().all():
            continue
        for col in numeric_columns:
            if col in stats_by_group[group_val]:
                mean, std = stats_by_group[group_val][col]
                if std and not np.isnan(std):
                    vals = df_group[col]
                    outliers = df_group.loc[np.abs(vals - mean) > threshold * std, primary_id]
                    if not outliers.empty:
                        extremes['by_group'][group_val] = outliers.tolist()

    # Detekce extrémů podle shluků
    for cl_key, pid_list in clusters.items():
        if not pid_list:
            continue
        df_cluster = df_orig[df_orig[primary_id].isin(pid_list)]
        for col in numeric_columns:
            mean = df_cluster[col].mean()
            std = df_cluster[col].std()
            if std and not np.isnan(std):
                outliers = df_cluster.loc[np.abs(df_cluster[col] - mean) > threshold * std, primary_id]
                if not outliers.empty:
                    extremes['by_cluster'][cl_key] = outliers.tolist()

    # Uložení výsledků
    os.makedirs(f"{output_path}json", exist_ok=True)
    with open(f"{output_path}json/extremes.json", "w", encoding="utf-8") as f:
        json.dump(extremes, f, indent=4)

def extract_and_save_pie_data(som, data: np.ndarray, df_orig: pd.DataFrame, categorical_columns: list, output_dir: str) -> None:
    """Generuje data pro koláčové grafy podle neuronů SOM.
    
    Args:
        som: Trénovaná SOM síť
        data (np.ndarray): Předzpracovaná data
        df_orig (pd.DataFrame): Původní data
        categorical_columns (list): Seznam kategoriálních sloupců
        output_dir (str): Cesta pro výstupní soubory
        
    Note:
        Pro každý kategoriální sloupec vytváří JSON s počty kategorií pro každý neuron.
        Formát: {"categories": {1: "kategorie1", ...}, "counts": {"i_j": {1: počet, ...}}}
    """
    os.makedirs(output_dir, exist_ok=True)
    m, n = som.m, som.n

    for col in categorical_columns:
        categories = df_orig[col].dropna().unique().tolist()
        cat_map = {i+1: cat for i, cat in enumerate(categories)}

        pie_counts = defaultdict(Counter)

        numeric_counts = {}
        for idx, x in enumerate(data):
            i, j = som.find_bmu(x)
            key = f"{i}_{j}"
            label = df_orig.iloc[idx][col]
            pie_counts[key][label] += 1

        numeric_counts = {
            key: {i+1: cnts.get(cat, 0) for i, cat in enumerate(categories)}
            for key, cnts in pie_counts.items()
        }

        out = {
            "categories": cat_map,
            "counts": numeric_counts
        }
        fn = os.path.join(output_dir, f"pie_data_{col}.json")
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

def extract_and_save_pie_data_from_clusters(df_orig: pd.DataFrame,
                                          cluster_file: str,
                                          categorical_columns: list,
                                          output_dir: str,
                                          primary_id: str) -> None:
    """Generuje data pro koláčové grafy podle shluků.
    
    Args:
        df_orig (pd.DataFrame): Původní data
        cluster_file (str): Cesta k souboru se shluky
        categorical_columns (list): Seznam kategoriálních sloupců
        output_dir (str): Cesta pro výstupní soubory
        primary_id (str): Název sloupce s primárním klíčem
        
    Note:
        Pro každý kategoriální sloupec vytváří JSON s počty kategorií pro každý shluk.
        Formát: {"categories": {"1": "kategorie1", ...}, "counts": {"i_j": {"1": počet, ...}}}
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Načtení shluků
    with open(cluster_file, 'r', encoding='utf-8') as f:
        clusters = json.load(f)

    # Mapování primárních ID na řádky
    pid_to_row = {row[primary_id]: row for _, row in df_orig.iterrows()}

    for col in categorical_columns:
        # Vytvoření mapy kategorií
        cats = sorted(df_orig[col].dropna().unique().tolist())
        cat_map = OrderedDict((str(i+1), cats[i]) for i in range(len(cats)))

        # Počítání kategorií pro každý shluk
        counts_out = {}
        for pos, pid_list in clusters.items():
            ctr = Counter()
            for pid in pid_list:
                label = pid_to_row[pid][col]
                ctr[label] += 1
            counts_out[pos] = {
                str(i+1): ctr.get(cats[i], 0)
                for i in range(len(cats))
            }

        out = {
            "categories": cat_map,
            "counts": counts_out
        }
        fn = os.path.join(output_dir, f"json/pie_data_{col}.json")
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Použití: python3 project_processor.py <uid_hash>")
        sys.exit(1)    

    uid_hash = sys.argv[1]
    process_project(uid_hash)