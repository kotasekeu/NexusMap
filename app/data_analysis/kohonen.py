import importlib.util
import numpy as np
from utils import log_message

class KohonenSOM:
    def __init__(self, m, n, dim, learning_rate=0.9, radius=None, radius_decay=0.99, lr_decay=0.995,
                 min_learning_rate=0.01):
        # m, n rozměr mapy, dim - dimenze dat (počet sloupců csv se kterými pracujeme), learnin_rate - výchozí hodnota, menší než 1, radius - pokud není nastaven bere se
        # polovina rozměru výchozího pole, radius_decay - hodnota snižování poloměru pro výpočet váhy, lr_decay - hodnota pro snižování atributu učení

        # Krok 0: Inicializace vah, poloměru sousedství a parametru učení
        self.m = m  # počet řádků v mřížce
        self.n = n  # počet sloupců v mřížce
        self.dim = dim  # dimenze vstupních dat
        self.learning_rate = learning_rate
        self.min_learning_rate = min_learning_rate
        self.radius = radius if radius else max(m, n) / 2
        self.radius_decay = radius_decay
        self.lr_decay = lr_decay

        # Krok 0: Inicializace vah (náhodně)
        self.weights = np.random.rand(m, n, dim)
        # Normalizace vah po inicializaci
        self.normalize_weights()

    def normalize_weights(self):
        """Normalizuje váhy neuronů."""
        for i in range(self.m):
            for j in range(self.n):
                norm = np.linalg.norm(self.weights[i, j])
                if norm > 0:  # Zabránění dělení nulou
                    self.weights[i, j] = self.weights[i, j] / norm

    def train(self, data):
        """Trénuje Kohonenovu SOM na zadaných datech."""
        iteration = 0
        num_samples = data.shape[0]

        while self.learning_rate > self.min_learning_rate:
            # Projít celou epochu (všechny vzorky)
            for sample_idx in range(num_samples):
                # Krok 2: Výběr vstupního vektoru
                sample = data[sample_idx]

                # Krok 3: Najít nejlepšího shodného neuronu (BMU)
                bmu_idx = self.find_bmu(sample)

                # Krok 5: Aktualizace vah
                self.update_weights(sample, bmu_idx)

                # Logování průběhu
                iteration += 1
                if (iteration <= 1000 and iteration % 100 == 0) or (iteration > 1000 and iteration % 1000 == 0):
                    log_message(f"Vstupní vektor č. {iteration}: trénování stále probíhá...")

            # Krok 6: Dynamická úprava learning rate po dokončení epochy
            self.learning_rate = self.learning_rate * self.lr_decay

            # Krok 7: Zmenšení poloměru sousedství po dokončení epochy
            self.radius *= self.radius_decay

            # Logování průběhu
            iteration += 1
            if (iteration <= 1000 and iteration % 100 == 0) or (iteration > 1000 and iteration % 1000 == 0):
                log_message(f"Průchod č. {iteration}: trénování stále probíhá...")
                log_message(f"learning rate {self.learning_rate}...")

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
        """Aktualizuje váhy neuronů a vrací počet aktualizovaných neuronů."""
        updated_neurons = 0

        for i in range(self.m):
            for j in range(self.n):
                distance_to_bmu = np.linalg.norm(np.array([i, j]) - np.array(bmu_idx))
                if distance_to_bmu <= self.radius:
                    influence = np.exp(-distance_to_bmu ** 2 / (2 * (self.radius ** 2)))
                    weight_change = influence * self.learning_rate * (sample - self.weights[i, j])
                    self.weights[i, j] += weight_change

                    # Sledujeme pouze významné změny
                    if np.linalg.norm(weight_change) > 1e-6:
                        updated_neurons += 1

        # Normalizace vah po aktualizaci
        self.normalize_weights()
        return updated_neurons

    def update_learning_rate_dynamic(self, initial_learning_rate, update_ratio, min_learning_rate=0.01):
        """Dynamicky upravuje learning rate podle míry změny."""
        return initial_learning_rate * 0.995  # Klasické snižování
