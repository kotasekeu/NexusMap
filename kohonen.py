"""
Implementace Kohonenovy Self-Organizing Map (SOM) sítě.

Tento modul poskytuje implementaci Kohonenovy SOM sítě s následujícími vlastnostmi:
- Podpora čtvercové i hexagonální mřížky
- Různé typy útlumu učení a poloměru
- Adaptivní velikost dávky
- Early stopping na základě MQE
- Normalizace vah
- Vektorizované operace pro lepší výkon
- Tři režimy zpracování: deterministický, stochastický a hybridní
"""

import numpy as np
import math
from utils import log_message
from sklearn.metrics import pairwise_distances_argmin_min
from collections import defaultdict
import sys
from tqdm import tqdm
from datetime import datetime, timedelta

class KohonenSOM:
    """Implementace Kohonenovy Self-Organizing Map sítě.
    
    Args:
        dim (int): Dimenze vstupních vektorů
        m (int): Výška mřížky SOM
        n (int): Šířka mřížky SOM
        learning_rate (float, optional): Počáteční rychlost učení. Výchozí hodnota je 0.9
        min_learning_rate (float, optional): Minimální rychlost učení. Výchozí hodnota je 0.1
        radius (float, optional): Počáteční poloměr sousedství. Pokud None, použije se max(m,n)/2
        min_radius (float, optional): Minimální poloměr sousedství. Výchozí hodnota je 0.1
        processing_type (str, optional): Typ zpracování ('deterministic', 'stochastic', 'hybrid'). Výchozí hodnota je 'hybrid'
        num_batches (int, optional): Počet dávek pro zpracování. Výchozí hodnota je 10
        min_batch_percent (float, optional): Minimální procento vzorků v dávce. Výchozí hodnota je 0.1
        max_batch_percent (float, optional): Maximální procento vzorků v dávce. Výchozí hodnota je 5
        lr_decay_type (str, optional): Typ útlumu rychlosti učení. Výchozí hodnota je 'exp-drop'
        radius_decay_type (str, optional): Typ útlumu poloměru. Výchozí hodnota je 'exp-drop'
        batch_growth_type (str, optional): Typ růstu velikosti dávky. Výchozí hodnota je 'exp-growth'
        random_seed (int, optional): Seed pro generátor náhodných čísel
        growth_g (float, optional): Parametr pro exponenciální růst. Výchozí hodnota je 15.0
        normalize_weights_flag (bool, optional): Zda normalizovat váhy. Výchozí hodnota je False
        epoch_multiplier (float, optional): Násobitel počtu epoch. Výchozí hodnota je 1.0
        map_type (str, optional): Typ mřížky ('hex' nebo 'square'). Výchozí hodnota je 'hex'
        min_q_error (float, optional): Minimální požadovaná kvantizační chyba pro early stopping
        max_epochs_without_improvement (int, optional): Maximální počet epoch bez zlepšení pro early stopping
        mqe_recording_interval (int, optional): Interval pro záznam kvantizační chyby. Výchozí hodnota je 10

    Note:
        Podporované typy zpracování:
        - 'deterministic': Zpracování všech vstupních vektorů v každé epoše
        - 'stochastic': Zpracování jednoho náhodného vektoru v každé epoše
        - 'hybrid': Adaptivní velikost dávky podle parametrů batch_growth_type, min_batch_percent, max_batch_percent
        
        Podporované typy útlumu:
        - 'logarithmic': Logaritmický útlum
        - 'linear-growth': Lineární růst
        - 'linear-drop': Lineární pokles
        - 'exponential': Exponenciální útlum
        - 'exp-growth': Exponenciální růst
        - 'exp-drop': Exponenciální pokles
    """
    
    def __init__(self, dim, m, n, learning_rate=0.9, min_learning_rate=0.1,
                 radius=None, min_radius=0.1, processing_type='hybrid',
                 num_batches=10, min_batch_percent=0.1, max_batch_percent=5,
                 lr_decay_type='exp-drop', radius_decay_type='exp-drop', batch_growth_type='exp-growth',
                 random_seed=None, growth_g=15.0, normalize_weights_flag=False, epoch_multiplier=1.0, map_type='hex', min_q_error=None,
                 max_epochs_without_improvement=None, mqe_recording_interval=10):        
        # Základní parametry sítě
        self.m = m
        self.n = n
        self.dim = dim
        
        # Parametry učení
        self.learning_rate = learning_rate if learning_rate >= min_learning_rate else min_learning_rate
        self.min_learning_rate = min_learning_rate
        
        # Nastavení poloměru
        self.min_radius = min_radius
        self.set_radius(radius)
        
        # Typ zpracování
        if processing_type not in ['deterministic', 'stochastic', 'hybrid']:
            raise ValueError("Typ zpracování musí být 'deterministic', 'stochastic' nebo 'hybrid'")
        self.processing_type = processing_type
        
        # Parametry dávkového zpracování (pouze pro hybridní režim)
        self.num_batches = num_batches
        self.max_batch_percent = max_batch_percent if max_batch_percent > min_batch_percent else min_batch_percent
        self.min_batch_percent = min_batch_percent

        # Typy útlumu a růstu
        self.lr_decay_type = lr_decay_type
        self.radius_decay_type = radius_decay_type
        self.batch_growth_type = batch_growth_type

        # Další parametry
        self.growth_g = float(growth_g)
        self.epoch_multiplier = float(epoch_multiplier)
        self.map_type = map_type
        self.normalize_weights_flag = normalize_weights_flag    
        self.min_q_error = min_q_error
        self.max_epochs_without_improvement = max_epochs_without_improvement
        self.mqe_recording_interval = mqe_recording_interval

        # Metriky trénování
        self.total_weight_updates = 0
        self.best_mqe = float('inf')
        self.mqe_history = []  # Seznam pro ukládání historie kvantizační chyby
        self.epochs_history = []  # Seznam pro ukládání čísel epoch
        self.learning_rate_history = []  # Seznam pro ukládání historie learning rate
        self.radius_history = []  # Seznam pro ukládání historie radius
        self.batch_size_history = []  # Seznam pro ukládání historie velikosti dávky

        # Inicializace vah
        self.base_seed = random_seed

        if random_seed is not None:
            np.random.seed(random_seed)
        self.weights = np.random.rand(m, n, dim)
        self.normalize_weights()

    def normalize_weights(self) -> None:
        """Normalizuje váhy neuronů na jednotkovou délku."""
        for i in range(self.m):
            for j in range(self.n):
                norm = np.linalg.norm(self.weights[i, j])
                if norm > 0:
                    self.weights[i, j] /= norm

    def get_decay_value(self, t: int, N: int, start: float, end: float, decay_type: str) -> float:
        """Vypočítá hodnotu útlumu nebo růstu pro daný časový krok.

        Args:
            t (int): Aktuální časový krok
            N (int): Celkový počet kroků
            start (float): Počáteční hodnota
            end (float): Koncová hodnota
            decay_type (str): Typ útlumu nebo růstu
                - Pro pokles (LR, R): 'static', 'logarithmic-drop', 'linear-drop', 'exponential', 'exp-drop'
                - Pro růst (batch size): 'linear-growth', 'logarithmic-growth', 'exp-growth'

        Returns:
            float: Hodnota útlumu nebo růstu

        Raises:
            ValueError: Pokud je zadán neznámý typ útlumu/růstu
        """
        if N <= 1:
            return start

        if decay_type == 'static':
            return start

        elif decay_type == 'linear-drop':
            return start - (t / (N - 1)) * (start - end)

        elif decay_type == 'linear-growth':
            return start + (t / (N - 1)) * (end - start)

        elif decay_type == 'exp-drop':
            norm = (1 - np.exp(-self.growth_g * t / N)) / (1 - np.exp(-self.growth_g))
            return start - norm * (start - end)

        elif decay_type == 'exp-growth':
            return start + (end - start) * (np.exp(self.growth_g * t / N) - 1) / (np.exp(self.growth_g) - 1)

        elif decay_type == 'log-drop':
            norm = np.log(self.growth_g * t + 1) / np.log(self.growth_g * N + 1)
            return start - norm * (start - end)

        elif decay_type == 'log-growth':
            return start + (end - start) * (np.log(self.growth_g * t + 1) / np.log(self.growth_g * N + 1))

        elif decay_type == 'step-down':
            step_count = 10
            step_size = N // step_count
            current_step = min(t // step_size, step_count - 1)
            factor = 0.7 ** current_step
            return max(end, start * factor)

        else:
            raise ValueError(f"Unknown decay_type: {decay_type}")

    def get_batch_percent(self, t: int, N: int) -> float:
        """Vypočítá procento vzorků pro aktuální dávku.

        Args:
            t (int): Aktuální časový krok
            N (int): Celkový počet kroků

        Returns:
            float: Procento vzorků pro dávku
        """
        # Pro růstové decay typy: 'linear-growth', 'logarithmic-growth', 'exp-growth'
        return self.get_decay_value(t, N, self.min_batch_percent, self.max_batch_percent, self.batch_growth_type)

    def train(self, data: np.ndarray) -> None:
        """Trénuje SOM síť na zadaných datech.
        
        Args:
            data (np.ndarray): Vstupní data ve tvaru (n_samples, n_features)
        """
        start_time = datetime.now()
        log_message(f"Začátek trénování: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        total_samples = data.shape[0]               
        total_epochs = int(total_samples * self.epoch_multiplier)
        
        no_improvement_count = 0

        self.epochs_run = 0
        self.mqe_history = []  # Reset historie MQE
        self.epochs_history = []  # Reset historie epoch
        
        # Vytvoření progress baru s informacemi o čase
        pbar = tqdm(total=total_epochs, desc=f"Epochy (začátek: {start_time.strftime('%H:%M:%S')})", 
                   bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
        
        for epoch in range(total_epochs):
            samples_per_batch = 1;
            # Výpočet parametrů učení pro celou epochu
            current_lr = self.get_decay_value(epoch, total_epochs, self.learning_rate, self.min_learning_rate, self.lr_decay_type)
            current_radius = self.get_decay_value(epoch, total_epochs, self.radius, self.min_radius, self.radius_decay_type)

            # Inicializace samples_per_batch pouze pro hybridní režim
            if self.processing_type == 'hybrid':
                batch_percent = self.get_batch_percent(epoch, total_epochs)
                samples_per_batch = math.ceil(total_samples * batch_percent / 100)

            # Zpracování dávek
            if self.processing_type == 'stochastic':
                if self.base_seed is not None:
                    np.random.seed(self.base_seed + epoch)
                idx = np.random.randint(0, total_samples)
                sample = data[idx]
                bmu_idx = self.find_bmu(sample)
                self.update_weights(sample, bmu_idx, current_lr, current_radius)
            elif self.processing_type == 'deterministic':
                # Pro deterministický režim zpracujeme všechny vzorky postupně
                for sample in data:
                    bmu_idx = self.find_bmu(sample)
                    self.update_weights(sample, bmu_idx, current_lr, current_radius)
            else:  # hybridní režim
                # Pro hybridní režim použijeme náhodné indexy pro dávky
                if self.base_seed is not None:
                    np.random.seed(self.base_seed + epoch)
                indices = np.random.permutation(total_samples)
                # Rozdělení indexů na dávky
                for batch_idx in range(self.num_batches):
                    start_idx = batch_idx * (total_samples // self.num_batches)
                    end_idx = min((batch_idx + 1) * (total_samples // self.num_batches), total_samples)
                    batch_indices = indices[start_idx:end_idx]

                    # Omezení velikosti dávky pokud je potřeba
                    if samples_per_batch < len(batch_indices):
                        batch_indices = batch_indices[:samples_per_batch]

                    # Aktualizace vah pro každý vzorek v dávce
                    for idx in batch_indices:
                        sample = data[idx]
                        bmu_idx = self.find_bmu(sample)
                        self.update_weights(sample, bmu_idx, current_lr, current_radius)

            # Aktualizace počítadla aktualizací vah
            if self.processing_type == 'stochastic':
                self.total_weight_updates += 1
            else:
                self.total_weight_updates += total_samples

            # Normalizace vah pokud je požadována
            if self.normalize_weights_flag:
                self.normalize_weights()

            # Výpočet MQE podle typu zpracování
            should_compute_mqe = False
            total_qe = None  # Inicializace total_qe
            
            # Výpočet MQE v každé epoše pro deterministický režim, jinak podle intervalu
            if self.processing_type == 'deterministic':
                should_compute_mqe = True
            else:
                # Přizpůsobení intervalu podle počtu epoch
                interval = max(1, total_epochs // 500)
                if epoch % interval == 0:
                    should_compute_mqe = True

            if should_compute_mqe:
                # Výpočet MQE
                codebook_vectors = self.weights.reshape(-1, self.dim)
                bmu_indexes = np.array([r * self.n + c for r, c in (self.find_bmu(x) for x in data)])
                _, total_qe = self.compute_quantization_error(data, codebook_vectors, bmu_indexes, (self.m, self.n), compute_neuron_map=False)

                # Ukládání historie MQE a parametrů
                self.mqe_history.append(total_qe)
                self.epochs_history.append(epoch)
                self.learning_rate_history.append(current_lr)
                self.radius_history.append(current_radius)
                if self.processing_type == 'hybrid':
                    self.batch_size_history.append(samples_per_batch)
                                
                # Kontrola podmínek pro ukončení
                if self.min_q_error is not None and total_qe <= self.min_q_error:
                    log_message(f"Dosažena limitní MQE {self.min_q_error}. Ukončuji trénování.")
                    break

                if total_qe < self.best_mqe:
                    self.best_mqe = total_qe
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
                    if self.max_epochs_without_improvement is not None and no_improvement_count >= self.max_epochs_without_improvement:
                        log_message(f"Žádné zlepšení po {self.max_epochs_without_improvement} epochách. Ukončuji trénování.")
                        break

            # Logování průběhu
            if epoch % 500 == 0:
                elapsed_time = datetime.now() - start_time
                if total_qe is not None:
                    log_message(f"{epoch}|{total_samples}|{samples_per_batch}|{current_radius:.4f}|{current_lr:.6f}|{total_qe:.6f} (čas: {str(elapsed_time).split('.')[0]})")
                else:
                    log_message(f"{epoch}|{total_samples}|{samples_per_batch}|{current_radius:.4f}|{current_lr:.6f}|N/A (čas: {str(elapsed_time).split('.')[0]})")        

            # Aktualizace progress baru
            pbar.update(1)
            self.epochs_run = epoch + 1

        # Zavření progress baru
        pbar.close()

        # Výpis souhrnných informací
        end_time = datetime.now()
        total_time = end_time - start_time
        print(f"\nSouhrn trénování:")
        print(f"Začátek: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Konec: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Celkový čas: {str(total_time).split('.')[0]}")
        print(f"Celkový počet aktualizací vah: {self.total_weight_updates}")
        print(f"Nejlepší dosažená MQE: {self.best_mqe:.6f}")

    def find_bmu(self, sample: np.ndarray) -> tuple[int, int]:
        """Najde Best Matching Unit (BMU) pro daný vzorek.
        
        Args:
            sample (np.ndarray): Vstupní vzorek
            
        Returns:
            tuple[int, int]: Souřadnice (i,j) BMU v mřížce
        """
        flat = self.weights.reshape(-1, self.dim)
        diffs = flat - sample
        dists = np.linalg.norm(diffs, axis=1)
        idx = np.argmin(dists)
        return divmod(idx, self.n)

    def update_weights(self, sample: np.ndarray, bmu_idx: tuple[int, int], learning_rate: float, radius: float) -> None:
        """Aktualizuje váhy neuronů v okolí BMU.
        
        Args:
            sample (np.ndarray): Vstupní vzorek
            bmu_idx (tuple[int, int]): Souřadnice BMU
            learning_rate (float): Aktuální rychlost učení
            radius (float): Aktuální poloměr sousedství
        """
        # Vytvoření mřížky souřadnic
        i_coords = np.arange(self.m)[:, np.newaxis]
        j_coords = np.arange(self.n)[np.newaxis, :]
        
        # Výpočet vzdáleností pro všechny neurony najednou
        distances = np.zeros((self.m, self.n))
        for i in range(self.m):
            for j in range(self.n):
                distances[i, j] = self.grid_distance((i, j), bmu_idx)
        
        # Výpočet vlivu pro všechny neurony najednou
        influence = np.exp(-distances ** 2 / (2 * (radius ** 2)))
        
        # Aktualizace vah pro všechny neurony najednou
        self.weights += influence[:, :, np.newaxis] * learning_rate * (sample - self.weights)

    def grid_distance(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """Vypočítá vzdálenost mezi dvěma neurony v mřížce.
        
        Args:
            a (tuple[int, int]): Souřadnice prvního neuronu
            b (tuple[int, int]): Souřadnice druhého neuronu
            
        Returns:
            float: Vzdálenost mezi neurony
            
        Note:
            Pro čtvercovou mřížku používá eukleidovskou vzdálenost,
            pro hexagonální mřížku používá vzdálenost v hexagonálních souřadnicích.
        """
        i1, j1 = a
        i2, j2 = b
        if self.map_type == 'square':
            return math.hypot(i1 - i2, j1 - j2)
        # Hexagonální souřadnice
        q1, r1 = j1, i1
        q2, r2 = j2, i2
        x1, z1 = q1, r1
        y1 = -x1 - z1
        x2, z2 = q2, r2
        y2 = -x2 - z2
        return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) / 2
    
    def compute_quantization_error(self, data: np.ndarray, codebook_vectors: np.ndarray, 
                                 bmu_indexes: np.ndarray, som_shape: tuple[int, int],
                                 compute_neuron_map: bool = False) -> tuple[np.ndarray | None, float]:
        """Vypočítá kvantizační chybu pro jednotlivé neurony a celkovou chybu.
        
        Args:
            data (np.ndarray): Vstupní vzory
            codebook_vectors (np.ndarray): Váhové vektory neuronů
            bmu_indexes (np.ndarray): Indexy BMU pro každý vzorek
            som_shape (tuple[int, int]): Tvar mřížky SOM
            compute_neuron_map (bool): Zda počítat mapu chyb pro jednotlivé neurony
            
        Returns:
            tuple[np.ndarray | None, float]: Mapa chyb neuronů (None pokud compute_neuron_map=False) a celková kvantizační chyba
        """
        # Získání vah vítězných neuronů pro každý vzorek
        winning_weights = codebook_vectors[bmu_indexes]
        
        # Výpočet celkové kvantizační chyby
        total_qe = np.linalg.norm(data - winning_weights, axis=1).mean()

        # Výpočet mapy chyb pro neurony (pouze pokud je požadována)
        neuron_error_map = None
        if compute_neuron_map:
            # Vytvoření masky pro každý neuron
            neuron_masks = np.zeros((len(codebook_vectors), len(data)), dtype=bool)
            neuron_masks[bmu_indexes, np.arange(len(data))] = True
            
            # Výpočet průměrné chyby pro každý neuron
            neuron_errors = np.zeros(len(codebook_vectors))
            for i in range(len(codebook_vectors)):
                if np.any(neuron_masks[i]):
                    neuron_errors[i] = np.linalg.norm(data[neuron_masks[i]] - codebook_vectors[i], axis=1).mean()
            
            neuron_error_map = neuron_errors.reshape(som_shape)

        return neuron_error_map, total_qe
    
    def set_radius(self, radius: float | None) -> None:
        """Nastaví počáteční poloměr sousedství.
        
        Args:
            radius (float | None): Počáteční poloměr sousedství. Pokud None, použije se max(m,n)/2
        """
        if radius is None:
            self.radius = max(self.m, self.n) / 2
        elif radius < self.min_radius:
            self.radius = self.min_radius
        else:
            self.radius = radius
    