import torch
from ObjectiveFunction import loss
from ..simulation import Map
import numpy as np

# example map
map = Map(10, 10, 5, (0,0), [(1,1), (2,2), (3,3), (4,4), (5,5)])


def update(env_map):

    positions = torch.as_tensor(
        np.array(list(env_map.get_tank_positions().values()), dtype=np.float32),
        dtype=torch.float32,
    )
    optimizer = torch.optim.SGD(positions, lr=0.00001)  # using Stochastic Gradient Descent

    # Dummy input and target

    # Training loop
    for epoch in range(100):  # 100 epochs
        print("Hello")
        optimizer.zero_grad()       # clear previous gradients

        l = loss(positions, env_map) # compute loss
        l.backward()             # backward pass (compute gradients)
        optimizer.step()            # update weights


        print(f"Epoch {epoch+1}: Loss = {l.item():.4f}")

    
