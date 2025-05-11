# Mesh Radio Simulation Web Interface

A modern defense-tech style dashboard for visualizing the Mesh Radio tank simulation.

## Features

- Real-time visualization of tank movements and mesh network connections
- Interactive controls to start, pause, and reset the simulation
- Parameter adjustment panel for customizing the simulation
- Ability to destroy tanks to test network robustness
- Minimalist, modern defense-tech aesthetic

## Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

## Installation

1. Navigate to the web directory:
   ```
   cd web
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the Flask server:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Dashboard Controls

- **START**: Begin the simulation
- **PAUSE**: Pause the simulation
- **RESET**: Reset the simulation to its initial state

### Parameter Adjustments

The side panel allows you to adjust various simulation parameters:

- **Number of Tanks**: Adjust the number of tanks in the simulation
- **Max Step Size**: Control the maximum movement distance per step
- **Sigma X/Y**: Adjust the terrain generation parameters

Click "APPLY CHANGES" to update the simulation with the new parameters.

### Actions

- **DESTROY RANDOM TANK**: Randomly select and destroy a tank to test network robustness

### Visualization Elements

- **Blue Circles**: Tanks
- **Yellow Star**: Headquarters (HQ)
- **Red X**: Target locations
- **White Dashed Lines**: Radio connections between tanks
- **Background Colors**: Terrain altitude (darker = lower, lighter = higher)

## Architecture

The application consists of:

1. **Backend** (Flask server):
   - Runs the simulation
   - Exposes API endpoints for controlling the simulation
   - Provides simulation state data

2. **Frontend** (HTML/CSS/JavaScript):
   - Renders the simulation using Canvas
   - Provides user interface for controlling the simulation
   - Fetches and displays real-time simulation data
