import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def validate_input_file(input_path: str, settings: dict) -> bool:
    """Ověří správnost vstupního CSV souboru."""
    try:
        # Načtení souboru bez datových typů
        df = pd.read_csv(input_path, delimiter=';', nrows=1)
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
    """Normalizuje data z input.csv do preprocess.csv."""
    # Načtení dat z CSV souboru
    df = pd.read_csv(input_path, delimiter=';')

    # Vybrání relevantních sloupců
    data = df[settings["selected_columns"]].copy()

    # Ošetření NaN hodnot
    for col, replacement in settings["nan_replacement"].items():
        if col in data.columns:
            data[col] = data[col].fillna(replacement)

    # Převod kategoriálních dat na numerická
    for col in settings["categorical_columns"]:
        if col in data.columns:
            data[col] = pd.factorize(data[col])[0]

    # Normalizace dat
    scaler = MinMaxScaler()
    data_normalized = scaler.fit_transform(data)

    # Uložení normalizovaných dat do výstupního souboru
    normalized_df = pd.DataFrame(data_normalized, columns=settings["selected_columns"])
    normalized_df.to_csv(output_path, index=False, sep=';')

def transform_categorical_columns(data: list, settings: dict) -> list:
    """Převede kategoriální data na číselná podle nastavení."""
    pass