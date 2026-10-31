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
    Banor relativt referenspunkten i banplanet (y längs banan, x radiellt).
    Alla objekt ritas, även steget (objekt 0), eftersom det nu rör sig av rekylen.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    for k in range(positions.shape[0]):
        style = {"color": "black", "linestyle": "--"} if k == 0 else {}
        ax.plot(positions[k, :, 1], positions[k, :, 0], label=labels[k], **style)
    ax.plot(0, 0, "k+", markersize=12, label="Reference point")
    ax.set_xlabel("Along-track y [m]")
    ax.set_ylabel("Radial x [m]")
    ax.set_title("Trajectories relative to reference orbit (orbital plane)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig