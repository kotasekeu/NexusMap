# evolutionary_som_config.py

# Tento soubor definuje výchozí a testovací parametry pro trénink Kohonenovy samo-organizační mapy (SOM).
# U každého parametru lze zadat buď jednu hodnotu (statické nastavení), nebo pole variant (pro testování více konfigurací).
# Evoluční algoritmus následně automaticky vybere nebo iteruje varianty.
#
# Příklady použití variant:
#
# ČÍSELNÁ HODNOTA (jedna nebo více):
# "learning_rate": 0.5                    → použije se pevná hodnota 0.5
# "learning_rate": [0.1, 0.5, 0.9]        → testují se tři různé hodnoty
#
# TEXTOVÁ HODNOTA:
# "lr_decay_type": "linear"              → použije se "linear"
# "lr_decay_type": ["linear", "exp-drop"] → testují se oba typy útlumu
#
# ROZMĚROVÉ HODNOTY (např. velikost mapy):
# "map_size": (20, 20)                    → jedna velikost
# "map_size": [(10, 10), (20, 20)]        → testují se dvě varianty

# --- Začátek konfigurace ---

# Základní nastavení parametrů pro Kohonenův SOM a evoluční testování

CONFIG = {
    # Nastavení evolučního algoritmu
    # Velikost populace v každé generaci
    "population_size": 10,       

    # Počet generací
    "generations": 5,        

    # Předpona pro identifikátor konfigurace
    "uid_prefix": "evolution",

    # Parametry Kohonenova SOM
    # Počáteční learning rate – určuje rychlost učení na začátku tréninku
    "learning_rate": 0.9,

    # Minimální learning rate – dolní mez pro útlum learning rate
    "min_learning_rate": 0.1,

    # Počáteční poloměr sousedství – pokud není zadán, určuje se automaticky
    "radius": None,

    # Minimální poloměr – dolní mez pro útlum radiusu během tréninku
    "min_radius": 0.1,

    # Počet batchů v rámci jedné epochy – jak často se aktualizují váhy
    "num_batches": 10,

    # Minimální procento dat použitých v jednom kroku
    "min_batch_percent": 0.1,

    # Maximální procento dat použitých v jednom kroku
    "max_batch_percent": 5.0,

    # Typ útlumu learning rate – zde exponenciální pokles
    "lr_decay_type": "exp-drop",

    # Typ útlumu radiusu – zde také exponenciální pokles
    "radius_decay_type": "exp-drop",

    # Typ růstu počtu vzorků v čase – zde exponenciální růst
    "batch_growth_type": "exp-growth",

    # Náhodné semínko pro replikovatelnost výsledků
    "random_seed": 42,

    # Parametr G pro růstovou funkci – ovlivňuje tvar exp-growth
    "growth_g": [10.0, 15.0, 25.0],

    # Počet vstupních vzorků pro generovaná data
    "sample_size": 1000,

    # Počet vstupních atributů (rozměrů) pro generovaná data
    "input_dim": 5,

    # Velikost výstupní mapy (šířka, výška)
    "map_size": (20, 20),

    # Násobitel určující počet epoch (sample_size * epoch_multiplier)
    "epoch_multiplier": 1.0
}