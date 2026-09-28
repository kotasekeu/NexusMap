"""
Evolutionary optimization of Kohonen self-organizing map (SOM) parameters.

This module implements an evolutionary algorithm for optimizing SOM parameters.
The goal is to find a parameter configuration that minimizes the quantization error
while keeping the computation time reasonable.

Main features:
- Parallel evaluation of configurations
- Automatic result backups
- Support for custom input data
- Export of results to CSV and TXT
"""

import random
import copy
from os.path import exists
import os
import csv
import hashlib
import time
import shutil
from datetime import datetime
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.metrics import pairwise_distances_argmin_min
from multiprocessing import Pool, cpu_count
import sys
import pandas as pd
import argparse
import json
import psutil

# Make the project root importable when the script is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evolutionary_som_config import CONFIG
from kohonen import KohonenSOM
from preprocess import normalize_data

# Weights for the multi-criteria fitness function
W_ERROR = 0.7  # weight of the quantization error
W_TIME = 0.3   # weight of the computation time

# Global variables
INPUT_FILE = None
NORMALIZED_DATA = None
WORKING_DIR = None

def get_working_directory(input_file: str = None) -> str:
    """
    Determines the working directory for storing results.

    Args:
        input_file: Path to the input file (optional)

    Returns:
        str: Path to the working directory with the created reports folder
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
    Loads the configuration from a JSON file or uses the default CONFIG.

    Args:
        config_path: Path to the JSON configuration file

    Returns:
        dict: Loaded configuration

    Raises:
        SystemExit: If the file does not exist or is not valid JSON
    """
    if config_path:
        if not os.path.exists(config_path):
            print(f"Error: Configuration file {config_path} does not exist.")
            sys.exit(1)
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Configuration file {config_path} is not valid JSON: {e}")
            sys.exit(1)
            
        return config
    return CONFIG

def crossover(parent1: dict, parent2: dict, param_space: dict) -> dict:
    """
    Uniform crossover of two parent configurations.

    Args:
        parent1: First parent configuration
        parent2: Second parent configuration
        param_space: Parameter space with possible values

    Returns:
        dict: New configuration created by crossover
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
    Creates a random configuration from the parameter space.

    Args:
        param_space: Dictionary with possible values for each parameter

    Returns:
        dict: Randomly generated configuration
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
    Mutates one random value in the configuration.

    Args:
        config: Configuration to mutate
        param_space: Parameter space with possible values

    Returns:
        dict: Mutated configuration
    """
    key = random.choice(list(param_space.keys()))
    if isinstance(param_space[key], list):
        config[key] = random.choice(param_space[key])
    return config

def run_evolution(param_space: dict) -> None:
    """
    Main loop of the evolutionary algorithm.

    Args:
        param_space: Parameter space to optimize
    """
    try:
        population = [random_config(param_space) for _ in range(POPULATION_SIZE)]
        for gen in range(GENERATIONS):
            print(f"Generation {gen + 1}/{GENERATIONS}")

            with Pool(processes=min(12, cpu_count(), POPULATION_SIZE)) as pool:
                try:
                    args = [(ind, i, gen) for i, ind in enumerate(population)]
                    results = []
                    for i, arg in enumerate(args):
                        try:
                            result = pool.apply_async(evaluate_individual, arg)
                            results.append(result)
                        except Exception as e:
                            print(f"Error initializing process {i}: {e}")

                    scored = []
                    for i, r in enumerate(results):
                        try:
                            scored.append(r.get(timeout=3600))
                        except Exception as e:
                            print(f"[ERROR] Individual {i} failed: {e}")
                except Exception as e:
                    print(f"Error evaluating population: {str(e)}")
                    pool.terminate()
                    pool.join()
                    raise e

            # Normalization and fitness computation
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

            # Selection and reproduction
            scored_f.sort(key=lambda x: x[0], reverse=True)
            best = scored_f[0]
            print(f" Best QE: {best[1]:.6f} | Time: {best[3]:.2f}s | Fitness: {best[0]:.4f}")

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
        print("\nStopping the evolutionary algorithm...")
        return
    except Exception as e:
        print(f"\nError running the evolutionary algorithm: {str(e)}")
        return

    print(f"Generation {gen + 1} – successful: {len(scored)}/{POPULATION_SIZE}")

def get_uid(config: dict) -> str:
    """
    Creates a unique identifier for the configuration.

    Args:
        config: Configuration to identify

    Returns:
        str: MD5 hash of the configuration (8 characters)
    """    
    config_str = str(sorted(config.items()))
    return hashlib.md5(config_str.encode()).hexdigest()

def log_message(uid: str, message: str) -> None:
    """
    Writes a message to the log.

    Args:
        uid: Configuration identifier or "SYSTEM"
        message: Message text
    """    
    log_path = os.path.join(WORKING_DIR, "log.txt")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{now}] [{uid}] {message}\n")

def log_result_to_csv(uid: str, config: dict, score: float, duration: float, total_weight_updates: int) -> None:
    """
    Writes configuration results to CSV.

    Args:
        uid: Configuration identifier
        config: Configuration parameters
        score: Quantization error
        duration: Computation time in seconds
        total_weight_updates: Total number of weight updates
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
    Logs evaluation progress.

    Args:
        current: Number of completed configurations
        total: Total number of configurations
    """    
    progress_path = os.path.join(WORKING_DIR, "progress.log")
    with open(progress_path, "a") as f:
        f.write(f"{current}/{total} completed\n")

def get_or_generate_data(sample_size: int, input_dim: int) -> np.ndarray:
    """
    Returns a dataset of the requested size.

    Args:
        sample_size: Number of samples
        input_dim: Number of dimensions

    Returns:
        np.ndarray: Data of shape (sample_size, input_dim)
    """
    file_name = f"data_{sample_size}x{input_dim}.npy"
    file_path = os.path.join(WORKING_DIR, file_name)

    if os.path.exists(file_path):
        return np.load(file_path)

    data, _ = make_blobs(n_samples=sample_size, n_features=input_dim, centers=5, random_state=CONFIG["random_seed"])
    np.save(file_path, data)
    log_message("SYSTEM", f"Generated new data: {file_name}")
    return data

def log_status_to_csv(uid: str, population_id: int, generation: int, status: str, 
                     start_time: str = None, end_time: str = None) -> None:
    """
    Logs the configuration status to CSV.

    Args:
        uid: Configuration identifier
        population_id: Population ID
        generation: Generation number
        status: Status (started/completed/failed)
        start_time: Start time
        end_time: End time
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
    Saves the best configuration of the generation.

    Args:
        uid: Configuration identifier
        config: Configuration parameters
        score: Quantization error
        duration: Computation time
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
    Loads and normalizes data from CSV.

    Args:
        input_file: Path to the CSV file

    Returns:
        np.ndarray: Normalized data
    """
    global NORMALIZED_DATA
    
    if NORMALIZED_DATA is not None:
        return NORMALIZED_DATA

    preprocess_file = os.path.join(os.path.dirname(input_file), "preprocess-" + os.path.basename(input_file))
    if not os.path.exists(preprocess_file):
        preprocess_file = normalize_data(input_file, {})
    NORMALIZED_DATA = pd.read_csv(preprocess_file, delimiter=',').values
    log_message("SYSTEM", f"Loaded and normalized data from external file: {input_file}")
    return NORMALIZED_DATA

def extract_uid_from_path(file_path: str) -> str:
    """
    Extracts the UID from a file path.

    Args:
        file_path: File path

    Returns:
        str: Extracted UID or None
    """
    parts = file_path.split('/')
    for part in parts:
        if part.startswith('nxmpp'):
            return part
    return None

def evaluate_individual(ind: dict, population_id: int, generation: int) -> tuple:
    """
    Evaluates a single SOM configuration.

    Args:
        ind: Configuration to evaluate
        population_id: Population ID
        generation: Generation number

    Returns:
        tuple: (quantization error, configuration, computation time, number of updates)

    Raises:
        Exception: On evaluation error
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
        log_message(uid, f"Configuration evaluated – quantization error: {som.best_mqe:.8f}, time: {duration:.2f}s")
        log_result_to_csv(uid, ind, som.best_mqe, duration, som.total_weight_updates)
        
        log_status_to_csv(uid, population_id, generation, "completed", 
                         datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S"),
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return (som.best_mqe, copy.deepcopy(ind), duration, som.total_weight_updates)
        
    except Exception as e:
        log_status_to_csv(uid, population_id, generation, "failed", 
                         datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S"),
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        log_message(uid, f"Evaluation error: {str(e)}")
        raise e

def analyze_results() -> None:
    """
    Analyzes the evolutionary algorithm results and creates files with the best configurations.
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
    
    log_message("SYSTEM", "Results analysis completed - created best_configurations_full.csv and summary.txt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evolutionary optimization of the Kohonen network')
    parser.add_argument('-i', '--input', help='Path to the input CSV file')
    parser.add_argument('-c', '--config', help='Path to a custom configuration file')
    args = parser.parse_args()

    config = load_config(args.config)

    if args.input:
        if not os.path.exists(args.input):
            print(f"Error: Input file {args.input} does not exist.")
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