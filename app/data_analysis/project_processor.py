import sys
from database import fetch_project, update_project_status
from preprocess import validate_input_file, normalize_data
from utils import log_message, set_uid_hash, clear_files
from kohonen import KohonenSOM
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from matplotlib.lines import Line2D
from visualization import generate_maps
import os
from collections import defaultdict, Counter,OrderedDict

# vytahneme data z databaze podle uid
def get_project_detail(uid_hash: str) -> dict:
    project = fetch_project(uid_hash)
    if not project:
        log_message(f"Projekt s UID {uid_hash} nenalezen nebo analýza již byla dokončena.")
        sys.exit(1)
    return project

# vezmeme jen nastavení z detailu projektu
def load_project_settings(project: dict) -> dict:
    try:
        import json
        settings = json.loads(project["som_settings"])
        return settings
    except (KeyError, ValueError) as e:
        log_message(f"Chyba při načítání nastavení projektu: {e}")
        sys.exit(1)

#  doplnit budou zvlašť data pro csv soubor a pro mapu
#def load_som_settings(project: dict) -> dict:


def train_and_analyze_som(preprocess_file: str, som_settings: dict, settings: dict,output_path: str, uid_hash: str) -> None:
    """Trénuje SOM a generuje výstupy."""
    # Načtení předzpracovaných dat
    data = pd.read_csv(preprocess_file, delimiter=';').values

    # Inicializace SOM je zde kontrola existence konkrétních nastavení tak aby nedošlo k chybějícímu atributu
    som = KohonenSOM(
        m=som_settings["som_height"],
        n=som_settings["som_width"],
        dim=data.shape[1],
        radius=som_settings.get("initial_sigma", max(som_settings["som_height"], som_settings["som_width"]) / 2),
        learning_rate=som_settings.get("learning_rate", 0.9),
        min_learning_rate=som_settings.get("min_learning_rate", 0.1),
        num_batches=som_settings.get("num_batches", 10),
        min_batch_percent=som_settings.get("min_batch_percent", 0.1),
        max_batch_percent=som_settings.get("max_batch_percent", 5),
        lr_decay_type=som_settings.get("lr_decay_type", "linear-drop"),
        radius_decay_type=som_settings.get("radius_decay_type", "linear-drop"),
        batch_growth_type=som_settings.get("batch_growth_type", "exp-growth"),
        random_seed=som_settings.get("random_seed", 42),
        growth_g=som_settings.get("growth_g", 15.0),
        normalize_weights_flag=som_settings.get("normalize_weights_flag", False),
        epoch_multiplier=som_settings.get("epoch_multiplier", 1),
        map_type=som_settings.get("map_type", "hex")        
    ) 

    # Trénování SOM
    som.train(data)

    # Uložení vstupních dat
    np.savetxt(f"{output_path}/data.csv", data, delimiter=";")

    # Uložení naučených vah
    np.save(f"{output_path}/weights.npy", som.weights)


    # Načteme původní DataFrame s primárním klíčem
    df_orig = pd.read_csv(f"{output_path}/input.csv", delimiter=';')

    # Uložíme shluky
    cluster_file = f"{output_path}/clusters.json"

    extract_and_save_clusters(
        som,
        data,
        df_orig,
        cluster_file,
        settings["primary_id"]
    )

    extract_and_save_pie_data(
        som,
        data,
        df_orig,
        settings["categorical_column"],
        output_dir=f"{output_path}/"
    )

    # načíst data
    df_orig = pd.read_csv(f"{output_path}/input.csv", delimiter=';')
    clusters = json.load(open(cluster_file))

    # spočítat statistiky podle zemí
    stats = compute_group_statistics(df_orig,
                                    settings["legend_column"],
                                    settings["analysis_columns"])
    
    #detekovat extrémy s prahovou hodnotou např. 2σ
    extremes = detect_extremes(df_orig,
                            clusters,
                            stats,
                            threshold=settings.get("std_threshold", 2),
                            legend_column=settings["legend_column"],
                            analysis_columns=settings["analysis_columns"],
                            primary_id=settings["primary_id"])
    
    # uložit výsledek
    with open(f"{output_path}/extremes.json", "w", encoding="utf-8") as f:
        json.dump(extremes, f, indent=4)


    # extract_and_save_pie_data_from_clusters(
    #     df_orig,
    #     f"{output_path}/clusters.json",
    #     settings['categorical_column'],
    #     f"{output_path}/",
    #     settings['primary_id']
    # )

    generate_maps(som, data, preprocess_file, output_path, som_settings, settings)


def extract_and_save_clusters(som, data: np.ndarray, df_orig, cluster_filename: str, primary_id: str):
    """Uloží JSON shluků: klíč 'i_j' → seznam primárních ID vzorků (jako čisté Python int)."""
    clusters = {}
    for idx, sample in enumerate(data):
        i, j = som.find_bmu(sample)
        key = f"{i}_{j}"
        
        # převést numpy.int64 na Python int
        pid_raw = df_orig.iloc[idx][primary_id]  # použije správný index
        pid = int(pid_raw)
        clusters.setdefault(key, []).append(pid)
    with open(cluster_filename, 'w', encoding='utf-8') as f:
        json.dump(clusters, f, indent=4)        

# hlavní metoda co řídí všechno
def process_project(uid_hash: str) -> None:
    # Nastavení uid_hash pro logování
    set_uid_hash(uid_hash)
    
    log_message(f"Spouštím zpracování projektu s UID {uid_hash}...")
    # # Aktualizace stavu - běžící projektu v databázi
    # update_project_status(uid_hash, 2)

    # Načtení detailů projektu
    project = get_project_detail(uid_hash)
    settings = load_project_settings(project)

    # Kontrola vstupního souboru
    input_file = f"/userfiles/{uid_hash}/input.csv"
    if not validate_input_file(input_file, settings):
        log_message(f"Neplatný vstupní soubor pro projekt {uid_hash}.")
        sys.exit(1)

    # Předzpracování dat
    preprocess_file = f"/userfiles/{uid_hash}/preprocess.csv"
    normalize_data(input_file, preprocess_file, settings)

    output_path = f"/userfiles/{uid_hash}/"
    kohonen_settings = {
        "som_height": 9,
        "som_width": 9,
        "map_type": "square",
        "normalize_weights_flag": True        
    }    

    train_and_analyze_som(preprocess_file, kohonen_settings, settings,output_path, uid_hash)

    # Aktualizace stavu projektu v databázi
    # update_project_status(uid_hash, 1) odkomentovat, v prubehu testovani by se nepoustela analyza znovu
    log_message(f"Zpracování projektu {uid_hash} bylo dokončeno.")



def compute_group_statistics(df_orig: pd.DataFrame,
                             group_by: str,
                             analysis_columns: list[str]) -> dict[str, dict[str, tuple[float, float]]]:
    """
    Pro každý unikátní klíč ve sloupci group_by spočítá průměr a směrodatnou odchylku pro zadané sloupce.
    Vrací slovník: { group_value: { col: (mean, std) } }.
    """
    stats = {}
    grouped = df_orig.groupby(group_by)[analysis_columns]    
    agg = grouped.agg(['mean', 'std'])
    for key, row in agg.iterrows():
        stats[key] = {col: (row[(col, 'mean')], row[(col, 'std')]) for col in analysis_columns}
    return stats


def detect_extremes(df_orig: pd.DataFrame,
                    clusters: dict[str, list[int]],
                    stats_by_group: dict[str, dict[str, tuple[float, float]]],
                    threshold: float,
                    legend_column: str,
                    analysis_columns: list[str],
                    primary_id: str) -> dict:
    """
    Detekuje extrémní vzorky podle globálních skupin (legend_column) a uvnitř clusterů.
    Vrací slovník:
      {
        'by_group': { group_value: [primary_id, ...], ... },
        'by_cluster': { cluster_key: [primary_id, ...], ... }
      }
    """
    extremes = {'by_group': {}, 'by_cluster': {}}

    # Extrémy podle globálního členění
    for group_val, cols_stats in stats_by_group.items():
        mask = (df_orig[legend_column] == group_val)
        df_group = df_orig[mask]
        for col in analysis_columns:
            mean, std = cols_stats[col]
            if std and not np.isnan(std):
                vals = df_group[col]
                outliers = df_group.loc[np.abs(vals - mean) > threshold * std, primary_id]
                if not outliers.empty:
                    extremes['by_group'][group_val] = outliers.astype(int).tolist()

    # Extrémy podle clusteru
    for cl_key, pid_list in clusters.items():
        if not pid_list:
            continue
        df_cluster = df_orig[df_orig[primary_id].isin(pid_list)]
        for col in analysis_columns:
            mean = df_cluster[col].mean()
            std = df_cluster[col].std()
            if std and not np.isnan(std):
                outliers = df_cluster.loc[np.abs(df_cluster[col] - mean) > threshold * std, primary_id]
                if not outliers.empty:
                    extremes['by_cluster'][cl_key] = outliers.astype(int).tolist()

    return extremes

def extract_and_save_pie_data(
    som,
    data: np.ndarray,
    df_orig,
    categorical_columns: list,
    output_dir: str
):
    """
    Pro každý sloupec v categorical_columns:
      1) načte hodnoty z df_orig,
      2) spočítá pro každý neuron (i,j) počty jednotlivých kategorií,
      3) uloží JSON: seznam kategorií + counts per 'i_j'.
    """
    os.makedirs(output_dir, exist_ok=True)
    m, n = som.m, som.n

    for col in categorical_columns:
        # unikátní kategorie v původním DF (př.: ['setosa','versicolor','virginica'])
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


def extract_and_save_pie_data_from_clusters(
    df_orig,
    cluster_file: str,
    categorical_columns: list,
    output_dir: str,
    primary_id: str
):
    """
    Pro každý sloupec v categorical_columns:
      • Načte clusters.json: { "i_j": [pid1,pid2,…], … }
      • Pro každý klastr spočítá Counter kategorií podle df_orig[primary_id]→df_orig[col]
      • Uloží JSON s číselnými klíči kategorií i counts
    """
    os.makedirs(output_dir, exist_ok=True)
    # nahrání klastrů
    with open(cluster_file, 'r', encoding='utf-8') as f:
        clusters = json.load(f)

    # pro každou kategorii připravíme mapu pid→label
    pid_to_row = {int(row[primary_id]): row for _, row in df_orig.iterrows()}

    for col in categorical_columns:
        # zjistíme unikátní kategorie a vytvarujeme mapu 1→název
        cats = sorted(df_orig[col].dropna().unique().tolist())
        cat_map = OrderedDict((str(i+1), cats[i]) for i in range(len(cats)))

        counts_out = {}
        for pos, pid_list in clusters.items():
            ctr = Counter()
            for pid in pid_list:
                label = pid_to_row[pid][col]
                ctr[label] += 1
            # převedeme na číselné klíče
            counts_out[pos] = {
                str(i+1): ctr.get(cats[i], 0)
                for i in range(len(cats))
            }

        out = {
            "categories": cat_map,
            "counts": counts_out
        }
        fn = os.path.join(output_dir, f"pie_data_{col}.json")
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Použití: python3 project_processor.py <uid_hash>")
        sys.exit(1)    


    uid_hash = sys.argv[1]
    clear_files(uid_hash)
    process_project(uid_hash)
