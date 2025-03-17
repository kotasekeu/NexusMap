import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon

class KohonenSOM:
    def __init__(self, x, y, input_len, learning_rate=0.5, radius=None, decay_function=None):
        # Inicializace parametrů sítě
        self.x = x  # Šířka výsledné 2D mapy
        self.y = y  # Výška výsledné 2D mapy
        self.input_len = input_len  # Délka vstupního vektoru
        self.learning_rate = learning_rate  # Počáteční rychlost učení
        self.radius = radius if radius else max(x, y) / 2  # Počáteční poloměr sousedství
        self.decay_function = decay_function if decay_function else self.default_decay_function  # Funkce pro snižování parametrů
        self.weights = np.random.rand(x, y, input_len)  # Inicializace vah náhodnými hodnotami

    def default_decay_function(self, initial_value, iteration, max_iter):
        # Výchozí funkce pro snižování parametrů (exponenciální pokles)
        return initial_value * np.exp(-iteration / max_iter)

    def find_bmu(self, input_vector):
        # Najde nejlepšího shodného neuronu (BMU) pro daný vstupní vektor
        distances = np.linalg.norm(self.weights - input_vector, axis=-1)  # Vypočítá euklidovské vzdálenosti
        return np.unravel_index(np.argmin(distances), (self.x, self.y))  # Vrátí index BMU

    def update_weights(self, input_vector, bmu, iteration, max_iter):
        # Aktualizuje váhy neuronů
        learning_rate = self.decay_function(self.learning_rate, iteration, max_iter)  # Snížení rychlosti učení
        radius = self.decay_function(self.radius, iteration, max_iter)  # Snížení poloměru sousedství

        for i in range(self.x):
            for j in range(self.y):
                distance_to_bmu = np.linalg.norm(np.array([i, j]) - np.array(bmu))  # Vzdálenost neuronu od BMU
                if distance_to_bmu <= radius:
                    influence = np.exp(
                        -distance_to_bmu ** 2 / (2 * (radius ** 2)))  # Výpočet vlivu na základě vzdálenosti
                    self.weights[i, j] += influence * learning_rate * (
                                input_vector - self.weights[i, j])  # Aktualizace vah

    def train(self, data, num_iterations):
        # Trénování sítě
        for iteration in range(num_iterations):
            input_vector = data[np.random.randint(0, len(data))]  # Náhodný výběr vstupního vektoru
            bmu = self.find_bmu(input_vector)  # Najde BMU pro vstupní vektor
            self.update_weights(input_vector, bmu, iteration, num_iterations)  # Aktualizuje váhy

    def map_vects(self, data):
        # Mapuje vstupní vektory na BMU
        return np.array([self.find_bmu(x) for x in data])

    def visualize_map(self, filename='som_map.jpg'):
        # Vytvoření obrázku s barevnou mapou
        fig, ax = plt.subplots(figsize=(10, 10))

        for i in range(self.x):
            for j in range(self.y):
                hexagon = RegularPolygon((i + 0.5 * (j % 2), j * np.sqrt(3) / 2),
                                         numVertices=6,
                                         radius=1 / np.sqrt(3),
                                         orientation=np.radians(0),  # Pootáčení hexagonů pro vertikální strany
                                         facecolor=self.weights[i, j],
                                         edgecolor='k')
                ax.add_patch(hexagon)

        ax.set_xlim(-1, self.x + 1)
        ax.set_ylim(-1, self.y * np.sqrt(3) / 2 + 1)
        ax.set_aspect('equal')
        plt.title('Kohonenova samoorganizující mapa')
        plt.axis('off')

        # Uložení obrázku do souboru
        plt.savefig(filename)
        plt.close()


#tady mi to dělá hezkou mapu


# Příklad použití
data = np.random.rand(100, 3)  # Generování náhodných dat
# print(data);

som = KohonenSOM(30, 30, 3, learning_rate=0.1)  # Inicializace SOM
som.train(data, 1000)  # Trénování SOM

mapped = som.map_vects(data)  # Mapování dat na BMU
# print(mapped)  # Výpis výsledků
som.visualize_map('som_map.jpg')
