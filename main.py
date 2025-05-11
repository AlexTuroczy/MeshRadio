from simulation import Map, viz
from optimization import Update
import math
import random
import threading
import time
import os
import sys
from pathlib import Path
import json
import numpy as np

# Flask web app imports
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Constants
MAX_STEP_SIZE = .3

# STARTS
CLOSE_START = [(10, 10), (10, 11), (10, 12.3),
                        (10, 9.5), (10.3, 13), (11, 12)]
SPREAD_OUT = [(10, 10), (15, 60), (30, 80),
                        (60, 20), (80, 75), (45, 45)]

# Altitude centers
BASE_IRRELEVANT_ALTS = [[20, 20], [70, 70], [40, 80]]
TARGET_INTERESTING_ALTS = [[45, 20], [30, 10], [40, 20]]

# Sigmas
GOOD_FOR_SPARSE_SIGS = [20,20]
VALLEYS_SIGS = [16,4]

SPAWN_AROUND_HQ = [(7,42), (7,43), (7,44), (7, 44), (5,43), (8, 46), (8, 47), (9, 47), (9, 44), (9,45)]

# Global variables for web app
app = Flask(__name__, 
            static_folder='web/static',
            template_folder='web/templates')
CORS(app)
simulation_running = False
simulation_thread = None
simulation_state = {}
simulation_step = 0
env = None

# Function to convert numpy arrays to lists for JSON serialization
def convert_numpy_to_python(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return [convert_numpy_to_python(i) for i in obj]
    else:
        return obj

def reset_targets(env):
    target_pos = env.get_targets_pos()[0]
    target_pos2 = env.get_targets_pos()[1]
    hq_pos = env.get_hq_pos()
    for tank in range(env.get_nb_tanks()):
        if env.get_tank_distance_to_position(tank, target_pos[0], target_pos[1]) < 2:
            env.set_tank_return_goal(tank)
        if env.get_tank_distance_to_position(tank, target_pos2[0], target_pos2[1]) < 2:
            env.set_tank_return_goal(tank)
        elif env.get_tank_distance_to_position(tank, hq_pos[0], hq_pos[1]) < 2:
            if random.randint(0,1) == 0:
                env.set_tank_target(tank, 0)
            else:
                env.set_tank_target(tank, 1)
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

def init_environment():
    global env
    
    # Load config if available
    config_path = Path('web/config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        map_x_size = config['simulation']['map_x_size']
        map_y_size = config['simulation']['map_y_size']
        nb_tanks = config['simulation']['nb_tanks']
        hq_pos = tuple(config['simulation']['hq_pos'])
        targets = [tuple(target) for target in config['simulation']['targets']][:2]
    else:
        # Use default values from main
        map_x_size = 50
        map_y_size = 50
        nb_tanks = 10
        hq_pos = (5, 45)
        targets = [(45, 10), (40, 45)]
    
    # Initialize environment using main.py structure
    env = Map(
        map_x_size, map_y_size, nb_tanks, hq_pos,
        init_positions=SPAWN_AROUND_HQ[:nb_tanks],
        targets=targets,
        altitude_centers=TARGET_INTERESTING_ALTS,
        sigmas=VALLEYS_SIGS
    )
    
    # Set initial targets for tanks
    env.set_targets_all_tanks(0)
    for i in range(min(4, nb_tanks)):
        env.set_tank_target(i, 1)
    
    return env

def run_simulation_web():
    global simulation_running, simulation_state, simulation_step, env
    
    while simulation_running:
        # Store previous positions
        prev_pos = env.get_tank_pos_dict()
        
        # Calculate next positions
        next_positions = Update.update(env)
        
        # Apply movement with normalization
        next_pos_normed = devide_by_norm(next_positions, prev_pos)
        
        # Update tank positions
        env.set_pos_all_tanks(next_pos_normed)
        
        # Reset targets
        env = reset_targets(env)
        
        # Update simulation state
        simulation_state = env.get_state_dict()
        simulation_step += 1
        
        # Sleep to control simulation speed
        time.sleep(0.1)

def main():
    global env
    
    # Initialize environment
    env = init_environment()

    # Check if we should run in web mode or console mode
    if '--web' in sys.argv:
        # Start Flask app in a separate thread
        flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False))
        flask_thread.daemon = True
        flask_thread.start()
        print("Web interface started at http://localhost:5000")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
    else:
        # Original main.py console mode
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
            env = reset_targets(env)
            viz.render(env.get_state_dict())
            print(f"Iteration {i}")

        print("Simulation finished – close the window to exit.")
        viz.hold()

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    # Convert numpy arrays to Python lists before serialization
    serializable_state = convert_numpy_to_python(simulation_state)
    
    return jsonify({
        "state": serializable_state,
        "step": simulation_step,
        "running": simulation_running
    })

@app.route('/api/start', methods=['POST'])
def start_simulation():
    global simulation_running, simulation_thread
    
    if not simulation_running:
        simulation_running = True
        simulation_thread = threading.Thread(target=run_simulation_web)
        simulation_thread.daemon = True
        simulation_thread.start()
        return jsonify({"status": "started"})
    
    return jsonify({"status": "already running"})

@app.route('/api/stop', methods=['POST'])
def stop_simulation():
    global simulation_running
    
    if simulation_running:
        simulation_running = False
        return jsonify({"status": "stopped"})
    
    return jsonify({"status": "not running"})

@app.route('/api/reset', methods=['POST'])
def reset_simulation():
    global simulation_running, simulation_step, env
    
    # Stop simulation if running
    simulation_running = False
    if simulation_thread and simulation_thread.is_alive():
        simulation_thread.join(1)
    
    # Reset simulation
    simulation_step = 0
    env = init_environment()
    
    return jsonify({"status": "reset"})

@app.route('/api/kill_tank', methods=['POST'])
def kill_tank_api():
    data = request.json
    tank_idx = data.get('tank_idx')
    
    if tank_idx is not None and tank_idx < env.get_nb_tanks():
        env.set_tank_destroyed_or_missing(tank_idx)
        return jsonify({"status": "success", "message": f"Tank {tank_idx} destroyed"})
    
    return jsonify({"status": "error", "message": "Invalid tank index"})

@app.route('/api/config', methods=['GET'])
def get_config():
    config_path = Path('web/config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        return jsonify(config)
    else:
        return jsonify({
            "simulation": {
                "map_x_size": 50,
                "map_y_size": 50,
                "nb_tanks": 10,
                "hq_pos": [5, 45],
                "targets": [[45, 10], [40, 45]],
                "altitude_centers": TARGET_INTERESTING_ALTS,
                "sigmas": VALLEYS_SIGS,
                "max_step_size": MAX_STEP_SIZE
            }
        })

@app.route('/api/params', methods=['GET'])
def get_params():
    params = {
        "map_x_size": env.get_map_size()[0],
        "map_y_size": env.get_map_size()[1],
        "nb_tanks": env.get_nb_tanks(),
        "hq_pos": env.get_hq_pos(),
        "targets": env.get_targets_pos(),
        "altitude_centers": TARGET_INTERESTING_ALTS,
        "sigmas": VALLEYS_SIGS,
        "max_step_size": MAX_STEP_SIZE
    }
    return jsonify(convert_numpy_to_python(params))

@app.route('/api/params', methods=['POST'])
def update_params():
    global env, MAX_STEP_SIZE, VALLEYS_SIGS
    
    data = request.json
    
    # Update configuration
    if 'max_step_size' in data:
        MAX_STEP_SIZE = data['max_step_size']
    
    if 'sigmas' in data and len(data['sigmas']) == 2:
        VALLEYS_SIGS = data['sigmas']
    
    # Reset environment with new parameters
    env = init_environment()
    
    return jsonify({"status": "success"})

if __name__ == "__main__":
    main()
