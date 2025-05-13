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
        settings = json.loads(project["project_settings"])
        return settings
    except (KeyError, ValueError) as e:
        log_message(f"Chyba při načítání nastavení projektu: {e}")
        sys.exit(1)

def load_som_settings(project: dict) -> dict:
    try:
        import json
        settings = json.loads(project["som_settings"])
        return settings
    except (KeyError, ValueError) as e:
        log_message(f"Chyba při načítání nastavení projektu: {e}")
        sys.exit(1)

#  doplnit budou zvlašť data pro csv soubor a pro mapu
#def load_som_settings(project: dict) -> dict:


def train_and_analyze_som(preprocess_file: str, som_settings: dict, project_settings: dict,output_path: str, uid_hash: str) -> None:
    """Trénuje SOM a generuje výstupy."""
    # Načtení předzpracovaných dat
    data = pd.read_csv(preprocess_file, delimiter=',').values

    # Inicializace SOM
    som = KohonenSOM(        
        dim=data.shape[1],
        **som_settings
    ) 

    # Trénování SOM
    som.train(data)

    # Uložení vstupních dat
    np.savetxt(f"{output_path}csv/data.csv", data, delimiter=",")

    # Uložení naučených vah
    np.save(f"{output_path}weights.npy", som.weights)


    # Načteme původní DataFrame s primárním klíčem
    df_orig = pd.read_csv(f"{output_path}csv/input.csv", delimiter=',')

    # Uložíme shluky
    cluster_file = f"{output_path}json/clusters.json"

    extract_and_save_clusters(
        som,
        data,
        df_orig,
        cluster_file,
        project_settings["primary_id"]
    )

    extract_and_save_pie_data(
        som,
        data,
        df_orig,
        project_settings["categorical_column"],
        output_dir=f"{output_path}"
    )

    # načíst data
    df_orig = pd.read_csv(f"{output_path}csv/input.csv", delimiter=',')
    clusters = json.load(open(cluster_file))

    # spočítat statistiky podle sloupců
    stats = compute_group_statistics(df_orig,
                                    project_settings["legend_column"],
                                    project_settings["analysis_columns"],
                                    project_settings)
    #detekovat extrémy s prahovou hodnotou např. 2σ
    detect_extremes(df_orig,
                            output_path,
                            clusters,
                            stats,
                            threshold=project_settings.get("std_threshold", 2),
                            legend_column=project_settings["legend_column"],
                            analysis_columns=project_settings["analysis_columns"],
                            primary_id=project_settings["primary_id"],
                            project_settings=project_settings)    


    extract_and_save_pie_data_from_clusters(
        df_orig,
        f"{output_path}json/clusters.json",
        project_settings['categorical_column'],
        f"{output_path}",
        project_settings['primary_id']
    )

    generate_maps(som, data, preprocess_file, output_path, som_settings, project_settings)


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
    
    os.makedirs(os.path.dirname(cluster_filename), exist_ok=True)

    with open(cluster_filename, 'w', encoding='utf-8') as f:
        json.dump(clusters, f, indent=4)        

# hlavní metoda co řídí všechno
def process_project(uid_hash: str) -> None:
    # Nastavení uid_hash pro logování
    set_uid_hash(uid_hash)
    output_path = f"/userfiles/{uid_hash}/"
    
    log_message(f"Spouštím zpracování projektu s UID {uid_hash}...")

    # Načtení detailů projektu
    project = get_project_detail(uid_hash)

    # Aktualizace stavu - běžící projektu v databázi
    update_project_status(uid_hash, 2)

    project_settings = load_project_settings(project)
    som_settings = load_som_settings(project)

    # Kontrola vstupního souboru
    input_file = f"{output_path}csv/input.csv"
    if not validate_input_file(input_file, project_settings):
        log_message(f"Neplatný vstupní soubor pro projekt {uid_hash}.")
        sys.exit(1)

    # Předzpracování dat
    preprocess_file = normalize_data(input_file, uid_hash, project_settings)

    train_and_analyze_som(preprocess_file, som_settings, project_settings,output_path, uid_hash)

    # Aktualizace stavu projektu v databázi
    update_project_status(uid_hash, 1)
    log_message(f"Zpracování projektu {uid_hash} bylo dokončeno.")


def compute_group_statistics(df_orig: pd.DataFrame,
                             group_by: str,
                             analysis_columns: list[str],
                             project_settings: dict) -> dict[str, dict[str, tuple[float, float]]]:    
    stats = {}
    
    # Použijeme pouze sloupce definované jako numerické v nastavení
    if 'numerical_column' in project_settings:
        numeric_columns = [col for col in project_settings['numerical_column'] if col in df_orig.columns]
    else:
        # Fallback na původní logiku, pokud numerical_column není definováno
        numeric_columns = df_orig[analysis_columns].select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        log_message("Varování: Žádné numerické sloupce pro analýzu.")
        return stats

    # Zajistíme, že group_by sloupec je v DataFrame
    if group_by not in df_orig.columns:
        log_message(f"Varování: Sloupec {group_by} nenalezen v datech.")
        return stats

    grouped = df_orig.groupby(group_by)[numeric_columns]
    agg = grouped.agg(['mean', 'std'])

    for key, row in agg.iterrows():
        stats[key] = {col: (row[(col, 'mean')], row[(col, 'std')]) for col in numeric_columns}
    return stats


def detect_extremes(df_orig: pd.DataFrame,
                    output_path: str,
                    clusters: dict[str, list[int]],
                    stats_by_group: dict[str, dict[str, tuple[float, float]]],
                    threshold: float,
                    legend_column: str,
                    analysis_columns: list[str],
                    primary_id: str,
                    project_settings: dict) -> dict:
    extremes = {'by_group': {}, 'by_cluster': {}}

    # Použijeme pouze sloupce definované jako numerické v nastavení
    if 'numerical_column' in project_settings:
        numeric_columns = [col for col in project_settings['numerical_column'] if col in df_orig.columns]
    else:
        # Fallback na původní logiku, pokud numerical_column není definováno
        numeric_columns = df_orig[analysis_columns].select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_columns:
        log_message("Varování: Žádné numerické sloupce pro detekci extrémů.")
        return extremes

    # Extrémy podle globálního členění
    for group_val, cols_stats in stats_by_group.items():
        mask = (df_orig[legend_column] == group_val)
        df_group = df_orig[mask]
        for col in numeric_columns:  # Použijeme pouze numerické sloupce
            if col in cols_stats:  # Kontrola, zda sloupec existuje ve statistikách
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
        for col in numeric_columns:  # Použijeme pouze numerické sloupce
            mean = df_cluster[col].mean()
            std = df_cluster[col].std()
            if std and not np.isnan(std):
                outliers = df_cluster.loc[np.abs(df_cluster[col] - mean) > threshold * std, primary_id]
                if not outliers.empty:
                    extremes['by_cluster'][cl_key] = outliers.astype(int).tolist()

    # uložit výsledek
    os.makedirs(f"{output_path}json", exist_ok=True)
    with open(f"{output_path}json/extremes.json", "w", encoding="utf-8") as f:
        json.dump(extremes, f, indent=4)

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
        fn = os.path.join(output_dir, f"json/pie_data_{col}.json")
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Použití: python3 project_processor.py <uid_hash>")
        sys.exit(1)    

    uid_hash = sys.argv[1]
    # clear_files(uid_hash)
    process_project(uid_hash)