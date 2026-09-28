"""
Main module for processing a data analysis run.

This module handles:
- Loading the run configuration (project and SOM settings) from a JSON file
- Validating and preprocessing input data
- Training the Kohonen SOM network
- Analysis and detection of extremes in the data
- Generating output files and visualizations
"""

import sys
from preprocess import validate_input_file, normalize_data
from utils import log_message, set_log_dir
from kohonen import KohonenSOM
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import shutil
from matplotlib.lines import Line2D
from visualization import generate_maps
import os
from collections import defaultdict, Counter, OrderedDict
import time
import psutil

def load_config(config_file: str) -> tuple[dict, dict]:
    """Loads project and SOM settings from a JSON configuration file.

    Args:
        config_file (str): Path to a JSON file with "project_settings" and "som_settings" keys

    Returns:
        tuple[dict, dict]: Project settings and SOM settings

    Raises:
        SystemExit: If the file cannot be loaded or is missing a required key
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config["project_settings"], config["som_settings"]
    except (OSError, KeyError, ValueError) as e:
        log_message(f"Error loading configuration {config_file}: {e}")
        print(f"Error loading configuration {config_file}: {e}")
        sys.exit(1)

def train_and_analyze_som(preprocess_file: str, som_settings: dict, project_settings: dict, output_path: str) -> None:
    """Trains the SOM network and generates the analysis outputs.

    Args:
        preprocess_file (str): Path to the preprocessed file
        som_settings (dict): SOM network settings
        project_settings (dict): Project settings
        output_path (str): Path for output files (with a trailing separator)

    Note:
        The function performs:
        1. SOM network training
        2. Saving input data and trained weights
        3. Extracting and saving clusters
        4. Generating data for pie charts
        5. Computing statistics and detecting extremes
        6. Generating visualizations
    """
    # Load the preprocessed data
    data = pd.read_csv(preprocess_file, delimiter=',').values

    # Initialize and train the SOM
    max_memory = psutil.virtual_memory().used // (1024 ** 2)  # in MB before training
    start_time = time.time()
    som = KohonenSOM(dim=data.shape[1], **som_settings)
    som.train(data)
    duration = time.time() - start_time
    # Measure memory after training
    max_memory = max(max_memory, psutil.virtual_memory().used // (1024 ** 2))
    # Save training metrics
    metrics = {
        "duration": duration,
        "total_weight_updates": som.total_weight_updates,
        "best_mqe": som.best_mqe,
        "epochs": getattr(som, 'epochs_run', None),
        "map_size": [som.m, som.n],
        "map_type": som.map_type,
        "max_memory_mb": max_memory
    }
    os.makedirs(f"{output_path}json", exist_ok=True)
    with open(f"{output_path}json/results.json", 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4)

    # Save input data and weights
    np.savetxt(f"{output_path}csv/data.csv", data, delimiter=",")
    np.save(f"{output_path}weights.npy", som.weights)

    # Load the original data
    df_orig = pd.read_csv(f"{output_path}csv/input.csv", delimiter=',')

    # Extract and save clusters
    cluster_file = f"{output_path}json/clusters.json"
    extract_and_save_clusters(som, data, df_orig, cluster_file, project_settings["primary_id"])

    # Generate data for pie charts
    extract_and_save_pie_data(som, data, df_orig, project_settings["categorical_column"], output_path)

    # Load data for analysis
    clusters = json.load(open(cluster_file))

    # Compute statistics and detect extremes
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

    # Generate pie charts for clusters
    extract_and_save_pie_data_from_clusters(
        df_orig,
        f"{output_path}json/clusters.json",
        project_settings['categorical_column'],
        f"{output_path}",
        project_settings['primary_id']
    )

    # Generate visualizations
    generate_maps(som, data, preprocess_file, output_path, som_settings, project_settings)

def extract_and_save_clusters(som, data: np.ndarray, df_orig: pd.DataFrame, cluster_filename: str, primary_id: str) -> None:
    """Extracts data clusters and saves them to a JSON file.

    Args:
        som: Trained SOM network
        data (np.ndarray): Preprocessed data
        df_orig (pd.DataFrame): Original data
        cluster_filename (str): Path to the output JSON file
        primary_id (str): Name of the primary key column

    Note:
        Creates JSON in the format: {"i_j": [pid1, pid2, ...], ...}
        where i_j are the neuron coordinates and pid are the samples' primary IDs
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

def process_project(input_file: str, config_file: str, output_dir: str) -> None:
    """Main function for processing a run.

    Args:
        input_file (str): Path to the input CSV file
        config_file (str): Path to the JSON configuration file
        output_dir (str): Directory for all outputs (created if missing)

    Note:
        Processing steps:
        1. Load the configuration and validate the input data
        2. Copy the input to {output_dir}/csv/input.csv
        3. Preprocess data
        4. Train and analyze the SOM
    """
    output_path = os.path.join(os.path.abspath(output_dir), "")
    os.makedirs(f"{output_path}csv", exist_ok=True)
    set_log_dir(output_path)

    log_message(f"Starting processing of {input_file} into {output_path}...")

    # Load the configuration and validate data
    project_settings, som_settings = load_config(config_file)

    if not validate_input_file(input_file, project_settings):
        log_message(f"Invalid input file {input_file}.")
        sys.exit(1)

    # The rest of the pipeline reads the input from the output directory
    local_input = f"{output_path}csv/input.csv"
    if os.path.abspath(input_file) != local_input:
        shutil.copyfile(input_file, local_input)

    # Preprocessing and analysis
    preprocess_file = normalize_data(local_input, project_settings)

    # Save project settings including the detected column types
    os.makedirs(f"{output_path}json", exist_ok=True)
    with open(f"{output_path}json/project_settings.json", 'w', encoding='utf-8') as f:
        json.dump(project_settings, f, indent=4, ensure_ascii=False)

    train_and_analyze_som(preprocess_file, som_settings, project_settings, output_path)

    log_message(f"Processing completed, outputs are in {output_path}")
    print(f"Done. Outputs are in {output_path}")

def compute_group_statistics(df_orig: pd.DataFrame,
                           segmentation_column: str,
                           selected_columns: list[str],
                           project_settings: dict) -> dict[str, dict[str, tuple[float, float]]]:
    """Computes statistics for data groups.

    Args:
        df_orig (pd.DataFrame): Original data
        segmentation_column (str): Column used for segmentation
        selected_columns (list[str]): List of columns selected for analysis
        project_settings (dict): Project settings

    Returns:
        dict: Statistics in the format {group: {column: (mean, standard deviation)}}
    """
    stats = {}

    # Select numerical columns
    if 'numerical_column' in project_settings:
        numeric_columns = [col for col in project_settings['numerical_column'] if col in df_orig.columns]
    else:
        numeric_columns = df_orig[selected_columns].select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        log_message("Warning: No numerical columns for analysis.")
        return stats

    # If segmentation_column is empty, use the first categorical column
    if not segmentation_column or segmentation_column not in df_orig.columns:
        if 'categorical_column' in project_settings and project_settings['categorical_column']:
            segmentation_column = project_settings['categorical_column'][0]
            log_message(f"Using the first categorical column '{segmentation_column}' for segmentation.")
        else:
            log_message("Warning: No column available for segmentation.")
            return stats

    # Compute statistics
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
    """Detects extreme values in the data.

    Args:
        df_orig (pd.DataFrame): Original data
        output_path (str): Path for output files
        clusters (dict): Cluster dictionary
        stats_by_group (dict): Per-group statistics
        threshold (float): Threshold for extreme detection
        segmentation_column (str): Column used for segmentation
        selected_columns (list[str]): List of columns selected for analysis
        primary_id (str): Name of the primary key column
        project_settings (dict): Project settings

    Returns:
        dict: Extreme values in the format {'by_group': {...}, 'by_cluster': {...}}
    """
    extremes = {'by_group': {}, 'by_cluster': {}}

    # Select numerical columns
    if 'numerical_column' in project_settings:
        numeric_columns = [col for col in project_settings['numerical_column'] if col in df_orig.columns]
    else:
        numeric_columns = df_orig[selected_columns].select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        log_message("Warning: No numerical columns for extreme detection.")
        return extremes

    # Detect extremes by group
    if segmentation_column and segmentation_column in df_orig.columns:
        unique_groups = df_orig[segmentation_column].unique()
        for group_val in unique_groups:
            mask = (df_orig[segmentation_column] == group_val)
            df_group = df_orig[mask]
            # Skip if the group is empty or contains only NaN values in numerical columns
            if df_group.shape[0] == 0 or df_group[numeric_columns].isnull().all().all():
                continue
            for col in numeric_columns:
                if col in stats_by_group[group_val]:
                    mean, std = stats_by_group[group_val][col]
                    if std and not np.isnan(std):
                        vals = df_group[col]
                        outliers = df_group.loc[np.abs(vals - mean) > threshold * std, primary_id]
                        if not outliers.empty:
                            # Convert numpy.int64 to a standard Python int
                            group_key = str(group_val) if isinstance(group_val, (np.integer, np.floating)) else group_val
                            extremes['by_group'][group_key] = [int(x) if isinstance(x, (np.integer, np.floating)) else x for x in outliers.tolist()]

    # Detect extremes by cluster
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
                    extremes['by_cluster'][cl_key] = [int(x) if isinstance(x, (np.integer, np.floating)) else x for x in outliers.tolist()]

    # Save results
    os.makedirs(f"{output_path}json", exist_ok=True)
    with open(f"{output_path}json/extremes.json", "w", encoding="utf-8") as f:
        json.dump(extremes, f, indent=4)

def extract_and_save_pie_data(som, data: np.ndarray, df_orig: pd.DataFrame, categorical_columns: list, output_dir: str) -> None:
    """Generates pie chart data per SOM neuron.

    Args:
        som: Trained SOM network
        data (np.ndarray): Preprocessed data
        df_orig (pd.DataFrame): Original data
        categorical_columns (list): List of categorical columns
        output_dir (str): Path for output files

    Note:
        For each categorical column, creates a JSON with category counts for each neuron.
        Format: {"categories": {1: "category1", ...}, "counts": {"i_j": {1: count, ...}}}
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
    """Generates pie chart data per cluster.

    Args:
        df_orig (pd.DataFrame): Original data
        cluster_file (str): Path to the clusters file
        categorical_columns (list): List of categorical columns
        output_dir (str): Path for output files
        primary_id (str): Name of the primary key column

    Note:
        For each categorical column, creates a JSON with category counts for each cluster.
        Format: {"categories": {"1": "category1", ...}, "counts": {"i_j": {"1": count, ...}}}
    """
    os.makedirs(output_dir, exist_ok=True)

    # Load clusters
    with open(cluster_file, 'r', encoding='utf-8') as f:
        clusters = json.load(f)

    # Map primary IDs to rows
    pid_to_row = {row[primary_id]: row for _, row in df_orig.iterrows()}

    for col in categorical_columns:
        # Build the category map
        cats = sorted(df_orig[col].dropna().unique().tolist())
        cat_map = OrderedDict((str(i+1), cats[i]) for i in range(len(cats)))

        # Count categories for each cluster
        counts_out = {}
        for pos, pid_list in clusters.items():
            ctr = Counter()
            for pid in pid_list:
                if pd.isna(pid) or pid not in pid_to_row:
                    continue
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