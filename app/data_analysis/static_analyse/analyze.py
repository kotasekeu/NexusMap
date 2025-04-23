# import sys
# import json
# import os
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# from sklearn.preprocessing import StandardScaler, MinMaxScaler
# from sklearn.metrics import pairwise_distances_argmin_min
# from collections import defaultdict, Counter
# import math
# from datetime import datetime
# import argparse
# from project_processor import process_project

# class KohonenSOM:
#     def __init__(self, m: int, n: int, dim: int, learning_rate: float = 0.9, min_learning_rate: float = 0.1,
#                  radius: float = None, min_radius: float = 0.1,
#                  num_batches: int = 10, min_batch_percent: float = 0.1, max_batch_percent: float = 5,
#                  lr_decay_type: str = 'exp-drop', radius_decay_type: str = 'exp-drop', batch_growth_type: str = 'exp-growth',
#                  random_seed: int = None, growth_g: float = 15.0, normalize_weights_flag: bool = False, 
#                  epoch_multiplier: float = 1.0, map_type: str = 'hex', min_q_error: float = None):
#         """Inicializace Kohonenovy sítě s výchozími hodnotami."""
#         self.m = m
#         self.n = n
#         self.dim = dim
#         self.learning_rate = learning_rate
#         self.min_learning_rate = min_learning_rate
#         self.radius = radius if radius else max(m, n) / 2
#         self.min_radius = min_radius

#         self.num_batches = num_batches
#         self.min_batch_percent = min_batch_percent
#         self.max_batch_percent = max_batch_percent

#         self.lr_decay_type = lr_decay_type
#         self.radius_decay_type = radius_decay_type
#         self.batch_growth_type = batch_growth_type

#         self.growth_g = growth_g
#         self.epoch_multiplier = epoch_multiplier
#         self.map_type = map_type
#         self.normalize_weights_flag = normalize_weights_flag    
#         self.min_q_error = min_q_error

#         if random_seed is not None:
#             np.random.seed(random_seed)

#         self.weights = np.random.rand(m, n, dim)
#         self.normalize_weights()

#     def normalize_weights(self):
#         """Normalizuje váhy sítě."""
#         for i in range(self.m):
#             for j in range(self.n):
#                 norm = np.linalg.norm(self.weights[i, j])
#                 if norm > 0:
#                     self.weights[i, j] /= norm

#     @staticmethod
#     def get_decay_value(t: int, N: int, start: float, end: float, decay_type: str, growth_g: float = 15.0) -> float:
#         """Vypočítá hodnotu útlumu podle zadaného typu."""
#         if decay_type == 'logarithmic':
#             return start - (np.log10(t + 1) / np.log10(N)) * (start - end)
#         elif decay_type == 'linear-growth':
#             return start + (t / (N - 1)) * (end - start)
#         elif decay_type == 'linear-drop':
#             return start - (t / (N - 1)) * (start - end)
#         elif decay_type == 'exponential':
#             k = np.log(start / end) / N
#             return start * np.exp(-k * t)
#         elif decay_type == 'exp-growth':
#             return start + (end - start) * (np.exp(growth_g * t / N) - 1) / (np.exp(growth_g) - 1)
#         elif decay_type == 'exp-drop':
#             log_max = np.log(N + 1)
#             return end + (np.log(N - t + 1) / log_max) * (start - end)
#         else:
#             raise ValueError("Unknown decay type")

#     @staticmethod
#     def get_batch_percent(t: int, N: int, min_batch_percent: float, max_batch_percent: float, batch_growth_type: str, growth_g: float) -> float:
#         """Vypočítá procento vzorků pro batch."""
#         return KohonenSOM.get_decay_value(t, N, min_batch_percent, max_batch_percent, batch_growth_type, growth_g)

#     @staticmethod
#     def calculate_mqe(weights: np.ndarray, data: np.ndarray) -> float:
#         """Vypočítá Mean Quantization Error."""
#         weights_flat = weights.reshape(-1, data.shape[1])
#         _, distances = pairwise_distances_argmin_min(data, weights_flat)
#         return np.mean(distances)

#     @staticmethod
#     def find_bmu(weights: np.ndarray, sample: np.ndarray, n: int) -> tuple[int, int]:
#         """Najde Best Matching Unit pro vzorek."""
#         flat = weights.reshape(-1, sample.shape[0])
#         diffs = flat - sample
#         dists = np.linalg.norm(diffs, axis=1)
#         idx = np.argmin(dists)
#         return divmod(idx, n)

#     @staticmethod
#     def grid_distance(a: tuple[int,int], b: tuple[int,int], map_type: str) -> float:
#         """Vypočítá vzdálenost v mřížce."""
#         i1, j1 = a;  i2, j2 = b
#         if map_type == 'square':
#             return math.hypot(i1 - i2, j1 - j2)
#         q1, r1 = j1, i1
#         q2, r2 = j2, i2
#         x1, z1 = q1, r1;  y1 = -x1 - z1
#         x2, z2 = q2, r2;  y2 = -x2 - z2
#         return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) / 2

#     @staticmethod
#     def update_weights(weights: np.ndarray, sample: np.ndarray, bmu_idx: tuple[int,int], 
#                       learning_rate: float, radius: float, map_type: str) -> np.ndarray:
#         """Aktualizuje váhy sítě."""
#         m, n, dim = weights.shape
#         new_weights = weights.copy()
        
#         for i in range(m):
#             for j in range(n):
#                 distance_to_bmu = KohonenSOM.grid_distance((i, j), bmu_idx, map_type)
#                 if distance_to_bmu <= radius:
#                     influence = np.exp(-distance_to_bmu ** 2 / (2 * (radius ** 2)))
#                     new_weights[i, j] += influence * learning_rate * (sample - weights[i, j])
        
#         return new_weights

#     def train(self, data: np.ndarray) -> None:
#         """Trénuje SOM síť."""
#         print(f"Epocha|počet zpracovanych vektorů celkem|počet vektorů zpracovaných v batch|radius|lr|MQE")
#         total_samples = data.shape[0]
#         total_epochs = int(total_samples * self.epoch_multiplier)
#         total_weight_updates = 0
#         total_processed_samples = 0
#         best_mqe = float('inf')
#         no_improvement_count = 0
#         patience = 50

#         for epoch in range(total_epochs):
#             batch_percent = self.get_batch_percent(
#                 epoch, total_epochs, 
#                 self.min_batch_percent, 
#                 self.max_batch_percent,
#                 self.batch_growth_type,
#                 self.growth_g
#             )
#             total_samples_to_process = math.ceil(total_samples * batch_percent / 100)
#             samples_per_batch = math.ceil(total_samples_to_process / self.num_batches)
#             total_processed_samples += (samples_per_batch * self.num_batches)

#             for batch_idx in range(self.num_batches):
#                 start_idx = batch_idx * (total_samples // self.num_batches)
#                 end_idx = min((batch_idx + 1) * (total_samples // self.num_batches), total_samples)
#                 batch_data = data[start_idx:end_idx]

#                 if samples_per_batch < len(batch_data):
#                     batch_indices = np.random.choice(len(batch_data), samples_per_batch, replace=False)
#                     batch_data = batch_data[batch_indices]

#                 current_lr = self.get_decay_value(
#                     epoch, total_epochs, 
#                     self.learning_rate, 
#                     self.min_learning_rate,
#                     self.lr_decay_type,
#                     self.growth_g
#                 )
#                 current_radius = self.get_decay_value(
#                     epoch, total_epochs, 
#                     self.radius, 
#                     self.min_radius,
#                     self.radius_decay_type,
#                     self.growth_g
#                 )

#                 for sample in batch_data:
#                     bmu_idx = self.find_bmu(self.weights, sample, self.n)
#                     self.weights = self.update_weights(
#                         self.weights, sample, bmu_idx, 
#                         current_lr, current_radius, self.map_type
#                     )
#                     total_weight_updates += 1

#                     if self.normalize_weights_flag:
#                         self.normalize_weights()        

#             current_mqe = self.calculate_mqe(self.weights, data)
#             if self.min_q_error is not None and current_mqe <= self.min_q_error:
#                 print(f"Dosažena limitní MQE {self.min_q_error}. Ukončuji trénování.")
#                 break

#             if current_mqe < best_mqe:
#                 best_mqe = current_mqe
#                 no_improvement_count = 0
#             else:
#                 no_improvement_count += 1
#                 if no_improvement_count >= patience:
#                     print(f"Žádné zlepšení po {patience} epochách. Ukončuji trénování.")
#                     break

#             if epoch % 100 == 0:                
#                 print(f"{epoch}|{total_samples_to_process}|{samples_per_batch}|{current_radius:.4f}|{current_lr:.6f}|{current_mqe:.6f}")                

#         print(f"\nSouhrn trénování:")
#         print(f"Celkový počet aktualizací vah: {total_weight_updates}")
#         print(f"Nejlepší dosažená MQE: {best_mqe:.6f}")

# def validate_files(input_file: str, project_config_file: str, som_config_file: str = None, output_dir: str = None) -> tuple[dict, dict, str]:
#     """
#     Validuje vstupní soubory a načítá konfigurace.
    
#     Args:
#         input_file: Cesta k vstupnímu CSV souboru
#         project_config_file: Cesta k konfiguračnímu souboru projektu
#         som_config_file: Cesta k konfiguračnímu souboru SOM (volitelné)
#         output_dir: Cesta k cílovému adresáři (volitelné)
        
#     Returns:
#         Tuple obsahující (project_config, som_config, output_dir)
        
#     Raises:
#         FileNotFoundError: Pokud některý ze souborů neexistuje
#         json.JSONDecodeError: Pokud některý z konfiguračních souborů není platný JSON
#     """
#     # Kontrola existence souborů
#     if not os.path.exists(input_file):
#         raise FileNotFoundError(f"Vstupní soubor {input_file} neexistuje.")
    
#     if not os.path.exists(project_config_file):
#         raise FileNotFoundError(f"Konfigurační soubor {project_config_file} neexistuje.")
    
#     # Načtení konfiguračních souborů
#     with open(project_config_file, 'r', encoding='utf-8') as f:
#         project_config = json.load(f)

#     # Načtení SOM konfigurace, pokud je zadána
#     som_config = None
#     if som_config_file:
#         if not os.path.exists(som_config_file):
#             raise FileNotFoundError(f"Konfigurační soubor {som_config_file} neexistuje.")
#         with open(som_config_file, 'r', encoding='utf-8') as f:
#             som_config = json.load(f)

#     # Určení cílového adresáře
#     if not output_dir:
#         output_dir = os.path.dirname(os.path.abspath(input_file))
#     else:
#         if not os.path.exists(output_dir):
#             os.makedirs(output_dir)

#     return project_config, som_config, output_dir

# def normalize_data(data: pd.DataFrame, numeric_columns: list) -> np.ndarray:
#     """
#     Normalizuje numerická data pomocí StandardScaler.
    
#     Args:
#         data: DataFrame s daty
#         numeric_columns: Seznam názvů numerických sloupců
        
#     Returns:
#         Normalizovaná data jako numpy array
#     """
#     scaler = StandardScaler()
#     numeric_data = data[numeric_columns].values
#     return scaler.fit_transform(numeric_data)

# def process_data(input_file: str, project_config: dict, output_dir: str) -> tuple[np.ndarray, pd.DataFrame]:
#     """
#     Zpracuje vstupní data a uloží normalizovaná data.
    
#     Args:
#         input_file: Cesta k vstupnímu CSV souboru
#         project_config: Konfigurace projektu
#         output_dir: Cesta k výstupnímu adresáři
        
#     Returns:
#         Tuple (normalizovaná data, původní DataFrame)
#     """
#     # Načtení dat
#     df = pd.read_csv(input_file, delimiter=';')
#     cols = project_config.get("selected_columns", [])
#     data = df[cols].copy()

#     # 1) Náhrada NaN
#     for col, repl in project_config.get("nan_replacement", {}).items():
#         if col in data:
#             data[col] = data[col].fillna(repl)

#     # 2) Rozdělení na číselné vs. textové
#     processed = pd.DataFrame()
#     for col in cols:
#         series = data[col]
#         if pd.api.types.is_numeric_dtype(series):
#             # číselné: převést + nahradit zbytky NaN
#             num = pd.to_numeric(series, errors="coerce")
#             num = num.fillna(project_config.get("nan_replacement", {}).get(col, 0))
#             processed[col] = num
#         else:
#             # textové: rozhodnout podle počtu unikátů
#             n_uniques = series.nunique(dropna=True)
#             if n_uniques <= 20:
#                 # kategorie: label‑encoding
#                 processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
#             else:
#                 # volný text: též factorize (případně později zvláštní zpracování)
#                 processed[col] = pd.factorize(series.fillna(""), sort=True)[0]
#         print(f"Sloupec '{col}': typ {'číselný' if pd.api.types.is_numeric_dtype(data[col]) else 'kategoriální'} (unikátů {data[col].nunique(dropna=True)})")

#     # 3) Škálování všech sloupců do [0,1]
#     scaler = MinMaxScaler()
#     scaled = scaler.fit_transform(processed.values)
#     normalized_df = pd.DataFrame(scaled, columns=cols)

#     # Uložení normalizovaných dat
#     normalized_df.to_csv(f"{output_dir}/normalized_data.csv", index=False, sep=';')
    
#     return scaled, df

# def train_and_analyze_som(data: np.ndarray, som_config: dict, output_dir: str) -> KohonenSOM:
#     """
#     Trénuje SOM a generuje výstupy.
    
#     Args:
#         data: Normalizovaná vstupní data
#         som_config: Konfigurace SOM
#         output_dir: Cesta k výstupnímu adresáři
        
#     Returns:
#         Natrénovaná instance KohonenSOM
#     """
#     # Inicializace SOM s výchozími hodnotami
#     som = KohonenSOM(
#         m=som_config.get("m", 10),
#         n=som_config.get("n", 10),
#         dim=data.shape[1],
#         radius=som_config.get("radius", None),
#         learning_rate=som_config.get("learning_rate", 0.9),
#         min_learning_rate=som_config.get("min_learning_rate", 0.1),
#         num_batches=som_config.get("num_batches", 10),
#         min_batch_percent=som_config.get("min_batch_percent", 0.1),
#         max_batch_percent=som_config.get("max_batch_percent", 5),
#         lr_decay_type=som_config.get("lr_decay_type", "exp-drop"),
#         radius_decay_type=som_config.get("radius_decay_type", "exp-drop"),
#         batch_growth_type=som_config.get("batch_growth_type", "exp-growth"),
#         random_seed=som_config.get("random_seed", None),
#         growth_g=som_config.get("growth_g", 15.0),
#         normalize_weights_flag=som_config.get("normalize_weights_flag", False),
#         epoch_multiplier=som_config.get("epoch_multiplier", 1.0),
#         map_type=som_config.get("map_type", "hex"),
#         min_q_error=som_config.get("min_q_error", None)
#     )

#     # Trénování SOM
#     som.train(data)

#     # Uložení vah
#     np.save(f"{output_dir}/weights.npy", som.weights)

#     return som

# def generate_visualizations(som: KohonenSOM, data: np.ndarray, df: pd.DataFrame, 
#                           project_config: dict, output_dir: str) -> None:
#     """
#     Generuje vizualizace SOM mapy.
    
#     Args:
#         som: Natrénovaná instance KohonenSOM
#         data: Normalizovaná vstupní data
#         df: Původní DataFrame
#         project_config: Konfigurace projektu
#         output_dir: Cesta k výstupnímu adresáři
#     """
#     # Vytvoření adresáře pro vizualizace
#     vis_dir = f"{output_dir}/visualization"
#     os.makedirs(vis_dir, exist_ok=True)

#     # Generování U-matrix
#     generate_u_matrix(som, f"{vis_dir}/u-matrix.png")

#     # Generování hit-mapy
#     generate_hit_map(som, data, f"{vis_dir}/hit-map.png")

#     # Generování komponentních rovin
#     for dim in range(som.dim):
#         column_name = df.columns[dim] if dim < len(df.columns) else None
#         generate_component_plane(som, dim, f"{vis_dir}/component_{dim}.png", column_name)

# def generate_u_matrix(som: KohonenSOM, output_file: str) -> None:
#     """Generuje U-matrix vizualizaci."""
#     m, n = som.m, som.n
#     weights = som.weights.reshape(m, n, -1)
#     u = np.zeros((m, n))

#     for i in range(m):
#         for j in range(n):
#             neigh = []
#             for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
#                 ni, nj = i+di, j+dj
#                 if 0 <= ni < m and 0 <= nj < n:
#                     neigh.append(np.linalg.norm(weights[i,j] - weights[ni,nj]))
#             u[i,j] = np.mean(neigh) if neigh else 0

#     plt.figure(figsize=(10, 8))
#     plt.imshow(u, cmap='viridis')
#     plt.colorbar(label='U-Matrix distance')
#     plt.savefig(output_file)
#     plt.close()

# def generate_hit_map(som: KohonenSOM, data: np.ndarray, output_file: str) -> None:
#     """Generuje hit-mapu."""
#     m, n = som.m, som.n
#     counts = np.zeros((m, n))

#     for sample in data:
#         i, j = som.find_bmu(som.weights, sample, som.n)
#         counts[i, j] += 1

#     plt.figure(figsize=(10, 8))
#     plt.imshow(counts, cmap='Blues')
#     plt.colorbar(label='Hits')
#     plt.savefig(output_file)
#     plt.close()

# def generate_component_plane(som: KohonenSOM, component: int, output_file: str, column_name: str = None) -> None:
#     """Generuje komponentní rovinu."""
#     m, n = som.m, som.n
#     plane = som.weights.reshape(-1, som.dim)[:, component].reshape(m, n)

#     plt.figure(figsize=(10, 8))
#     plt.imshow(plane, cmap='coolwarm')
#     plt.colorbar(label=column_name if column_name else f'Component {component}')
#     plt.savefig(output_file)
#     plt.close()

# def parse_args():
#     """Parsuje argumenty příkazové řádky."""
#     parser = argparse.ArgumentParser(
#         description='Analýza dat pomocí SOM sítě',
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog="""
# Příklady použití:
#     # Základní použití
#     python3 analyze.py -i data/input.csv -pc config/project.json
    
#     # S SOM konfigurací
#     python3 analyze.py -i data/input.csv -pc config/project.json -sc config/som.json
    
#     # S výstupním adresářem
#     python3 analyze.py -i data/input.csv -pc config/project.json -d output/results
    
#     # Se všemi parametry
#     python3 analyze.py -i data/input.csv -pc config/project.json -sc config/som.json -d output/results
#         """
#     )
    
#     parser.add_argument('-i', '--input', required=True,
#                       help='Cesta k vstupnímu CSV souboru')
#     parser.add_argument('-pc', '--project-config', required=True,
#                       help='Cesta k konfiguračnímu souboru projektu')
#     parser.add_argument('-sc', '--som-config',
#                       help='Cesta k konfiguračnímu souboru SOM (volitelné)')
#     parser.add_argument('-d', '--output-dir',
#                       help='Cesta k cílovému adresáři (volitelné)')
    
#     return parser.parse_args()

# def main():
#     try:
#         args = parse_args()
#         project_config, som_config, output_dir = validate_files(
#             args.input, args.project_config, args.som_config, args.output_dir
#         )
        
#         # Zpracování dat
#         normalized_data, df = process_data(args.input, project_config, output_dir)
        
#         # Trénování SOM
#         som = train_and_analyze_som(normalized_data, som_config or {}, output_dir)
        
#         # Generování vizualizací
#         generate_visualizations(som, normalized_data, df, project_config, output_dir)
        
#         print(f"Analýza dokončena. Výstupy uloženy v {output_dir}")
        
#     except (FileNotFoundError, json.JSONDecodeError) as e:
#         print(f"Chyba: {str(e)}")
#         sys.exit(1)

# if __name__ == "__main__":
#     main() 