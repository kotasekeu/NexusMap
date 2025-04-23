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

# --- Nastavení parametrů evolučního algoritmu ---

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
    total_evaluations = GENERATIONS * POPULATION_SIZE
    current_eval = 0
    # Zaloguj celkový počet evaluací
    log_progress(0, total_evaluations)

    # vygeneruje náhodné nastavení pro každou populaci
    population = [random_config(param_space) for _ in range(POPULATION_SIZE)]    
    
    for gen in range(GENERATIONS):
        print(f"Generace {gen + 1}/{GENERATIONS}")
        
        with Pool(processes=cpu_count()) as pool:
            scored = pool.map(evaluate_individual, population)

        # for score, ind, duration, total_weight_updates in scored:
        #     current_eval += 1
        #     log_progress(current_eval, total_evaluations)                   

        scored.sort(key=lambda x: x[0], reverse=False)
        best = scored[0]
        print(f" Nejlepší skóre: {best[0]:.8f} | Čas: {best[2]:.4f} s | Upraveno vah:{best[3]}")

        # --- Výběr a generace nové populace ---
        top = [ind for _, ind, _, _ in scored[:POPULATION_SIZE // 2]]
        next_gen = top[:]
        while len(next_gen) < POPULATION_SIZE:
            parent = random.choice(top)
            child = mutate(copy.deepcopy(parent), param_space)
            next_gen.append(child)

        population = next_gen        
        log_final_best(get_uid(best[1]), best[1], best[0], duration=best[2] if len(best) > 2 else 0.0)

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
    log_dir = f"/userfiles/{CONFIG['uid_prefix']}"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "log.txt")
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
    log_dir = f"/userfiles/{CONFIG['uid_prefix']}"
    os.makedirs(log_dir, exist_ok=True)
    csv_path = os.path.join(log_dir, "results.csv")

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
    log_dir = f"/userfiles/{CONFIG['uid_prefix']}"
    os.makedirs(log_dir, exist_ok=True)
    progress_path = os.path.join(log_dir, "progress.log")
    with open(progress_path, "a") as f:
        f.write(f"{current}/{total} dokončeno\n")

def clear_files(uid_hash: str) -> None:
    """
    Zálohuje existující výsledky (logy, CSV, progress) do složky backup-{timestamp}.
    Slouží ke zjednodušení zachování předchozích běhů optimalizace bez přepisování.

    :param uid_hash: Název složky (prefix), obvykle např. "evolution"
    """
    from datetime import datetime
    directory = f"/userfiles/{uid_hash}"
    if not os.path.exists(directory):
        return
    backup_dir = os.path.join(directory, f"backup-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}")
    os.makedirs(backup_dir, exist_ok=True)
    for filename in os.listdir(directory):
        if filename != "input.csv":
            file_path = os.path.join(directory, filename)
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
    uid_prefix = CONFIG["uid_prefix"]
    file_name = f"data_{sample_size}x{input_dim}.npy"
    file_path = f"/userfiles/{uid_prefix}/{file_name}"

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
    log_dir = f"/userfiles/{CONFIG['uid_prefix']}"
    os.makedirs(log_dir, exist_ok=True)
    best_path = os.path.join(log_dir, "final_best.txt")
    with open(best_path, "a") as f:
        f.write(f"UID: {uid}\n")
        f.write(f"Score (quantization error): {score:.6f}\n")
        f.write(f"Duration: {duration:.2f} s\n")
        f.write("Parameters:\n")
        for k, v in config.items():
            f.write(f"  {k}: {v}\n")

def evaluate_individual(ind):
    """
    Vyhodnotí jednu konfiguraci: provede trénink Kohonen sítě, změří čas, spočítá chybu a zaloguje.

    :param ind: Slovník s parametry jedné konfigurace
    :return: Tuple (score, config, duration) – pro další zpracování v evoluci
    """
    start_time = time.time()

    sample_size = ind["sample_size"]
    input_dim = ind["input_dim"]
    data = get_or_generate_data(sample_size, input_dim)
    map_width, map_height = ind["map_size"]    

    som = KohonenSOM(
        dim=input_dim,
        m=map_width, 
        n=map_height, 
        **{k: v for k, v in ind.items() if k not in ['sample_size', 'input_dim', 'map_size']}   
    )

    som.train(data)
    
    # codebook_vectors = som.weights.reshape(-1, som.dim)
    # bmu_indexes = np.array([som.find_bmu(x)[0] * som.n + som.find_bmu(x)[1] for x in data])
    # neuron_error_map, total_qe = som.compute_quantization_error(data, codebook_vectors, bmu_indexes, (som.m, som.n))    

    duration = time.time() - start_time
    uid = get_uid(ind)

    # print(f"Upraveno vah:{som.total_weight_updates}")
    # print(f"MQE: {som.best_mqe:.8f}")
    # print(f"Doba trvání: {duration:.2f}s")
    # print(f"--------------------------------")
    log_message(uid, f"Konfigurace vyhodnocena – kvantizační chyba: {som.best_mqe:.8f}, čas: {duration:.2f}s")
    log_result_to_csv(uid, ind, som.best_mqe, duration, som.total_weight_updates)

    return (som.best_mqe, copy.deepcopy(ind), duration, som.total_weight_updates)


# --- Spuštění algoritmu ---
if __name__ == "__main__":
    clear_files(CONFIG["uid_prefix"])
    POPULATION_SIZE = CONFIG["population_size"]
    GENERATIONS = CONFIG["generations"]    

    som_config = CONFIG.copy()
    som_config.pop("population_size", None)
    som_config.pop("generations", None)
    som_config.pop("uid_prefix", None)

    run_evolution(som_config)