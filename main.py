from simulation import Map, viz
from optimization import Update

def main():
    env = Map(
        100, 100, 6, (50, 50),
        init_positions=[(10, 10), (15, 60), (30, 80),
                        (60, 20), (80, 75), (45, 45)],
        targets=[(90, 10), (10, 90), (80, 50)],
        altitude_centers=[[20, 20], [70, 70], [40, 80]],
        sigmas=[20,20]
    )

    # -------- callback that kills a tank in the environment ----------
    def kill_tank(idx: int):
        if idx < env.get_nb_tanks():
            env.set_tank_destroyed_or_missing(idx)
            print(f"Tank {idx} destroyed")

    viz.init_live(
    click_kill_callback=kill_tank,
    hit_radius=2.0,
    hit_image_path="images/angry_king.jpg",  # ← tweak the path
    hit_image_zoom=0.4,
)

    iters = 100
    for i in range(iters):
        next_positions = Update.update(env)
        env.set_pos_all_tanks(next_positions)
        viz.render(env.get_state_dict())
        print(f"Iteration {i}")

    print("Simulation finished – close the window to exit.")
    viz.hold()

if __name__ == "__main__":
    main()
