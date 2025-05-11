from csv import DictReader
from typing import Dict

import torch
import numpy as np

import networkx as nx

# ---------------------------------------------------------------------------
#  Tunable weights for the composite objective
# ---------------------------------------------------------------------------
DIST_WEIGHT = 2#300.0          # encourages spatial dispersion / coverage
CONNECT_WEIGHT = 3  # enforces k‑connectivity robustness
TARGET_WEIGHT = 1
HQ_WEIGHT = 100

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
    connectivity_to_hq = connectivity_hq_loss(positions, env_map.get_hq_pos())

    return -DIST_WEIGHT * dispersion + CONNECT_WEIGHT * connectivity + TARGET_WEIGHT * target_seeking + HQ_WEIGHT * connectivity_to_hq


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


def closest_loss(positions: torch.Tensor):
    D = torch.cdist(positions, positions, p=2) + torch.eye(positions.shape[0]) * 1e7
    closest_dist, _ = torch.min(D, axis=0)
    loss = 1 / (1 + closest_dist)**2
    return loss.mean()



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
        elevations[i] = env_map._evaluate_altitude_torch(positions[i], env_map.altitude_centers)

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


def iamclosestinmycc(ccs, node, closest, positions):
    cc = [cc for cc in ccs if node in cc][0]
    min_dist = float('inf')
    best_node = node
    for c_node in cc:
        dist_to = dist(positions[closest], positions[c_node])
        if dist_to < min_dist:
            min_dist = dist_to
            best_node = c_node

    return best_node == node

def iamclosestinmycc_to_hq(ccs, node, hq_pos, positions):
        if ccs == []:
            return True
        cc = [cc for cc in ccs if node in cc][0]
        min_dist = float('inf')
        best_node = node
        for c_node in cc:
            dist_to = dist(positions[c_node], hq_pos)
            if dist_to < min_dist:
                min_dist = dist_to
                best_node = c_node

        return best_node == node

def connectivity_hq_loss(positions, hq_pos):
    loss = 0
    online, ccs = online_nodes(positions, hq_pos)
    mask = torch.isin(torch.arange(positions.shape[0]), torch.tensor(list(online)))
    mask_out = torch.ones((positions.shape[0], positions.shape[0])) * 1e7
    mask_out[:, mask] = 0
    D = torch.cdist(positions, positions, p=2) + mask_out + torch.eye(positions.shape[0]) * 1e7

    for node in range(positions.shape[0]):
        if not node in online:
            if len(online) > 0:
                closest = torch.argmin(D[node])
                if iamclosestinmycc(ccs, node, closest, positions):
                    loss += dist(positions[closest], positions[node])
            else:
                if iamclosestinmycc_to_hq(ccs, node, hq_pos, positions):
                    loss += dist(positions[node], hq_pos)

    # dists = []
    # for node in range(positions.shape[0]):
    #     dist_to_hq = dist(positions[node], hq_pos)
    #     # if dist_to_hq < min_dist_to_hq:
    #     #     min_dist_to_hq = dist_to_hq
    #     dists.append(dist_to_hq)
    # dists = sorted(dists)
    # for i in range(len(dists)):
    #     loss += 0.1**i * dists[i]
    return loss


def dist(pos1, pos2):
    if isinstance(pos2, np.ndarray):
        pos2 = torch.tensor(pos2)
    return torch.dist(pos1, pos2)

RADIUS = 20
RADIUS_HQ = 20

def online_nodes(positions, hq_pos):
    graph = nx.Graph()
    for i in range(positions.shape[0]):
        graph.add_node(i)

    hq_id = positions.shape[0]

    graph.add_node(hq_id)

    for i in range(positions.shape[0]):
        for j in range(positions.shape[0]):
            if not i == j and dist(positions[i], positions[j]) < RADIUS:
                graph.add_edge(i, j)

        if dist(positions[i], hq_pos) < RADIUS_HQ:
            graph.add_edge(i, hq_id)

    connected_components = nx.connected_components(graph)
    connected_components = [cc for cc in connected_components]
    hq_connected_component = [comp for comp in connected_components if hq_id in comp][0]
    hq_connected_component.remove(hq_id)
    return hq_connected_component, [comp for comp in connected_components if not hq_id in comp]
    
