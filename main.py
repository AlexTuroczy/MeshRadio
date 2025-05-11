from simulation import Map, viz
from optimization import Update

import math

MAX_STEP_SIZE = 1

# STARTS
CLOSE_START = [(10, 10), (10, 11), (10, 12.3),
                        (10, 9.5), (10.3, 13), (11, 12)]
SPREAD_OUT = [(10, 10), (15, 60), (30, 80),
                        (60, 20), (80, 75), (45, 45)]

# Altitude centers
BASE_IRRELEVANT_ALTS = [[20, 20], [70, 70], [40, 80]]
TARGET_INTERESTING_ALTS = [[80, 40], [60, 10], [90, 20]]

# Sigmas
GOOD_FOR_SPARSE_SIGS = [20,20]
VALLEYS_SIGS = [16,4]

def main():
    env = Map(
        100, 100, 6, (50, 50),
        init_positions=CLOSE_START,
        targets=[(90, 10), (10, 90), (80, 50)],
        altitude_centers=TARGET_INTERESTING_ALTS,
        sigmas=VALLEYS_SIGS
    )

    env.set_targets_all_tanks(0)

    # -------- callback that kills a tank in the environment ----------
    def kill_tank(idx: int):
        if idx < env.get_nb_tanks():
            env.set_tank_destroyed_or_missing(idx)
            print(f"Tank {idx} destroyed")

    viz.init_live(
    click_kill_callback=kill_tank,
    hit_radius=2.0,
    hit_image_path="images/angry_king.jpg",  # ← tweak the path
    hit_image_zoom=0.05,
    hit_image_offset=(-6, -0.5),
)

    iters = 1000
    for i in range(iters):
        prev_pos = env.get_tank_pos_dict()
        next_positions = Update.update(env)
        next_pos_normed = devide_by_norm(next_positions, prev_pos)
        env.set_pos_all_tanks(next_pos_normed)
        env = reset_targets(env, target_id=0)
        viz.render(env.get_state_dict())
        print(f"Iteration {i}")

    print("Simulation finished – close the window to exit.")
    viz.hold()

def reset_targets(env, target_id=0):
    target_pos = env.get_targets_pos()[target_id]
    hq_pos = env.get_hq_pos()
    for tank in range(env.get_nb_tanks()):
        if env.get_tank_distance_to_position(tank, target_pos[0], target_pos[1]) < 1:
            env.set_tank_return_goal(tank)
        elif env.get_tank_distance_to_position(tank, hq_pos[0], hq_pos[1]) < 1:
            env.set_tank_target(tank, 0)
    return env

def devide_by_norm(next_positions, prev_pos):
    delta = {k: next_positions[k] - prev_pos[k] for k in prev_pos.keys()}
    norm = {k: l2_norm(delta[k]) for k in delta.keys()}
    new_pos_delta = {}
    for k in delta.keys():
        new_pos_delta[k] = MAX_STEP_SIZE * delta[k] / norm[k] if norm[k] >= 1 else delta[k]
    new_pos = {k: prev_pos[k] + new_pos_delta[k] for k in prev_pos.keys()}
    return new_pos

def l2_norm(vec):
    return math.sqrt(vec[0]**2 + vec[1]**2)

if __name__ == "__main__":
    main()
