"""
Implementation of the Kohonen Self-Organizing Map (SOM) network.

This module provides an implementation of the Kohonen SOM network with the following features:
- Support for both square and hexagonal grids
- Various decay types for learning rate and radius
- Adaptive batch size
- Early stopping based on MQE
- Weight normalization
- Vectorized operations for better performance
- Three processing modes: deterministic, stochastic and hybrid
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
    """Implementation of the Kohonen Self-Organizing Map network.

    Args:
        dim (int): Dimension of the input vectors
        m (int): Height of the SOM grid
        n (int): Width of the SOM grid
        learning_rate (float, optional): Initial learning rate. Defaults to 0.9
        min_learning_rate (float, optional): Minimum learning rate. Defaults to 0.1
        radius (float, optional): Initial neighborhood radius. If None, max(m,n)/2 is used
        min_radius (float, optional): Minimum neighborhood radius. Defaults to 0.1
        processing_type (str, optional): Processing type ('deterministic', 'stochastic', 'hybrid'). Defaults to 'hybrid'
        num_batches (int, optional): Number of batches to process. Defaults to 10
        min_batch_percent (float, optional): Minimum percentage of samples in a batch. Defaults to 0.1
        max_batch_percent (float, optional): Maximum percentage of samples in a batch. Defaults to 5
        lr_decay_type (str, optional): Learning rate decay type. Defaults to 'exp-drop'
        radius_decay_type (str, optional): Radius decay type. Defaults to 'exp-drop'
        batch_growth_type (str, optional): Batch size growth type. Defaults to 'exp-growth'
        random_seed (int, optional): Seed for the random number generator
        growth_g (float, optional): Parameter for exponential growth. Defaults to 15.0
        normalize_weights_flag (bool, optional): Whether to normalize weights. Defaults to False
        epoch_multiplier (float, optional): Multiplier for the number of epochs. Defaults to 1.0
        map_type (str, optional): Grid type ('hex' or 'square'). Defaults to 'hex'
        min_q_error (float, optional): Minimum required quantization error for early stopping
        max_epochs_without_improvement (int, optional): Maximum number of epochs without improvement for early stopping
        mqe_recording_interval (int, optional): Interval for recording the quantization error. Defaults to 10

    Note:
        Supported processing types:
        - 'deterministic': Processes all input vectors in every epoch
        - 'stochastic': Processes one random vector in every epoch
        - 'hybrid': Adaptive batch size based on batch_growth_type, min_batch_percent, max_batch_percent

        Supported decay types:
        - 'logarithmic': Logarithmic decay
        - 'linear-growth': Linear growth
        - 'linear-drop': Linear drop
        - 'exponential': Exponential decay
        - 'exp-growth': Exponential growth
        - 'exp-drop': Exponential drop
    """
    
    def __init__(self, dim, m, n, learning_rate=0.9, min_learning_rate=0.1,
                 radius=None, min_radius=0.1, processing_type='hybrid',
                 num_batches=10, min_batch_percent=0.1, max_batch_percent=5,
                 lr_decay_type='exp-drop', radius_decay_type='exp-drop', batch_growth_type='exp-growth',
                 random_seed=None, growth_g=15.0, normalize_weights_flag=False, epoch_multiplier=1.0, map_type='hex', min_q_error=None,
                 max_epochs_without_improvement=None, mqe_recording_interval=10):        
        # Basic network parameters
        self.m = m
        self.n = n
        self.dim = dim

        # Learning parameters
        self.learning_rate = learning_rate if learning_rate >= min_learning_rate else min_learning_rate
        self.min_learning_rate = min_learning_rate
        
        # Radius setup
        self.min_radius = min_radius
        self.set_radius(radius)

        # Processing type
        if processing_type not in ['deterministic', 'stochastic', 'hybrid']:
            raise ValueError("Processing type must be 'deterministic', 'stochastic' or 'hybrid'")
        self.processing_type = processing_type
        
        # Batch processing parameters (hybrid mode only)
        self.num_batches = num_batches
        self.max_batch_percent = max_batch_percent if max_batch_percent > min_batch_percent else min_batch_percent
        self.min_batch_percent = min_batch_percent

        # Decay and growth types
        self.lr_decay_type = lr_decay_type
        self.radius_decay_type = radius_decay_type
        self.batch_growth_type = batch_growth_type

        # Other parameters
        self.growth_g = float(growth_g)
        self.epoch_multiplier = float(epoch_multiplier)
        self.map_type = map_type
        self.normalize_weights_flag = normalize_weights_flag    
        self.min_q_error = min_q_error
        self.max_epochs_without_improvement = max_epochs_without_improvement
        self.mqe_recording_interval = mqe_recording_interval

        # Training metrics
        self.total_weight_updates = 0
        self.best_mqe = float('inf')
        self.mqe_history = []  # Quantization error history
        self.epochs_history = []  # Epoch numbers
        self.learning_rate_history = []  # Learning rate history
        self.radius_history = []  # Radius history
        self.batch_size_history = []  # Batch size history

        # Weight initialization
        self.base_seed = random_seed

        if random_seed is not None:
            np.random.seed(random_seed)
        self.weights = np.random.rand(m, n, dim)
        self.normalize_weights()

    def normalize_weights(self) -> None:
        """Normalizes neuron weights to unit length."""
        for i in range(self.m):
            for j in range(self.n):
                norm = np.linalg.norm(self.weights[i, j])
                if norm > 0:
                    self.weights[i, j] /= norm

    def get_decay_value(self, t: int, N: int, start: float, end: float, decay_type: str) -> float:
        """Computes the decay or growth value for the given time step.

        Args:
            t (int): Current time step
            N (int): Total number of steps
            start (float): Start value
            end (float): End value
            decay_type (str): Decay or growth type
                - For drop (LR, R): 'static', 'logarithmic-drop', 'linear-drop', 'exponential', 'exp-drop'
                - For growth (batch size): 'linear-growth', 'logarithmic-growth', 'exp-growth'

        Returns:
            float: Decay or growth value

        Raises:
            ValueError: If an unknown decay/growth type is given
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
        """Computes the percentage of samples for the current batch.

        Args:
            t (int): Current time step
            N (int): Total number of steps

        Returns:
            float: Percentage of samples for the batch
        """
        # For growth decay types: 'linear-growth', 'logarithmic-growth', 'exp-growth'
        return self.get_decay_value(t, N, self.min_batch_percent, self.max_batch_percent, self.batch_growth_type)

    def train(self, data: np.ndarray) -> None:
        """Trains the SOM network on the given data.

        Args:
            data (np.ndarray): Input data of shape (n_samples, n_features)
        """
        start_time = datetime.now()
        log_message(f"Training started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        total_samples = data.shape[0]               
        total_epochs = int(total_samples * self.epoch_multiplier)
        
        no_improvement_count = 0

        self.epochs_run = 0
        self.mqe_history = []  # Reset MQE history
        self.epochs_history = []  # Reset epoch history

        # Create a progress bar with timing info
        pbar = tqdm(total=total_epochs, desc=f"Epochs (start: {start_time.strftime('%H:%M:%S')})", 
                   bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
        
        for epoch in range(total_epochs):
            samples_per_batch = 1;
            # Compute learning parameters for the whole epoch
            current_lr = self.get_decay_value(epoch, total_epochs, self.learning_rate, self.min_learning_rate, self.lr_decay_type)
            current_radius = self.get_decay_value(epoch, total_epochs, self.radius, self.min_radius, self.radius_decay_type)

            # Initialize samples_per_batch for hybrid mode only
            if self.processing_type == 'hybrid':
                batch_percent = self.get_batch_percent(epoch, total_epochs)
                samples_per_batch = math.ceil(total_samples * batch_percent / 100)

            # Batch processing
            if self.processing_type == 'stochastic':
                if self.base_seed is not None:
                    np.random.seed(self.base_seed + epoch)
                idx = np.random.randint(0, total_samples)
                sample = data[idx]
                bmu_idx = self.find_bmu(sample)
                self.update_weights(sample, bmu_idx, current_lr, current_radius)
            elif self.processing_type == 'deterministic':
                # In deterministic mode, process all samples sequentially
                for sample in data:
                    bmu_idx = self.find_bmu(sample)
                    self.update_weights(sample, bmu_idx, current_lr, current_radius)
            else:  # hybrid mode
                # In hybrid mode, use random indices for batches
                if self.base_seed is not None:
                    np.random.seed(self.base_seed + epoch)
                indices = np.random.permutation(total_samples)
                # Split indices into batches
                for batch_idx in range(self.num_batches):
                    start_idx = batch_idx * (total_samples // self.num_batches)
                    end_idx = min((batch_idx + 1) * (total_samples // self.num_batches), total_samples)
                    batch_indices = indices[start_idx:end_idx]

                    # Limit the batch size if needed
                    if samples_per_batch < len(batch_indices):
                        batch_indices = batch_indices[:samples_per_batch]

                    # Update weights for each sample in the batch
                    for idx in batch_indices:
                        sample = data[idx]
                        bmu_idx = self.find_bmu(sample)
                        self.update_weights(sample, bmu_idx, current_lr, current_radius)

            # Update the weight update counter
            if self.processing_type == 'stochastic':
                self.total_weight_updates += 1
            else:
                self.total_weight_updates += total_samples

            # Normalize weights if requested
            if self.normalize_weights_flag:
                self.normalize_weights()

            # Compute MQE depending on the processing type
            should_compute_mqe = False
            total_qe = None  # Initialize total_qe

            # Compute MQE every epoch in deterministic mode, otherwise at an interval
            if self.processing_type == 'deterministic':
                should_compute_mqe = True
            else:
                # Adjust the interval to the number of epochs
                interval = max(1, total_epochs // 500)
                if epoch % interval == 0:
                    should_compute_mqe = True

            if should_compute_mqe:
                # Compute MQE
                codebook_vectors = self.weights.reshape(-1, self.dim)
                bmu_indexes = np.array([r * self.n + c for r, c in (self.find_bmu(x) for x in data)])
                _, total_qe = self.compute_quantization_error(data, codebook_vectors, bmu_indexes, (self.m, self.n), compute_neuron_map=False)

                # Store MQE and parameter history
                self.mqe_history.append(total_qe)
                self.epochs_history.append(epoch)
                self.learning_rate_history.append(current_lr)
                self.radius_history.append(current_radius)
                if self.processing_type == 'hybrid':
                    self.batch_size_history.append(samples_per_batch)
                                
                # Check stopping conditions
                if self.min_q_error is not None and total_qe <= self.min_q_error:
                    log_message(f"Reached MQE limit {self.min_q_error}. Stopping training.")
                    break

                if total_qe < self.best_mqe:
                    self.best_mqe = total_qe
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
                    if self.max_epochs_without_improvement is not None and no_improvement_count >= self.max_epochs_without_improvement:
                        log_message(f"No improvement after {self.max_epochs_without_improvement} epochs. Stopping training.")
                        break

            # Progress logging
            if epoch % 500 == 0:
                elapsed_time = datetime.now() - start_time
                if total_qe is not None:
                    log_message(f"{epoch}|{total_samples}|{samples_per_batch}|{current_radius:.4f}|{current_lr:.6f}|{total_qe:.6f} (time: {str(elapsed_time).split('.')[0]})")
                else:
                    log_message(f"{epoch}|{total_samples}|{samples_per_batch}|{current_radius:.4f}|{current_lr:.6f}|N/A (time: {str(elapsed_time).split('.')[0]})")        

            # Update the progress bar
            pbar.update(1)
            self.epochs_run = epoch + 1

        # Close the progress bar
        pbar.close()

        # Print summary information
        end_time = datetime.now()
        total_time = end_time - start_time
        print(f"\nTraining summary:")
        print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total time: {str(total_time).split('.')[0]}")
        print(f"Total weight updates: {self.total_weight_updates}")
        print(f"Best MQE reached: {self.best_mqe:.6f}")

    def find_bmu(self, sample: np.ndarray) -> tuple[int, int]:
        """Finds the Best Matching Unit (BMU) for the given sample.

        Args:
            sample (np.ndarray): Input sample

        Returns:
            tuple[int, int]: Grid coordinates (i,j) of the BMU
        """
        flat = self.weights.reshape(-1, self.dim)
        diffs = flat - sample
        dists = np.linalg.norm(diffs, axis=1)
        idx = np.argmin(dists)
        return divmod(idx, self.n)

    def update_weights(self, sample: np.ndarray, bmu_idx: tuple[int, int], learning_rate: float, radius: float) -> None:
        """Updates the weights of neurons in the BMU neighborhood.

        Args:
            sample (np.ndarray): Input sample
            bmu_idx (tuple[int, int]): BMU coordinates
            learning_rate (float): Current learning rate
            radius (float): Current neighborhood radius
        """
        # Create the coordinate grid
        i_coords = np.arange(self.m)[:, np.newaxis]
        j_coords = np.arange(self.n)[np.newaxis, :]

        # Compute distances for all neurons at once
        distances = np.zeros((self.m, self.n))
        for i in range(self.m):
            for j in range(self.n):
                distances[i, j] = self.grid_distance((i, j), bmu_idx)
        
        # Compute influence for all neurons at once
        influence = np.exp(-distances ** 2 / (2 * (radius ** 2)))

        # Update weights for all neurons at once
        self.weights += influence[:, :, np.newaxis] * learning_rate * (sample - self.weights)

    def grid_distance(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """Computes the distance between two neurons in the grid.

        Args:
            a (tuple[int, int]): Coordinates of the first neuron
            b (tuple[int, int]): Coordinates of the second neuron

        Returns:
            float: Distance between the neurons

        Note:
            Uses Euclidean distance for the square grid
            and hex-coordinate distance for the hexagonal grid.
            The hex grid uses "odd-r" offset rows (odd rows shifted right by
            half a cell), the same layout the visualizations draw.
        """
        i1, j1 = a
        i2, j2 = b
        if self.map_type == 'square':
            return math.hypot(i1 - i2, j1 - j2)
        # Convert odd-r offset coordinates to cube coordinates
        x1, z1 = j1 - i1 // 2, i1
        y1 = -x1 - z1
        x2, z2 = j2 - i2 // 2, i2
        y2 = -x2 - z2
        return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) / 2
    
    def compute_quantization_error(self, data: np.ndarray, codebook_vectors: np.ndarray, 
                                 bmu_indexes: np.ndarray, som_shape: tuple[int, int],
                                 compute_neuron_map: bool = False) -> tuple[np.ndarray | None, float]:
        """Computes the quantization error per neuron and the total error.

        Args:
            data (np.ndarray): Input samples
            codebook_vectors (np.ndarray): Neuron weight vectors
            bmu_indexes (np.ndarray): BMU index for each sample
            som_shape (tuple[int, int]): Shape of the SOM grid
            compute_neuron_map (bool): Whether to compute the per-neuron error map

        Returns:
            tuple[np.ndarray | None, float]: Neuron error map (None if compute_neuron_map=False) and the total quantization error
        """
        # Get the winning neuron weights for each sample
        winning_weights = codebook_vectors[bmu_indexes]

        # Compute the total quantization error
        total_qe = np.linalg.norm(data - winning_weights, axis=1).mean()

        # Compute the per-neuron error map (only if requested)
        neuron_error_map = None
        if compute_neuron_map:
            # Create a mask for each neuron
            neuron_masks = np.zeros((len(codebook_vectors), len(data)), dtype=bool)
            neuron_masks[bmu_indexes, np.arange(len(data))] = True

            # Compute the mean error for each neuron
            neuron_errors = np.zeros(len(codebook_vectors))
            for i in range(len(codebook_vectors)):
                if np.any(neuron_masks[i]):
                    neuron_errors[i] = np.linalg.norm(data[neuron_masks[i]] - codebook_vectors[i], axis=1).mean()
            
            neuron_error_map = neuron_errors.reshape(som_shape)

        return neuron_error_map, total_qe
    
    def set_radius(self, radius: float | None) -> None:
        """Sets the initial neighborhood radius.

        Args:
            radius (float | None): Initial neighborhood radius. If None, max(m,n)/2 is used
        """
        if radius is None:
            self.radius = max(self.m, self.n) / 2
        elif radius < self.min_radius:
            self.radius = self.min_radius
        else:
            self.radius = radius
    