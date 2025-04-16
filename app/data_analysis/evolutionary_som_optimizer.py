import random
import numpy as np
from copy import deepcopy
from sklearn.datasets import make_blobs
from sklearn.metrics import pairwise_distances_argmin_min
from utils import log_message, set_uid_hash
import pandas as pd
from project_processor import get_project_detail, load_project_settings, validate_input_file, normalize_data

# Importuj svůj upravený KohonenSOM
from kohonen import KohonenSOM

# === Parametry optimalizace ===
PARAM_SPACE = {
    "learning_rate": (0.1, 1.0),
    "min_learning_rate": (0.01, 0.5),
    "radius": (1.0, 15.0),
    "min_radius": (0.1, 5.0),
    "num_batches": (5, 20),
    "min_batch_percent": (0.1, 2.0),
    "max_batch_percent": (2.1, 20.0),
    "growth_g": (1.0, 30.0),
    "lr_decay_type": ["linear", "logarithmic", "exp-drop"],
    "radius_decay_type": ["linear", "logarithmic", "exp-drop"],
    "batch_growth_type": ["linear", "exp-growth"]
}

MAP_SIZES = [(10, 10), (20, 20), (30, 30)]

# === Hodnocení kvality SOM ===
def evaluate_som_quality(som, data):
    weights_flat = som.weights.reshape(-1, som.dim)
    closest, dists = pairwise_distances_argmin_min(data, weights_flat)
    return -np.mean(dists)  # menší vzdálenost = lepší, proto -

# === Generování dat ===
def generate_data(n_samples=200, n_features=5, n_clusters=5):
    X, _ = make_blobs(n_samples=n_samples, n_features=n_features, centers=n_clusters, random_state=42)
    return X

# === Generování náhodné konfigurace ===
def random_config():
    config = {}
    for key, value in PARAM_SPACE.items():
        if isinstance(value, tuple):
            config[key] = round(random.uniform(*value), 4)
        else:
            config[key] = random.choice(value)
    return config

# === Mutace jednoho parametru ===
def mutate(config):
    key = random.choice(list(PARAM_SPACE.keys()))
    if isinstance(PARAM_SPACE[key], tuple):
        config[key] = round(random.uniform(*PARAM_SPACE[key]), 4)
    else:
        config[key] = random.choice(PARAM_SPACE[key])
    return config

# === Evoluční optimalizace ===
def optimize_som(data, generations=5, population_size=10):
    population = [random_config() for _ in range(population_size)]
    best = None

    for gen in range(generations):
        scored = []
        for individual in population:
            for m, n in MAP_SIZES:
                som = KohonenSOM(
                    m=m, n=n, dim=data.shape[1],
                    learning_rate=individual["learning_rate"],
                    min_learning_rate=individual["min_learning_rate"],
                    radius=individual["radius"],
                    min_radius=individual["min_radius"],
                    num_batches=int(individual["num_batches"]),
                    min_batch_percent=individual["min_batch_percent"],
                    max_batch_percent=individual["max_batch_percent"],
                    lr_decay_type=individual["lr_decay_type"],
                    radius_decay_type=individual["radius_decay_type"],
                    batch_growth_type=individual["batch_growth_type"],
                    growth_g=individual["growth_g"],
                    random_seed=42
                )
                som.train(data)
                score = evaluate_som_quality(som, data)
                scored.append((score, deepcopy(individual), (m, n)))

        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0]
        print(f"Generace {gen}: Nejlepší skóre {best[0]:.4f} na mapě {best[2]}\nConfig: {best[1]}")

        top = [ind for _, ind, _ in scored[:population_size//2]]
        next_gen = top[:]
        while len(next_gen) < population_size:
            parent = random.choice(top)
            child = mutate(deepcopy(parent))
            next_gen.append(child)

        population = next_gen

    print("\n=== NEJLEPŠÍ KONFIGURACE ===")
    print(f"Skóre: {best[0]:.4f}, Mapa: {best[2]}")
    for k, v in best[1].items():
        print(f"{k}: {v}")

# === Hlavní běh ===
if __name__ == "__main__":
        
    uid_hash = 'evolutionary_som_optimizer'
    set_uid_hash(uid_hash)

    # Načtení detailů projektu
    project = get_project_detail('nxmpp67fea8630c3dd9.64069613')
    settings = load_project_settings(project)

    # Kontrola vstupního souboru
    input_file = f"/userfiles/{uid_hash}/input.csv"
    if not validate_input_file(input_file, settings):
        log_message(f"Neplatný vstupní soubor pro projekt {uid_hash}.")
        sys.exit(1)

    # Předzpracování dat
    preprocess_file = f"/userfiles/{uid_hash}/preprocess.csv"
    normalize_data(input_file, preprocess_file, settings)
    data = pd.read_csv(preprocess_file, delimiter=';').values
    
    optimize_som(data)