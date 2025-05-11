import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from utils import log_message
import os
import sys
from database import update_project_settings

def validate_input_file(input_path: str, settings: dict) -> bool:
    """Ověří správnost vstupního CSV souboru."""
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
    """Normalizuje data z input.csv do preprocess.csv podle vybraných sloupců a typu dat.
    Args:
        input_path: Cesta k vstupnímu CSV souboru
        settings: Slovník s nastavením pro normalizaci
        
    Returns:
        str: Cesta k vytvořenému výstupnímu souboru preprocess.csv
    """

    df = pd.read_csv(input_path, delimiter=',')
    cols = settings.get("selected_columns", df.columns.tolist())
    data = df[cols].copy()

    # 1) Náhrada NaN
    nan_replacement = settings.get("nan_replacement", {})
    for col, repl in nan_replacement.items():
        if col in data:
            data[col] = data[col].fillna(repl)

    # 2) Rozdělení na číselné vs. textové
    processed = pd.DataFrame()
    categorical_column = [];
    for col in cols:
        series = data[col]
        if pd.api.types.is_numeric_dtype(series):
            # číselné: převést + nahradit zbytky NaN
            num = pd.to_numeric(series, errors="coerce")
            num = num.fillna(nan_replacement.get(col, 0))
            processed[col] = num
        else:
            # textové: rozhodnout podle počtu unikátů
            n_uniques = series.nunique(dropna=True)
            if n_uniques <= 20:
                # kategorie: label‑encoding
                processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
                categorical_column.append(col)
            else:
                # volný text: též factorize (případně později zvláštní zpracování)
                processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
        log_message(f"Sloupec '{col}': typ {'číselný' if pd.api.types.is_numeric_dtype(data[col]) else 'kategoriální'} (unikátů {data[col].nunique(dropna=True)})")

    # 3) Škálování všech sloupců do [0,1]
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(processed.values)
    normalized_df = pd.DataFrame(scaled, columns=cols)

    # Vytvoření cesty pro výstupní soubor ve stejném adresáři
    output_path = os.path.join(os.path.dirname(input_path), "preprocess-" + os.path.basename(input_path))
    normalized_df.to_csv(output_path, index=False, sep=',')

    settings['categorical_column'] = categorical_column

    if uid_hash:
        update_project_settings(uid_hash, settings)

    return output_path