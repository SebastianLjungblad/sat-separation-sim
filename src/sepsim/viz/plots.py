import matplotlib.pyplot as plt
import numpy as np


def plot_distances(pairs, distances, t, labels, safety=10.0):
    """
    Avstånd över tid för alla par, med säkerhetsavstånd.

    pairs:     lista med (i, j) från pairwise_distances
    distances: form (antal_par, N)
    t:         tidpunkter [s], form (N,)
    labels:    namn på objekten, t.ex. ["Dispenser", "Sat 1", "Sat 2"]
    safety:    säkerhetsavstånd [m]
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    for (i, j), d in zip(pairs, distances):
        d_plot = np.where(d > 0, d, np.nan)       # log-skala klarar inte 0
        ax.plot(t / 60, d_plot, label=f"{labels[i]}–{labels[j]}")

    ax.axhline(safety, color="red", linestyle="--", label=f"Safety distance ({safety:g} m)")

    ax.set_yscale("log")
    ax.set_xlabel("Time since mission start [min]")
    ax.set_ylabel("Distance [m]")
    ax.set_title("Relative distance between objects")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig

def plot_trajectories(positions, labels):
    """
    Banor relativt dispensern i banplanet (y längs banan, x radiellt).

    positions: form (antal_objekt, N, 3), objekt 0 = dispensern
    labels:    namn på objekten, t.ex. ["Dispenser", "Sat 1", "Sat 2"]
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for k in range(1, positions.shape[0]):     # börja på 1: hoppa över dispensern
        y = positions[k, :, 1]                 # längs banan
        x = positions[k, :, 0]                 # radiellt
        ax.plot(y, x, label=labels[k])

    ax.plot(0, 0, "k^", markersize=10, label=labels[0])   # dispensern i origo

    ax.set_xlabel("Along-track y [m]")
    ax.set_ylabel("Radial x [m]")
    ax.set_title("Trajectories relative to dispenser (orbital plane)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig