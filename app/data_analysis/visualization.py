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
from scipy.stats import gaussian_kde
from scipy.spatial.distance import cdist



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
    
    # Výpočet kvantizační chyby pro každý neuron
    dist_map = np.zeros((m, n))
    counts = np.zeros((m, n))
    
    for sample in data:
        i, j = som.find_bmu(sample)
        dist_map[i, j] += np.linalg.norm(sample - som.weights[i, j])
        counts[i, j] += 1
    
    # Průměrná kvantizační chyba pro každý neuron
    with np.errstate(divide='ignore', invalid='ignore'):
        dist_map = np.divide(dist_map, counts, out=np.zeros_like(dist_map), where=counts>0)
    
    # Normalizace hodnot do rozsahu [0,1]
    max_dist = np.max(dist_map)
    if max_dist > 0:
        dist_map = dist_map / max_dist
    
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

def generate_heatmap(
    som,
    data: np.ndarray,
    output_file: str,
    map_type: str = 'square',
    cmap: str = 'Blues',
    show_numbers: bool = False
):
    """
    Klasická heatmapa návštěvnosti neuronů:
      • čtvercová: imshow(mat)
      • hexagonální: hex-patch podle counts
    """
    check_folder(output_file)
    m, n = som.m, som.n

    # spočítat counts
    counts = np.zeros((m, n), dtype=int)
    for sample in data:
        i, j = som.find_bmu(sample)
        counts[i, j] += 1

    # normalizace barev
    norm = Normalize(vmin=counts.min(), vmax=counts.max())
    fig, ax = plt.subplots(figsize=(20, 12))

    if map_type == 'square':
        # otočit, aby řádek 0 byl nahoře
        mat = counts[::-1, :]
        im = ax.imshow(mat, cmap=cmap, norm=norm)
        if show_numbers:
            for i in range(m):
                for j in range(n):
                    cnt = counts[m-1-i, j]
                    if cnt:
                        ax.text(j, i, cnt, ha='center', va='center', color='white')

    elif map_type == 'hex':
        # hexagonální mřížka
        X, Y = _grid_coordinates(m, n, 'hex')
        for idx, ((i, j), cnt) in enumerate(np.ndenumerate(counts)):
            x, y = X[idx], Y[idx]
            color = plt.get_cmap(cmap)(norm(cnt))
            hexagon = RegularPolygon(
                (x, y), numVertices=6, radius=0.5,
                facecolor=color, edgecolor='white'
            )
            ax.add_patch(hexagon)
            if show_numbers and cnt:
                ax.text(x, y, cnt, ha='center', va='center', color='white')
        im = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
        ax.set_xlim(X.min() - 0.6, X.max() + 0.6)
        ax.set_ylim(Y.min() - 0.6, Y.max() + 0.6)

    else:
        raise ValueError("Unsupported map_type: choose 'square' or 'hex'")

    # společný colorbar
    fig.colorbar(im, ax=ax, label='Hits')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0.08)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()


def generate_density_contour_map(
    som,
    data: np.ndarray,
    output_file: str,
    map_type: str = 'hex',
    levels: int = 10,
    bandwidth: float = None,
    cmap: str = 'viridis'
):
    """Kernel density estimation a izolinie na mapě."""
    check_folder(output_file)
    m,n = som.m, som.n
    # souřadnice všech BMU pro každý vzorek
    coords = []
    X,Y = _grid_coordinates(m,n,map_type)
    for x in data:
        i,j = som.find_bmu(x)
        idx = i*n + j
        coords.append((X[idx],Y[idx]))
    coords = np.array(coords).T  # shape (2,N)
    # KDE
    kde = gaussian_kde(coords, bw_method=bandwidth)
    # grid centrálních bodů
    grid = np.vstack([X.ravel(), Y.ravel()])
    Z = kde(grid).reshape(X.shape)
    # vykreslení
    fig,ax = plt.subplots(figsize=(12,8))
    if map_type=='hex':
        for xi, yi, zi in zip(X, Y, Z.ravel()):
            hexagon = RegularPolygon(
                xy=(xi, yi),
                numVertices=6,
                radius=0.5,
                facecolor=plt.get_cmap(cmap)(zi / Z.max()),
                edgecolor='white'
            )
        #    hexagon = RegularPolygon(
        #         (xi, yi), 6, 0.5,
        #         facecolor=plt.get_cmap(cmap)(zi/Z.max()),
        #         edgecolor='white'
        #     )
            ax.add_patch(hexagon)
    else:
        mat = Z[::-1].reshape(m,n)
        ax.imshow(mat, cmap=cmap, origin='upper')
    cs = ax.contour(
        X.reshape(m,n), Y.reshape(m,n), Z.reshape(m,n),
        levels=levels, colors='k', linewidths=0.5
    )
    ax.set_aspect('equal'); ax.axis('off')
    plt.tight_layout(); plt.savefig(output_file, bbox_inches='tight'); plt.close()

def generate_class_probability_map(
    som,
    data: np.ndarray,
    labels: np.ndarray,
    categories: list,
    output_file: str,
    map_type: str = 'hex',
    cmap: str = 'tab10'
):
    """Každý neuron barevně podle nejpravděpodobnější třídy, alpha podle p."""
    check_folder(output_file)
    m,n = som.m, som.n
    counts = { (i,j):{cat:0 for cat in categories} for i in range(m) for j in range(n) }
    for x,lbl in zip(data,labels):
        i,j = som.find_bmu(x)
        counts[(i,j)][lbl]+=1
    X,Y = _grid_coordinates(m,n,map_type)
    fig,ax = plt.subplots(figsize=(12,8))
    cmap_obj = ListedColormap(plt.get_cmap(cmap).colors[:len(categories)])
    for (i,j),cnts in counts.items():
        total = sum(cnts.values()); 
        if total==0: continue
        # třída a pravděpodobnost
        best = max(cnts, key=cnts.get)
        p = cnts[best]/total
        idx = categories.index(best)
        xi, yi = X[i*n+j], Y[i*n+j]
        hexagon = RegularPolygon(
            (xi, yi), 6, 0.5,
            facecolor=cmap_obj(idx),
            alpha=p, edgecolor='white'
        )
        ax.add_patch(hexagon)
    handles = [Patch(facecolor=cmap_obj(i), label=categories[i]) for i in range(len(categories))]
    ax.legend(handles, bbox_to_anchor=(1.02,1), loc='upper left', borderaxespad=0)
    ax.set_aspect('equal'); ax.axis('off')
    plt.tight_layout(); plt.savefig(output_file, bbox_inches='tight'); plt.close()

def generate_topology_preservation_map(
    som,
    data: np.ndarray,
    output_file: str,
    map_type: str = 'hex',
    neighbour_steps: int = 1,
    cmap: str = 'magma'
):
    """Lokální topographic error per neuron."""
    check_folder(output_file)
    m,n = som.m, som.n
    # flatten váhy
    W = som.weights.reshape(m*n, -1)
    # pro každý vzorek zjistit dva nejbližší neurony
    top_err = { (i,j):[] for i in range(m) for j in range(n) }
    for x in data:
        # dist k všem
        d = cdist(W, x.reshape(1,-1)).ravel()
        b1,b2 = np.argsort(d)[:2]
        i1,j1 = divmod(b1,n); i2,j2 = divmod(b2,n)
        # adjacency
        if abs(i1-i2)+abs(j1-j2) > neighbour_steps:
            top_err[(i1,j1)].append(1)
        else:
            top_err[(i1,j1)].append(0)
    # průměrná chyba
    vals = np.array([ np.mean(top_err[(i,j)]) if top_err[(i,j)] else 0
                  for i in range(m) for j in range(n) ])
    X,Y = _grid_coordinates(m,n,map_type)
    fig,ax = plt.subplots(figsize=(12,8))
    norm=Normalize(0,1); cmap_obj=plt.get_cmap(cmap)
    for idx,(i,j) in enumerate([(i,j) for i in range(m) for j in range(n)]):
        xi, yi = X[idx],Y[idx]; v=vals[idx]
        hexagon = RegularPolygon(
            xy=(xi, yi),
            numVertices=6,
            radius=0.5,
            facecolor=cmap_obj(norm(v)),
            edgecolor='white'
        )
        ax.add_patch(hexagon)
    fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,label='Topo‑error')
    ax.set_aspect('equal'); ax.axis('off')
    plt.tight_layout(); plt.savefig(output_file,bbox_inches='tight'); plt.close()

def generate_component_correlation_map(
    som,
    data: np.ndarray,
    df_orig,
    output_file: str,
    features: tuple,
    corr_method: str = 'pearson',
    map_type: str = 'hex',
    cmap: str = 'coolwarm'
):
    """Korelace dvou featur na úrovni každého neuronu."""
    check_folder(output_file)
    m,n = som.m, som.n
    bins = { (i,j): [] for i in range(m) for j in range(n) }
    for x,row in zip(data, df_orig.to_dict('records')):
        i,j = som.find_bmu(x)
        bins[(i,j)].append((row[features[0]], row[features[1]]))
    corr = []
    for i in range(m):
        for j in range(n):
            pts = bins[(i,j)]
            if len(pts)>1:
                arr=np.array(pts)
                corr.append( np.corrcoef(arr[:,0],arr[:,1])[0,1] )
            else:
                corr.append(0)
    corr = np.nan_to_num(corr)
    X,Y=_grid_coordinates(m,n,map_type)
    fig,ax=plt.subplots(figsize=(12,8))
    norm=Normalize(vmin=-1,vmax=1); cmap_obj=plt.get_cmap(cmap)
    for idx,v in enumerate(corr):
        xi,yi=X[idx],Y[idx]
        # hexagon=RegularPolygon((xi,yi),6,0.5,facecolor=cmap_obj(norm(v)),edgecolor='white')
        hexagon = RegularPolygon(
            xy=(xi, yi),
            numVertices=6,
            radius=0.5,
            facecolor=cmap_obj(norm(v)),
            edgecolor='white'
        )
        ax.add_patch(hexagon)
    fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,label=f"Corr {features[0]}∼{features[1]}")
    ax.set_aspect('equal'); ax.axis('off')
    plt.tight_layout(); plt.savefig(output_file,bbox_inches='tight'); plt.close()

def generate_feature_combination_map(
    som,
    data: np.ndarray,
    df_orig,
    output_file: str,
    features: tuple,
    map_type: str = 'hex'
):
    """RGB mapa z průměrů tří featur."""
    check_folder(output_file)
    m,n = som.m, som.n
    bins = { (i,j): [] for i in range(m) for j in range(n) }
    for x,row in zip(data, df_orig.to_dict('records')):
        i,j = som.find_bmu(x)
        bins[(i,j)].append((row[f],row[g],row[h]) 
                           for f,g,h in [features])
    # spočítat průměry
    rgb = []
    for i in range(m):
        for j in range(n):
            vals = np.array(list(bins[(i,j)]))
            if vals.size:
                mean = vals.mean(axis=0)
            else:
                mean = np.zeros(3)
            rgb.append(mean)
    # normalizovat kanály zvlášť
    rgba = np.vstack(rgb)
    mins=rgba.min(axis=0); maxs=rgba.max(axis=0)
    normed = (rgba - mins)/(maxs-mins)
    X,Y=_grid_coordinates(m,n,map_type)
    fig,ax=plt.subplots(figsize=(12,8))
    for idx,(r,g,b) in enumerate(normed):
        xi,yi=X[idx],Y[idx]
        hexagon = RegularPolygon(
            xy=(xi, yi),
            numVertices=6,
            radius=0.5,
            facecolor=(r,g,b),
            edgecolor='white'
        )
        ax.add_patch(hexagon)
    ax.set_aspect('equal'); ax.axis('off')
    plt.tight_layout(); plt.savefig(output_file,bbox_inches='tight'); plt.close()


def check_folder(output_file: str):
    folder = os.path.dirname(output_file)
    if not os.path.exists(folder):
        os.makedirs(folder)





def get_size_of_point(m,n,map_type):
    if map_type == 'hex':    
        if m == 10:
            point_size = 10000
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




def generate_maps(som, data, preprocess_file,output_path, som_settings, settings):
    # parametr mřížky
    map_type = som_settings.get("map_type", "square")

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

    #6) Heatmap
    generate_heatmap(
        som,
        data,
        f"{output_path}/visualization/heatmap_{map_type}.png",
        map_type=map_type
    )

    # 4) Density/Contour map  
    generate_density_contour_map(
        som,
        data,
        f"{output_path}/visualization/density_map_hex.png",
        map_type='hex',
        levels=12,          # počet izoliníí
        bandwidth=1.0,      # šířka kernelu
        cmap='viridis'
    )

    # 5) Class‑Probability / Confidence map  
    # generate_class_probability_map(
    #     som,
    #     data,
    #     labels,             # 1D pole kategorií pro každý vzorek
    #     categories,         # seznam unikátních kategorií
    #     f"{output_path}/visualization/class_probability_map_hex.png",
    #     map_type='hex',
    #     cmap='plasma'
    # )

    # 6) Topology Preservation map  
    generate_topology_preservation_map(
        som,
        data,
        f"{output_path}/visualization/topology_preservation_map_hex.png",
        map_type='hex',
        neighbour_steps=1,  # vzdálenost sousedů v mřížce
        cmap='magma'
    )

    df_orig = pd.read_csv(f"{output_path}/input.csv", delimiter=';', nrows=0)
    # 7) Component Correlation map  
    generate_component_correlation_map(
        som,
        data,
        df_orig,
        f"{output_path}/visualization/component_correlation_map_hex.png",
        features=('SepalLengthCm', 'PetalWidthCm'),
        corr_method='pearson',
        map_type='hex',
        cmap='coolwarm'
    )

    # 8) Feature Combination plane  
    generate_feature_combination_map(
        som,
        data,
        df_orig,
        f"{output_path}/visualization/feature_combination_map_hex.png",        
        features=('SepalLengthCm','PetalLengthCm','PetalWidthCm'),
        map_type='hex'
    )