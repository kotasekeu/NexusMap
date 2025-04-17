import numpy as np
import math
from utils import log_message

class KohonenSOM:
    def __init__(self, m, n, dim, learning_rate=0.9, min_learning_rate=0.1,
                 radius=None, min_radius=0.1,
                 num_batches=10, min_batch_percent=0.1, max_batch_percent=5,
                 lr_decay_type='exp-drop', radius_decay_type='exp-drop', batch_growth_type='exp-growth',
                 random_seed=None, growth_g=15.0):
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
        elif decay_type == 'linear':
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
        total_samples = data.shape[0]
        total_epochs = total_samples

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

            if epoch % 100 == 0:
                # log_message(f"Epocha {epoch}/{total_epochs}")
                # log_message(f"Zpracovaných vzorků: {total_samples_to_process}")
                # log_message(f"LR: {current_lr:.6f} | Radius: {current_radius:.4f} | Samples per batch: {samples_per_batch}")
                # log_message(f"Decay: LR={self.lr_decay_type}, Radius={self.radius_decay_type}, Batch={self.batch_growth_type}")
                # log_message(f"% vzorků z celku: {batch_percent:.4f}%")
                log_message(f"{epoch}|{total_samples_to_process}|{samples_per_batch}|{current_radius:.4f}|{current_lr:.6f}")

    def find_bmu(self, sample):
        min_dist = float('inf')
        bmu_idx = None
        for i in range(self.m):
            for j in range(self.n):
                dist = np.linalg.norm(sample - self.weights[i, j])
                if dist < min_dist:
                    min_dist = dist
                    bmu_idx = (i, j)
        return bmu_idx

    def update_weights(self, sample, bmu_idx, learning_rate, radius):
        for i in range(self.m):
            for j in range(self.n):
                distance_to_bmu = np.linalg.norm(np.array([i, j]) - np.array(bmu_idx))
                if distance_to_bmu <= radius:
                    influence = np.exp(-distance_to_bmu ** 2 / (2 * (radius ** 2)))
                    self.weights[i, j] += influence * learning_rate * (sample - self.weights[i, j])
        self.normalize_weights()