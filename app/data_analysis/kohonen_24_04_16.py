# import importlib.util
# import numpy as np
# from utils import log_message
# import math
#
# class KohonenSOM:
#     def __init__(self, m, n, dim, learning_rate=0.9, radius=None, radius_decay=0.99, lr_decay=0.995,
#                  min_learning_rate=0.1, num_batches=10, min_batch_percent=0.1, max_batch_percent=5,
#                  growth_type='logarithmic'):
#         # m, n rozměr mapy, dim - dimenze dat (počet sloupců csv se kterými pracujeme), learnin_rate - výchozí hodnota, menší než 1, radius - pokud není nastaven bere se
#         # polovina rozměru výchozího pole, radius_decay - hodnota snižování poloměru pro výpočet váhy, lr_decay - hodnota pro snižování atributu učení
#
#         # Základní parametry
#         self.m = m  # počet řádků v mřížce
#         self.n = n  # počet sloupců v mřížce
#         self.dim = dim  # dimenze vstupních dat
#         self.learning_rate = learning_rate  # počáteční learning rate
#         self.min_learning_rate = min_learning_rate  # koncový learning rate
#         self.radius = radius if radius else max(m, n) / 2  # počáteční poloměr
#         self.radius_decay = radius_decay
#         self.lr_decay = lr_decay
#
#         # Nové parametry pro batch trénování
#         self.num_batches = num_batches
#         self.min_batch_percent = min_batch_percent
#         self.max_batch_percent = max_batch_percent
#         self.growth_type = growth_type
#
#         # Krok 0: Inicializace vah (náhodně)
#         self.weights = np.random.rand(m, n, dim)
#         # Normalizace vah po inicializaci
#         self.normalize_weights()
#
#     def normalize_weights(self):
#         """Normalizuje váhy neuronů."""
#         for i in range(self.m):
#             for j in range(self.n):
#                 norm = np.linalg.norm(self.weights[i, j])
#                 if norm > 0:  # Zabránění dělení nulou
#                     self.weights[i, j] = self.weights[i, j] / norm
#
#     def calculate_total_samples_to_process(self, total_samples, epoch, total_epochs):
#         """Vypočítá celkový počet vzorků zpracovaných v dané epoše."""
#         if self.growth_type == 'logarithmic':
#             # Logaritmický růst od min_batch_percent do max_batch_percent
#             min_samples = math.ceil((total_samples * self.min_batch_percent) / 100)
#             max_samples = math.ceil((total_samples * self.max_batch_percent) / 100)
#
#             # Logaritmický růst pomocí exponenciální funkce
#             # Použijeme přirozený logaritmus pro plynulejší růst
#             log_scale = math.log(max_samples / min_samples)
#             current_scale = math.log(epoch + 1) / math.log(total_epochs)
#             return math.ceil(min_samples * math.exp(current_scale * log_scale))
#         else:
#             # Lineární růst
#             min_samples = math.ceil((total_samples * self.min_batch_percent) / 100)
#             max_samples = math.ceil((total_samples * self.max_batch_percent) / 100)
#             return math.ceil(min_samples + (max_samples - min_samples) * (epoch / total_epochs))
#
#     def calculate_learning_rate(self, epoch, total_epochs):
#         """Vypočítá learning rate pro danou epochu s logaritmickým poklesem."""
#         if self.growth_type == 'logarithmic':
#             # Logaritmický pokles od learning_rate do min_learning_rate
#             log_scale = math.log(self.min_learning_rate / self.learning_rate)
#             current_scale = math.log(epoch + 1) / math.log(total_epochs)
#             return self.learning_rate * math.exp(current_scale * log_scale)
#         else:
#             # Lineární pokles
#             return self.learning_rate + (self.min_learning_rate - self.learning_rate) * (epoch / total_epochs)
#
#     def calculate_radius(self, epoch, total_epochs):
#         """Vypočítá poloměr sousedství pro danou epochu s logaritmickým poklesem."""
#         if self.growth_type == 'logarithmic':
#             # Logaritmický pokles od počátečního poloměru k 0
#             min_radius = 0.1  # minimální poloměr pro stabilitu
#             log_scale = math.log(min_radius / self.radius)
#             current_scale = math.log(epoch + 1) / math.log(total_epochs)
#             return max(min_radius, self.radius * math.exp(current_scale * log_scale))
#         else:
#             # Lineární pokles
#             return self.radius * (1 - (epoch / total_epochs))
#
#     def train(self, data):
#         """Trénuje Kohonenovu SOM na zadaných datech."""
#         total_samples = data.shape[0]
#         total_epochs = total_samples  # Počet epoch = počet vzorků
#         batch_size = total_samples // self.num_batches  # Fixní velikost každého batch
#
#         for epoch in range(total_epochs):
#             # Výpočet celkového počtu vzorků zpracovaných v této epoše
#             total_samples_to_process = self.calculate_total_samples_to_process(total_samples, epoch, total_epochs)
#
#             # Výpočet počtu vzorků na batch (zaokrouhleno nahoru)
#             samples_per_batch = math.ceil(total_samples_to_process / self.num_batches)
#
#             # Projít všechny batch
#             for batch_idx in range(self.num_batches):
#                 # Výpočet rozsahu vzorků pro tento batch
#                 start_idx = batch_idx * batch_size
#                 end_idx = min((batch_idx + 1) * batch_size, total_samples)
#                 batch_data = data[start_idx:end_idx]
#
#                 # Výběr náhodných vzorků z batch
#                 if samples_per_batch < len(batch_data):
#                     batch_indices = np.random.choice(len(batch_data), samples_per_batch, replace=False)
#                     batch_data = batch_data[batch_indices]
#
#                 # Aktualizace parametrů pro tuto epochu
#                 current_learning_rate = self.calculate_learning_rate(epoch, total_epochs)
#                 current_radius = self.calculate_radius(epoch, total_epochs)
#
#                 # Projít všechny vybrané vzorky v batch
#                 for sample in batch_data:
#                     # Najít BMU
#                     bmu_idx = self.find_bmu(sample)
#
#                     # Aktualizovat váhy s aktuálními parametry
#                     self.update_weights(sample, bmu_idx, current_learning_rate, current_radius)
#
#             # Logování průběhu
#             if (epoch % 200 == 0):
#                 log_message(f"Epocha {epoch}/{total_epochs}:")
#                 log_message(f"Celkem zpracováno vzorků: {total_samples_to_process}")
#                 log_message(f"Vzorků na batch: {samples_per_batch}")
#                 log_message(f"Learning rate: {current_learning_rate:.6f}")
#                 log_message(f"Poloměr sousedství: {current_radius:.2f}")
#
#     def find_bmu(self, sample):
#         min_dist = float('inf')
#         bmu_idx = None
#
#         for i in range(self.m):
#             for j in range(self.n):
#                 dist = np.linalg.norm(sample - self.weights[i, j])
#                 if dist < min_dist:
#                     min_dist = dist
#                     bmu_idx = (i, j)
#
#         return bmu_idx
#
#     def update_weights(self, sample, bmu_idx, learning_rate, radius):
#         """Aktualizuje váhy neuronů s danými parametry."""
#         for i in range(self.m):
#             for j in range(self.n):
#                 distance_to_bmu = np.linalg.norm(np.array([i, j]) - np.array(bmu_idx))
#                 if distance_to_bmu <= radius:
#                     influence = np.exp(-distance_to_bmu ** 2 / (2 * (radius ** 2)))
#                     weight_change = influence * learning_rate * (sample - self.weights[i, j])
#                     self.weights[i, j] += weight_change
#
#         # Normalizace vah po aktualizaci
#         self.normalize_weights()
#
#     def update_learning_rate_dynamic(self, initial_learning_rate, update_ratio, min_learning_rate=0.01):
#         """Dynamicky upravuje learning rate podle míry změny."""
#         return initial_learning_rate * 0.995  # Klasické snižování
