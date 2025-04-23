import numpy as np
import math
from utils import log_message
from sklearn.metrics import pairwise_distances_argmin_min
from collections import defaultdict

class KohonenSOM:
    def __init__(self, dim, m, n, learning_rate=0.9, min_learning_rate=0.1,
                 radius=None, min_radius=0.1,
                 num_batches=10, min_batch_percent=0.1, max_batch_percent=5,
                 lr_decay_type='exp-drop', radius_decay_type='exp-drop', batch_growth_type='exp-growth',
                 random_seed=None, growth_g=15.0, normalize_weights_flag=False, epoch_multiplier=1.0, map_type='hex', min_q_error=None,
                 max_epochs_without_improvement=None):        
        self.m = m
        self.n = n
        self.dim = dim
        self.learning_rate = learning_rate if learning_rate >= min_learning_rate else min_learning_rate
        self.min_learning_rate = min_learning_rate
        
        if radius is None:
            self.radius = max(m, n) / 2
        elif radius < min_radius:
            self.radius = min_radius
        else:
            self.radius = radius    

        self.min_radius = min_radius
        self.num_batches = num_batches
        
        self.max_batch_percent = max_batch_percent if max_batch_percent > min_batch_percent else min_batch_percent
        self.min_batch_percent = min_batch_percent

        self.lr_decay_type = lr_decay_type
        self.radius_decay_type = radius_decay_type
        self.batch_growth_type = batch_growth_type

        self.growth_g = growth_g
        self.epoch_multiplier = epoch_multiplier
        self.map_type = map_type

        self.normalize_weights_flag = normalize_weights_flag    

        self.min_q_error = min_q_error
        self.max_epochs_without_improvement = max_epochs_without_improvement

        self.total_weight_updates = 0
        self.best_mqe = float('inf')

        if random_seed is not None:
            np.random.seed(random_seed)

        self.weights = np.random.rand(m, n, dim)
        self.normalize_weights()

    def normalize_weights(self):
        for i in range(self.m):
            for j in range(self.n):
                norm = np.linalg.norm(self.weights[i, j])
                if norm > 0:
                    self.weights[i, j] /= norm

    def get_decay_value(self, t, N, start, end, decay_type):
        if decay_type == 'logarithmic':
            return start - (np.log10(t + 1) / np.log10(N)) * (start - end)
        elif decay_type == 'linear-growth':
            return start + (t / (N - 1)) * (end - start)
        elif decay_type == 'linear-drop':
            return start - (t / (N - 1)) * (start - end)
        elif decay_type == 'exponential':
            k = np.log(start / end) / N
            return start * np.exp(-k * t)
        elif decay_type == 'exp-growth':
            return start + (end - start) * (np.exp(self.growth_g * t / N) - 1) / (np.exp(self.growth_g) - 1)
        elif decay_type == 'exp-drop':
            log_max = np.log(N + 1)
            return end + (np.log(N - t + 1) / log_max) * (start - end)
        else:
            raise ValueError("Unknown decay type")

    def get_batch_percent(self, t, N):
        return self.get_decay_value(t, N, self.min_batch_percent, self.max_batch_percent, self.batch_growth_type)

    def train(self, data):
        log_message(f"Epocha|počet zpracovanych vektorů celkem|počet vektorů zpracovaných v batch|radius|lr|MQE")
        total_samples = data.shape[0]
        total_epochs = int(total_samples * self.epoch_multiplier)
        no_improvement_count = 0  # počet epoch bez zlepšení

        for epoch in range(total_epochs):
            batch_percent = self.get_batch_percent(epoch, total_epochs)
            total_samples_to_process = math.ceil(total_samples * batch_percent / 100)
            samples_per_batch = math.ceil(total_samples_to_process / self.num_batches)

            for batch_idx in range(self.num_batches):
                start_idx = batch_idx * (total_samples // self.num_batches)
                end_idx = min((batch_idx + 1) * (total_samples // self.num_batches), total_samples)
                batch_data = data[start_idx:end_idx]

                if samples_per_batch < len(batch_data):
                    batch_indices = np.random.choice(len(batch_data), samples_per_batch, replace=False)
                    batch_data = batch_data[batch_indices]

                current_lr = self.get_decay_value(epoch, total_epochs, self.learning_rate, self.min_learning_rate, self.lr_decay_type)
                current_radius = self.get_decay_value(epoch, total_epochs, self.radius, self.min_radius, self.radius_decay_type)

                for sample in batch_data:
                    bmu_idx = self.find_bmu(sample)
                    self.update_weights(sample, bmu_idx, current_lr, current_radius)
                    self.total_weight_updates += 1

            if self.normalize_weights_flag:
                self.normalize_weights()        

            # Získání codebook vectors a BMU indexů
            codebook_vectors = self.weights.reshape(-1, self.dim)
            bmu_indexes = np.array([self.find_bmu(x)[0] * self.n + self.find_bmu(x)[1] for x in data])
            
            neuron_error_map, total_qe = self.compute_quantization_error(data, codebook_vectors, bmu_indexes, (self.m, self.n))

            # Kontrola dosažení limitní MQE
            if self.min_q_error is not None and total_qe <= self.min_q_error:
                log_message(f"Dosažena limitní MQE {self.min_q_error}. Ukončuji trénování.")
                break

            # Kontrola zlepšení a early stopping
            if total_qe < self.best_mqe:
                self.best_mqe = total_qe
                no_improvement_count = 0
            else:
                no_improvement_count += 1
                if self.max_epochs_without_improvement is not None and no_improvement_count >= self.max_epochs_without_improvement:
                    log_message(f"Žádné zlepšení po {self.max_epochs_without_improvement} epochách. Ukončuji trénování.")
                    break

            if epoch % 100 == 0:                
                log_message(f"{epoch}|{total_samples_to_process}|{samples_per_batch}|{current_radius:.4f}|{current_lr:.6f}|{total_qe:.6f}")                

        # Výpis souhrnných informací na konci trénování
        print(f"\nSouhrn trénování:")
        print(f"Celkový počet aktualizací vah: {self.total_weight_updates}")
        print(f"Nejlepší dosažená MQE: {self.best_mqe:.6f}")

    def find_bmu(self, sample):
        # vektorová implementace hledání BMU
        flat = self.weights.reshape(-1, self.dim)  # (m*n, dim)

        diffs = flat - sample  # broadcast
        dists = np.linalg.norm(diffs, axis=1)
        idx = np.argmin(dists)
        return divmod(idx, self.n)  # (i, j)

    def update_weights(self, sample, bmu_idx, learning_rate, radius):
        for i in range(self.m):
            for j in range(self.n):
                distance_to_bmu = self.grid_distance((i, j), bmu_idx)
                if distance_to_bmu <= radius:
                    influence = np.exp(-distance_to_bmu ** 2 / (2 * (radius ** 2)))
                    self.weights[i, j] += influence * learning_rate * (sample - self.weights[i, j])

    def grid_distance(self, a: tuple[int,int], b: tuple[int,int]) -> float:
        i1, j1 = a;  i2, j2 = b
        if self.map_type == 'square':
            return math.hypot(i1 - i2, j1 - j2)
        # pro hex použijeme axial souřadnice (q = j, r = i):
        q1, r1 = j1, i1
        q2, r2 = j2, i2
        # cube coords: x=q, z=r, y=-x-z
        x1, z1 = q1, r1;  y1 = -x1 - z1
        x2, z2 = q2, r2;  y2 = -x2 - z2
        return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) / 2
    
    def compute_quantization_error(self, data, codebook_vectors, bmu_indexes, som_shape):
        """
        Vypočítá kvantizační chybu pro jednotlivé neurony a celkovou chybu pro dataset.

        Parameters:
        - data: np.ndarray of shape (n_samples, n_features) – vstupní vzory
        - codebook_vectors: np.ndarray of shape (n_neurons, n_features) – váhové vektory neuronů
        - bmu_indexes: np.ndarray of shape (n_samples,) – index každého neuronu přiřazeného vstupnímu vzoru
        - som_shape: tuple – tvar mřížky SOM (např. (10, 10))

        Returns:
        - neuron_error_map: np.ndarray of shape som_shape – kvantizační chyba na každý neuron
        - total_qe: float – průměrná kvantizační chyba pro celý dataset
        """
        n_neurons = codebook_vectors.shape[0]
        neuron_errors = defaultdict(list)

        # Pro každé x spočítáme vzdálenost k jeho BMU
        distances = []
        for x, bmu in zip(data, bmu_indexes):
            dist = np.linalg.norm(x - codebook_vectors[bmu])
            distances.append(dist)
            neuron_errors[bmu].append(dist)

        # Kvantizační chyba pro každý neuron (průměr vzdáleností všech jemu přiřazených vzorů)
        neuron_error_map = np.zeros(n_neurons)
        for i in range(n_neurons):
            if neuron_errors[i]:
                neuron_error_map[i] = np.mean(neuron_errors[i])
            else:
                neuron_error_map[i] = 0.0

        # Změníme do mřížky SOM tvaru (např. 10x10)
        neuron_error_map = neuron_error_map.reshape(som_shape)

        # Celková kvantizační chyba pro dataset
        total_qe = np.mean(distances)

        return neuron_error_map, total_qe
    