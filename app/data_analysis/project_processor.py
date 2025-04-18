import sys
from database import fetch_project, update_project_status
from preprocess import validate_input_file, normalize_data
from output import generate_heatmap
from utils import log_message, set_uid_hash, clear_files
from kohonen import KohonenSOM
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from matplotlib.lines import Line2D
from visualization import generate_u_matrix, generate_hit_map, generate_component_plane, generate_cluster_map, generate_distance_map 

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
        map_type=som_settings.get("map_type", "hex")
    ) 

    # Trénování SOM
    som.train(data)

    # Uložení vstupních dat
    np.savetxt(f"{output_path}/data.csv", data, delimiter=",")

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
    

    # načíst data
    df_orig = pd.read_csv(f"{output_path}/input.csv", delimiter=';')
    clusters = json.load(open(cluster_file))

    # spočítat statistiky podle zemí
    stats = compute_group_statistics(df_orig,
                                    settings["legend_column"],
                                    settings["analysis_columns"])

    # detekovat extrémy s prahovou hodnotou např. 2σ
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






    generate_maps(som, data, output_path, som_settings)










    # # 2) vykreslíme a uložíme statickou mapu
    # image_file = f"{output_path}/heatmap.jpg"
    # render_static_map(
    #     som,
    #     data,
    #     df_norm,
    #     image_file,
    #     legend_column="country",
    #     legend_title="název legendy"
    # )

    # Generování heatmapy
    generate_heatmap(som, data, output_path)

def extract_and_save_clusters(som, data: np.ndarray, df_orig, cluster_filename: str, primary_id: str):
    """Uloží JSON shluků: klíč 'i_j' → seznam primárních ID vzorků (jako čisté Python int)."""
    clusters = {}
    for idx, sample in enumerate(data):
        i, j = som.find_bmu(sample)
        key = f"{i}_{j}"
        # převést numpy.int64 na Python int
        pid_raw = df_orig.iloc[idx][primary_id]
        pid = int(pid_raw)
        clusters.setdefault(key, []).append(pid)
    with open(cluster_filename, 'w', encoding='utf-8') as f:
        json.dump(clusters, f, indent=4)        

def render_static_map(som, data: np.ndarray, df, output_image: str,
                      legend_column: str, legend_title: str, figsize=(12,12)):
    """Vykreslí body do JPG/PNG a uloží statickou mapu s legendou."""
    plt.figure(figsize=figsize)
    unique_vals = df[legend_column].unique()
    cmap = plt.get_cmap('hsv', len(unique_vals))
    colors = {v: cmap(i) for i, v in enumerate(unique_vals)}

    # vykreslení bodů
    for idx, sample in enumerate(data):
        i, j = som.find_bmu(sample)
        x = i + np.random.rand() * 0.9
        y = j + np.random.rand() * 0.9
        c = colors[df[legend_column].iloc[idx]]
        plt.plot(x, y, 'o', color=c, markersize=3)

    plt.xlim(0, som.m)
    plt.ylim(0, som.n)
    plt.grid(True)

    # legenda
    handles = [Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=colors[val], markersize=8, label=val)
               for val in unique_vals]
    plt.legend(handles=handles, title=legend_title, bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.savefig(output_image)
    plt.close()



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
        "som_height": 20,
        "som_width": 20,
        "map_type": "hex"
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


def generate_maps(som, data, output_path, settings):
    # parametr mřížky
    map_type = settings.get("map_type", "square")

    # 1) U‑Matrix
    generate_u_matrix(
        som,
        f"{output_path}/u_matrix_{map_type}.png",
        map_type=map_type
    )

    # 2) Hit‑mapa
    generate_hit_map(
        som,
        data,
        f"{output_path}/hit_map_{map_type}.png",
        map_type=map_type
    )

    # 3) Component‑plane pro každou dimenzi
    for dim in range(som.dim):
        generate_component_plane(
            som,
            component=dim,
            output_file=f"{output_path}/component_{dim}_{map_type}.png",
            map_type=map_type
        )

    # 4) Cluster‑map
    clusters = json.load(open(f"{output_path}/clusters.json", encoding="utf-8"))
    generate_cluster_map(
        som,
        clusters,
        f"{output_path}/cluster_map_{map_type}.png",
        map_type=map_type
    )

    # 5) Distance‑map (prům. kvantizační chyba)
    generate_distance_map(
        som,
        data,
        f"{output_path}/distance_map_{map_type}.png",
        map_type=map_type
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Použití: python3 project_processor.py <uid_hash>")
        sys.exit(1)    


    uid_hash = sys.argv[1]
    clear_files(uid_hash)
    process_project(uid_hash)
