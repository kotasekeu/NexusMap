import numpy as np
import math
from utils import log_message

class KohonenSOM:
    def __init__(self, m, n, dim, learning_rate=0.9, min_learning_rate=0.1,
                 radius=None, min_radius=0.1,
                 num_batches=10, min_batch_percent=0.1, max_batch_percent=5,
                 lr_decay_type='exp-drop', radius_decay_type='exp-drop', batch_growth_type='exp-growth',
                 random_seed=None, growth_g=15.0, normalize_weights_flag=False, epoch_multiplier=1.0, map_type='hex'):
        if random_seed is not None:
            np.random.seed(random_seed)

        self.m = m
        self.n = n
        self.dim = dim
        self.learning_rate = learning_rate
        self.min_learning_rate = min_learning_rate
        self.radius = radius if radius else max(m, n) / 2
        self.min_radius = min_radius

        self.num_batches = num_batches
        self.min_batch_percent = min_batch_percent
        self.max_batch_percent = max_batch_percent

        self.lr_decay_type = lr_decay_type
        self.radius_decay_type = radius_decay_type
        self.batch_growth_type = batch_growth_type

        self.growth_g = growth_g
        self.epoch_multiplier = epoch_multiplier
        self.map_type = map_type

        # pokud chcete defaultně normalizovat, změňte na True
        self.normalize_weights_flag = normalize_weights_flag    

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
        log_message(f"Epocha|počet zpracovanych vektorů celkem|počet vektorů zpracovaných v batch|radius|lr|q error")
        total_samples = data.shape[0]
        total_epochs = int(total_samples * self.epoch_multiplier)
        total_weight_updates = 0  # celkový počet aktualizací vah
        total_processed_samples = 0  # celkový počet zpracovaných vzorků

        for epoch in range(total_epochs):
            batch_percent = self.get_batch_percent(epoch, total_epochs)
            total_samples_to_process = math.ceil(total_samples * batch_percent / 100)
            samples_per_batch = math.ceil(total_samples_to_process / self.num_batches)
            total_processed_samples += (samples_per_batch * self.num_batches)

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
                    total_weight_updates += 1  # počítáme aktualizace vah

                    if self.normalize_weights_flag:
                        self.normalize_weights()

            if epoch % 100 == 0:
                errors = [np.linalg.norm(sample - self.weights[self.find_bmu(sample)]) for sample in data]
                q_error = np.mean(errors)
                log_message(f"{epoch}|{total_samples_to_process}|{samples_per_batch}|{current_radius:.4f}|{current_lr:.6f}|{q_error:.6f}")

        # Výpis souhrnných informací na konci trénování
        print(f"\nSouhrn trénování:")
        print(f"Celkový počet aktualizací vah: {total_weight_updates}")

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