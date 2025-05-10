import torch
import numpy as np

# ---------------------------------------------------------------------------
#  Tunable weights for the composite objective
# ---------------------------------------------------------------------------
DIST_WEIGHT = 1.0          # encourages spatial dispersion / coverage
CONNECT_WEIGHT = 1.0       # enforces k‑connectivity robustness

# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

def loss(env_map, k: int = 2) -> torch.Tensor:
    """Compute the composite loss for the current environment state.

    Parameters
    ----------
    env_map : object
        Must expose:
            get_tank_positions() -> Dict[id, Tuple[float, float]]
            get_threshold()      -> float (communication radius)
    k : int, default=2
        Required neighbour count for *k*-connectivity.

    Returns
    -------
    torch.Tensor
        Differentiable scalar objective (higher ⇒ worse).
    """

    positions = torch.as_tensor(
        np.array(list(env_map.get_tank_positions().values()), dtype=np.float32),
        dtype=torch.float32,
    )
    threshold = float(env_map.get_threshold())

    disp = dist_loss(positions)
    conn = connectivity_loss(positions, k, threshold)
    return DIST_WEIGHT * disp + CONNECT_WEIGHT * conn


# ---------------------------------------------------------------------------
#  Helper losses
# ---------------------------------------------------------------------------

def dist_loss(positions: torch.Tensor, exclude_self: bool = True) -> torch.Tensor:
    """Mean pair‑wise Euclidean distance between points (coverage term)."""
    D = torch.cdist(positions, positions, p=2)
    if exclude_self:
        mask = ~torch.eye(D.size(0), dtype=torch.bool, device=D.device)
        return D[mask].mean()
    return D.mean()


def connectivity_loss(
    positions: torch.Tensor,
    k: int,
    threshold: float,
) -> torch.Tensor:
    """Penalty for tanks that do **not** meet the *k*-neighbour requirement.

    Steps:
    1. Compute the degree (neighbour count) of every tank using the provided
       communication radius.
    2. If a tank's degree is **≥ k** it contributes **zero** to the loss.
    3. Otherwise include *all* positive gaps (``distance − threshold``) between
       that tank and every other tank.  The overall loss is the mean of these
       selected gaps, giving smooth, fully‑differentiable gradients.

    Parameters
    ----------
    positions : torch.Tensor, shape (N, 2)
    k         : int, minimum required neighbours
    threshold : float, communication radius

    Returns
    -------
    torch.Tensor – scalar ≥ 0.  Zero when the swarm is *k*-connected.
    """

    # Pair‑wise distances (N, N) – diagonal set to 0 so it won't affect gaps
    D = torch.cdist(positions, positions, p=2)
    D.fill_diagonal_(0.0)

    # Degree: count of neighbours already within range
    deg = (D < threshold).sum(dim=1)  # (N,)

    # Mask rows that violate the degree requirement (1 ⇒ penalise, 0 ⇒ ignore)
    mask = (deg < k).float()          # (N,)
    if mask.max() == 0:
        # Every tank satisfied ⇒ zero loss (keeps graph clean)
        return positions.new_zeros(())

    # Positive gaps for *all* pairs (distance beyond threshold)
    delta = torch.relu(D - threshold)  # (N, N)

    # Row‑scale by mask to include only deficient tanks
    penalised = delta * mask.unsqueeze(1)  # broadcast (N,1) → (N,N)

    return penalised.mean()
