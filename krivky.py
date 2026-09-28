import numpy as np
import matplotlib.pyplot as plt

def get_decay_value(t, N, start, end, decay_type, growth_g=1.0):
    if N <= 1:
        return start

    if decay_type == 'static':
        return start

    elif decay_type == 'linear-drop':
        return start - (t / (N - 1)) * (start - end)

    elif decay_type == 'linear-growth':
        return start + (t / (N - 1)) * (end - start)

    elif decay_type == 'exp-drop':
        norm = (1 - np.exp(-growth_g * t / N)) / (1 - np.exp(-growth_g))
        return start - norm * (start - end)

    elif decay_type == 'exp-growth':
        return start + (end - start) * (np.exp(growth_g * t / N) - 1) / (np.exp(growth_g) - 1)

    elif decay_type == 'log-drop':
        norm = np.log(growth_g * t + 1) / np.log(growth_g * N + 1)
        return start - norm * (start - end)

    elif decay_type == 'log-growth':
        return start + (end - start) * (np.log(growth_g * t + 1) / np.log(growth_g * N + 1))

    elif decay_type == 'step-down':
        step_count = 10
        step_size = N // step_count
        current_step = min(t // step_size, step_count - 1)
        factor = 0.7 ** current_step
        return max(end, start * factor)

    else:
        raise ValueError(f"Unknown decay_type: {decay_type}")

# Settings
N = 10_000
t_vals = np.arange(N)
growth_g = 5.0
decay_types = [
    'static', 'linear-drop', 'linear-growth',
    'exp-drop', 'exp-growth', 'log-drop', 'log-growth', 'step-down'
]

def plot_decay(title, start, end, direction='both', filename='krivka.png'):
    plt.figure(figsize=(10, 6))
    for decay_type in decay_types:
        if direction == 'drop' and 'growth' in decay_type:
            continue
        if (direction == 'drop' and ('growth' in decay_type or 'static' == decay_type)) or \
           (direction == 'growth' and ('drop' in decay_type or decay_type == 'step-down')):
            continue
        vals = [get_decay_value(t, N, start, end, decay_type, growth_g) for t in t_vals]
        plt.plot(t_vals, vals, label=decay_type)
    plt.title(title)
    plt.xlabel("Number of passes through the dataset")
    plt.ylabel("Parameter value")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()


plot_decay("Learning rate (0.9 → 0.1) - decay curves", 0.9, 0.1, direction='drop', filename="krivka_lr.png")
plot_decay("Neighborhood radius (20 → 1) - decay curves", 20, 1, direction='drop', filename="krivka_radius.png")
plot_decay("Input vectors processed per pass [%] (0.01 → 100)", 0.01, 100, direction='growth', filename="krivka_batch.png")


# Plot decay variants with different g values
def plot_decay_with_g_variants(title, start, end, decay_type, direction, filename):
    plt.figure(figsize=(10, 6))
    for g in [0.1, 1, 5, 15, 25, 50]:
        vals = [get_decay_value(t, N, start, end, decay_type, growth_g=g) for t in t_vals]
        plt.plot(t_vals, vals, label=f"{decay_type} (g={g})")
    plt.title(f"{title}")
    plt.xlabel("Number of passes through the dataset")
    plt.ylabel("Parameter value")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()

# Plot decay variants with different g
plot_decay_with_g_variants("Learning rate / Neighborhood radius", 0.9, 0.1, "exp-drop", "drop", "krivka_exp_drop_g.png")
plot_decay_with_g_variants("Learning rate / Neighborhood radius", 0.9, 0.1, "log-drop", "drop", "krivka_log_drop_g.png")
plot_decay_with_g_variants("Growth curves of the number of updated input vectors per pass through the dataset.", 0.01, 100, "exp-growth", "growth", "krivka_exp_growth_g.png")
plot_decay_with_g_variants("Growth curves of the number of updated input vectors per pass through the dataset.", 0.01, 100, "log-growth", "growth", "krivka_log_growth_g.png")

def plot_combined_growth_with_g(title, start, end, filename):
    plt.figure(figsize=(10, 6))
    for decay_type in ["exp-growth", "log-growth"]:
        for g in [1, 5, 15, 25, 50]:
            vals = [get_decay_value(t, N, start, end, decay_type, growth_g=g) for t in t_vals]
            plt.plot(t_vals, vals, label=f"{decay_type} (g={g})")
    plt.title(f"{title}")
    plt.xlabel("Number of passes through the dataset")
    plt.ylabel("Input vectors processed per pass [%]")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    # Separate legend
    handles, labels = plt.gca().get_legend_handles_labels()
    fig_legend = plt.figure(figsize=(8, 2))
    fig_legend.legend(handles, labels, loc='center', ncol=3)
    fig_legend.tight_layout()
    fig_legend.savefig("krivka_growth_combined_legend.png", dpi=300)
    plt.close(fig_legend)
    plt.close()

plot_combined_growth_with_g("Growth curves of the number of updated input vectors per pass through the dataset.", 0.01, 100, "krivka_growth_combined.png")
