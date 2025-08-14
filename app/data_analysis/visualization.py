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
            label='Průměrná vzdálenost mezi sousedy'
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
            label='Počet vzorků'
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
    ax.plot(best_epoch, best_mqe, 'ro', markersize=10, label=f'Nejlepší MQE: {best_mqe:.6f}')
    
    # Nastavení popisků
    ax.set_xlabel('Číslo epochy', fontsize=12)
    ax.set_ylabel('Kvantizační chyba (MQE)', fontsize=12)
    ax.set_title('Vývoj kvantizační chyby během trénování', fontsize=14, pad=20)
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
    ax1.set_xlabel('Číslo epochy', fontsize=12)
    ax1.set_ylabel('Learning rate', fontsize=12)
    ax1.set_title('Vývoj learning rate během trénování', fontsize=14, pad=20)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.tick_params(axis='both', which='major', labelsize=10)

    ax2.plot(epochs, som.radius_history, 'r-', linewidth=2)
    ax2.set_xlabel('Číslo epochy', fontsize=12)
    ax2.set_ylabel('Poloměr sousedství', fontsize=12)
    ax2.set_title('Vývoj poloměru sousedství během trénování', fontsize=14, pad=20)
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.tick_params(axis='both', which='major', labelsize=10)

    if hasattr(som, 'batch_size_history') and len(som.batch_size_history) > 0:
        ax3.plot(epochs, som.batch_size_history, 'g-', linewidth=2)
        ax3.set_xlabel('Číslo epochy', fontsize=12)
        ax3.set_ylabel('Velikost dávky', fontsize=12)
        ax3.set_title('Vývoj velikosti dávky během trénování', fontsize=14, pad=20)
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