import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle, RegularPolygon, Wedge, Circle, Patch
from matplotlib.lines import Line2D
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, ListedColormap
import sys
import pandas as pd
from collections import defaultdict, Counter
import json
from sklearn.metrics import pairwise_distances_argmin_min
from sklearn.decomposition import PCA

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


def save_quantization_error_to_json(original_neuron_error_map: np.ndarray, total_quantization_error: float, output_path: str):
    """Uloží kvantizační chyby do JSON souboru.

    Args:
        original_neuron_error_map (np.ndarray): Mapa kvantizačních chyb pro každý neuron (nenormalizovaná).
        total_quantization_error (float): Celková kvantizační chyba.
        output_path (str): Kořenová cesta pro výstupní soubory.
    """
    json_dir = os.path.join(output_path, 'json')
    os.makedirs(json_dir, exist_ok=True)
    json_file_path = os.path.join(json_dir, 'quantization_error.json')

    neuron_errors_dict = {}
    for i in range(original_neuron_error_map.shape[0]):
        for j in range(original_neuron_error_map.shape[1]):
            neuron_errors_dict[f"{i}_{j}"] = original_neuron_error_map[i, j]

    error_data = {
        'total_quantization_error': total_quantization_error,
        'neuron_quantization_errors': neuron_errors_dict
    }
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(error_data, f, ensure_ascii=False, indent=4)
  

def generate_u_matrix(som, output_file: str, map_type: str = 'square', cmap: str = 'viridis', save_legend: bool = True):
    """
    Unified Distance Matrix: vykreslí průměrné vzdálenosti mezi sousedy neuronů.

    Args:
        som: Instance SOM s vlastnostmi m,n a weights
        output_file: Cesta k výstupnímu souboru
        map_type: Typ mřížky ('square' nebo 'hex')
        cmap: Název colormapy
        save_legend: Zda generovat samostatnou legendu
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

    # Získání rozsahu hodnot pro colorbar
    vmin, vmax = u.min(), u.max()

    # Generuje souřadnice center neuronů podle typu mřížky
    X, Y = _grid_coordinates(m, n, map_type)
    # Vytváří novou figuru a osy pro vykreslení
    fig, ax = plt.subplots(figsize=(20,12))

    element_size = get_size_of_point(m,n,map_type)
    sc = ax.scatter(X, Y, c=u.flatten(), s=element_size, cmap=cmap, marker='h' if map_type == 'hex' else 's')   

    _set_axes_limits(ax, som.m, som.n, map_type)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    plt.close()

    # Generování samostatné legendy
    if save_legend:
        generate_legend(
            vmin=vmin,
            vmax=vmax,
            output_file=output_file,
            cmap=cmap,
            label='Average Neighbor Distance'
        )


def generate_hit_map(som, data: np.ndarray, output_file: str,
                    map_type: str = 'square', cmap: str = 'Blues',
                    show_numbers: bool = False, save_legend: bool = True):
    """
    Heatmap návštěvnosti neuronů: velikost/barva bodu podle četnosti vzorků.

    Args:
        som: Instance SOM s vlastnostmi m,n
        data: Vstupní data
        output_file: Cesta k výstupnímu souboru
        map_type: Typ mřížky ('square' nebo 'hex')
        cmap: Název colormapy
        show_numbers: Zda zobrazit počty vzorků v buňkách
        save_legend: Zda generovat samostatnou legendu
    """
    check_folder(output_file)
    m, n = som.m, som.n
    counts = {(i,j): 0 for i in range(m) for j in range(n)}
    for sample in data:
        i, j = som.find_bmu(sample)
        counts[(i,j)] += 1

    # hodnoty counts v pořadí i=0..m-1, j=0..n-1
    vals = np.array([counts[(i,j)] for i in range(m) for j in range(n)])
    vmin, vmax = vals.min(), vals.max()

    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(20,12))

    element_size = get_size_of_point(m,n,map_type)    
    sc = ax.scatter(X, Y, c=vals, s=element_size, cmap=cmap, marker='h' if map_type == 'hex' else 's')

    if show_numbers:
        for i in range(m):
            for j in range(n):
                if counts[(i,j)] != 0:
                    ax.text(X[i*n+j], Y[i*n+j], str(counts[(i,j)]), ha='center', va='center', color='red')

    _set_axes_limits(ax, som.m, som.n, map_type)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    plt.close()

    # Generování samostatné legendy
    if save_legend:
        generate_legend(
            vmin=vmin,
            vmax=vmax,
            output_file=output_file,
            cmap=cmap,
            label='Sample Count'
        )


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
        data_mean: Střední hodnota pro denormalizaci
        data_std: Směrodatná odchylka pro denormalizaci
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

    # 2) Vykreslení samostatné legendy
    if save_legend:
        generate_legend(
            vmin=vmin,
            vmax=vmax,
            output_file=output_file,
            cmap=cmap,
            label=column_name or f"Component {component}"
        )

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

    # Přidání popisků pozic neuronů
    for i in range(m):
        for j in range(n):
            ax.text(X[i*n+j], Y[i*n+j], f'({i},{j})', ha='center', va='center', size=6)

    _set_axes_limits(ax, m, n, map_type)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    plt.close()

def generate_legend(
    categories: dict = None,
    vmin: float = None,
    vmax: float = None,
    output_file: str = None,
    cmap: str = 'coolwarm',
    label: str = None,
    figsize: tuple = (2, 12),
    legend_type: str = 'colorbar'
) -> None:
    """Generuje samostatnou legendu pro vizualizace.
    
    Args:
        categories (dict, optional): Slovník kategorií pro kategorickou legendu {id: label}
        vmin (float, optional): Minimální hodnota pro colorbar
        vmax (float, optional): Maximální hodnota pro colorbar
        output_file (str): Cesta k výstupnímu souboru mapy
        cmap (str): Název colormapy
        label (str, optional): Popisek legendy
        figsize (tuple): Velikost figury (šířka, výška)
        legend_type (str): Typ legendy ('colorbar' nebo 'categorical')
    """
    # Nastavení fontu pro matplotlib
    plt.rcParams['font.family'] = 'DejaVu Sans'
    
    # Vytvoření cesty pro legendu
    output_dir = os.path.dirname(output_file)
    legends_dir = os.path.join(output_dir, 'legends')
    os.makedirs(legends_dir, exist_ok=True)
    
    # Vytvoření názvu souboru pro legendu
    base_name = os.path.basename(output_file)
    legend_file = os.path.join(legends_dir, base_name)

    # Vytvoření figury
    fig = plt.figure(figsize=figsize)

    if legend_type == 'colorbar':
        # Vytvoření colorbar legendy
        cax = fig.add_axes([0.35, 0.02, 0.3, 0.96])
        norm = Normalize(vmin=vmin, vmax=vmax)
        cbar = fig.colorbar(
            plt.cm.ScalarMappable(norm=norm, cmap=cmap),
            cax=cax,
            orientation='vertical',
            extend='neither',
            extendfrac=0.0,
            label=label
        )

        # Nastavení tiků
        orig_ticks = cbar.get_ticks()
        middle_ticks = [t for t in orig_ticks if vmin < t < vmax]
        new_ticks = [vmin] + middle_ticks + [vmax]
        cbar.set_ticks(new_ticks)
        cbar.set_ticklabels([f"{t:.2f}" for t in new_ticks])

        # Nastavení rozsahu a pozice
        cbar.ax.set_ylim(vmin, vmax)
        cbar.ax.yaxis.set_label_position('right')
        cbar.ax.yaxis.tick_right()

        # Úprava vzhledu
        for spine in ['top', 'bottom', 'left', 'right']:
            cax.spines[spine].set_visible(False)
        cax.tick_params(axis='y', which='both', length=5, labelsize=10)

    else:  # categorical
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
        
        # Vytvoření barevné palety
        cmap = plt.get_cmap(cmap)
        n_categories = len(categories)
        
        # Vytvoření patches pro každou kategorii
        handles = [
            Patch(
                facecolor=cmap(i/n_categories),
                label=categories[str(i+1)],
                edgecolor='white'
            )
            for i in range(n_categories)
        ]
        
        # Vytvoření legendy
        ax.legend(
            handles=handles,
            loc='center',
            title=label,
            frameon=False,
            ncol=1
        )
        ax.axis('off')

    # Uložení a zavření
    plt.savefig(legend_file, bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)

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

    _set_axes_limits(ax, m, n, map_type)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    plt.close()

    # Generování samostatné legendy pro koláčový graf
    generate_legend(
        categories=data['categories'],
        output_file=output_file,
        cmap=cmap,
        label=os.path.basename(json_file).replace('pie_data_', '').replace('.json', ''),
        figsize=(4, len(data['categories']) * 0.4),
        legend_type='categorical'
    )

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
                                    map_type: str = 'square', cmap: str = 'magma', save_legend: bool = True):
    """
    Zobrazení průměrné kvantizační chyby na neuron z předpočítané mapy chyb.

    Args:
        som: Instance SOM s vlastnostmi m,n
        neuron_error_map: Předpočítaná mapa chyb
        output_file: Cesta k výstupnímu souboru
        map_type: Typ mřížky ('square' nebo 'hex')
        cmap: Název colormapy
        save_legend: Zda generovat samostatnou legendu
    """
    check_folder(output_file)
    m, n = som.m, som.n
    
    # Normalizace hodnot do rozsahu [0,1]
    max_dist = np.max(neuron_error_map)
    if max_dist > 0:
        neuron_error_map = neuron_error_map / max_dist
    
    vmin, vmax = neuron_error_map.min(), neuron_error_map.max()
    
    X, Y = _grid_coordinates(m, n, map_type)
    fig, ax = plt.subplots(figsize=(20,12))

    element_size = get_size_of_point(m,n,map_type)    
    sc = ax.scatter(X, Y, c=neuron_error_map.flatten(), s=element_size, cmap=cmap, marker='h' if map_type == 'hex' else 's')
    
    _set_axes_limits(ax, som.m, som.n, map_type)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.margins(0)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    plt.close()

    # Generování samostatné legendy
    if save_legend:
        generate_legend(
            vmin=vmin,
            vmax=vmax,
            output_file=output_file,
            cmap=cmap,
            label='Průměrná kvantizační chyba'
        )

def sanitize_filename(filename: str) -> str:
    """Převede název sloupce na bezpečný název souboru.
    
    Args:
        filename (str): Původní název
        
    Returns:
        str: Bezpečný název souboru
    """
    # Nahrazení nebezpečných znaků
    filename = filename.lower()
    filename = filename.replace(' ', '_')
    # Odstranění diakritiky
    filename = ''.join(c for c in filename if c.isalnum() or c in '_-')
    return filename

def generate_mqe_history_plot(som, output_file: str):
    """Vykreslí graf vývoje kvantizační chyby během trénování.
    
    Args:
        som: Instance SOM s vlastnostmi mqe_history a epochs_history
        output_file: Cesta k výstupnímu souboru
    """
    check_folder(output_file)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Vykreslení křivky MQE
    ax.plot(som.epochs_history, som.mqe_history, 'b-', linewidth=2)
    
    # Zvýraznění nejlepší dosažené hodnoty
    best_mqe_idx = np.argmin(som.mqe_history)
    best_mqe = som.mqe_history[best_mqe_idx]
    best_epoch = som.epochs_history[best_mqe_idx]
    ax.plot(best_epoch, best_mqe, 'ro', markersize=10, label=f'Best MQE: {best_mqe:.6f}')
    
    # Nastavení popisků
    ax.set_xlabel('Training Steps', fontsize=12)
    ax.set_ylabel('MQE', fontsize=12)
    ax.set_title('Quantization Error Convergence', fontsize=14, pad=20)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(fontsize=10)
    
    # Nastavení formátu os
    ax.tick_params(axis='both', which='major', labelsize=10)
    
    # Uložení grafu
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def generate_parameters_history_plot(som, output_file: str):
    """Vykreslí grafy vývoje parametrů učení během trénování.
    
    Args:
        som: Instance SOM s vlastnostmi learning_rate_history, radius_history a epochs_history
        output_file: Cesta k výstupnímu souboru
    """
    check_folder(output_file)
    
    # Vytvoření grafu s 2 nebo 3 subploty podle dostupnosti batch_size_history
    if hasattr(som, 'batch_size_history') and len(som.batch_size_history) > 0:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
    else:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    epochs = som.epochs_history

    ax1.plot(epochs, som.learning_rate_history, 'b-', linewidth=2)
    ax1.set_xlabel('Training Steps', fontsize=12)
    ax1.set_ylabel('Learning rate', fontsize=12)
    ax1.set_title('Learning Rate Evolution', fontsize=14, pad=20)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.tick_params(axis='both', which='major', labelsize=10)

    ax2.plot(epochs, som.radius_history, 'r-', linewidth=2)
    ax2.set_xlabel('Training Steps', fontsize=12)
    ax2.set_ylabel('Neighborhood Radius', fontsize=12)
    ax2.set_title('Radius Evolution', fontsize=14, pad=20)
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.tick_params(axis='both', which='major', labelsize=10)

    if hasattr(som, 'batch_size_history') and len(som.batch_size_history) > 0:
        ax3.plot(epochs, som.batch_size_history, 'g-', linewidth=2)
        ax3.set_xlabel('Training Steps', fontsize=12)
        ax3.set_ylabel('Batch Size', fontsize=12)
        ax3.set_title('Batch Size Evolution', fontsize=14, pad=20)
        ax3.grid(True, linestyle='--', alpha=0.7)
        ax3.tick_params(axis='both', which='major', labelsize=10)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def generate_maps(som, data, preprocess_file, output_path, som_settings, settings):
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
        f"{output_path}/visualization/u-matrix.png",
        map_type=map_type
    )

    # 2) Hit‑mapa
    generate_hit_map(
        som,
        data,
        f"{output_path}/visualization/hit.png",
        map_type,
        'Blues',
        True,
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
        
        # Pokud nemáme název sloupce, použijeme číslo dimenze
        safe_name = sanitize_filename(col_name) if col_name else f"dimension_{dim}"

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
            output_file=f"{output_path}/visualization/component_{safe_name}.png",
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
        f"{output_path}/visualization/cluster.png",
        map_type=map_type
    )

    # 5) Distance‑map (prům. kvantizační chyba) a uložení chyb do JSON
    codebook_vectors = som.weights.reshape(-1, som.dim)
    bmu_indexes = np.array([som.find_bmu(x)[0] * som.n + som.find_bmu(x)[1] for x in data])
    original_neuron_error_map, total_quantization_error = som.compute_quantization_error(data, codebook_vectors, bmu_indexes, (som.m, som.n), compute_neuron_map=True)    
    # Uložení chyb do JSON
    save_quantization_error_to_json(original_neuron_error_map, total_quantization_error, output_path)

    generate_distance_map_from_error_map(
        som,
        original_neuron_error_map,
        f"{output_path}/visualization/distance.png",
        map_type=map_type
    )

    # 6) Graf vývoje kvantizační chyby
    if hasattr(som, 'mqe_history') and len(som.mqe_history) > 0:
        generate_mqe_history_plot(
            som,
            f"{output_path}/visualization/mqe-history.png"
        )

    # 7) Graf vývoje parametrů učení
    if (hasattr(som, 'learning_rate_history') and len(som.learning_rate_history) > 0 and
        hasattr(som, 'radius_history') and len(som.radius_history) > 0):
        
        generate_parameters_history_plot(
            som,
            f"{output_path}/visualization/parameters-history.png"
        )
    else:
        print("Debug - Chybí historie parametrů:")
        print(f"Learning rate history existuje: {hasattr(som, 'learning_rate_history')}, délka: {len(som.learning_rate_history) if hasattr(som, 'learning_rate_history') else 0}")
        print(f"Radius history existuje: {hasattr(som, 'radius_history')}, délka: {len(som.radius_history) if hasattr(som, 'radius_history') else 0}")
        print(f"Batch size history existuje: {hasattr(som, 'batch_size_history')}, délka: {len(som.batch_size_history) if hasattr(som, 'batch_size_history') else 0}")

    # Vykreslení jednotlivých kategoriálních sloupců
    for column_name in settings['categorical_column']:
        if not any(column_name in group for group in settings.get('categorical_groups', {}).values()):
            plot_pie_map_from_json(
                som,
                f"{output_path}/json/pie_data_{column_name}.json",
                f"{output_path}/visualization/pie-map_{column_name}.png",
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

    # 8) Topografická mapa: kontrola zachování topografie (původní data vs. organizovaná SOM mřížka)
    topology_projection = compute_topology_projection(som, data, map_type=map_type)
    if topology_projection is not None:
        generate_topology_map(
            som,
            topology_projection,
            original_neuron_error_map,
            f"{output_path}/visualization/topology.png",
            map_type=map_type
        )
        generate_topology_map_html(
            som,
            topology_projection,
            original_neuron_error_map,
            f"{output_path}/visualization/topology_interactive.html",
            map_type=map_type
        )

    # 9) Topografická mapa 3D (rotovatelná) — vyžaduje alespoň 3 dimenze vstupního prostoru
    topology_projection_3d = compute_topology_projection(som, data, map_type=map_type, n_components=3)
    if topology_projection_3d is not None:
        generate_topology_map_html3d(
            som,
            topology_projection_3d,
            original_neuron_error_map,
            f"{output_path}/visualization/topology_interactive_3d.html",
            map_type=map_type
        )


def _topology_grid_edges(m: int, n: int, map_type: str = 'square') -> list:
    """
    Vrátí seznam hran (dvojic sousedních neuronů) mřížky SOM. Používá stejnou
    konvenci sousedství jako `_grid_coordinates` (offsetové řádky pro hex),
    aby si topografická mapa a ostatní mapy v tomto souboru vizuálně
    odpovídaly.

    Args:
        m: Počet řádků mřížky
        n: Počet sloupců mřížky
        map_type: Typ mřížky ('square' nebo 'hex')

    Returns:
        list: Seznam hran ve tvaru [((i1,j1),(i2,j2)), ...]
    """
    edges = []
    for i in range(m):
        for j in range(n):
            if j + 1 < n:
                edges.append(((i, j), (i, j + 1)))
            if i + 1 < m:
                if map_type == 'hex':
                    # Sudé/liché řádky jsou v `_grid_coordinates` posunuty o půl buňky
                    neighbours = (j - 1, j) if i % 2 == 0 else (j, j + 1)
                    for nj in neighbours:
                        if 0 <= nj < n:
                            edges.append(((i, j), (i + 1, nj)))
                else:
                    edges.append(((i, j), (i + 1, j)))
    return edges


def _topology_edge_lengths(weights_proj_grid: np.ndarray, edges: list, threshold_pct: float = 85):
    """
    Spočítá délku každé hrany mřížky v promítnutém (2D) prostoru a označí
    hrany, které jsou neobvykle protažené (nad `threshold_pct` percentilem).

    Protažená/zkřížená hrana znamená, že dva sousední neurony v mřížce SOM
    reprezentují ve skutečnosti velmi odlišná data — tedy že síť na daném
    místě neuchovala topografii vstupního prostoru (nebo jde o artefakt
    projekce do 2D).

    Returns:
        tuple: (délky hran, boolean maska protažených hran)
    """
    if not edges:
        return np.array([]), np.array([], dtype=bool)
    lengths = np.array([
        np.linalg.norm(weights_proj_grid[i1, j1] - weights_proj_grid[i2, j2])
        for (i1, j1), (i2, j2) in edges
    ])
    threshold = np.percentile(lengths, threshold_pct)
    stretched = lengths > threshold
    return lengths, stretched


def compute_topology_projection(som, data: np.ndarray, map_type: str = 'square',
                                n_components: int = 2, sample_limit: int = 3000,
                                random_seed: int = 42) -> dict | None:
    """
    Připraví společnou 2D/3D projekci (PCA) původních vstupních dat a
    naučených vah neuronů SOM a dopočítá geometrii mřížky nad touto projekcí.

    Data i váhy jsou promítnuty pomocí jedné a téže PCA (natrénované na obou
    dohromady), takže výsledek jde přímo vizuálně porovnat: shluk bodů jsou
    původní data, mřížka spojená hranami je „organizovaná" reprezentace SOM.
    Pokud síť zachovala topografii, mřížka kopíruje tvar shluku beze
    zkřížení; protažené/zkřížené hrany ukazují na topologickou chybu.

    Args:
        som: Natrénovaná instance SOM s vlastnostmi m, n, dim a weights
        data: Vstupní (normalizovaná) trénovací data, tvar (n_samples, dim)
        map_type: Typ mřížky ('square' nebo 'hex')
        n_components: Počet dimenzí projekce (2 pro 2D mapu, 3 pro rotovatelnou 3D mapu)
        sample_limit: Maximální počet vykreslovaných vzorků dat (výkon/velikost souboru)
        random_seed: Seed pro náhodný výběr vzorků při omezení jejich počtu

    Returns:
        dict | None: Slovník s klíči 'data_proj', 'weights_proj' (tvar m,n,n_components),
            'edges', 'lengths', 'stretched' a 'var_exp', nebo None pokud má
            vstupní prostor méně dimenzí, než požaduje `n_components`
    """
    m, n, dim = som.m, som.n, som.dim
    weights_flat = som.weights.reshape(-1, dim)

    if dim < n_components:
        print(f"Topografická mapa: vynechána, vstupní prostor má méně než {n_components} dimenze.")
        return None

    # Omezení počtu vykreslovaných vzorků kvůli výkonu a velikosti výstupních souborů
    if len(data) > sample_limit:
        rng = np.random.default_rng(random_seed)
        sample_idx = rng.choice(len(data), size=sample_limit, replace=False)
        data_sample = data[sample_idx]
    else:
        data_sample = data

    # Společná PCA nad daty i vahami, aby obě strany sdílely stejný souřadný systém
    n_components = min(n_components, weights_flat.shape[1])
    pca = PCA(n_components=n_components)
    combined = np.vstack([data_sample, weights_flat])
    combined_proj = pca.fit_transform(combined)

    data_proj = combined_proj[:len(data_sample)]
    weights_proj = combined_proj[len(data_sample):].reshape(m, n, n_components)

    edges = _topology_grid_edges(m, n, map_type)
    lengths, stretched = _topology_edge_lengths(weights_proj, edges)

    return {
        'data_proj': data_proj,
        'weights_proj': weights_proj,
        'edges': edges,
        'lengths': lengths,
        'stretched': stretched,
        'var_exp': pca.explained_variance_ratio_,
    }


def generate_topology_map(som, projection: dict, neuron_error_map: np.ndarray,
                         output_file: str, map_type: str = 'square'):
    """
    Vykreslí statickou topografickou mapu: shluk původních dat promítnutý do
    2D (PCA) s přeloženou mřížkou neuronů SOM. Slouží ke kontrole zachování
    topografie — protažené hrany (oranžově) značí místa, kde síť topografii
    vstupních dat neuchovala (nebo jde o artefakt projekce do 2D).

    Args:
        som: Natrénovaná instance SOM s vlastnostmi m, n
        projection: Výstup funkce `compute_topology_projection`
        neuron_error_map: Mapa kvantizační chyby na neuron (pro obarvení neuronů)
        output_file: Cesta k výstupnímu souboru PNG
        map_type: Typ mřížky ('square' nebo 'hex'), jen pro popisek grafu
    """
    check_folder(output_file)
    m, n = som.m, som.n

    data_proj = projection['data_proj']
    weights_proj = projection['weights_proj']
    edges = projection['edges']
    stretched = projection['stretched']
    var_exp = projection['var_exp']

    n_neurons = m * n
    dot_size = max(10, min(60, 4000 / n_neurons))
    lw = max(0.3, min(1.0, 100 / n_neurons))

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor('#f8f8f8')

    # Vrstva 1: původní data (mírně průhledná, na pozadí)
    ax.scatter(data_proj[:, 0], data_proj[:, 1], color='#2980b9', alpha=0.15,
              s=4, zorder=1, linewidths=0)

    # Vrstva 2: hrany mřížky, barevně odlišené podle protažení
    for e_idx, ((i1, j1), (i2, j2)) in enumerate(edges):
        ax.plot(
            [weights_proj[i1, j1, 0], weights_proj[i2, j2, 0]],
            [weights_proj[i1, j1, 1], weights_proj[i2, j2, 1]],
            color='#e67e22' if stretched[e_idx] else '#2c3e50',
            lw=lw, alpha=0.6 if stretched[e_idx] else 0.8, zorder=3,
        )

    # Vrstva 3: neurony obarvené podle průměrné kvantizační chyby
    nqe_flat = neuron_error_map.ravel()
    sc = ax.scatter(
        weights_proj[:, :, 0].ravel(), weights_proj[:, :, 1].ravel(),
        c=nqe_flat, cmap='plasma', s=dot_size, zorder=5,
        edgecolors='white', linewidths=0.4,
    )
    plt.colorbar(sc, ax=ax, label='Průměrná kvantizační chyba neuronu', shrink=0.75)

    var_str = f'PC1 {var_exp[0]:.1%} / PC2 {var_exp[1]:.1%}' if len(var_exp) >= 2 else f'PC1 {var_exp[0]:.1%}'
    n_stretched = int(stretched.sum())
    ax.set_title(
        f'Topografická mapa — původní data vs. organizovaná SOM mřížka\n'
        f'{m}×{n}, {"hex" if map_type == "hex" else "square"}  |  {var_str}  |  '
        f'protažené hrany: {n_stretched} (možná topologická chyba)',
        fontsize=11,
    )
    ax.set_xlabel('Komponenta 1', fontsize=10)
    ax.set_ylabel('Komponenta 2', fontsize=10)

    legend = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#2980b9',
              markersize=8, alpha=0.7, label='Původní data'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='crimson',
              markersize=8, label='Neuron (barva = kvantizační chyba)'),
        Line2D([0], [0], color='#2c3e50', lw=1.2, label='Hrana mřížky (v pořádku)'),
        Line2D([0], [0], color='#e67e22', lw=1.2, label='Protažená hrana (možná topologická chyba)'),
    ]
    ax.legend(handles=legend, fontsize=8, loc='best')

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close(fig)


def generate_topology_map_html(som, projection: dict, neuron_error_map: np.ndarray,
                              output_file: str, map_type: str = 'square'):
    """
    Vykreslí interaktivní HTML verzi topografické mapy (Plotly.js přes CDN,
    bez nutnosti mít v backendu nainstalovaný balíček plotly). Umožňuje
    přiblížení a najetí myší na neuron pro zobrazení jeho souřadnic a
    průměrné kvantizační chyby.

    Args:
        som: Natrénovaná instance SOM s vlastnostmi m, n
        projection: Výstup funkce `compute_topology_projection`
        neuron_error_map: Mapa kvantizační chyby na neuron
        output_file: Cesta k výstupnímu HTML souboru
        map_type: Typ mřížky ('square' nebo 'hex'), jen pro popisek grafu
    """
    check_folder(output_file)
    m, n = som.m, som.n

    data_proj = projection['data_proj']
    weights_proj = projection['weights_proj']
    edges = projection['edges']
    stretched = projection['stretched']
    var_exp = projection['var_exp']

    nqe_flat = neuron_error_map.ravel()

    traces = [
        {
            'type': 'scatter',
            'mode': 'markers',
            'x': data_proj[:, 0].tolist(),
            'y': data_proj[:, 1].tolist(),
            'marker': {'color': '#2980b9', 'size': 3, 'opacity': 0.30},
            'name': 'Původní data',
            'hoverinfo': 'skip',
        },
    ]

    # Hrany mřížky jako dvě samostatné stopy (normální / protažené), aby šly
    # v legendě zapínat a vypínat zvlášť
    edge_x = {'normal': [], 'stretched': []}
    edge_y = {'normal': [], 'stretched': []}
    for e_idx, ((i1, j1), (i2, j2)) in enumerate(edges):
        bucket = 'stretched' if stretched[e_idx] else 'normal'
        edge_x[bucket] += [float(weights_proj[i1, j1, 0]), float(weights_proj[i2, j2, 0]), None]
        edge_y[bucket] += [float(weights_proj[i1, j1, 1]), float(weights_proj[i2, j2, 1]), None]

    traces.append({
        'type': 'scatter', 'mode': 'lines',
        'x': edge_x['normal'], 'y': edge_y['normal'],
        'line': {'color': '#2c3e50', 'width': 1},
        'name': 'Hrana mřížky (v pořádku)', 'hoverinfo': 'skip', 'opacity': 0.75,
    })
    if edge_x['stretched']:
        traces.append({
            'type': 'scatter', 'mode': 'lines',
            'x': edge_x['stretched'], 'y': edge_y['stretched'],
            'line': {'color': '#e67e22', 'width': 1, 'dash': 'dot'},
            'name': 'Protažená hrana (možná topologická chyba)',
            'hoverinfo': 'skip', 'opacity': 0.6,
        })

    hover_text = [
        f'Neuron [{i},{j}]<br>Průměrná kvantizační chyba: {neuron_error_map[i, j]:.4f}'
        for i in range(m) for j in range(n)
    ]
    traces.append({
        'type': 'scatter', 'mode': 'markers',
        'x': weights_proj[:, :, 0].ravel().tolist(),
        'y': weights_proj[:, :, 1].ravel().tolist(),
        'marker': {
            'color': nqe_flat.tolist(), 'colorscale': 'Plasma', 'size': 8,
            'colorbar': {'title': 'Průměrná QE', 'thickness': 14},
            'line': {'color': 'white', 'width': 0.5},
        },
        'text': hover_text, 'hovertemplate': '%{text}<extra></extra>',
        'name': 'Neurony SOM',
    })

    var_str = f'PC1 {var_exp[0]:.1%} / PC2 {var_exp[1]:.1%}' if len(var_exp) >= 2 else f'PC1 {var_exp[0]:.1%}'
    n_stretched = int(stretched.sum())
    layout = {
        'title': {
            'text': (f'Topografická mapa — původní data vs. organizovaná SOM mřížka<br>'
                     f'<sub>{m}×{n}, {"hex" if map_type == "hex" else "square"} | {var_str} | '
                     f'protažené hrany: {n_stretched}</sub>'),
            'font': {'size': 14},
        },
        'xaxis': {'title': 'Komponenta 1'},
        'yaxis': {'title': 'Komponenta 2', 'scaleanchor': 'x'},
        'plot_bgcolor': '#f8f8f8',
        'hovermode': 'closest',
        'autosize': True,
        'margin': {'l': 40, 'r': 40, 't': 80, 'b': 40},
    }

    html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>Topografická mapa SOM</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
  html, body {{ margin: 0; padding: 0; height: 100%; }}
  #topology-plot {{ width: 100vw; height: 100vh; }}
</style>
</head>
<body>
<div id="topology-plot"></div>
<script>
  var data = {json.dumps(traces)};
  var layout = {json.dumps(layout)};
  Plotly.newPlot('topology-plot', data, layout, {{responsive: true}});
</script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_topology_map_html3d(som, projection: dict, neuron_error_map: np.ndarray,
                                output_file: str, map_type: str = 'square'):
    """
    Vykreslí interaktivní ROTOVATELNOU 3D verzi topografické mapy (Plotly.js
    Scatter3d přes CDN, bez nutnosti mít v backendu nainstalovaný balíček
    plotly). Tažením myší lze kamerou otáčet — jeden pevný pohled často
    skryje, jestli je mřížka souvislá plocha, nebo někde přeložená/zkřížená.

    Args:
        som: Natrénovaná instance SOM s vlastnostmi m, n
        projection: Výstup funkce `compute_topology_projection(..., n_components=3)`
        neuron_error_map: Mapa kvantizační chyby na neuron
        output_file: Cesta k výstupnímu HTML souboru
        map_type: Typ mřížky ('square' nebo 'hex'), jen pro popisek grafu
    """
    check_folder(output_file)
    m, n = som.m, som.n

    data_proj = projection['data_proj']
    weights_proj = projection['weights_proj']
    edges = projection['edges']
    stretched = projection['stretched']
    var_exp = projection['var_exp']

    nqe_flat = neuron_error_map.ravel()

    traces = [
        {
            'type': 'scatter3d',
            'mode': 'markers',
            'x': data_proj[:, 0].tolist(),
            'y': data_proj[:, 1].tolist(),
            'z': data_proj[:, 2].tolist(),
            'marker': {'color': '#2980b9', 'size': 1.5, 'opacity': 0.25},
            'name': 'Původní data',
            'hoverinfo': 'skip',
        },
    ]

    # Hrany mřížky jako dvě samostatné stopy (normální / protažené)
    edge_x = {'normal': [], 'stretched': []}
    edge_y = {'normal': [], 'stretched': []}
    edge_z = {'normal': [], 'stretched': []}
    for e_idx, ((i1, j1), (i2, j2)) in enumerate(edges):
        bucket = 'stretched' if stretched[e_idx] else 'normal'
        edge_x[bucket] += [float(weights_proj[i1, j1, 0]), float(weights_proj[i2, j2, 0]), None]
        edge_y[bucket] += [float(weights_proj[i1, j1, 1]), float(weights_proj[i2, j2, 1]), None]
        edge_z[bucket] += [float(weights_proj[i1, j1, 2]), float(weights_proj[i2, j2, 2]), None]

    traces.append({
        'type': 'scatter3d', 'mode': 'lines',
        'x': edge_x['normal'], 'y': edge_y['normal'], 'z': edge_z['normal'],
        'line': {'color': '#2c3e50', 'width': 2},
        'name': 'Hrana mřížky (v pořádku)', 'hoverinfo': 'skip', 'opacity': 0.75,
    })
    if edge_x['stretched']:
        traces.append({
            'type': 'scatter3d', 'mode': 'lines',
            'x': edge_x['stretched'], 'y': edge_y['stretched'], 'z': edge_z['stretched'],
            'line': {'color': '#e67e22', 'width': 2},
            'name': 'Protažená hrana (možná topologická chyba)',
            'hoverinfo': 'skip', 'opacity': 0.6,
        })

    hover_text = [
        f'Neuron [{i},{j}]<br>Průměrná kvantizační chyba: {neuron_error_map[i, j]:.4f}'
        for i in range(m) for j in range(n)
    ]
    traces.append({
        'type': 'scatter3d', 'mode': 'markers',
        'x': weights_proj[:, :, 0].ravel().tolist(),
        'y': weights_proj[:, :, 1].ravel().tolist(),
        'z': weights_proj[:, :, 2].ravel().tolist(),
        'marker': {
            'color': nqe_flat.tolist(), 'colorscale': 'Plasma', 'size': 4,
            'colorbar': {'title': 'Průměrná QE', 'thickness': 14},
            'line': {'color': 'white', 'width': 0.5},
        },
        'text': hover_text, 'hovertemplate': '%{text}<extra></extra>',
        'name': 'Neurony SOM',
    })

    var_str = f'PC1 {var_exp[0]:.1%} / PC2 {var_exp[1]:.1%} / PC3 {var_exp[2]:.1%}'
    n_stretched = int(stretched.sum())
    layout = {
        'title': {
            'text': (f'Topografická mapa 3D — původní data vs. organizovaná SOM mřížka<br>'
                     f'<sub>{m}×{n}, {"hex" if map_type == "hex" else "square"} | {var_str} | '
                     f'protažené hrany: {n_stretched} | tažením myší otočíte pohled</sub>'),
            'font': {'size': 14},
        },
        'scene': {
            'xaxis': {'title': 'Komponenta 1'},
            'yaxis': {'title': 'Komponenta 2'},
            'zaxis': {'title': 'Komponenta 3'},
            'aspectmode': 'data',
        },
        'hovermode': 'closest',
        'autosize': True,
        'margin': {'l': 10, 'r': 10, 't': 80, 'b': 10},
    }

    html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>Topografická mapa SOM 3D</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
  html, body {{ margin: 0; padding: 0; height: 100%; }}
  #topology-plot-3d {{ width: 100vw; height: 100vh; }}
</style>
</head>
<body>
<div id="topology-plot-3d"></div>
<script>
  var data = {json.dumps(traces)};
  var layout = {json.dumps(layout)};
  Plotly.newPlot('topology-plot-3d', data, layout, {{responsive: true}});
</script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)