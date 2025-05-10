import pandas as pd
import numpy as np

# Define parameters
time_steps = 100
objects = ['tank1', 'tank2']

# Create empty list to hold data
data = []

np.random.seed(42)  # for reproducibility

# Generate random positions and connectivity states
for t in range(time_steps):
    for obj in objects:
        x = np.random.uniform(0, 4000)
        y = np.random.uniform(0, 4000)
        connected = np.random.choice([True, False])

        data.append({
            'time': t,
            'object_id': obj,
            'x': x,
            'y': y,
            'connected': connected
        })

# Create DataFrame and save to CSV
positions_df = pd.DataFrame(data)
positions_df.to_csv('positions.csv', index=False)

print("positions.csv has been created successfully.")
