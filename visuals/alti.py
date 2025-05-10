import pandas as pd
import numpy as np

# Define grid size
size_x, size_y = 4000, 4000

# Generate grid coordinates
x_coords = np.arange(size_x)
y_coords = np.arange(size_y)

# Create mesh grid
X, Y = np.meshgrid(x_coords, y_coords)

# Define altitude to progressively increase (example: altitude = x + y)
altitude = X + Y

# Flatten the arrays for CSV output
data = {
    'x': X.flatten(),
    'y': Y.flatten(),
    'altitude': altitude.flatten()
}

# Create DataFrame and export to CSV
terrain_df = pd.DataFrame(data)
terrain_df.to_csv('terrain.csv', index=False)

print("terrain.csv has been created successfully.")