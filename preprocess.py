"""
Module for preprocessing input data.

This module handles:
- Validation of the input CSV file
- Data normalization
- Detection and handling of missing values
- Splitting columns into categorical, numerical and text columns
- Grouping categorical columns by prefix
- Scaling values to the [0,1] range
"""

import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from utils import log_message
import os
import sys
import json

def validate_input_file(input_path: str, settings: dict) -> bool:
    """Validates the input CSV file.

    Args:
        input_path (str): Path to the input CSV file
        settings (dict): Project settings dictionary containing the list of required columns

    Returns:
        bool: True if the file is valid, False on error

    Note:
        Checks that the file exists and that all required columns are present.
    """
    try:
        # Load the file without data types
        df = pd.read_csv(input_path, delimiter=',', nrows=1)
    except Exception as e:
        print(f"Error loading file: {e}")
        return False

    # Check that all required columns exist
    missing_columns = [col for col in settings["selected_columns"] if col not in df.columns]
    if missing_columns:
        print(f"Missing required columns: {', '.join(missing_columns)}")
        return False

    return True


def normalize_data(input_path: str, settings: dict) -> str:
    """Normalizes the input data and prepares it for analysis.

    Args:
        input_path (str): Path to the input CSV file
        settings (dict): Project settings dictionary, updated in place with the detected column types

    Returns:
        str: Path to the normalized output file

    Note:
        The normalization process includes:
        1. Replacing missing values
        2. Splitting columns into types (categorical, numerical, text)
        3. Grouping categorical columns by prefix
        4. Scaling values to the [0,1] range
    """
    df = pd.read_csv(input_path, delimiter=',')
    # The primary ID only identifies records, so it is not used as a training feature
    primary_id = settings.get('primary_id')
    cols = [col for col in settings.get("selected_columns", df.columns.tolist()) if col != primary_id]
    data = df[cols].copy()

    # 1) Replace missing values (NaN)
    nan_replacement = settings.get("nan_replacement", {})
    for col, repl in nan_replacement.items():
        if col in data:
            data[col] = data[col].fillna(repl)

    # 2) Split columns into types
    processed = pd.DataFrame()
    categorical_column = []
    numerical_column = []
    string_column = []
    categorical_groups = {}
    
    for col in cols:
        series = data[col]
        
        # Special case for an ID column
        if col.startswith('id_') or col.endswith('_id'):
            processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
            categorical_column.append(col)
            log_message(f"Column '{col}': type categorical (ID column)")
            continue
            
        # Check the number of unique values for all columns
        n_uniques = series.nunique(dropna=True)
        
        if pd.api.types.is_numeric_dtype(series):
            if n_uniques <= 30:  # Numeric columns with few unique values are categorical
                processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
                categorical_column.append(col)
                log_message(f"Column '{col}': type categorical (numeric with {n_uniques} unique values)")
            else:
                # Numeric columns with more unique values are numerical
                num = pd.to_numeric(series, errors="coerce")
                num = num.fillna(nan_replacement.get(col, 0))
                processed[col] = num
                numerical_column.append(col)
                log_message(f"Column '{col}': type numeric ({n_uniques} unique values)")
        else:
            # Text columns
            if n_uniques <= 30:
                # Categorical columns: label encoding
                processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
                categorical_column.append(col)
                log_message(f"Column '{col}': type categorical (text with {n_uniques} unique values)")
                
                # Group by prefix
                parts = col.split('_')
                if len(parts) > 1:
                    prefix = parts[0]
                    if prefix not in categorical_groups:
                        categorical_groups[prefix] = []
                    categorical_groups[prefix].append(col)
            else:
                # Text columns with many unique values
                processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
                string_column.append(col)
                log_message(f"Column '{col}': type text ({n_uniques} unique values)")

    # 3) Scale all columns to the [0,1] range
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(processed.values)
    normalized_df = pd.DataFrame(scaled, columns=cols)

    # Save the normalized data
    output_path = os.path.join(os.path.dirname(input_path), "preprocess-" + os.path.basename(input_path))
    normalized_df.to_csv(output_path, index=False, sep=',')

    # Update project settings
    settings['categorical_column'] = categorical_column
    settings['numerical_column'] = numerical_column
    settings['string_column'] = string_column
    settings['categorical_groups'] = {k: v for k, v in categorical_groups.items() if len(v) > 1}

    return output_path