from optimization import GradDescent
from simulation import Map

def main():
    iters = 100

    env = Map(100, 100, 5, (0,0),[(1,1), (2,2), (3,3), (4,4), (5,5)])
    for i in range(iters):
        next_positions = GradDescent.update(env)
        env.set_pos_all_tanks(next_positions)
        print(f"Iteration {i}")

if __name__ == "__main__":
    main()