import torch
from optimization import Loss
from simulation import Map
import numpy as np

# example map
map = Map(10, 10, 5, (4.5,6), [(1.4,1.3), (2,2), (3,3), (4,4), (5,5)])


def update(env_map,k=3):

    torch.autograd.set_detect_anomaly(True)

    positions = torch.as_tensor(
        np.array(list(env_map.get_tank_pos_dict().values()), dtype=np.float32),
        dtype=torch.float32
    )
    positions.requires_grad = True
    optimizer = torch.optim.SGD([positions], lr=0.01)  # using Stochastic Gradient Descent

    map_bounds ={"x": env_map.x_size, "y": env_map.y_size}
    # Dummy input and target

    # Training loop
    for epoch in range(100):
        optimizer.zero_grad()
        # ---- clip AFTER the optimiser step, with no_grad ----


        loss = Loss.loss(positions, env_map ,k=k)
        loss.backward()
        optimizer.step()                      # gradient update


        with torch.no_grad():
            positions[:, 0].clamp_(0, map_bounds["x"])  # clip x
            positions[:, 1].clamp_(0, map_bounds["y"])  # clip y

        print(f"Epoch {epoch+1}: Loss = {loss.item():.4f}")

    positions = positions.detach().numpy()
    print(positions)
    ret = {i: np.array(positions[i]) for i in range(positions.shape[0])}
    return ret

    
