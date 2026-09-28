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
    Generates neuron center coordinates for a square or hex grid.
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
        # for a hexagon: width = 1, height = √3/2*2 = √3 ≈1.732
        dx = 0.5
        dy = np.sqrt(3) / 2
    else:
        dx = dy = 0.5

    ax.set_xlim(X.min() - dx, X.max() + dx)
    ax.set_ylim(Y.min() - dy, Y.max() + dy)
    ax.margins(0)


def save_quantization_error_to_json(original_neuron_error_map: np.ndarray, total_quantization_error: float, output_path: str):
    """Saves quantization errors to a JSON file.

    Args:
        original_neuron_error_map (np.ndarray): Quantization error map for each neuron (not normalized).
        total_quantization_error (float): Total quantization error.
        output_path (str): Root path for output files.
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
    Unified Distance Matrix: plots the average distances between neighboring neurons.

    Args:
        som: SOM instance with m, n and weights attributes
        output_file: Path to the output file
        map_type: Grid type ('square' or 'hex')
        cmap: Colormap name
        save_legend: Whether to generate a separate legend
    """
    # Ensure the output folder exists
    check_folder(output_file)
    # Get the SOM grid dimensions
    m, n = som.m, som.n
    # Reshape the SOM weights into a 3D array for easier access
    weights = som.weights.reshape(m, n, -1)
    # Initialize the array for the average distances
    u = np.zeros((m, n))
    # Iterate over all neurons in the grid
    for i in range(m):
        for j in range(n):
            # Initialize the list of neighboring neurons
            neigh = []
            # Iterate over all four neighbors (up, down, left, right)
            for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                # Compute the neighbor's position
                ni, nj = i+di, j+dj
                # Check that the neighbor lies inside the grid
                if 0 <= ni < m and 0 <= nj < n:
                    # Compute the distance between the two neighboring neurons
                    neigh.append(np.linalg.norm(weights[i,j] - weights[ni,nj]))
            # Compute the average distance to the neighbors
            u[i,j] = np.mean(neigh) if neigh else 0

    # Get the value range for the colorbar
    vmin, vmax = u.min(), u.max()

    # Generate neuron center coordinates for the grid type
    X, Y = _grid_coordinates(m, n, map_type)
    # Create a new figure and axes for plotting
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

    # Generate a separate legend
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
    Neuron hit heatmap: point size/color by sample frequency.

    Args:
        som: SOM instance with m, n attributes
        data: Input data
        output_file: Path to the output file
        map_type: Grid type ('square' or 'hex')
        cmap: Colormap name
        show_numbers: Whether to show sample counts in the cells
        save_legend: Whether to generate a separate legend
    """
    check_folder(output_file)
    m, n = som.m, som.n
    counts = {(i,j): 0 for i in range(m) for j in range(n)}
    for sample in data:
        i, j = som.find_bmu(sample)
        counts[(i,j)] += 1

    # counts values in order i=0..m-1, j=0..n-1
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

    # Generate a separate legend
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
    data_min: float = None,
    data_range: float = None
):
    """
    Plots a component plane (weight dimension) to output_file (without legend) and,
    if save_legend, creates a separate legend file in the same folder.

    Args:
        som: SOM instance with m, n, dim and .weights attributes
        component: Index of the weight vector dimension
        output_file: Path to the output component map image
        map_type: 'square' or 'hex'
        cmap: Matplotlib colormap name
        column_name: Legend label (attribute name)
        save_legend: Whether to generate a separate legend image
        data_min: Original column minimum for denormalization
        data_range: Original column range (max - min) for denormalization
    """
    # Create the target folder
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load the component values
    m, n, dim = som.m, som.n, som.dim
    vals = som.weights.reshape(-1, dim)[:, component]
    # first take the normalized weights
    vals_norm = som.weights.reshape(-1, dim)[:, component]
    if data_min is not None and data_range is not None:
        vals = vals_norm * data_range + data_min
    else:
        vals = vals_norm

    # Scale colors to the real value ranges
    vmin, vmax = vals.min(), vals.max()
    norm = Normalize(vmin=vmin, vmax=vmax)

    # 1) Plot the map without a legend
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
    # save the map…
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

    # 2) Plot a separate legend
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
    Assigns each cell a color by its cluster and shows the position of each element.
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

    # Add neuron position labels
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
    """Generates a separate legend for visualizations.

    Args:
        categories (dict, optional): Category dictionary for a categorical legend {id: label}
        vmin (float, optional): Minimum value for the colorbar
        vmax (float, optional): Maximum value for the colorbar
        output_file (str): Path to the map's output file
        cmap (str): Colormap name
        label (str, optional): Legend label
        figsize (tuple): Figure size (width, height)
        legend_type (str): Legend type ('colorbar' or 'categorical')
    """
    # Set the matplotlib font
    plt.rcParams['font.family'] = 'DejaVu Sans'

    # Build the legend path
    output_dir = os.path.dirname(output_file)
    legends_dir = os.path.join(output_dir, 'legends')
    os.makedirs(legends_dir, exist_ok=True)
    
    # Build the legend file name
    base_name = os.path.basename(output_file)
    legend_file = os.path.join(legends_dir, base_name)

    # Create the figure
    fig = plt.figure(figsize=figsize)

    if legend_type == 'colorbar':
        # Create a colorbar legend
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

        # Set ticks
        orig_ticks = cbar.get_ticks()
        middle_ticks = [t for t in orig_ticks if vmin < t < vmax]
        new_ticks = [vmin] + middle_ticks + [vmax]
        cbar.set_ticks(new_ticks)
        cbar.set_ticklabels([f"{t:.2f}" for t in new_ticks])

        # Set range and position
        cbar.ax.set_ylim(vmin, vmax)
        cbar.ax.yaxis.set_label_position('right')
        cbar.ax.yaxis.tick_right()

        # Adjust appearance
        for spine in ['top', 'bottom', 'left', 'right']:
            cax.spines[spine].set_visible(False)
        cax.tick_params(axis='y', which='both', length=5, labelsize=10)

    else:  # categorical
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
        
        # Create the color palette
        cmap = plt.get_cmap(cmap)
        n_categories = len(categories)

        # Create patches for each category
        handles = [
            Patch(
                facecolor=cmap(i/n_categories),
                label=categories[str(i+1)],
                edgecolor='white'
            )
            for i in range(n_categories)
        ]
        
        # Create the legend
        ax.legend(
            handles=handles,
            loc='center',
            title=label,
            frameon=False,
            ncol=1
        )
        ax.axis('off')

    # Save and close
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
    
    # Add the base grid in light gray
    element_size = get_size_of_point(m,n,map_type)
    ax.scatter(X, Y, c='#FBFBFB', s=element_size, marker='h' if map_type == 'hex' else 's')
    
    for pos, cnts in data['counts'].items():
        i, j = map(int, pos.split('_'))
        idx = i * n + j
        x, y = X[idx], Y[idx]
        total = sum(cnts[k] for k in cat_keys)
        if total == 0:
            continue

        # compute fractions
        fracs = [cnts[k] / total for k in cat_keys]
        nonzero = [f for f in fracs if f > 0]

        if len(nonzero) == 1:
            # single category → full circle
            k0 = fracs.index(1.0)
            circ = Circle(
                (x, y), radius,
                facecolor=cmap(k0 / len(cat_keys)),
                edgecolor='white'
            )
            ax.add_patch(circ)
        else:
            # multiple segments
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

    # Generate a separate legend for the pie chart
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
            point_size = 2300  # default for hex
    else:
        if m == 10:
            point_size = 5500
        elif m == 20:
            point_size = 1100
        elif m == 30:
            point_size = 450
        else:
            point_size = 1100  # default for square
    return point_size

def generate_distance_map_from_error_map(som, neuron_error_map: np.ndarray, output_file: str,
                                    map_type: str = 'square', cmap: str = 'magma', save_legend: bool = True):
    """
    Displays the mean quantization error per neuron from a precomputed error map.

    Args:
        som: SOM instance with m, n attributes
        neuron_error_map: Precomputed error map
        output_file: Path to the output file
        map_type: Grid type ('square' or 'hex')
        cmap: Colormap name
        save_legend: Whether to generate a separate legend
    """
    check_folder(output_file)
    m, n = som.m, som.n

    # Normalize values to the [0,1] range
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

    # Generate a separate legend
    if save_legend:
        generate_legend(
            vmin=vmin,
            vmax=vmax,
            output_file=output_file,
            cmap=cmap,
            label='Mean quantization error'
        )

def sanitize_filename(filename: str) -> str:
    """Converts a column name into a safe file name.

    Args:
        filename (str): Original name

    Returns:
        str: Safe file name
    """
    # Replace unsafe characters
    filename = filename.lower()
    filename = filename.replace(' ', '_')
    # Remove diacritics
    filename = ''.join(c for c in filename if c.isalnum() or c in '_-')
    return filename

def generate_mqe_history_plot(som, output_file: str):
    """Plots the quantization error evolution during training.

    Args:
        som: SOM instance with mqe_history and epochs_history attributes
        output_file: Path to the output file
    """
    check_folder(output_file)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot the MQE curve
    ax.plot(som.epochs_history, som.mqe_history, 'b-', linewidth=2)

    # Highlight the best value reached
    best_mqe_idx = np.argmin(som.mqe_history)
    best_mqe = som.mqe_history[best_mqe_idx]
    best_epoch = som.epochs_history[best_mqe_idx]
    ax.plot(best_epoch, best_mqe, 'ro', markersize=10, label=f'Best MQE: {best_mqe:.6f}')
    
    # Set labels
    ax.set_xlabel('Training Steps', fontsize=12)
    ax.set_ylabel('MQE', fontsize=12)
    ax.set_title('Quantization Error Convergence', fontsize=14, pad=20)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(fontsize=10)

    # Set axis format
    ax.tick_params(axis='both', which='major', labelsize=10)

    # Save the plot
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def generate_parameters_history_plot(som, output_file: str):
    """Plots the evolution of learning parameters during training.

    Args:
        som: SOM instance with learning_rate_history, radius_history and epochs_history attributes
        output_file: Path to the output file
    """
    check_folder(output_file)

    # Create a figure with 2 or 3 subplots depending on batch_size_history availability
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
    # grid parameter — take it from the trained SOM so the plots match the training grid
    map_type = som.map_type

    # pull out the columns that were normalized
    df_all = pd.read_csv(f"{output_path}/csv/input.csv", delimiter=',')
    # take only numerical columns
    numeric_cols = settings['numerical_column']
    df_num = df_all[numeric_cols]

    # the data were scaled with MinMaxScaler, so min and range are needed to scale weights back
    mins = df_num.min().values
    ranges = (df_num.max() - df_num.min()).values

    # 1) U‑Matrix
    generate_u_matrix(
        som,
        f"{output_path}/visualization/u-matrix.png",
        map_type=map_type
    )

    # 2) Hit map
    generate_hit_map(
        som,
        data,
        f"{output_path}/visualization/hit.png",
        map_type,
        'Blues',
        True,
        True
    )

    # 3) Component plane for each dimension
    # Load the CSV header for column names
    df = pd.read_csv(preprocess_file, delimiter=';', nrows=0)
    column_names = df.columns.tolist()

    # Split column names by commas before the loop
    column_names_list = column_names[0].split(',') if column_names else []

    for dim in range(som.dim):
        # Skip map generation for the primary_id column
        if dim < len(column_names_list) and column_names_list[dim] == settings['primary_id']:
            continue

        col_name = column_names_list[dim] if dim < len(column_names_list) else None
        
        # If there is no column name, use the dimension number
        safe_name = sanitize_filename(col_name) if col_name else f"dimension_{dim}"

        # if this column is numerical, find its index in numeric_cols
        if col_name in numeric_cols:
            idx = numeric_cols.index(col_name)
            data_min = mins[idx]
            data_range = ranges[idx]
        else:
            data_min = data_range = None

        generate_component_plane(
            som,
            component=dim,
            output_file=f"{output_path}/visualization/component_{safe_name}.png",
            map_type=map_type,
            cmap='coolwarm',
            column_name=col_name,
            save_legend=True,
            data_min=data_min,
            data_range=data_range
        )

    # 4) Cluster map
    clusters = json.load(open(f"{output_path}/json/clusters.json", encoding="utf-8"))
    generate_cluster_map(
        som,
        clusters,
        f"{output_path}/visualization/cluster.png",
        map_type=map_type
    )

    # 5) Distance map (mean quantization error) and saving errors to JSON
    codebook_vectors = som.weights.reshape(-1, som.dim)
    bmu_indexes = np.array([som.find_bmu(x)[0] * som.n + som.find_bmu(x)[1] for x in data])
    original_neuron_error_map, total_quantization_error = som.compute_quantization_error(data, codebook_vectors, bmu_indexes, (som.m, som.n), compute_neuron_map=True)    
    # Save errors to JSON
    save_quantization_error_to_json(original_neuron_error_map, total_quantization_error, output_path)

    generate_distance_map_from_error_map(
        som,
        original_neuron_error_map,
        f"{output_path}/visualization/distance.png",
        map_type=map_type
    )

    # 6) Quantization error evolution plot
    if hasattr(som, 'mqe_history') and len(som.mqe_history) > 0:
        generate_mqe_history_plot(
            som,
            f"{output_path}/visualization/mqe-history.png"
        )

    # 7) Learning parameters evolution plot
    if (hasattr(som, 'learning_rate_history') and len(som.learning_rate_history) > 0 and
        hasattr(som, 'radius_history') and len(som.radius_history) > 0):
        
        generate_parameters_history_plot(
            som,
            f"{output_path}/visualization/parameters-history.png"
        )
    else:
        print("Debug - Missing parameter history:")
        print(f"Learning rate history exists: {hasattr(som, 'learning_rate_history')}, length: {len(som.learning_rate_history) if hasattr(som, 'learning_rate_history') else 0}")
        print(f"Radius history exists: {hasattr(som, 'radius_history')}, length: {len(som.radius_history) if hasattr(som, 'radius_history') else 0}")
        print(f"Batch size history exists: {hasattr(som, 'batch_size_history')}, length: {len(som.batch_size_history) if hasattr(som, 'batch_size_history') else 0}")

    # Plot individual categorical columns
    for column_name in settings['categorical_column']:
        if not any(column_name in group for group in settings.get('categorical_groups', {}).values()):
            plot_pie_map_from_json(
                som,
                f"{output_path}/json/pie_data_{column_name}.json",
                f"{output_path}/visualization/pie-map_{column_name}.png",
                map_type
            )
    
    # Plot groups of categorical columns
    for group_name, columns in settings.get('categorical_groups', {}).items():
        json_files = [f"{output_path}/json/pie_data_{col}.json" for col in columns]
        combined_data = {
            'categories': {},
            'counts': defaultdict(lambda: defaultdict(int))
        }
        
        # Merge data from all JSON files in the group
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Add categories prefixed with the column name
                column_name = os.path.basename(json_file).replace('pie_data_', '').replace('.json', '')
                for k, v in data['categories'].items():
                    # Keep the original numeric keys, but add a prefix to distinguish them
                    combined_data['categories'][f"{column_name}_{k}"] = f"{column_name}: {v}"

                # Merge counts
                for pos, counts in data['counts'].items():
                    for k, v in counts.items():
                        combined_data['counts'][pos][f"{column_name}_{k}"] = v
        
        # Convert data to the format expected by plot_pie_map_from_json
        formatted_data = {
            'categories': {},
            'counts': {}
        }
        
        # Sort categories by the numeric part of the key
        sorted_keys = sorted(combined_data['categories'].keys(), 
                           key=lambda x: int(x.split('_')[-1]))
        
        # Renumber categories starting from 1
        for new_key, old_key in enumerate(sorted_keys, 1):
            formatted_data['categories'][str(new_key)] = combined_data['categories'][old_key]
            
            # Recompute counts for the new keys
            for pos in combined_data['counts']:
                if pos not in formatted_data['counts']:
                    formatted_data['counts'][pos] = {}
                if old_key in combined_data['counts'][pos]:
                    formatted_data['counts'][pos][str(new_key)] = combined_data['counts'][pos][old_key]
        
        # Save the reformatted data to a temporary JSON file
        temp_json = f"{output_path}/json/temp_pie_data_{group_name}.json"
        with open(temp_json, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False)
        
        # Plot using the existing function
        plot_pie_map_from_json(
            som,
            temp_json,
            f"{output_path}/visualization/pie_map_group_{group_name}.png",
            map_type
        )

    # 8) Topographic map: check topology preservation (original data vs. organized SOM grid)
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

    # 9) 3D topographic map (rotatable) — requires at least 3 input space dimensions
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
    Returns the list of edges (pairs of neighboring neurons) of the SOM grid.
    Uses the same neighborhood convention as `_grid_coordinates` (offset rows
    for hex) so that the topographic map visually matches the other maps
    in this file.

    Args:
        m: Number of grid rows
        n: Number of grid columns
        map_type: Grid type ('square' or 'hex')

    Returns:
        list: List of edges in the form [((i1,j1),(i2,j2)), ...]
    """
    edges = []
    for i in range(m):
        for j in range(n):
            if j + 1 < n:
                edges.append(((i, j), (i, j + 1)))
            if i + 1 < m:
                if map_type == 'hex':
                    # Even/odd rows are shifted by half a cell in `_grid_coordinates`
                    neighbours = (j - 1, j) if i % 2 == 0 else (j, j + 1)
                    for nj in neighbours:
                        if 0 <= nj < n:
                            edges.append(((i, j), (i + 1, nj)))
                else:
                    edges.append(((i, j), (i + 1, j)))
    return edges


def _topology_edge_lengths(weights_proj_grid: np.ndarray, edges: list, threshold_pct: float = 85):
    """
    Computes the length of each grid edge in the projected (2D) space and flags
    edges that are unusually stretched (above the `threshold_pct` percentile).

    A stretched/crossed edge means that two neighboring neurons in the SOM grid
    actually represent very different data — i.e. the network did not preserve
    the topology of the input space at that spot (or it is an artifact of the
    2D projection).

    Returns:
        tuple: (edge lengths, boolean mask of stretched edges)
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
    Prepares a joint 2D/3D projection (PCA) of the original input data and
    the trained SOM neuron weights, and computes the grid geometry on top of it.

    Data and weights are projected with one and the same PCA (fitted on both
    together), so the result can be compared visually: the point cloud is the
    original data, the edge-connected grid is the "organized" SOM representation.
    If the network preserved the topology, the grid follows the shape of the
    cloud without crossings; stretched/crossed edges indicate a topological error.

    Args:
        som: Trained SOM instance with m, n, dim and weights attributes
        data: Input (normalized) training data, shape (n_samples, dim)
        map_type: Grid type ('square' or 'hex')
        n_components: Number of projection dimensions (2 for a 2D map, 3 for a rotatable 3D map)
        sample_limit: Maximum number of data samples to plot (performance/file size)
        random_seed: Seed for random sample selection when limiting their number

    Returns:
        dict | None: Dictionary with keys 'data_proj', 'weights_proj' (shape m,n,n_components),
            'edges', 'lengths', 'stretched' and 'var_exp', or None if the input
            space has fewer dimensions than `n_components` requires
    """
    m, n, dim = som.m, som.n, som.dim
    weights_flat = som.weights.reshape(-1, dim)

    if dim < n_components:
        print(f"Topographic map: skipped, the input space has fewer than {n_components} dimensions.")
        return None

    # Limit the number of plotted samples for performance and output file size
    if len(data) > sample_limit:
        rng = np.random.default_rng(random_seed)
        sample_idx = rng.choice(len(data), size=sample_limit, replace=False)
        data_sample = data[sample_idx]
    else:
        data_sample = data

    # Joint PCA over data and weights so both share the same coordinate system
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
    Plots a static topographic map: the original data cloud projected to
    2D (PCA) with the SOM neuron grid overlaid. Used to check topology
    preservation — stretched edges (orange) mark places where the network did
    not preserve the input data topology (or it is a 2D projection artifact).

    Args:
        som: Trained SOM instance with m, n attributes
        projection: Output of `compute_topology_projection`
        neuron_error_map: Per-neuron quantization error map (for coloring neurons)
        output_file: Path to the output PNG file
        map_type: Grid type ('square' or 'hex'), used only for the plot title
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

    # Layer 1: original data (slightly transparent, in the background)
    ax.scatter(data_proj[:, 0], data_proj[:, 1], color='#2980b9', alpha=0.15,
              s=4, zorder=1, linewidths=0)

    # Layer 2: grid edges, colored by stretch
    for e_idx, ((i1, j1), (i2, j2)) in enumerate(edges):
        ax.plot(
            [weights_proj[i1, j1, 0], weights_proj[i2, j2, 0]],
            [weights_proj[i1, j1, 1], weights_proj[i2, j2, 1]],
            color='#e67e22' if stretched[e_idx] else '#2c3e50',
            lw=lw, alpha=0.6 if stretched[e_idx] else 0.8, zorder=3,
        )

    # Layer 3: neurons colored by mean quantization error
    nqe_flat = neuron_error_map.ravel()
    sc = ax.scatter(
        weights_proj[:, :, 0].ravel(), weights_proj[:, :, 1].ravel(),
        c=nqe_flat, cmap='plasma', s=dot_size, zorder=5,
        edgecolors='white', linewidths=0.4,
    )
    plt.colorbar(sc, ax=ax, label='Mean quantization error per neuron', shrink=0.75)

    var_str = f'PC1 {var_exp[0]:.1%} / PC2 {var_exp[1]:.1%}' if len(var_exp) >= 2 else f'PC1 {var_exp[0]:.1%}'
    n_stretched = int(stretched.sum())
    ax.set_title(
        f'Topographic map — original data vs. organized SOM grid\n'
        f'{m}×{n}, {"hex" if map_type == "hex" else "square"}  |  {var_str}  |  '
        f'stretched edges: {n_stretched} (possible topological error)',
        fontsize=11,
    )
    ax.set_xlabel('Component 1', fontsize=10)
    ax.set_ylabel('Component 2', fontsize=10)

    legend = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#2980b9',
              markersize=8, alpha=0.7, label='Original data'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='crimson',
              markersize=8, label='Neuron (color = quantization error)'),
        Line2D([0], [0], color='#2c3e50', lw=1.2, label='Grid edge (OK)'),
        Line2D([0], [0], color='#e67e22', lw=1.2, label='Stretched edge (possible topological error)'),
    ]
    ax.legend(handles=legend, fontsize=8, loc='best')

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close(fig)


def generate_topology_map_html(som, projection: dict, neuron_error_map: np.ndarray,
                              output_file: str, map_type: str = 'square'):
    """
    Plots an interactive HTML version of the topographic map (Plotly.js via CDN,
    without requiring the plotly package on the backend). Supports zooming
    and hovering over a neuron to show its coordinates and mean
    quantization error.

    Args:
        som: Trained SOM instance with m, n attributes
        projection: Output of `compute_topology_projection`
        neuron_error_map: Per-neuron quantization error map
        output_file: Path to the output HTML file
        map_type: Grid type ('square' or 'hex'), used only for the plot title
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
            'name': 'Original data',
            'hoverinfo': 'skip',
        },
    ]

    # Grid edges as two separate traces (normal / stretched) so they can be
    # toggled independently in the legend
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
        'name': 'Grid edge (OK)', 'hoverinfo': 'skip', 'opacity': 0.75,
    })
    if edge_x['stretched']:
        traces.append({
            'type': 'scatter', 'mode': 'lines',
            'x': edge_x['stretched'], 'y': edge_y['stretched'],
            'line': {'color': '#e67e22', 'width': 1, 'dash': 'dot'},
            'name': 'Stretched edge (possible topological error)',
            'hoverinfo': 'skip', 'opacity': 0.6,
        })

    hover_text = [
        f'Neuron [{i},{j}]<br>Mean quantization error: {neuron_error_map[i, j]:.4f}'
        for i in range(m) for j in range(n)
    ]
    traces.append({
        'type': 'scatter', 'mode': 'markers',
        'x': weights_proj[:, :, 0].ravel().tolist(),
        'y': weights_proj[:, :, 1].ravel().tolist(),
        'marker': {
            'color': nqe_flat.tolist(), 'colorscale': 'Plasma', 'size': 8,
            'colorbar': {'title': 'Mean QE', 'thickness': 14},
            'line': {'color': 'white', 'width': 0.5},
        },
        'text': hover_text, 'hovertemplate': '%{text}<extra></extra>',
        'name': 'SOM neurons',
    })

    var_str = f'PC1 {var_exp[0]:.1%} / PC2 {var_exp[1]:.1%}' if len(var_exp) >= 2 else f'PC1 {var_exp[0]:.1%}'
    n_stretched = int(stretched.sum())
    layout = {
        'title': {
            'text': (f'Topographic map — original data vs. organized SOM grid<br>'
                     f'<sub>{m}×{n}, {"hex" if map_type == "hex" else "square"} | {var_str} | '
                     f'stretched edges: {n_stretched}</sub>'),
            'font': {'size': 14},
        },
        'xaxis': {'title': 'Component 1'},
        'yaxis': {'title': 'Component 2', 'scaleanchor': 'x'},
        'plot_bgcolor': '#f8f8f8',
        'hovermode': 'closest',
        'autosize': True,
        'margin': {'l': 40, 'r': 40, 't': 80, 'b': 40},
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SOM Topographic Map</title>
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
    Plots an interactive ROTATABLE 3D version of the topographic map (Plotly.js
    Scatter3d via CDN, without requiring the plotly package on the backend).
    Dragging with the mouse rotates the camera — a single fixed view often
    hides whether the grid is a continuous sheet or folded/crossed somewhere.

    Args:
        som: Trained SOM instance with m, n attributes
        projection: Output of `compute_topology_projection(..., n_components=3)`
        neuron_error_map: Per-neuron quantization error map
        output_file: Path to the output HTML file
        map_type: Grid type ('square' or 'hex'), used only for the plot title
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
            'name': 'Original data',
            'hoverinfo': 'skip',
        },
    ]

    # Grid edges as two separate traces (normal / stretched)
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
        'name': 'Grid edge (OK)', 'hoverinfo': 'skip', 'opacity': 0.75,
    })
    if edge_x['stretched']:
        traces.append({
            'type': 'scatter3d', 'mode': 'lines',
            'x': edge_x['stretched'], 'y': edge_y['stretched'], 'z': edge_z['stretched'],
            'line': {'color': '#e67e22', 'width': 2},
            'name': 'Stretched edge (possible topological error)',
            'hoverinfo': 'skip', 'opacity': 0.6,
        })

    hover_text = [
        f'Neuron [{i},{j}]<br>Mean quantization error: {neuron_error_map[i, j]:.4f}'
        for i in range(m) for j in range(n)
    ]
    traces.append({
        'type': 'scatter3d', 'mode': 'markers',
        'x': weights_proj[:, :, 0].ravel().tolist(),
        'y': weights_proj[:, :, 1].ravel().tolist(),
        'z': weights_proj[:, :, 2].ravel().tolist(),
        'marker': {
            'color': nqe_flat.tolist(), 'colorscale': 'Plasma', 'size': 4,
            'colorbar': {'title': 'Mean QE', 'thickness': 14},
            'line': {'color': 'white', 'width': 0.5},
        },
        'text': hover_text, 'hovertemplate': '%{text}<extra></extra>',
        'name': 'SOM neurons',
    })

    var_str = f'PC1 {var_exp[0]:.1%} / PC2 {var_exp[1]:.1%} / PC3 {var_exp[2]:.1%}'
    n_stretched = int(stretched.sum())
    layout = {
        'title': {
            'text': (f'Topographic map 3D — original data vs. organized SOM grid<br>'
                     f'<sub>{m}×{n}, {"hex" if map_type == "hex" else "square"} | {var_str} | '
                     f'stretched edges: {n_stretched} | drag to rotate the view</sub>'),
            'font': {'size': 14},
        },
        'scene': {
            'xaxis': {'title': 'Component 1'},
            'yaxis': {'title': 'Component 2'},
            'zaxis': {'title': 'Component 3'},
            'aspectmode': 'data',
        },
        'hovermode': 'closest',
        'autosize': True,
        'margin': {'l': 10, 'r': 10, 't': 80, 'b': 10},
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SOM Topographic Map 3D</title>
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