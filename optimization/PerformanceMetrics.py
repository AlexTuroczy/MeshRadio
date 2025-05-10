import numpy as np
import networkx as nx
from simulation import Map
import torch

def dropout_reliability(env_map, prob_drop=0.25):
    """ Takes env map and does Monte-Carlo simulation to determine probability that all nodes are connected """

    num_repetitions = 1000
    positions = torch.as_tensor(
            np.array(list(env_map.get_tank_pos_dict().values()), dtype=np.float32),
            dtype=torch.float32
        )
    positions.requires_grad = False

    num_nodes = positions.shape[0]


    for _ in range(num_repetitions):

        # sample nodes to drop out
        dropped_out_trial = np.random.binomial(n=1, p=prob_drop, size=num_nodes)
        num_remaining_nodes = dropped_out_trial.sum()


        pos_dropped = positions[dropped_out_trial]

        D = torch.cdist(positions, positions, p=2)
        
        G = nx.Graph()
        for i in range(num_remaining_nodes):


        
        


