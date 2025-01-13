import importlib.util
import numpy as np

class KohonenSOM:
    def __init__(self, m, n, dim, learning_rate=0.1, radius=None, radius_decay=0.99, lr_decay=0.99,
                 min_learning_rate=0.01):
        # Krok 0: Inicializace vah, poloměru sousedství a parametru učení
        self.m = m  # počet řádků v mřížce
        self.n = n  # počet sloupců v mřížce
        self.dim = dim  # dimenze vstupních dat
        self.learning_rate = learning_rate
        self.min_learning_rate = min_learning_rate
        self.radius = radius if radius else max(m, n) / 2
        self.radius_decay = radius_decay
        self.lr_decay = lr_decay

        # Inicializace vah (náhodně)
        self.weights = np.random.rand(m, n, dim)

    def train(self, data):
        # Krok 1: Opakovat kroky 2-8, dokud není splněna podmínka ukončení
        iteration = 0
        while self.learning_rate > self.min_learning_rate:
            # Krok 2: Pro každý vstupní vektor x
            sample = data[np.random.randint(0, data.shape[0])]

            # Krok 3: Vypočítat vzdálenosti mezi vstupním vzorkem a všemi neurony
            bmu_idx = self.find_bmu(sample)

            # Krok 5: Aktualizace vah
            self.update_weights(sample, bmu_idx)

            # Krok 6: Aktualizace parametru učení
            self.learning_rate *= self.lr_decay

            # Krok 7: Zmenšení poloměru sousedství
            self.radius *= self.radius_decay

            iteration += 1

    def find_bmu(self, sample):
        min_dist = float('inf')
        bmu_idx = None

        for i in range(self.m):
            for j in range(self.n):
                # Krok 3: Vypočítat vzdálenosti D(j)
                dist = np.linalg.norm(sample - self.weights[i, j])
                if dist < min_dist:
                    min_dist = dist
                    bmu_idx = (i, j)

        # Krok 4: Najít index J tak, že D(J) je minimum
        return bmu_idx

    def update_weights(self, sample, bmu_idx):
        radius_sq = self.radius ** 2
        learning_rate = self.learning_rate

        for i in range(self.m):
            for j in range(self.n):
                # Krok 5: Aktualizace vah neuronů v topologickém sousedství BMU
                dist_to_bmu_sq = np.sum((np.array([i, j]) - np.array(bmu_idx)) ** 2)
                if dist_to_bmu_sq < radius_sq:
                    influence = np.exp(-dist_to_bmu_sq / (2 * radius_sq))
                    self.weights[i, j] += learning_rate * influence * (sample - self.weights[i, j])