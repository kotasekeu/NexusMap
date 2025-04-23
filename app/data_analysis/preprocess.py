import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from utils import log_message

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


def normalize_data(input_path: str, output_path: str, settings: dict) -> None:
    """Normalizuje data z input.csv do preprocess.csv podle vybraných sloupců a typu dat."""
    df = pd.read_csv(input_path, delimiter=',')
    cols = settings["selected_columns"]
    data = df[cols].copy()

    # 1) Náhrada NaN
    for col, repl in settings.get("nan_replacement", {}).items():
        if col in data:
            data[col] = data[col].fillna(repl)

    # 2) Rozdělení na číselné vs. textové
    processed = pd.DataFrame()
    for col in cols:
        series = data[col]
        if pd.api.types.is_numeric_dtype(series):
            # číselné: převést + nahradit zbytky NaN
            num = pd.to_numeric(series, errors="coerce")
            num = num.fillna(settings.get("nan_replacement", {}).get(col, 0))
            processed[col] = num
        else:
            # textové: rozhodnout podle počtu unikátů
            n_uniques = series.nunique(dropna=True)
            if n_uniques <= 20:
                # kategorie: label‑encoding
                processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
            else:
                # volný text: též factorize (případně později zvláštní zpracování)
                processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
        log_message(f"Sloupec '{col}': typ {'číselný' if pd.api.types.is_numeric_dtype(data[col]) else 'kategoriální'} (unikátů {data[col].nunique(dropna=True)})")

    # 3) Škálování všech sloupců do [0,1]
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(processed.values)
    normalized_df = pd.DataFrame(scaled, columns=cols)

    normalized_df.to_csv(output_path, index=False, sep=',')