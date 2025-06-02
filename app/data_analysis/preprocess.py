"""
Modul pro předzpracování vstupních dat.

Tento modul zajišťuje:
- Validaci vstupního CSV souboru
- Normalizaci dat
- Detekci a zpracování chybějících hodnot
- Rozdělení sloupců na kategorické, numerické a textové
- Seskupení kategoriálních sloupců podle prefixu
- Škálování hodnot do rozsahu [0,1]
"""

import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from utils import log_message
import os
import sys
from database import update_project_settings
import json

def validate_input_file(input_path: str, settings: dict) -> bool:
    """Ověří správnost vstupního CSV souboru.
    
    Args:
        input_path (str): Cesta k vstupnímu CSV souboru
        settings (dict): Slovník s nastavením projektu obsahující seznam požadovaných sloupců
        
    Returns:
        bool: True pokud je soubor validní, False v případě chyby
        
    Note:
        Kontroluje existenci souboru a přítomnost všech požadovaných sloupců.
    """
    try:
        # Načtení souboru bez datových typů
        df = pd.read_csv(input_path, delimiter=',', nrows=1)
    except Exception as e:
        print(f"Chyba při načítání souboru: {e}")
        return False

    # Ověření, zda všechny požadované sloupce existují
    missing_columns = [col for col in settings["selected_columns"] if col not in df.columns]
    if missing_columns:
        print(f"Chybí požadované sloupce: {', '.join(missing_columns)}")
        return False

    return True


def normalize_data(input_path: str, uid_hash: str, settings: dict) -> str:
    """Normalizuje vstupní data a připraví je pro analýzu.
    
    Args:
        input_path (str): Cesta k vstupnímu CSV souboru
        uid_hash (str): Unikátní identifikátor projektu
        settings (dict): Slovník s nastavením projektu
        
    Returns:
        str: Cesta k normalizovanému výstupnímu souboru
        
    Note:
        Proces normalizace zahrnuje:
        1. Náhrada chybějících hodnot
        2. Rozdělení sloupců na typy (kategorické, numerické, textové)
        3. Seskupení kategoriálních sloupců podle prefixu
        4. Škálování hodnot do rozsahu [0,1]
    """
    df = pd.read_csv(input_path, delimiter=',')
    cols = settings.get("selected_columns", df.columns.tolist())
    data = df[cols].copy()

    # 1) Náhrada chybějících hodnot (NaN)
    nan_replacement = settings.get("nan_replacement", {})
    for col, repl in nan_replacement.items():
        if col in data:
            data[col] = data[col].fillna(repl)

    # 2) Rozdělení sloupců na typy
    processed = pd.DataFrame()
    categorical_column = []
    numerical_column = []
    string_column = []
    categorical_groups = {}
    
    for col in cols:
        series = data[col]
        
        # Speciální případ pro ID sloupec
        if col.startswith('id_') or col.endswith('_id'):
            processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
            categorical_column.append(col)
            log_message(f"Sloupec '{col}': typ kategoriální (ID sloupec)")
            continue
            
        # Kontrola počtu unikátních hodnot pro všechny sloupce
        n_uniques = series.nunique(dropna=True)
        
        if pd.api.types.is_numeric_dtype(series):
            if n_uniques <= 30:  # Číselné sloupce s malým počtem unikátních hodnot jsou kategorické
                processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
                categorical_column.append(col)
                log_message(f"Sloupec '{col}': typ kategoriální (číselný s {n_uniques} unikáty)")
            else:
                # Číselné sloupce s více unikáty jsou numerické
                num = pd.to_numeric(series, errors="coerce")
                num = num.fillna(nan_replacement.get(col, 0))
                processed[col] = num
                numerical_column.append(col)
                log_message(f"Sloupec '{col}': typ číselný ({n_uniques} unikátů)")
        else:
            # Textové sloupce
            if n_uniques <= 30:
                # Kategorické sloupce: label-encoding
                processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
                categorical_column.append(col)
                log_message(f"Sloupec '{col}': typ kategoriální (textový s {n_uniques} unikáty)")
                
                # Seskupení podle prefixu
                parts = col.split('_')
                if len(parts) > 1:
                    prefix = parts[0]
                    if prefix not in categorical_groups:
                        categorical_groups[prefix] = []
                    categorical_groups[prefix].append(col)
            else:
                # Textové sloupce s mnoha unikáty
                processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
                string_column.append(col)
                log_message(f"Sloupec '{col}': typ textový ({n_uniques} unikátů)")

    # Odstranění primary_id z numerických a kategorických sloupců
    primary_id = settings.get('primary_id')
    if primary_id in numerical_column:
        numerical_column = [col for col in numerical_column if col != primary_id]
    if primary_id in categorical_column:
        categorical_column = [col for col in categorical_column if col != primary_id]

    # 3) Škálování všech sloupců do rozsahu [0,1]
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(processed.values)
    normalized_df = pd.DataFrame(scaled, columns=cols)

    # Uložení normalizovaných dat
    output_path = os.path.join(os.path.dirname(input_path), "preprocess-" + os.path.basename(input_path))
    normalized_df.to_csv(output_path, index=False, sep=',')

    # Aktualizace nastavení projektu
    settings['categorical_column'] = categorical_column
    settings['numerical_column'] = numerical_column
    settings['string_column'] = string_column
    settings['categorical_groups'] = {k: v for k, v in categorical_groups.items() if len(v) > 1}

    if uid_hash:
        update_project_settings(uid_hash, settings)

    return output_path