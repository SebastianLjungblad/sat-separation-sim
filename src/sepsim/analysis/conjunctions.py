from itertools import combinations

import numpy as np

def pairwise_distances(positions: np.ndarray) -> tuple[list[tuple[int, int]], np.ndarray]:
    """
    positions: form (antal_objekt, N_tidpunkter, 3)
    Returnerar: lista med par (i, j) och avstånd med form (antal_par, N_tidpunkter)
    """

    n_objects = positions.shape[0]
    pairs = list(combinations(range(n_objects), 2))

    distances = []
    for i, j in pairs:
        diff = positions[i] - positions[j]
        d = np.linalg.norm(diff, axis=1)
        distances.append(d)

    return pairs, np.array(distances)

def closest_approach(distances: np.ndarray, t: np.ndarray, after: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """
    Minsta avstånd per par och tidpunkten då det inträffar,
    räknat bara för tidpunkter t >= after.

    distances: form (antal_par, N_tidpunkter)
    t:         form (N_tidpunkter,)
    after:     frigångstid [s], tidpunkter före den ignoreras
    Returnerar: (min_avstånd [m], tid_för_min [s]), båda med form (antal_par,)
    """
    if after > t[-1]:
        raise ValueError("after är större än simuleringens längd")

    mask = t >= after
    d_after = distances[:, mask]
    t_after = t[mask]

    idx = np.argmin(d_after, axis=1)
    min_dist = d_after.min(axis=1)
    t_min = t_after[idx]

    return min_dist, t_min
