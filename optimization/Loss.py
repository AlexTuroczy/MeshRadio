from csv import DictReader
from typing import Dict

import torch
import numpy as np

# ---------------------------------------------------------------------------
#  Tunable weights for the composite objective
# ---------------------------------------------------------------------------
DIST_WEIGHT = 1.0          # encourages spatial dispersion / coverage
CONNECT_WEIGHT = 1.5     # enforces k‑connectivity robustness
TARGET_WEIGHT = 0.2

# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

def loss(
    positions: torch.Tensor,
    env_map,
    k: int = 2,
) -> torch.Tensor:
    """Composite objective for the swarm given the current *trainable* positions.

    Parameters
    ----------
    positions : torch.Tensor, shape (N, 2)
        Tank coordinates **with** ``requires_grad=True`` so we can optimise
        them directly.
    env_map : Map‑like object
        Must implement ``get_threshold()`` to provide the communication radius.
        No other map fields are used inside the loss; this keeps the graph
        clean and avoids accidental in‑place edits of map state.
    k : int, default 2
        Required neighbour count for *k*-connectivity.

    Returns
    -------
    torch.Tensor
        Scalar differentiable loss. Lower is better.
    """

    threshold = float(env_map.get_tank_radius(0))

    dispersion = dist_loss(positions)
    connectivity = connectivity_loss(positions, k, threshold, env_map)
    target_seeking = target_seek_loss(positions, env_map.get_all_tank_targets())

    return - DIST_WEIGHT * dispersion + CONNECT_WEIGHT * connectivity + TARGET_WEIGHT * target_seeking


# ---------------------------------------------------------------------------
#  Helper losses
# ---------------------------------------------------------------------------

def dist_loss(positions: torch.Tensor, exclude_self: bool = True) -> torch.Tensor:
    """Mean pair‑wise Euclidean distance between all points (coverage term)."""
    D = torch.cdist(positions, positions, p=2)
    if exclude_self:
        mask = ~torch.eye(D.size(0), dtype=torch.bool, device=D.device)
        return D[mask].mean()
    return D.mean()



def connectivity_loss(
    positions: torch.Tensor,
    k: int,
    threshold: float,
    env_map
) -> torch.Tensor:
    """Penalty for tanks that do **not** meet the *k*-neighbour requirement.

    Fix for *inf* loss: we exclude self‑distances from **both** the degree
    computation *and* the gap penalty so no ∞ values ever enter the mean.
    """

    # 1) pair‑wise distances (N, N)
    D = torch.cdist(positions, positions, p=2)

    eye = torch.eye(D.size(0), dtype=torch.bool, device=D.device)

    # 2) degree of each node (ignore self‑distance by masking)
    deg = (D.masked_fill(eye, float('inf')) < threshold).sum(dim=1)

    deficient = deg < k               # boolean (N,)
    if not deficient.any():
        return positions.new_zeros(())

    elevations = torch.zeros(positions.shape[0])
    for i in range(positions.shape[0]):
        elevations[i] = env_map._evaluate_centers_torch(positions[i], env_map.altitude_centers)

    # 3) positive gaps beyond threshold (set diagonal gap to 0 so it NEVER
    #    pollutes the mean, even for deficient nodes)
    delta = torch.relu(D - elevations*threshold)
    delta = delta.masked_fill(eye, 0.0)   # kill diagonal

    # 4) keep only deficient rows
    penalised = delta * deficient.unsqueeze(1).float()

    return penalised.mean()

def target_seek_loss(positions: torch.Tensor, targets: Dict[int, np.ndarray]):
    tgts = torch.as_tensor(
        np.array(list(targets.values()), dtype=np.float32),
        dtype=torch.float32
    )

    return ((positions - tgts)**2).sum(dim=1).mean()

def dropout_loss(positions, env_map, max_dropout: int = 2, probability_dropout: float = 0.1, k: int = 2) -> torch.Tensor:
    """Drops positions and recomputes loss with eliminated nodes"""

    loss_term = 0

    for depth in range(max_dropout):
        for idx in adaptive_loops([positions.shape[0] for _ in range(depth)]):
            all_indices = torch.arange(positions.size(0))
            keep_indices = all_indices[~torch.isin(all_indices, idx)]

            positions_dropped = positions[keep_indices]
            loss_term += loss(positions_dropped, env_map, k) * (probability_dropout ** depth)
    
    return loss_term




def adaptive_loops(bounds):
    """
    Simulates a dynamic number of nested for loops.

    Args:
        bounds (list or tuple): A list of integers, each representing the upper bound of a loop.

    Yields:
        tuple: The current index for each loop level.
    """
    if bounds == (0,):
        yield torch.tensor([])
    else:
        for indices in np.ndindex(*bounds):
            yield torch.tensor(indices)
