import random
import numpy as np
import time
import csv
import os
import hashlib
from copy import deepcopy
from multiprocessing import Pool, cpu_count
from sklearn.datasets import make_blobs
from sklearn.metrics import pairwise_distances_argmin_min
from utils import log_message, set_uid_hash
from kohonen import KohonenSOM

PARAM_SPACE = {
    "learning_rate": (0.1, 1.0),
    "min_learning_rate": (0.01, 0.5),
    "radius": (1.0, 15.0),
    "min_radius": (0.1, 5.0),
    "num_batches": (9, 9),
    "min_batch_percent": (0.1, 2.0),
    "max_batch_percent": (2.1, 20.0),
    "growth_g": (1.0, 30.0),
    "lr_decay_type": ["linear", "logarithmic", "exp-drop"],
    "radius_decay_type": ["linear", "logarithmic", "exp-drop"],
    "batch_growth_type": ["linear", "exp-growth"]
}

MAP_SIZES = [(10, 10), (20, 20), (30, 30)]
FEATURE_COUNTS = [2, 4, 6, 8]
SAMPLE_SIZES = [200, 500, 1000, 2000, 4000]
EPOCH_MULTIPLIERS = [0.5, 1, 1.5]
RESULTS_FILE = "results_summary.csv"


def evaluate_som_quality(som, data):
    weights_flat = som.weights.reshape(-1, som.dim)
    closest, dists = pairwise_distances_argmin_min(data, weights_flat)
    return -np.mean(dists)


def generate_data(n_samples=200, n_features=5, n_clusters=5):
    X, _ = make_blobs(n_samples=n_samples, n_features=n_features, centers=n_clusters, random_state=42)
    return X


def random_config():
    config = {}
    for key, value in PARAM_SPACE.items():
        if isinstance(value, tuple):
            config[key] = round(random.uniform(*value), 4)
        else:
            config[key] = random.choice(value)
    return config


def mutate(config):
    key = random.choice(list(PARAM_SPACE.keys()))
    if isinstance(PARAM_SPACE[key], tuple):
        config[key] = round(random.uniform(*PARAM_SPACE[key]), 4)
    else:
        config[key] = random.choice(PARAM_SPACE[key])
    return config


def get_uid(label):
    return hashlib.md5(label.encode()).hexdigest()[:8]


def log_to_csv(uid, label, score, duration, best_config, map_size):
    file_exists = os.path.isfile(RESULTS_FILE)
    with open(RESULTS_FILE, mode='a', newline='') as csvfile:
        fieldnames = ['uid', 'label', 'score', 'duration', 'map_size'] + list(best_config.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        row = {
            'uid': uid,
            'label': label,
            'score': score,
            'duration': duration,
            'map_size': map_size,
            **best_config
        }
        writer.writerow(row)


def optimize_som_run(args):
    dim, samples, multiplier = args
    data = generate_data(n_samples=samples, n_features=dim)
    total_epochs = int(samples * multiplier)
    label = f"{samples}x{dim}_epochs{multiplier:.1f}"
    uid = get_uid(label)
    log_message(f"[{uid}] --- Začátek testu: {label} ---")

    population_size = 10
    generations = 5
    population = [random_config() for _ in range(population_size)]
    best = None

    for gen in range(generations):
        scored = []
        for individual in population:
            for m, n in MAP_SIZES:
                log_message(f"[{uid}] Test config: {individual} | MAP: ({m}, {n})")
                start_time = time.time()
                som = KohonenSOM(
                    m=m, n=n, dim=data.shape[1],
                    learning_rate=individual["learning_rate"],
                    min_learning_rate=individual["min_learning_rate"],
                    radius=individual["radius"],
                    min_radius=individual["min_radius"],
                    num_batches=9,
                    min_batch_percent=individual["min_batch_percent"],
                    max_batch_percent=individual["max_batch_percent"],
                    lr_decay_type=individual["lr_decay_type"],
                    radius_decay_type=individual["radius_decay_type"],
                    batch_growth_type=individual["batch_growth_type"],
                    growth_g=individual["growth_g"],
                    random_seed=42
                )
                som.train(data[:total_epochs])
                score = evaluate_som_quality(som, data[:total_epochs])
                duration = time.time() - start_time
                log_message(f"[{uid}] DONE in {duration:.2f}s | Score: {score:.4f}\n")
                scored.append((score, deepcopy(individual), (m, n), duration))

        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0]

        top = [ind for _, ind, _, _ in scored[:population_size//2]]
        next_gen = top[:]
        while len(next_gen) < population_size:
            parent = random.choice(top)
            child = mutate(deepcopy(parent))
            next_gen.append(child)

        population = next_gen

    log_message(f"[{uid}] === FINAL BEST ===")
    log_message(f"[{uid}] Score: {best[0]:.4f}, Map: {best[2]}, Time: {best[3]:.2f}s")
    for k, v in best[1].items():
        log_message(f"[{uid}] {k}: {v}")
    log_message(f"[{uid}] --- Konec testu: {label} ---\n")

    log_to_csv(uid, label, best[0], best[3], best[1], best[2])


if __name__ == "__main__":
    uid_hash = 'evolutionary_som_optimizer2'
    set_uid_hash(uid_hash)

    combinations = [(dim, samples, mult) for dim in FEATURE_COUNTS for samples in SAMPLE_SIZES for mult in EPOCH_MULTIPLIERS]
    with Pool(processes=min(cpu_count(), len(combinations))) as pool:
        pool.map(optimize_som_run, combinations)
