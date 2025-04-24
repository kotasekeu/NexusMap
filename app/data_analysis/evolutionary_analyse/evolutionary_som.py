# evolutionary_som.py
# Tento skript bude řídit běh evolučního algoritmu pro optimalizaci parametrů Kohonenovy sítě.

import random
import copy
from evolutionary_som_config import CONFIG
import os
import csv
import hashlib
import time
import os
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

# --- Nastavení parametrů evolučního algoritmu ---

# Váhy pro multi‐kriteriální fitness
W_ERROR = 0.7
W_TIME  = 0.3

# --- Globální proměnné ---
INPUT_FILE = None
NORMALIZED_DATA = None
WORKING_DIR = None

def get_working_directory(input_file: str = None) -> str:
    """
    Určí pracovní adresář na základě vstupního souboru nebo aktuálního adresáře.
    
    :param input_file: Cesta k vstupnímu souboru (volitelné)
    :return: Cesta k pracovnímu adresáři
    """
    if input_file:
        # Pokud je zadán vstupní soubor, použij jeho adresář
        base_dir = os.path.dirname(os.path.abspath(input_file))
    else:
        # Jinak použij adresář, ze kterého je spouštěn skript
        base_dir = os.getcwd()
    
    # Vytvoř složku reports v určeném adresáři
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    return reports_dir

def load_config(config_path: str = None):
    """
    Načte konfiguraci z JSON souboru nebo použije výchozí CONFIG.
    
    :param config_path: Cesta k JSON konfiguračnímu souboru
    :return: Načtená konfigurace
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

def crossover(parent1, parent2, param_space):
    """
    Uniformní křížení: pro každý parametr náhodně vybere hodnotu
    z jednoho ze dvou rodičů.
    """
    child = {}
    for key in param_space:
        if isinstance(param_space[key], list):
            child[key] = random.choice([parent1[key], parent2[key]])
        else:
            child[key] = parent1[key]
    return child

def random_config(param_space):
    """
    Vytvoří náhodnou konfiguraci (jedince) na základě zadaného prostoru parametrů.
    Pokud má parametr více variant (seznam), vybere jednu náhodně.
    Pokud je hodnota pevná, použije se přímo.

    :return: Slovník s jednou kompletní konfigurací pro evoluci
    """
    config = {}
    for key, value in param_space.items():
        if isinstance(value, list):
            config[key] = random.choice(value)  # Výběr jedné varianty z možných
        else:
            config[key] = value  # Použití jedné pevně dané hodnoty
    return config

def mutate(config, param_space):
    """
    Provádí jednoduchou mutaci jedné náhodné hodnoty v dané konfiguraci.
    Slouží k vytvoření nového jedince (dítěte) z existujícího rodiče.

    :param config: Aktuální konfigurace (jedinec), který bude mutován
    :param param_space: Prostor parametrů (slovník s variantami pro každý parametr)
    :return: Upravená (mutovaná) konfigurace
    """
    key = random.choice(list(param_space.keys()))
    if isinstance(param_space[key], list):
        config[key] = random.choice(param_space[key])
    return config

def run_evolution(param_space):
    """
    Hlavní smyčka evolučního algoritmu. Provádí optimalizaci v několika generacích:
    - Náhodně vytvoří populaci
    - Vyhodnotí každého jedince (paralelně)
    - Vybere nejlepší
    - Vytvoří novou generaci pomocí mutací
    - Loguje výsledky a nejlepší konfigurace

    :param param_space: Prostor všech parametrů, které se mají optimalizovat
    """
    population = [random_config(param_space) for _ in range(POPULATION_SIZE)]
    for gen in range(GENERATIONS):
        print(f"Generace {gen + 1}/{GENERATIONS}")

        # vyhodnotit
        with Pool(processes=cpu_count()) as pool:
            scored = pool.map(evaluate_individual, population)

        # normalizace
        qes = [s[0] for s in scored]
        times = [s[2] for s in scored]
        qe_min, qe_max   = min(qes), max(qes)
        t_min,  t_max    = min(times), max(times)
        # spočítat fitness pro každý jedinec
        scored_f = []
        for qe, cfg, dur, upd in scored:
            ne = (qe - qe_min) / (qe_max - qe_min) if qe_max > qe_min else 0.0
            nt = (dur - t_min) / (t_max - t_min) if t_max > t_min else 0.0
            fit = W_ERROR*(1 - ne) + W_TIME*(1 - nt)
            scored_f.append((fit, qe, cfg, dur, upd))

        # vybrat podle fitness
        scored_f.sort(key=lambda x: x[0], reverse=True)
        best = scored_f[0]
        print(f" Nejlepší QE: {best[1]:.6f} | Čas: {best[3]:.2f}s | Fitness: {best[0]:.4f}")

        # selekce top 50 %
        top = [entry[2] for entry in scored_f[:POPULATION_SIZE // 2]]
        next_gen = top[:]
        # generace nové populace s křížením + mutací
        while len(next_gen) < POPULATION_SIZE:
            p1, p2 = random.sample(top, 2)
            child  = crossover(p1, p2, param_space)
            child  = mutate(child, param_space)
            next_gen.append(child)

        population = next_gen
        # uložit nejlepší
        log_final_best(get_uid(best[2]), best[2], best[1], duration=best[3])

def get_uid(config):
    """
    Vytvoří krátký hash (UID) z dané konfigurace pro účely logování, pojmenování a identifikace.

    :param config: Slovník s hodnotami parametrů pro danou konfiguraci.
    :return: Zkrácený MD5 hash (8 znaků) jako unikátní identifikátor.
    """    
    config_str = str(sorted(config.items()))
    return hashlib.md5(config_str.encode()).hexdigest()

def log_message(uid, message):
    """
    Zapíše textovou zprávu do log.txt ve formátu [čas] [uid] zpráva.

    :param uid: Identifikátor konfigurace nebo "SYSTEM"
    :param message: Text zprávy pro log
    """    
    log_path = os.path.join(WORKING_DIR, "log.txt")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{now}] [{uid}] {message}\n")

def log_result_to_csv(uid, config, score, duration, total_weight_updates):
    """
    Zapíše výsledky jedné konfigurace do CSV včetně skóre a doby výpočtu.

    :param uid: Identifikátor konfigurace
    :param config: Použité parametry
    :param score: Výsledná kvantizační chyba
    :param duration: Doba trvání zpracování (v sekundách)
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

def log_progress(current, total):
    """
    Loguje průběžný stav vyhodnocených konfigurací do progress.log.

    :param current: Počet již vyhodnocených konfigurací
    :param total: Celkový počet konfigurací (generace × velikost populace)
    """    
    progress_path = os.path.join(WORKING_DIR, "progress.log")
    with open(progress_path, "a") as f:
        f.write(f"{current}/{total} dokončeno\n")

def clear_files(uid_hash: str) -> None:
    """
    Zálohuje existující výsledky (logy, CSV, progress) do složky backup-{timestamp}.
    Slouží ke zjednodušení zachování předchozích běhů optimalizace bez přepisování.

    :param uid_hash: Název složky (prefix), obvykle např. "evolution"
    """
    if not os.path.exists(WORKING_DIR):
        return
    backup_dir = os.path.join(WORKING_DIR, f"backup-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}")
    os.makedirs(backup_dir, exist_ok=True)
    for filename in os.listdir(WORKING_DIR):
        if filename != "input.csv":
            file_path = os.path.join(WORKING_DIR, filename)
            if os.path.isfile(file_path):
                try:
                    shutil.move(file_path, backup_dir)
                except Exception as e:
                    print(f"Chyba při přesunu {filename}: {e}")

def get_or_generate_data(sample_size: int, input_dim: int):
    """
    Vrací datovou sadu požadovaného rozměru. Pokud již existuje `.npy` soubor, použije ho.
    Jinak vytvoří nová syntetická data pomocí make_blobs, uloží a vrátí.

    :param sample_size: Počet vstupních vzorků
    :param input_dim: Počet vstupních atributů (dimenzí)
    :return: Numpy matice dat ve tvaru (sample_size, input_dim)
    """
    file_name = f"data_{sample_size}x{input_dim}.npy"
    file_path = os.path.join(WORKING_DIR, file_name)

    # Pokud existuje, načteme
    if os.path.exists(file_path):
        return np.load(file_path)

    # Pokud neexistuje, vygenerujeme a uložíme
    data, _ = make_blobs(n_samples=sample_size, n_features=input_dim, centers=5, random_state=CONFIG["random_seed"])
    np.save(file_path, data)
    log_message("SYSTEM", f"Vygenerována nová data: {file_name}")
    return data

def evaluate_som_quality(som, data):
    """
    Spočítá kvantizační chybu – průměrnou vzdálenost mezi vstupními daty a nejbližším uzlem v mapě (BMU).

    :param som: Trénovaná instance KohonenSOM
    :param data: Vstupní data, která byla použita při tréninku
    :return: Průměrná eukleidovská vzdálenost (float)
    """
    # Převedení vah SOM do plochého tvaru pro výpočet vzdáleností
    weights_flat = som.weights.reshape(-1, som.dim)
    
    # Nalezení nejbližších neuronů (BMU) a jejich vzdáleností pro každý vzorek
    bmu_indices, distances = pairwise_distances_argmin_min(data, weights_flat)
    
    # Výpočet průměrné kvantizační chyby
    quantization_error = np.mean(distances)
    
    return quantization_error

def log_final_best(uid, config, score, duration):
    """
    Uloží nejlepší konfiguraci generace do souboru final_best.txt.
    Výpis je formátovaný pro snadnou čitelnost a porovnání.

    :param uid: Hash konfigurace
    :param config: Parametry nejlepší konfigurace
    :param score: Výsledné skóre (kvantizační chyba)
    :param duration: Čas zpracování konfigurace
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
    Načte a normalizuje data z externího CSV souboru.
    
    :param input_file: Cesta k vstupnímu CSV souboru
    :return: Normalizovaná data jako numpy array
    """
    global NORMALIZED_DATA
    
    if NORMALIZED_DATA is not None:
        return NORMALIZED_DATA
        
    preprocess_file = normalize_data(input_file, {})
    NORMALIZED_DATA = pd.read_csv(preprocess_file, delimiter=',').values
    log_message("SYSTEM", f"Načtena a normalizována data z externího souboru: {input_file}")
    return NORMALIZED_DATA

def evaluate_individual(ind):
    """
    Vyhodnotí jednu konfiguraci: provede trénink Kohonen sítě, změří čas, spočítá chybu a zaloguje.

    :param ind: Slovník s parametry jedné konfigurace
    :return: Tuple (score, config, duration) – pro další zpracování v evoluci
    """
    start_time = time.time()

    sample_size = ind["sample_size"]
    input_dim = ind["input_dim"]
    map_width, map_height = ind["map_size"]    

    # Načtení dat - buď z externího souboru nebo generovaná
    if INPUT_FILE:
        data = load_input_data(INPUT_FILE)
    else:
        data = get_or_generate_data(sample_size, input_dim)

    som = KohonenSOM(
        dim=data.shape[1],        
        m=map_width, 
        n=map_height, 
        **{k: v for k, v in ind.items() if k not in ['sample_size', 'input_dim', 'map_size']}   
    )    

    som.train(data)
    
    duration = time.time() - start_time
    uid = get_uid(ind)
    set_uid_hash(uid)

    # print(f"Upraveno vah:{som.total_weight_updates}")
    # print(f"MQE: {som.best_mqe:.8f}")
    # print(f"Doba trvání: {duration:.2f}s")
    # print(f"--------------------------------")
    log_message(uid, f"Konfigurace vyhodnocena – kvantizační chyba: {som.best_mqe:.8f}, čas: {duration:.2f}s")
    log_result_to_csv(uid, ind, som.best_mqe, duration, som.total_weight_updates)

    return (som.best_mqe, copy.deepcopy(ind), duration, som.total_weight_updates)


# --- Spuštění algoritmu ---
if __name__ == "__main__":
    # Zpracování argumentů příkazové řádky
    parser = argparse.ArgumentParser(description='Evoluční optimalizace Kohonenovy sítě')
    parser.add_argument('-i', '--input', help='Cesta k vstupnímu CSV souboru')
    parser.add_argument('-c', '--config', help='Cesta k vlastnímu konfiguračnímu souboru')
    args = parser.parse_args()

    # Načtení konfigurace
    config = load_config(args.config)

    # Nastavení globální proměnné pro vstupní soubor
    if args.input:
        if not os.path.exists(args.input):
            print(f"Chyba: Vstupní soubor {args.input} neexistuje.")
            sys.exit(1)
        INPUT_FILE = args.input

    # Nastavení pracovního adresáře
    WORKING_DIR = get_working_directory(INPUT_FILE)

    clear_files(config["uid_prefix"])
    POPULATION_SIZE = config["population_size"]
    GENERATIONS = config["generations"]    

    som_config = config.copy()
    som_config.pop("population_size", None)
    som_config.pop("generations", None)
    som_config.pop("uid_prefix", None)

    run_evolution(som_config)