from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys
import os
import json
import threading
import time
import numpy as np

# Add parent directory to path so we can import from the simulation module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation import Map
from optimization import Update

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

# Global variables to store simulation state
simulation_running = False
simulation_thread = None
simulation_state = {}
simulation_step = 0
simulation_params = {
    "map_x_size": 100,
    "map_y_size": 100,
    "nb_tanks": 10,
    "hq_pos": (50, 50),
    "targets": [(90, 10), (10, 90), (80, 50)],
    "altitude_centers": [[80, 40], [60, 10], [90, 20]],
    "sigmas": [16, 4],
    "max_step_size": 0.3
}

# Initialize environment with default parameters
def init_environment():
    global env
    env = Map(
        simulation_params["map_x_size"],
        simulation_params["map_y_size"],
        simulation_params["nb_tanks"],
        simulation_params["hq_pos"],
        init_positions=[(55,55), (55,53), (55,50), (55, 45), (50,45), (45, 45), (45, 50), (45, 55), (50, 55), (53,55)][:simulation_params["nb_tanks"]],
        targets=simulation_params["targets"],
        altitude_centers=simulation_params["altitude_centers"],
        sigmas=simulation_params["sigmas"]
    )
    
    # Set initial targets for tanks
    env.set_targets_all_tanks(0)
    for i in range(min(4, simulation_params["nb_tanks"])):
        env.set_tank_target(i, 2)
    
    return env

# Initialize environment
env = init_environment()

# Function to run simulation in a separate thread
def run_simulation():
    global simulation_running, simulation_state, simulation_step
    
    while simulation_running:
        # Store previous positions
        prev_pos = env.get_tank_pos_dict()
        
        # Calculate next positions
        next_positions = Update.update(env)
        
        # Normalize movement
        next_pos_normed = {}
        for k in prev_pos.keys():
            delta = next_positions[k] - prev_pos[k]
            norm = (delta[0]**2 + delta[1]**2)**0.5
            if norm >= 1:
                delta = simulation_params["max_step_size"] * delta / norm
            next_pos_normed[k] = prev_pos[k] + delta
        
        # Update tank positions
        env.set_pos_all_tanks(next_pos_normed)
        
        # Reset targets if needed
        target_pos = env.get_targets_pos()[0]
        target_pos2 = env.get_targets_pos()[2]
        hq_pos = env.get_hq_pos()
        
        for tank in range(env.get_nb_tanks()):
            if env.get_tank_distance_to_position(tank, target_pos[0], target_pos[1]) < 2:
                env.set_tank_return_goal(tank)
            if env.get_tank_distance_to_position(tank, target_pos2[0], target_pos2[1]) < 2:
                env.set_tank_return_goal(tank)
            elif env.get_tank_distance_to_position(tank, hq_pos[0], hq_pos[1]) < 2:
                if tank % 2 == 0:
                    env.set_tank_target(tank, 0)
                else:
                    env.set_tank_target(tank, 2)
        
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
    return jsonify(convert_numpy_to_python(simulation_params))

@app.route('/api/params', methods=['POST'])
def update_params():
    global simulation_params, env
    
    data = request.json
    
    # Update parameters
    for key, value in data.items():
        if key in simulation_params:
            simulation_params[key] = value
    
    # Reset environment with new parameters
    env = init_environment()
    
    return jsonify({"status": "success", "params": convert_numpy_to_python(simulation_params)})

if __name__ == '__main__':
    app.run(debug=True)
