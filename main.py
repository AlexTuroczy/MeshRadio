from optimization import Update
from simulation import Map, viz

def main():
    iters = 1000

    env = Map(
        map_x_size=100,
        map_y_size=100,
        nb_nodes=6,
        hq_pos=(50, 50),                           # HQ dead‑centre
        init_positions=[                           # initial tank positions
            (10.1, 10),
            (10.05, 11),
            (10.11, 12),
            (10.3, 13),
            (10.14, 14),
            (10.08, 15),
        ],
        targets=[                                  # three targets
            (90, 10),
            (10, 90),
            (80, 50),
        ],
        altitude_centers=[                         # three “hills”
            [20, 20],     # south‑west
            [70, 70],     # north‑east
            [40, 80],     # north‑central
        ],
        sigmas=[                         # three “hills”
            20, 20,     # south‑west
        ],
    )
    viz.init_live(figsize=(6, 6), show_radius=False)   # ← NEW
    k = 2
    for i in range(iters):
        next_positions = Update.update(env, k=k)
        print(next_positions)
        env.set_pos_all_tanks(next_positions)
        env_state = env.get_state_dict()
        viz.render(env_state)
        print(f"Iteration {i}")
    
    # ------------- keep window alive -------------
    print("Simulation finished – close the window to exit.")
    viz.hold()

if __name__ == "__main__":
    main()