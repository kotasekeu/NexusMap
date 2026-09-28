# evolutionary_som_config.py

# This file defines default and test parameters for training the Kohonen self-organizing map (SOM).
# Each parameter can be given either a single value (static setting) or a list of variants (to test multiple configurations).
# The evolutionary algorithm then automatically selects or iterates over the variants.
#
# Examples of using variants:
#
# NUMERIC VALUE (one or more):
# "learning_rate": 0.5                    → the fixed value 0.5 is used
# "learning_rate": [0.1, 0.5, 0.9]        → three different values are tested
#
# TEXT VALUE:
# "lr_decay_type": "linear"              → "linear" is used
# "lr_decay_type": ["linear", "exp-drop"] → both decay types are tested
#
# MAP SIZE:
# "m": 20, "n": 20                        → a single size
# "m": [10, 20], "n": [10, 20]            → the height and width variants are tested

# --- Start of configuration ---

# Basic parameter settings for the Kohonen SOM and evolutionary testing

CONFIG = {
    # Evolutionary algorithm settings
    # Population size in each generation
    "population_size": 10,

    # Number of generations
    "generations": 5,

    # Prefix for the configuration identifier
    "uid_prefix": "evolution",

    # Kohonen SOM parameters
    # Initial learning rate – determines the learning speed at the start of training
    "learning_rate": [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3],

    # Minimum learning rate – lower bound for learning rate decay
    "min_learning_rate": [0.3, 0.2, 0.1, 0.05],

    # Initial neighborhood radius – determined automatically if not given
    "radius": [10.0, 5.0, 2.0],

    # Minimum radius – lower bound for radius decay during training
    "min_radius": [1.0, 0.5, 0.2, 0.1],

    # Number of batches per epoch – how often the weights are updated
    "num_batches": 10,

    # Minimum percentage of data used in one step
    "min_batch_percent": [1.0, 0.5, 0.2, 0.1],

    # Maximum percentage of data used in one step
    "max_batch_percent": [10.0, 5.0, 2.0],

    # Learning rate decay type – exponential drop here
    "lr_decay_type": ["linear-drop", "exp-drop"],

    # Radius decay type – also exponential drop here
    "radius_decay_type": ["linear-drop", "exp-drop"],

    # Growth type for the number of samples over time – exponential growth here
    "batch_growth_type": ["exp-growth", "linear-growth"],

    # Random seed for reproducible results
    "random_seed": None,

    # Parameter G for the growth function – affects the shape of exp-growth
    "growth_g": [5.0, 10.0, 15.0, 25.0, 50.0],

    # Number of input samples for generated data
    "sample_size": 500,

    # Number of input attributes (dimensions) for generated data
    "input_dim": 4,

    # Output map size (height m, width n)
    "m": 20,
    "n": 20,

    # Multiplier determining the number of epochs (sample_size * epoch_multiplier)
    "epoch_multiplier": 1.0,

    # Minimum map quality (Q-error)
    "min_q_error": None,

    # Map type
    "map_type": "square",

    # Weight normalization
    "normalize_weights_flag": [False, True],

    # Number of epochs without improvement before training stops
    "max_epochs_without_improvement": None
}