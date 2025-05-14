import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle, RegularPolygon, Wedge, Circle, Patch
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, ListedColormap
import sys
import pandas as pd
from collections import defaultdict, Counter
import json
from sklearn.metrics import pairwise_distances_argmin_min

def _grid_coordinates(m: int, n: int, map_type: str = 'square'):
    """
    Vygeneruje souřadnice center neuronů pro čtvercovou nebo hexa mřížku.
    Returns arrays X, Y of length m*n.
    """
    X, Y = [], []
    if map_type == 'square':
        for i in range(m):
            for j in range(n):
                X.append(j)
                Y.append(m - 1 - i)
    elif map_type == 'hex':
        dy = np.sqrt(3) / 2
        for i in range(m):
            for j in range(n):
                x = j + 0.5 * (i % 2)
                y = (m - 1 - i) * dy
                X.append(x)
                Y.append(y)
    else:
        raise ValueError("Unsupported map type: choose 'square' or 'hex'")
    return np.array(X), np.array(Y)

def _set_axes_limits(ax, m, n, map_type):
    X, Y = _grid_coordinates(m, n, map_type)
    if map_type == 'hex':
        # pro hexagon: šířka = 1, výška = √3/2*2 = √3 ≈1.732
        dx = 0.5
        dy = np.sqrt(3) / 2
    else:
        dx = dy = 0.5

    ax.set_xlim(X.min() - dx, X.max() + dx)
    ax.set_ylim(Y.min() - dy, Y.max() + dy)
    ax.margins(0)

def generate_u_matrix(som, output_file: str, map_type: str = 'square', cmap: str = 'viridis'):
    """
    Unified Distance Matrix: vykreslí průměrné vzdálenosti mezi sousedy neuronů.
    """
    # Kontroluje, zda existuje složka pro výstupní soubor
    check_folder(output_file)
    # Získá rozměry mřížky SOM
    m, n = som.m, som.n    
    # Přetváří váhy SOM do 3D pole pro snadnější přístup
    weights = som.weights.reshape(m, n, -1)
    # Inicializuje pole pro uložení průměrných vzdáleností
    u = np.zeros((m, n))
    # Iteruje přes všechny neurony v mřížce
    for i in range(m):
        for j in range(n):
            # Inicializuje seznam sousedních neuronů
            neigh = []
            # Iteruje přes všechny čtyři sousedy (nahoru, dolů, doleva, doprava)
            for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                # Vypočítává pozice sousedního neuronu
                ni, nj = i+di, j+dj
                # Kontroluje, zda sousední neuron leží uvnitř mřížky
                if 0 <= ni < m and 0 <= nj < n:
                    # Vypočítává vzdálenost mezi dvěma sousedními neurony
                    neigh.append(np.linalg.norm(weights[i,j] - weights[ni,nj]))
            # Vypočítává průměrnou vzdálenost od sousedních neuronů
            u[i,j] = np.mean(neigh) if neigh else 0
    # Generuje souřadnice center neuronů podle typu mřížky
    X, Y = _grid_coordinates(m, n, map_type)
    # Vytváří novou figuru a osy pro vykreslení
    fig, ax = plt.subplots(figsize=(20,12)) #20x12

    
    element_size = get_size_of_point(m,n,map_type)
    sc = ax.scatter(X, Y, c=u.flatten(), s=element_size, cmap=cmap, marker='h' if map_type == 'hex' else 's')   

    fig.colorbar(sc, ax=ax, label='U-Matrix distance')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0.08)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()


def generate_hit_map(som, data: np.ndarray, output_file: str,
                    map_type: str = 'square', cmap: str = 'Blues',
                    show_numbers: bool = False):
    """
    Heatmap návštěvnosti neuronů: velikost/barva bodu podle četnosti vzorků.
    """
    check_folder(output_file)
    m, n = som.m, som.n
    counts = {(i,j): 0 for i in range(m) for j in range(n)}
    for sample in data:
        i, j = som.find_bmu(sample)
        counts[(i,j)] += 1

    # hodnoty counts v pořadí i=0..m-1, j=0..n-1
    vals = np.array([counts[(i,j)] for i in range(m) for j in range(n)])

    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(20,12))

    element_size = get_size_of_point(m,n,map_type)    
    sc = ax.scatter(X, Y, c=vals, s=element_size, cmap=cmap, marker='h' if map_type == 'hex' else 's')

    if show_numbers:
        for i in range(m):
            for j in range(n):
                if counts[(i,j)] != 0:
                    ax.text(X[i*n+j], Y[i*n+j], str(counts[(i,j)]), ha='center', va='center', color='red')

    fig.colorbar(sc, ax=ax, label='Hits')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    plt.close()


def generate_component_plane(
    som,
    component: int,
    output_file: str,
    map_type: str = 'square',
    cmap: str = 'coolwarm',
    column_name: str = None,
    save_legend: bool = True,
    data_mean: float = None,
    data_std: float = None
):
    """
    Vykreslí komponentovou rovinu (váhový rozměr) do output_file (bez legendy) a
    pokud save_legend, vytvoří samostatný soubor legendy v téže složce.

    Args:
        som: Instance SOM s vlastnostmi m,n,dim a .weights
        component: Index dimenze váhového vektoru
        output_file: Cesta k výstupnímu obrázku komponentové mapy
        map_type: 'square' nebo 'hex'
        cmap: Název matplotlib colormap
        column_name: Popisek legendy (název atributu)
        save_legend: Zda generovat samostatný obrázek legendy
    """
    # Vytvoření cílové složky
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Načtení hodnot komponenty
    m, n, dim = som.m, som.n, som.dim
    vals = som.weights.reshape(-1, dim)[:, component]
    # nejprve vezmeme normalizované váhy
    vals_norm = som.weights.reshape(-1, dim)[:, component]
    if data_mean is not None and data_std is not None:
        vals = vals_norm * data_std + data_mean
    else:
        vals = vals_norm

    # Škálování barev podle reálných rozsahů
    vmin, vmax = vals.min(), vals.max()
    norm = Normalize(vmin=vmin, vmax=vmax)

    # 1) Vykreslení mapy bez legendy
    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(20, 12))
    sc = ax.scatter(
        X, Y,
        c=vals,
        s=get_size_of_point(m, n, map_type),
        cmap=cmap,
        norm=norm,
        marker='h' if map_type == 'hex' else 's'
    )
    _set_axes_limits(ax, som.m, som.n, map_type)

    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0)
    plt.tight_layout()
    # uložíme mapu…
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

    if save_legend:
        fig2 = plt.figure(figsize=(2, 12))
        cax = fig2.add_axes([0.35, 0.02, 0.3, 0.96])

        cbar = fig2.colorbar(
            plt.cm.ScalarMappable(norm=norm, cmap=cmap),
            cax=cax,
            orientation='vertical',
            extend='neither',
            extendfrac=0.0,
            label=column_name or f"Component {component}"
        )
        # váš blok po vytvoření cbar
        vmin, vmax = norm.vmin, norm.vmax
        orig_ticks = cbar.get_ticks()
        # vybereme jen ty, co skutečně leží mezi vmin a vmax
        middle_ticks = [t for t in orig_ticks if vmin < t < vmax]
        new_ticks = [vmin] + middle_ticks + [vmax]
        cbar.set_ticks(new_ticks)
        cbar.set_ticklabels([f"{t:.2f}" for t in new_ticks])

        # ručně omezíme výšku colorbaru na přesný rozsah
        cbar.ax.set_ylim(vmin, vmax)
        # popisek napravo
        cbar.ax.yaxis.set_label_position('right')
        cbar.ax.yaxis.tick_right()

        # schovej jen obrys ostatních stran, ale nech osu Y
        for spine in ['top', 'bottom', 'left']:
            cax.spines[spine].set_visible(False)
        cax.spines['right'].set_visible(False)  # popřípadě i tu
        # a nastav parametry tiků
        cax.tick_params(axis='y', which='both', length=5, labelsize=10)

        base, ext = os.path.splitext(output_file)
        legend_file = f"{base}_legend{ext}"
        plt.savefig(legend_file, bbox_inches='tight', pad_inches=0.02)
        plt.close(fig2)

def generate_cluster_map(som, clusters: dict, output_file: str,
                        map_type: str = 'square', palette: list = None):
    """
    Přiřadí každé buňce barvu podle jejího clusteru a zobrazí pozici každého prvku.
    """
    check_folder(output_file)
    m, n = som.m, som.n
    labels = np.full((m, n), -1, dtype=int)
    for idx, (key, _) in enumerate(clusters.items()):
        i, j = map(int, key.split('_'))
        if 0 <= i < m and 0 <= j < n:
            labels[i, j] = idx
    unique = np.unique(labels)
    if palette is None:
        cmap = plt.get_cmap('tab20', len(unique))
    else:
        cmap = plt.colors.ListedColormap(palette)
    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(20,12))

    element_size = get_size_of_point(m,n,map_type)
    sc = ax.scatter(X, Y, c=labels.flatten(), s=element_size, cmap=cmap, marker='h' if map_type == 'hex' else 's')
    for i in range(m):
        for j in range(n):
            ax.text(X[i*n+j], Y[i*n+j], f'({i},{j})', ha='center', va='center', size=6)
    # fig.colorbar(sc, ax=ax, label='Cluster')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0.08)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()

def plot_pie_map_from_json(
    som,
    json_file: str,
    output_file: str,
    map_type: str = 'hex',
    cmap: str = 'tab20b',
    radius: float = 0.4
):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cat_keys = sorted(data['categories'].keys(), key=int)
    cmap = plt.get_cmap(cmap)

    m, n = som.m, som.n
    X, Y = _grid_coordinates(m, n, map_type)

    fig, ax = plt.subplots(figsize=(20, 12))
    
    # Přidání základního rastru světle šedou barvou
    element_size = get_size_of_point(m,n,map_type)
    ax.scatter(X, Y, c='#FBFBFB', s=element_size, marker='h' if map_type == 'hex' else 's')
    
    for pos, cnts in data['counts'].items():
        i, j = map(int, pos.split('_'))
        idx = i * n + j
        x, y = X[idx], Y[idx]
        total = sum(cnts[k] for k in cat_keys)
        if total == 0:
            continue

        # spočítat podíly
        fracs = [cnts[k] / total for k in cat_keys]
        nonzero = [f for f in fracs if f > 0]

        if len(nonzero) == 1:
            # jediná kategorie → plný kruh
            k0 = fracs.index(1.0)
            circ = Circle(
                (x, y), radius,
                facecolor=cmap(k0 / len(cat_keys)),
                edgecolor='white'
            )
            ax.add_patch(circ)
        else:
            # více segmentů
            angle = 90
            for k0, f in enumerate(fracs):
                if f <= 0:
                    continue
                wedge = Wedge(
                    (x, y), radius,
                    theta1=angle,
                    theta2=angle + 360 * f,
                    facecolor=cmap(k0 / len(cat_keys)),
                    edgecolor='white'
                )
                ax.add_patch(wedge)
                angle += 360 * f

    cat_map  = data['categories']              
    cat_keys = sorted(cat_map.keys(), key=int)
    labels   = [cat_map[k] for k in cat_keys]    

    labels = [data['categories'][k] for k in cat_keys]
    handles = [
        Patch(facecolor=plt.get_cmap(cmap)(i/len(cat_keys)), label=labels[i])
        for i in range(len(labels))
    ]
    ax.legend(
        handles=handles,
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0
    )

    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0.08)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()


def check_folder(output_file: str):
    folder = os.path.dirname(output_file)
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_size_of_point(m,n,map_type):
    if map_type == 'hex':
        if m == 10:
            point_size = 9000
        elif m == 20:
            point_size = 2300
        elif m == 30:
            point_size = 900
        else:
            point_size = 2300  # výchozí hodnota pro hex
    else:
        if m == 10:
            point_size = 5500
        elif m == 20:
            point_size = 1100
        elif m == 30:
            point_size = 450
        else:
            point_size = 1100  # výchozí hodnota pro square
    return point_size

def generate_distance_map_from_error_map(som, neuron_error_map: np.ndarray, output_file: str,
                                    map_type: str = 'square', cmap: str = 'magma'):
    """
    Zobrazení průměrné kvantizační chyby na neuron z předpočítané mapy chyb.
    """
    check_folder(output_file)
    m, n = som.m, som.n
    
    # Normalizace hodnot do rozsahu [0,1]
    max_dist = np.max(neuron_error_map)
    if max_dist > 0:
        neuron_error_map = neuron_error_map / max_dist
    
    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(20,12))

    element_size = get_size_of_point(m,n,map_type)    
    sc = ax.scatter(X, Y, c=neuron_error_map.flatten(), s=element_size, cmap=cmap, marker='h' if map_type == 'hex' else 's')
    fig.colorbar(sc, ax=ax, label='Průměrná kvantizační chyba (compute_quantization_error)')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0.08)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()


def generate_maps(som, data, preprocess_file,output_path, som_settings, settings):
    # parametr mřížky
    map_type = som_settings.get("map_type", "square")

    # vytažení těch sloupců, co jste normalizovali
    df_all = pd.read_csv(f"{output_path}/csv/input.csv", delimiter=',')
    # vezmi jen numerické sloupce
    numeric_cols = settings['numerical_column']
    df_num = df_all[numeric_cols]

    # spočti průměry a odchylky jen těchto sloupců
    means = df_num.mean().values
    stds = df_num.std().values

    # 1) U‑Matrix
    generate_u_matrix(
        som,
        f"{output_path}/visualization/u-matrix_{map_type}.png",
        map_type=map_type
    )

    # 2) Hit‑mapa
    generate_hit_map(
        som,
        data,
        f"{output_path}/visualization/hit_map_{map_type}.png",
        map_type,
        'Blues',
        True
    )

    # 3) Component‑plane pro každou dimenzi
    # Načteme hlavičku CSV souboru pro názvy sloupců
    df = pd.read_csv(preprocess_file, delimiter=';', nrows=0)
    column_names = df.columns.tolist()
    
    # Rozdělení názvů sloupců podle čárek před cyklem
    column_names_list = column_names[0].split(',') if column_names else []
    
    for dim in range(som.dim):
        # Přeskočíme generování mapy pro primary_id sloupec
        if dim < len(column_names_list) and column_names_list[dim] == settings['primary_id']:
            continue

        col_name = column_names_list[dim] if dim < len(column_names_list) else None

        # jestli je tento sloupec numerický, najdi jeho index v numeric_cols
        if col_name in numeric_cols:
            idx = numeric_cols.index(col_name)
            data_mean = means[idx]
            data_std = stds[idx]
        else:
            data_mean = data_std = None

        generate_component_plane(
            som,
            component=dim,
            output_file=f"{output_path}/visualization/component_{dim}_{map_type}.png",
            map_type=map_type,
            cmap='coolwarm',
            column_name=col_name,
            save_legend=True,
            data_mean=data_mean,
            data_std=data_std
        )

    # 4) Cluster‑map
    clusters = json.load(open(f"{output_path}/json/clusters.json", encoding="utf-8"))
    generate_cluster_map(
        som,
        clusters,
        f"{output_path}/visualization/cluster_map_{map_type}.png",
        map_type=map_type
    )

    # 5) Distance‑map (prům. kvantizační chyba) - původní metoda
    codebook_vectors = som.weights.reshape(-1, som.dim)
    bmu_indexes = np.array([som.find_bmu(x)[0] * som.n + som.find_bmu(x)[1] for x in data])
    neuron_error_map, _ = som.compute_quantization_error(data, codebook_vectors, bmu_indexes, (som.m, som.n))
    generate_distance_map_from_error_map(
        som,
        neuron_error_map,
        f"{output_path}/visualization/distance_map_computed_{map_type}.png",
        map_type=map_type
    )

    # Vykreslení jednotlivých kategoriálních sloupců
    for column_name in settings['categorical_column']:
        if not any(column_name in group for group in settings.get('categorical_groups', {}).values()):
            plot_pie_map_from_json(
                som,
                f"{output_path}/json/pie_data_{column_name}.json",
                f"{output_path}/visualization/pie_map_{column_name}.png",
                map_type
            )
    
    # Vykreslení skupin kategoriálních sloupců
    for group_name, columns in settings.get('categorical_groups', {}).items():
        json_files = [f"{output_path}/json/pie_data_{col}.json" for col in columns]
        combined_data = {
            'categories': {},
            'counts': defaultdict(lambda: defaultdict(int))
        }
        
        # Spojení dat ze všech JSON souborů ve skupině
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Přidání kategorií s prefixem názvu sloupce
                column_name = os.path.basename(json_file).replace('pie_data_', '').replace('.json', '')
                for k, v in data['categories'].items():
                    # Zachováme původní číselné klíče, ale přidáme prefix pro rozlišení
                    combined_data['categories'][f"{column_name}_{k}"] = f"{column_name}: {v}"
                
                # Spojení počtů
                for pos, counts in data['counts'].items():
                    for k, v in counts.items():
                        combined_data['counts'][pos][f"{column_name}_{k}"] = v
        
        # Převedení dat do formátu, který očekává plot_pie_map_from_json
        formatted_data = {
            'categories': {},
            'counts': {}
        }
        
        # Seřazení kategorií podle číselné části klíče
        sorted_keys = sorted(combined_data['categories'].keys(), 
                           key=lambda x: int(x.split('_')[-1]))
        
        # Přečíslování kategorií od 1
        for new_key, old_key in enumerate(sorted_keys, 1):
            formatted_data['categories'][str(new_key)] = combined_data['categories'][old_key]
            
            # Přepočítání počtů pro nové klíče
            for pos in combined_data['counts']:
                if pos not in formatted_data['counts']:
                    formatted_data['counts'][pos] = {}
                if old_key in combined_data['counts'][pos]:
                    formatted_data['counts'][pos][str(new_key)] = combined_data['counts'][pos][old_key]
        
        # Uložení přeformátovaných dat do dočasného JSON souboru
        temp_json = f"{output_path}/json/temp_pie_data_{group_name}.json"
        with open(temp_json, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False)
        
        # Vykreslení pomocí existující metody
        plot_pie_map_from_json(
            som,
            temp_json,
            f"{output_path}/visualization/pie_map_group_{group_name}.png",
            map_type
        )