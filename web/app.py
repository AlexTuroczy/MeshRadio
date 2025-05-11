from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys
import os
import json
import threading
import time
import numpy as np
import random
import math
from pathlib import Path

# Add parent directory to path so we can import from the simulation module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation import Map
from optimization import Update

# Import constants from main.py
MAX_STEP_SIZE = 0.3

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

app = Flask(__name__)
CORS(app)

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

# Load shared configuration
config_path = Path(__file__).parent / 'config.json'
with open(config_path, 'r') as f:
    config = json.load(f)

# Global variables to store simulation state
simulation_running = False
simulation_thread = None
simulation_state = {}
simulation_step = 0

# Functions from main.py
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

# Initialize environment with parameters from main.py
def init_environment():
    global env
    
    # Get parameters from config
    map_x_size = config['simulation']['map_x_size']
    map_y_size = config['simulation']['map_y_size']
    nb_tanks = config['simulation']['nb_tanks']
    hq_pos = tuple(config['simulation']['hq_pos'])
    targets = [tuple(target) for target in config['simulation']['targets']]
    altitude_centers = config['simulation']['altitude_centers']
    sigmas = config['simulation']['sigmas']
    
    # Initialize environment using main.py structure
    env = Map(
        map_x_size, map_y_size, nb_tanks, hq_pos,
        init_positions=SPAWN_AROUND_HQ[:nb_tanks],
        targets=targets[:2],  # Use only first two targets
        altitude_centers=TARGET_INTERESTING_ALTS,
        sigmas=VALLEYS_SIGS
    )
    
    # Set initial targets for tanks as in main.py
    env.set_targets_all_tanks(0)
    for i in range(min(4, nb_tanks)):
        env.set_tank_target(i, 1)
    
    return env

# Initialize environment
env = init_environment()

# Function to run simulation in a separate thread - based on main.py loop
def run_simulation():
    global simulation_running, simulation_state, simulation_step, env
    
    while simulation_running:
        # Store previous positions
        prev_pos = env.get_tank_pos_dict()
        
        # Calculate next positions
        next_positions = Update.update(env)
        
        # Apply movement with normalization as in main.py
        next_pos_normed = devide_by_norm(next_positions, prev_pos)
        
        # Update tank positions
        env.set_pos_all_tanks(next_pos_normed)
        
        # Reset targets using the function from main.py
        env = reset_targets(env)
        
        # Update simulation state
        simulation_state = env.get_state_dict()
        simulation_step += 1
        
        # Sleep to control simulation speed
        time.sleep(0.1)

# Routes
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
        simulation_thread = threading.Thread(target=run_simulation)
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
def kill_tank():
    data = request.json
    tank_idx = data.get('tank_idx')
    
    if tank_idx is not None and tank_idx < env.get_nb_tanks():
        env.set_tank_destroyed_or_missing(tank_idx)
        return jsonify({"status": "success", "message": f"Tank {tank_idx} destroyed"})
    
    return jsonify({"status": "error", "message": "Invalid tank index"})

@app.route('/api/params', methods=['GET'])
def get_params():
    params = {
        "map_x_size": config['simulation']['map_x_size'],
        "map_y_size": config['simulation']['map_y_size'],
        "nb_tanks": config['simulation']['nb_tanks'],
        "hq_pos": config['simulation']['hq_pos'],
        "targets": config['simulation']['targets'][:2],
        "altitude_centers": TARGET_INTERESTING_ALTS,
        "sigmas": VALLEYS_SIGS,
        "max_step_size": MAX_STEP_SIZE
    }
    return jsonify(convert_numpy_to_python(params))

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(config)

@app.route('/api/params', methods=['POST'])
def update_params():
    global env
    
    data = request.json
    
    # Update configuration
    if 'nb_tanks' in data:
        config['simulation']['nb_tanks'] = data['nb_tanks']
    
    if 'max_step_size' in data:
        global MAX_STEP_SIZE
        MAX_STEP_SIZE = data['max_step_size']
    
    if 'sigmas' in data and len(data['sigmas']) == 2:
        global VALLEYS_SIGS
        VALLEYS_SIGS = data['sigmas']
    
    # Reset environment with new parameters
    env = init_environment()
    
    return jsonify({"status": "success", "params": convert_numpy_to_python({
        "nb_tanks": config['simulation']['nb_tanks'],
        "max_step_size": MAX_STEP_SIZE,
        "sigmas": VALLEYS_SIGS
    })})

if __name__ == '__main__':
    app.run(debug=True)
