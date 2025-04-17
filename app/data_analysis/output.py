import matplotlib.pyplot as plt
import numpy as np
import datetime

# def save_clusters(output_path: str, clusters: dict) -> None:
#     """Uloží clustery do souboru clusters.txt."""
#     pass
#

def generate_heatmap(som, data, output_path: str) -> None:
    """Generuje heatmapu SOM a ukládá ji jako map.jpg."""
    plt.figure(figsize=(10, 10))
    for sample in data:
        bmu = som.find_bmu(sample)
        plt.scatter(bmu[0] + np.random.rand() * 0.8, bmu[1] + np.random.rand() * 0.8, c="blue", alpha=0.5)

    plt.title("SOM Heatmap")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Uložení souboru s timestampem v názvu
    plt.savefig(f"{output_path}map_{timestamp}.jpg")
    plt.close()
