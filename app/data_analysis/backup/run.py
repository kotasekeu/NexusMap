
# Funkce pro trénink SOM s monitorováním kvantizační chyby, dynamickým learning rate a sigma
def train_som_with_monitoring(som, data, num_iterations, initial_learning_rate, initial_sigma, final_sigma,
                              log_file_path):
    quantization_errors = []

    np.random.seed(random_seed)  # Nastavení pevného náhodného semene uvnitř funkce
    with open(log_file_path, 'w') as log_file:
        for i in range(num_iterations):
            sample = data[np.random.randint(0, len(data))]
            bmu = som.winner(sample)
            current_learning_rate = initial_learning_rate * (1 - i / num_iterations)
            current_sigma = initial_sigma * (1 - i / num_iterations) + final_sigma * (i / num_iterations)
            som.learning_rate = current_learning_rate
            som.sigma = current_sigma
            som.update(sample, bmu, i, num_iterations)
            log_file.write(f'Iteration {i + 1}: Learning rate = {current_learning_rate}, sigma = {current_sigma}\n')
            if (i + 1) % (num_iterations // 20) == 0:  # Logování každých 5%
                quantization_error = np.mean(
                    [np.linalg.norm(sample - som._weights[som.winner(sample)]) for sample in data])
                quantization_errors.append(quantization_error)
                print(
                    f'Iteration {i + 1}/{num_iterations} - Learning rate: {current_learning_rate}, sigma: {current_sigma}, quantization error: {quantization_error}')

    return quantization_errors


# Trénink SOM
log_file_path = config.output_files['log_file']
quantization_errors = train_som_with_monitoring(som, data_normalized, num_iterations, initial_learning_rate,
                                                initial_sigma, final_sigma, log_file_path)


def visualize_som_with_precise_points_and_save_clusters(som, data, df, title, filename, cluster_filename):
    plt.figure(figsize=(15, 15))

    # Generování barev pro různé státy
    unique_legend_values = df[config.legend_column].unique()
    color_map = plt.get_cmap('hsv', len(unique_legend_values))
    legend_colors = {value: color_map(i) for i, value in enumerate(unique_legend_values)}

    grid_counts = np.zeros((som.get_weights().shape[0], som.get_weights().shape[1]))
    clusters = {}

    for cnt, xx in enumerate(data):
        w = som.winner(xx)
        grid_counts[w[0], w[1]] += 1
        cluster_key = f"({int(w[0])}, {int(w[1])})"
        if cluster_key not in clusters:
            clusters[cluster_key] = []
        clusters[cluster_key].append(df.iloc[cnt].to_dict())

    for cnt, xx in enumerate(data):
        w = som.winner(xx)
        plt.plot(w[0] + np.random.rand() * 0.9, w[1] + np.random.rand() * 0.9,
                 'o', markerfacecolor=legend_colors[df[config.legend_column].iloc[cnt]],
                 markeredgecolor=legend_colors[df[config.legend_column].iloc[cnt]], markersize=2)

    plt.xlim(0, som.get_weights().shape[0])
    plt.ylim(0, som.get_weights().shape[1])
    plt.grid()

    legend_elements = [Line2D([0], [0], marker='o', color='w', label=f'{value}',
                              markerfacecolor=color, markeredgecolor=color, markersize=12)
                       for value, color in legend_colors.items()]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1), title=config.legend_title)

    plt.title(title)
    plt.savefig(filename)
    plt.close()

    with open(cluster_filename, 'w', encoding='utf-8') as f:
        json.dump(clusters, f, indent=4)


# Volání funkce pro vizualizaci a uložení clusterů
visualize_som_with_precise_points_and_save_clusters(
    som, data_normalized, df, 'SOM Heatmap with Precise Points',
    config.output_files['som_map'], config.output_files['clusters_json']
)


# Funkce pro analýzu clusterů a generování HTML
def analyze_clusters_detailed(cluster_file):
    with open(cluster_file, 'r', encoding='utf-8') as f:
        clusters = json.load(f)

    clusters = {eval(key): value for key, value in clusters.items()}
    cluster_sizes = {key: len(items) for key, items in clusters.items()}

    # Vypočítat průměrné hodnoty pro každý cluster
    cluster_stats = {}
    for key, items in clusters.items():
        stats = {}
        for col in config.analysis_columns:
            values = [item[col] if item[col] is not None else 0 for item in items]
            stats[f'avg_{col}'] = np.mean(values) if values else 0
        stats['size'] = len(items)
        cluster_stats[key] = stats

    # Vypočítat počet cest do jednotlivých zemí v každém clusteru
    country_stats = {}
    for key, items in clusters.items():
        country_counts = {}
        for item in items:
            country = item[config.legend_column]
            if country not in country_counts:
                country_counts[country] = 0
            country_counts[country] += 1
        country_stats[key] = country_counts

    # Identifikace extrémů
    extremes = {}
    for key, items in clusters.items():
        for col in config.analysis_columns:
            values = [item[col] if item[col] is not None else 0 for item in items]
            avg_value = np.mean(values)
            std_value = np.std(values)
            extreme_items = [item for item in items if abs(item[col] - avg_value) > config.standard_deviation_value * std_value]
            if extreme_items:
                if key not in extremes:
                    extremes[key] = {}
                extremes[key][f'{col}_extremes'] = extreme_items

    # Vytvoření HTML výstupu

    html_output = "<!DOCTYPE HTML><html lang = 'cs'><head><meta charset = 'UTF-8'><style>"
    html_output += "table { width: 100%; border-collapse: collapse; }"
    html_output += "th, td { border: 1px solid black; padding: 8px; text-align: left; }"
    html_output += ".extreme { font-weight: bold; color: red; }"
    html_output += ".hidden { display: none; }"
    html_output += "</style></head><body>"

    for key, items in clusters.items():
        html_output += f"<h2>Cluster {key}:</h2>"
        stats = cluster_stats[key]
        html_output += f"<p>Size = {stats['size']}"
        for col in config.analysis_columns:
            html_output += f", Avg {col.capitalize()} = {stats[f'avg_{col}']:.2f}"
        html_output += "</p>"

        html_output += "<p>Country Stats:</p><ul>"
        for country, count in country_stats[key].items():
            html_output += f"<li>{country}: {count} trips</li>"
        html_output += "</ul>"

        # Extremes
        if key in extremes:
            for col in config.analysis_columns:
                if f'{col}_extremes' in extremes[key]:
                    html_output += f"<h3>{col.capitalize()} Extremes:</h3><table><tr>"
                    for col_name in items[0].keys():
                        html_output += f"<th>{col_name}</th>"
                    html_output += "</tr>"
                    for item in extremes[key][f'{col}_extremes']:
                        html_output += "<tr>"
                        for col_name, val in item.items():
                            if col_name == col:
                                html_output += f"<td class='extreme'>{val}</td>"
                            else:
                                html_output += f"<td>{val}</td>"
                        html_output += "</tr>"
                    html_output += "</table>"

        # All data in cluster
        html_output += f"<button onclick=\"document.getElementById('data_{key}').classList.toggle('hidden')\">Zobrazit data</button>"
        html_output += f"<div id='data_{key}' class='hidden'><table><tr>"
        for col_name in items[0].keys():
            html_output += f"<th>{col_name}</th>"
        html_output += "</tr>"
        for item in items:
            html_output += "<tr>"
            for col_name, val in item.items():
                html_output += f"<td>{val}</td>"
            html_output += "</tr>"
        html_output += "</table></div>"

    html_output += "</body></html>"

    with open(config.output_files['html_output'], 'w', encoding='utf-8') as f:
        f.write(html_output)

    return clusters, cluster_stats, country_stats, extremes


# Volání funkce pro analýzu a generování HTML
clusters, cluster_stats, country_stats, extremes = analyze_clusters_detailed(config.output_files['clusters_json'])