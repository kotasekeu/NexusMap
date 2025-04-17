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
from kohonen_24_04_17 import KohonenSOM
from sklearn.metrics import pairwise_distances_argmin_min
from multiprocessing import Pool, cpu_count

# --- Nastavení parametrů evolučního algoritmu ---
POPULATION_SIZE = CONFIG["population_size"]
GENERATIONS = CONFIG["generations"]

# --- Inicializace populace náhodnými konfiguracemi ---
def random_config(param_space):
    """Vytvoří náhodnou konfiguraci na základě zadaného rozsahu hodnot."""
    config = {}
    for key, value in param_space.items():
        if isinstance(value, list):
            config[key] = random.choice(value)  # Výběr jedné varianty z možných
        else:
            config[key] = value  # Použití jedné pevně dané hodnoty
    return config

# --- Mutace: náhodná změna jednoho parametru ---
def mutate(config, param_space):
    """Náhodně změní jednu hodnotu v konfiguraci."""
    key = random.choice(list(param_space.keys()))
    if isinstance(param_space[key], list):
        config[key] = random.choice(param_space[key])
    return config

# --- Spuštění evoluce ---
def run_evolution(param_space):
    population_size = CONFIG["population_size"]
    generations = CONFIG["generations"]

    total_evaluations = CONFIG["generations"] * CONFIG["population_size"]
    current_eval = 0
    # Zaloguj celkový počet evaluací
    log_progress(0, total_evaluations)

    population = [random_config(param_space) for _ in range(population_size)]

    for gen in range(generations):
        print(f"Generace {gen + 1}/{generations}")

        scored = []

        for ind in population:
            # --- Výpočet skóre ---
            start_time = time.time()

            sample_size = ind["sample_size"]
            input_dim = ind["input_dim"]
            data = get_or_generate_data(sample_size, input_dim)
            epochs = int(sample_size * ind["epoch_multiplier"])
            map_width, map_height = ind["map_size"]

            start_time = time.time()

            som = KohonenSOM(
                m=map_width, n=map_height, dim=input_dim,
                learning_rate=ind["learning_rate"],
                min_learning_rate=ind["min_learning_rate"],
                radius=ind["radius"],
                min_radius=ind["min_radius"],
                num_batches=ind["num_batches"],
                min_batch_percent=ind["min_batch_percent"],
                max_batch_percent=ind["max_batch_percent"],
                lr_decay_type=ind["lr_decay_type"],
                radius_decay_type=ind["radius_decay_type"],
                batch_growth_type=ind["batch_growth_type"],
                growth_g=ind["growth_g"],
                random_seed=ind["random_seed"]
            )

            som.train(data[:epochs])
            score = evaluate_som_quality(som, data[:epochs])

            duration = time.time() - start_time
            uid = get_uid(ind)

            log_message(uid, f"Konfigurace vyhodnocena – kvantizační chyba: {score:.6f}, čas: {duration:.2f}s")
            log_result_to_csv(uid, ind, score, duration)
            

            duration = time.time() - start_time

            # --- Logování výsledků ---
            uid = get_uid(ind)
            log_message(uid, f"Konfigurace vyhodnocena – skóre: {score:.4f}, čas: {duration:.2f}s")
            log_result_to_csv(uid, ind, score, duration)

            scored.append((score, copy.deepcopy(ind)))
            current_eval += 1
            log_progress(current_eval, total_evaluations)

        # --- Výběr nejlepší konfigurace ---
        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0]
        print(f" Nejlepší skóre: {best[0]:.4f}")

        # --- Výběr a generace nové populace ---
        top = [ind for _, ind in scored[:population_size // 2]]
        next_gen = top[:]
        while len(next_gen) < population_size:
            parent = random.choice(top)
            child = mutate(copy.deepcopy(parent), param_space)
            next_gen.append(child)

        population = next_gen        
        log_final_best(get_uid(best[1]), best[1], best[0], duration=best[2] if len(best) > 2 else 0.0)

# Vytvoří hash pro danou konfiguraci jako unikátní ID (např. pro logování)
def get_uid(config):
    config_str = str(sorted(config.items()))
    return hashlib.md5(config_str.encode()).hexdigest()[:8]

# Zaloguje zprávu do souboru evolution/log.txt
def log_message(uid, message):
    log_dir = f"/userfiles/{CONFIG['uid_prefix']}"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "log.txt")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{now}] [{uid}] {message}\n")

# Zapíše záznam do CSV výsledků
def log_result_to_csv(uid, config, score, duration):
    log_dir = f"/userfiles/{CONFIG['uid_prefix']}"
    os.makedirs(log_dir, exist_ok=True)
    csv_path = os.path.join(log_dir, "results.csv")

    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode="a", newline="") as f:
        fieldnames = ['uid', 'score', 'duration'] + list(config.keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        row = {'uid': uid, 'score': score, 'duration': duration, **config}
        writer.writerow(row)

def log_progress(current, total):
    log_dir = f"/userfiles/{CONFIG['uid_prefix']}"
    os.makedirs(log_dir, exist_ok=True)
    progress_path = os.path.join(log_dir, "progress.log")
    with open(progress_path, "a") as f:
        f.write(f"{current}/{total} dokončeno\n")

def clear_files(uid_hash: str) -> None:
    """Přesune existující soubory do zálohy, kromě input.csv."""
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
    """Vrátí generovaná data z cache nebo vytvoří nová, pokud neexistují."""
    uid_prefix = CONFIG["uid_prefix"]
    file_name = f"data_{sample_size}x{input_dim}.npy"
    file_path = f"/userfiles/{uid_prefix}/{file_name}"

    # Pokud existuje, načteme
    if os.path.exists(file_path):
        return np.load(file_path)

    # Pokud neexistuje, vygenerujeme a uložíme
    data, _ = make_blobs(n_samples=sample_size, n_features=input_dim, centers=5, random_state=42)
    np.save(file_path, data)
    log_message("SYSTEM", f"Vygenerována nová data: {file_name}")
    return data

def evaluate_som_quality(som, data):
    weights_flat = som.weights.reshape(-1, som.dim)
    _, dists = pairwise_distances_argmin_min(data, weights_flat)
    return np.mean(dists)

# --- Uložení nejlepší konfigurace do samostatného souboru ---
def log_final_best(uid, config, score, duration):
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

# --- Spuštění algoritmu ---
if __name__ == "__main__":
    clear_files(CONFIG["uid_prefix"])
    run_evolution(CONFIG)