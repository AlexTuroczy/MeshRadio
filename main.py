from optimization import Update
from simulation import Map

def main():
    iters = 100

    env = Map(100, 100, 5, (0,0),[(1,20), (20,22), (30,40), (12,99), (50,78)])
    for i in range(iters):
        next_positions = Update.update(env)
        print(next_positions)
        env.set_pos_all_tanks(next_positions)
        print(f"Iteration {i}")

if __name__ == "__main__":
    main()