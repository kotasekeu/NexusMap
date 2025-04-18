import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle, RegularPolygon


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
    check_folder(output_file)
    m, n = som.m, som.n
    weights = som.weights.reshape(m, n, -1)
    u = np.zeros((m, n))
    for i in range(m):
        for j in range(n):
            neigh = []
            for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                ni, nj = i+di, j+dj
                if 0 <= ni < m and 0 <= nj < n:
                    neigh.append(np.linalg.norm(weights[i,j] - weights[ni,nj]))
            u[i,j] = np.mean(neigh) if neigh else 0
    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(8,8))
    sc = ax.scatter(X, Y, c=u.flatten(), s=500 if map_type=='hex' else 200, cmap=cmap)
    fig.colorbar(sc, ax=ax, label='U-Matrix distance')
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_file)
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
    fig, ax = plt.subplots(figsize=(8,8))
    sc = ax.scatter(X, Y, c=vals, s=vals*10 + 20, cmap=cmap)
    fig.colorbar(sc, ax=ax, label='Hits')
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def generate_component_plane(som, component: int, output_file: str,
                             map_type: str = 'square', cmap: str = 'coolwarm'):
    """
    Komponentní rovina pro zvolenou dimenzi váhových vektorů.
    """
    check_folder(output_file)
    m, n, dim = som.m, som.n, som.dim
    plane = som.weights.reshape(-1, dim)[:, component].reshape(m, n)
    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(8,8))
    sc = ax.scatter(X, Y, c=plane.flatten(), s=500 if map_type=='hex' else 200, cmap=cmap)
    fig.colorbar(sc, ax=ax, label=f'Component {component}')
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def generate_cluster_map(som, clusters: dict, output_file: str,
                         map_type: str = 'square', palette: list = None):
    """
    Přiřadí každé buňce barvu podle jejího clusteru.
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
    fig, ax = plt.subplots(figsize=(8,8))
    sc = ax.scatter(X, Y, c=labels.flatten(), s=500 if map_type=='hex' else 200, cmap=cmap)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_file)
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
    fig, ax = plt.subplots(figsize=(8,8))
    sc = ax.scatter(X, Y, c=dist_map.flatten(), s=500 if map_type=='hex' else 200, cmap=cmap)
    fig.colorbar(sc, ax=ax, label='Avg quantization error')
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def check_folder(output_file: str):
    folder = os.path.dirname(output_file)
    if not os.path.exists(folder):
        os.makedirs(folder)
