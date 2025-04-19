import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle, RegularPolygon
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import sys
import pandas as pd
from matplotlib.patches import Wedge, Circle, Patch
from collections import defaultdict, Counter
import json

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


def generate_hit_map_with_numbers(som, data: np.ndarray, output_file: str,
                     map_type: str = 'hex', cmap: str = 'Blues'):
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
    # print(vals)
    # sys.exit()  

    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(20,12))

    element_size = get_size_of_point(m,n,map_type)    
    sc = ax.scatter(X, Y, c=vals, s=element_size, cmap=cmap, marker='h' if map_type == 'hex' else 's')

    fig.colorbar(sc, ax=ax, label='Hits')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0.08)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')    
    plt.close()


def generate_hit_map(som, data: np.ndarray, output_file: str,
                     map_type: str = 'square', cmap: str = 'Blues'):
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

    fig.colorbar(sc, ax=ax, label='Hits')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0.08)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()


def generate_component_plane(som, component: int, output_file: str,
                             map_type: str = 'square', cmap: str = 'coolwarm',
                             column_name: str = None):
    """
    Komponentní rovina pro zvolenou dimenzi váhových vektorů.
    
    Args:
        som: Instance SOM
        component: Index dimenze
        output_file: Cesta k výstupnímu souboru
        map_type: Typ mapy ('square' nebo 'hex')
        cmap: Barevná mapa
        column_name: Název sloupce pro legendu
    """
    check_folder(output_file)
    m, n, dim = som.m, som.n, som.dim
    plane = som.weights.reshape(-1, dim)[:, component].reshape(m, n)
    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(20,12))

    element_size = get_size_of_point(m,n,map_type)    
    sc = ax.scatter(X, Y, c=plane.flatten(), s=element_size, cmap=cmap, marker='h' if map_type == 'hex' else 's')
    
    # Použijeme název sloupce pro legendu, pokud je zadán
    legend_label = column_name if column_name else f'Component {component}'
    fig.colorbar(sc, ax=ax, label=legend_label)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0.08)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()


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

def generate_distance_map(som, data: np.ndarray, output_file: str,
                          map_type: str = 'square', cmap: str = 'magma'):
    """
    Zobrazení průměrné kvantizační chyby na neuron.
    """
    check_folder(output_file)
    m, n = som.m, som.n
    dist_map = np.zeros((m, n))
    counts = np.zeros((m, n))
    for sample in data:
        i, j = som.find_bmu(sample)
        dist_map[i, j] += np.linalg.norm(sample - som.weights[i, j])
        counts[i, j] += 1
    with np.errstate(divide='ignore', invalid='ignore'):
        dist_map = np.divide(dist_map, counts, out=np.zeros_like(dist_map), where=counts>0)
    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(20,12))

    element_size = get_size_of_point(m,n,map_type)    
    sc = ax.scatter(X, Y, c=dist_map.flatten(), s=element_size, cmap=cmap, marker='h' if map_type == 'hex' else 's')
    fig.colorbar(sc, ax=ax, label='Průměrná kvantizační chyba')
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
                    theta2=angle - 360 * f,
                    facecolor=cmap(k0 / len(cat_keys)),
                    edgecolor='white'
                )
                ax.add_patch(wedge)
                angle -= 360 * f  

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
        point_size = 9500
    else:
        point_size = 280000 / (max(m,n) ** 2.3)
    return point_size




def generate_maps(som, data, preprocess_file,output_path, som_settings, settings):
    # parametr mřížky
    map_type = som_settings.get("map_type", "square")

    # 1) U‑Matrix
    generate_u_matrix(
        som,
        f"{output_path}/visualization/u_matrix_{map_type}.png",
        map_type=map_type
    )

    # 2) Hit‑mapa
    generate_hit_map(
        som,
        data,
        f"{output_path}/visualization/hit_map_{map_type}.png",
        map_type=map_type
    )

    generate_hit_map_with_numbers(
        som,
        data,
        f"{output_path}/visualization/hit_map_with_numbers_{map_type}.png",
        map_type=map_type
    )

    # 3) Component‑plane pro každou dimenzi
    # Načteme hlavičku CSV souboru pro názvy sloupců
    df = pd.read_csv(preprocess_file, delimiter=';', nrows=0)
    column_names = df.columns.tolist()
    
    for dim in range(som.dim):
        generate_component_plane(
            som,
            component=dim,
            output_file=f"{output_path}/visualization/component_{dim}_{map_type}.png",
            map_type=map_type,
            column_name=column_names[dim] if dim < len(column_names) else None
        )

    # 4) Cluster‑map
    clusters = json.load(open(f"{output_path}/clusters.json", encoding="utf-8"))
    generate_cluster_map(
        som,
        clusters,
        f"{output_path}/visualization/cluster_map_{map_type}.png",
        map_type=map_type
    )

    # 5) Distance‑map (prům. kvantizační chyba)
    generate_distance_map(
        som,
        data,
        f"{output_path}/visualization/distance_map_{map_type}.png",
        map_type=map_type
    )
  
    for column_name in settings['categorical_column']:
        plot_pie_map_from_json(
            som,
            f"{output_path}/pie_data_{column_name}.json",
            f"{output_path}/visualization/pie_map_{column_name}.png",
            map_type
        )