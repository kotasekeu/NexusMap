"""
Evoluční optimalizace parametrů Kohonenovy samo-organizační mapy (SOM).

Tento modul implementuje evoluční algoritmus pro optimalizaci parametrů SOM.
Cílem je najít takovou konfiguraci parametrů, která minimalizuje kvantizační chybu
při zachování rozumné doby výpočtu.

Hlavní funkce:
- Paralelní vyhodnocování konfigurací
- Automatické zálohování výsledků
- Podpora vlastních vstupních dat
- Export výsledků do CSV a TXT
"""

import random
import copy
from os.path import exists
from evolutionary_som_config import CONFIG
import os
import csv
import hashlib
import time
import shutil
from datetime import datetime
import numpy as np
from sklearn.datasets import make_blobs
from kohonen import KohonenSOM
from sklearn.metrics import pairwise_distances_argmin_min
from multiprocessing import Pool, cpu_count
import sys
from project_processor import normalize_data
import pandas as pd
import argparse
from utils import set_uid_hash
import json
import psutil

# Váhy pro multi-kriteriální fitness funkci
W_ERROR = 0.7  # váha pro kvantizační chybu
W_TIME = 0.3   # váha pro dobu výpočtu

# Globální proměnné
INPUT_FILE = None
NORMALIZED_DATA = None
WORKING_DIR = None

def get_working_directory(input_file: str = None) -> str:
    """
    Určí pracovní adresář pro ukládání výsledků.
    
    Args:
        input_file: Cesta k vstupnímu souboru (volitelné)
        
    Returns:
        str: Cesta k pracovnímu adresáři s vytvořenou složkou reports
    """
    if input_file:
        base_dir = os.path.dirname(os.path.abspath(input_file))
    else:
        base_dir = os.getcwd()
    
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    return reports_dir

def load_config(config_path: str = None) -> dict:
    """
    Načte konfiguraci z JSON souboru nebo použije výchozí CONFIG.
    
    Args:
        config_path: Cesta k JSON konfiguračnímu souboru
        
    Returns:
        dict: Načtená konfigurace
        
    Raises:
        SystemExit: Pokud soubor neexistuje nebo není validní JSON
    """
    if config_path:
        if not os.path.exists(config_path):
            print(f"Chyba: Konfigurační soubor {config_path} neexistuje.")
            sys.exit(1)
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Chyba: Konfigurační soubor {config_path} není validní JSON: {e}")
            sys.exit(1)
            
        return config
    return CONFIG

def crossover(parent1: dict, parent2: dict, param_space: dict) -> dict:
    """
    Uniformní křížení dvou rodičovských konfigurací.
    
    Args:
        parent1: První rodičovská konfigurace
        parent2: Druhá rodičovská konfigurace
        param_space: Prostor parametrů s možnými hodnotami
        
    Returns:
        dict: Nová konfigurace vytvořená křížením
    """
    child = {}
    for key in param_space:
        if isinstance(param_space[key], list):
            child[key] = random.choice([parent1[key], parent2[key]])
        else:
            child[key] = parent1[key]
    return child

def random_config(param_space: dict) -> dict:
    """
    Vytvoří náhodnou konfiguraci z parametrového prostoru.
    
    Args:
        param_space: Slovník s možnými hodnotami pro každý parametr
        
    Returns:
        dict: Náhodně vygenerovaná konfigurace
    """
    config = {}
    for key, value in param_space.items():
        if isinstance(value, list):
            config[key] = random.choice(value)
        else:
            config[key] = value
    return config

def mutate(config: dict, param_space: dict) -> dict:
    """
    Provede mutaci jedné náhodné hodnoty v konfiguraci.
    
    Args:
        config: Konfigurace k mutaci
        param_space: Prostor parametrů s možnými hodnotami
        
    Returns:
        dict: Mutovaná konfigurace
    """
    key = random.choice(list(param_space.keys()))
    if isinstance(param_space[key], list):
        config[key] = random.choice(param_space[key])
    return config

def run_evolution(param_space: dict) -> None:
    """
    Hlavní smyčka evolučního algoritmu.
    
    Args:
        param_space: Prostor parametrů pro optimalizaci
    """
    try:
        population = [random_config(param_space) for _ in range(POPULATION_SIZE)]
        for gen in range(GENERATIONS):
            print(f"Generace {gen + 1}/{GENERATIONS}")

            with Pool(processes=min(12, cpu_count(), POPULATION_SIZE)) as pool:
                try:
                    args = [(ind, i, gen) for i, ind in enumerate(population)]
                    results = []
                    for i, arg in enumerate(args):
                        try:
                            result = pool.apply_async(evaluate_individual, arg)
                            results.append(result)
                        except Exception as e:
                            print(f"Chyba při inicializaci procesu {i}: {e}")

                    scored = []
                    for i, r in enumerate(results):
                        try:
                            scored.append(r.get(timeout=3600))
                        except Exception as e:
                            print(f"[CHYBA] Jedinec {i} selhal: {e}")
                except Exception as e:
                    print(f"Chyba při vyhodnocování populace: {str(e)}")
                    pool.terminate()
                    pool.join()
                    raise e

            # Normalizace a výpočet fitness
            qes = [s[0] for s in scored]
            times = [s[2] for s in scored]
            qe_min, qe_max = min(qes), max(qes)
            t_min, t_max = min(times), max(times)
            
            scored_f = []
            for qe, cfg, dur, upd in scored:
                ne = (qe - qe_min) / (qe_max - qe_min) if qe_max > qe_min else 0.0
                nt = (dur - t_min) / (t_max - t_min) if t_max > t_min else 0.0
                fit = W_ERROR*(1 - ne) + W_TIME*(1 - nt)
                scored_f.append((fit, qe, cfg, dur, upd))

            # Selekce a reprodukce
            scored_f.sort(key=lambda x: x[0], reverse=True)
            best = scored_f[0]
            print(f" Nejlepší QE: {best[1]:.6f} | Čas: {best[3]:.2f}s | Fitness: {best[0]:.4f}")

            top = [entry[2] for entry in scored_f[:POPULATION_SIZE // 2]]
            next_gen = top[:]
            
            while len(next_gen) < POPULATION_SIZE:
                p1, p2 = random.sample(top, 2)
                child = crossover(p1, p2, param_space)
                child = mutate(child, param_space)
                next_gen.append(child)

            population = next_gen
            log_final_best(get_uid(best[2]), best[2], best[1], duration=best[3])
            
    except KeyboardInterrupt:
        print("\nUkončuji evoluční algoritmus...")
        return
    except Exception as e:
        print(f"\nChyba při běhu evolučního algoritmu: {str(e)}")
        return

    print(f"Generace {gen + 1} – úspěšných: {len(scored)}/{POPULATION_SIZE}")

def get_uid(config: dict) -> str:
    """
    Vytvoří unikátní identifikátor pro konfiguraci.
    
    Args:
        config: Konfigurace k identifikaci
        
    Returns:
        str: MD5 hash konfigurace (8 znaků)
    """    
    config_str = str(sorted(config.items()))
    return hashlib.md5(config_str.encode()).hexdigest()

def log_message(uid: str, message: str) -> None:
    """
    Zapíše zprávu do logu.
    
    Args:
        uid: Identifikátor konfigurace nebo "SYSTEM"
        message: Text zprávy
    """    
    log_path = os.path.join(WORKING_DIR, "log.txt")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{now}] [{uid}] {message}\n")

def log_result_to_csv(uid: str, config: dict, score: float, duration: float, total_weight_updates: int) -> None:
    """
    Zapíše výsledky konfigurace do CSV.
    
    Args:
        uid: Identifikátor konfigurace
        config: Parametry konfigurace
        score: Kvantizační chyba
        duration: Doba výpočtu v sekundách
        total_weight_updates: Celkový počet aktualizací vah
    """    
    csv_path = os.path.join(WORKING_DIR, "results.csv")

    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode="a", newline="") as f:
        fieldnames = ['uid', 'score', 'duration', 'total_weight_updates'] + list(config.keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        row = {'uid': uid, 'score': score, 'duration': duration, 'total_weight_updates': total_weight_updates, **config}
        writer.writerow(row)

def log_progress(current: int, total: int) -> None:
    """
    Loguje průběh vyhodnocování.
    
    Args:
        current: Počet dokončených konfigurací
        total: Celkový počet konfigurací
    """    
    progress_path = os.path.join(WORKING_DIR, "progress.log")
    with open(progress_path, "a") as f:
        f.write(f"{current}/{total} dokončeno\n")

def get_or_generate_data(sample_size: int, input_dim: int) -> np.ndarray:
    """
    Vrací datovou sadu požadovaného rozměru.
    
    Args:
        sample_size: Počet vzorků
        input_dim: Počet dimenzí
        
    Returns:
        np.ndarray: Data ve tvaru (sample_size, input_dim)
    """
    file_name = f"data_{sample_size}x{input_dim}.npy"
    file_path = os.path.join(WORKING_DIR, file_name)

    if os.path.exists(file_path):
        return np.load(file_path)

    data, _ = make_blobs(n_samples=sample_size, n_features=input_dim, centers=5, random_state=CONFIG["random_seed"])
    np.save(file_path, data)
    log_message("SYSTEM", f"Vygenerována nová data: {file_name}")
    return data

def log_status_to_csv(uid: str, population_id: int, generation: int, status: str, 
                     start_time: str = None, end_time: str = None) -> None:
    """
    Loguje stav konfigurace do CSV.
    
    Args:
        uid: Identifikátor konfigurace
        population_id: ID populace
        generation: Číslo generace
        status: Stav (started/completed/failed)
        start_time: Čas spuštění
        end_time: Čas dokončení
    """
    csv_path = os.path.join(WORKING_DIR, "status.csv")
    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0

    with open(csv_path, mode="a", newline="") as f:
        fieldnames = ['uid', 'population_id', 'generation', 'status', 'start_time', 'end_time']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        
        row = {
            'uid': uid,
            'population_id': population_id,
            'generation': generation,
            'status': status,
            'start_time': start_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'end_time': end_time
        }
        writer.writerow(row)

def log_final_best(uid: str, config: dict, score: float, duration: float) -> None:
    """
    Uloží nejlepší konfiguraci generace.
    
    Args:
        uid: Identifikátor konfigurace
        config: Parametry konfigurace
        score: Kvantizační chyba
        duration: Doba výpočtu
    """
    best_path = os.path.join(WORKING_DIR, "final_best.txt")
    with open(best_path, "a") as f:
        f.write(f"UID: {uid}\n")
        f.write(f"Score (quantization error): {score:.6f}\n")
        f.write(f"Duration: {duration:.2f} s\n")
        f.write("Parameters:\n")
        for k, v in config.items():
            f.write(f"  {k}: {v}\n")

def load_input_data(input_file: str) -> np.ndarray:
    """
    Načte a normalizuje data z CSV.
    
    Args:
        input_file: Cesta k CSV souboru
        
    Returns:
        np.ndarray: Normalizovaná data
    """
    global NORMALIZED_DATA
    
    if NORMALIZED_DATA is not None:
        return NORMALIZED_DATA

    preprocess_file = os.path.join(os.path.dirname(input_file), "preprocess-input.csv")
    if not os.path.exists(preprocess_file):
        preprocess_file = normalize_data(input_file, {}, {})
    NORMALIZED_DATA = pd.read_csv(preprocess_file, delimiter=',').values
    log_message("SYSTEM", f"Načtena a normalizována data z externího souboru: {input_file}")
    return NORMALIZED_DATA

def extract_uid_from_path(file_path: str) -> str:
    """
    Extrahuje UID z cesty k souboru.
    
    Args:
        file_path: Cesta k souboru
        
    Returns:
        str: Extrahovaný UID nebo None
    """
    parts = file_path.split('/')
    for part in parts:
        if part.startswith('nxmpp'):
            return part
    return None

def evaluate_individual(ind: dict, population_id: int, generation: int) -> tuple:
    """
    Vyhodnotí jednu konfiguraci SOM.
    
    Args:
        ind: Konfigurace k vyhodnocení
        population_id: ID populace
        generation: Číslo generace
        
    Returns:
        tuple: (kvantizační chyba, konfigurace, doba výpočtu, počet aktualizací)
        
    Raises:
        Exception: Při chybě vyhodnocování
    """
    start_time = time.time()
    uid = get_uid(ind)
    
    try:
        print(f"[GEN {generation + 1}] Total RAM used: {psutil.virtual_memory().used // (1024 ** 2)} MB")
        log_status_to_csv(uid, population_id, generation, "started", 
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if "sample_size" in ind:
            sample_size = ind["sample_size"]

        if "input_dim" in ind:
            input_dim = ind["input_dim"]

        if INPUT_FILE:
            data = load_input_data(INPUT_FILE)
        else:
            data = get_or_generate_data(sample_size, input_dim)

        som = KohonenSOM(
            dim=data.shape[1],        
            **{k: v for k, v in ind.items() if k not in ['sample_size', 'input_dim']}
        )    

        som.train(data)
        
        duration = time.time() - start_time
        log_message(uid, f"Konfigurace vyhodnocena – kvantizační chyba: {som.best_mqe:.8f}, čas: {duration:.2f}s")
        log_result_to_csv(uid, ind, som.best_mqe, duration, som.total_weight_updates)
        
        log_status_to_csv(uid, population_id, generation, "completed", 
                         datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S"),
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return (som.best_mqe, copy.deepcopy(ind), duration, som.total_weight_updates)
        
    except Exception as e:
        log_status_to_csv(uid, population_id, generation, "failed", 
                         datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S"),
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        log_message(uid, f"Chyba při vyhodnocování: {str(e)}")
        raise e

def analyze_results() -> None:
    """
    Analyzuje výsledky evolučního algoritmu a vytvoří soubory s nejlepšími konfiguracemi.
    """
    df = pd.read_csv(os.path.join(WORKING_DIR, "results.csv"))
    df["score_combined"] = df["score"] * df["duration"] * df["total_weight_updates"]
    
    non_config_cols = [
        "uid", "score", "duration", "total_weight_updates",
        "score_combined", "config_count"
    ]
    
    compare_cols = [col for col in df.columns if col not in non_config_cols and not col.startswith("Unnamed")]
    best_rows = df.loc[df.groupby("uid")["score_combined"].idxmin()].copy()
    best_rows["config_count"] = df.groupby("uid")["uid"].transform("count")
    best_sorted = best_rows.sort_values("score_combined")
    
    static_cols = [col for col in compare_cols if df[col].nunique(dropna=False) == 1]
    dynamic_cols = [col for col in best_sorted.columns if col not in static_cols]
    best_sorted = best_sorted[dynamic_cols]
    
    best_sorted.to_csv(os.path.join(WORKING_DIR, "best_configurations_full.csv"), index=False)
    winner = best_sorted.iloc[0]

    with open(os.path.join(WORKING_DIR, "summary.txt"), "w", encoding="utf-8") as f:
        f.write("Best configuration:\n")
        for col in dynamic_cols:
            f.write(f"{col}: {winner[col]}\n")
        f.write("\nStatic parameters:\n")
        for col in static_cols:
            f.write(f"{col} = {df[col].iloc[0]}\n")
    
    log_message("SYSTEM", "Analýza výsledků dokončena - vytvořeny soubory best_configurations_full.csv a summary.txt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evoluční optimalizace Kohonenovy sítě')
    parser.add_argument('-i', '--input', help='Cesta k vstupnímu CSV souboru')
    parser.add_argument('-c', '--config', help='Cesta k vlastnímu konfiguračnímu souboru')
    args = parser.parse_args()

    config = load_config(args.config)

    if args.input:
        if not os.path.exists(args.input):
            print(f"Chyba: Vstupní soubor {args.input} neexistuje.")
            sys.exit(1)
        INPUT_FILE = args.input

    WORKING_DIR = get_working_directory(INPUT_FILE)

    POPULATION_SIZE = config["population_size"]
    GENERATIONS = config["generations"]    

    som_config = config.copy()
    som_config.pop("population_size", None)
    som_config.pop("generations", None)
    som_config.pop("uid_prefix", None)

    run_evolution(som_config)
    analyze_results()