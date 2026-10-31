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

def closest_approach(
    distances: np.ndarray, t: np.ndarray, after: float | np.ndarray = 0.0
) -> tuple[np.ndarray, np.ndarray]:
    """
    Minsta avstånd per par och tidpunkten då det inträffar.

    after: frigångstid [s], antingen ett tal (samma för alla par)
           eller en array med ett värde per par.
    """
    after = np.broadcast_to(np.asarray(after, dtype=float), (distances.shape[0],))
    if np.any(after > t[-1]):
        raise ValueError("after är större än simuleringens längd för minst ett par")

    valid = t[np.newaxis, :] >= after[:, np.newaxis]     # mask, form (antal_par, N)
    d = np.where(valid, distances, np.inf)                # ogiltiga tider → oändligt

    idx = np.argmin(d, axis=1)
    min_dist = d[np.arange(len(idx)), idx]
    return min_dist, t[idx]
