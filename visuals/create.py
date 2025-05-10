import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.image as mpimg

# Load terrain data
terrain_df = pd.read_csv('terrain.csv')
terrain_matrix = terrain_df.pivot(index='y', columns='x', values='altitude').values

# Load positions data
positions_df = pd.read_csv('positions.csv')
times = sorted(positions_df['time'].unique())

# Load tank images
tank_connected_img = mpimg.imread('tankconnected.png')
tank_disconnected_img = mpimg.imread('tankdisconnected.png')

# Setup plot
fig, ax = plt.subplots(figsize=(10, 8))

# Terrain plot extent
extent = [terrain_df['x'].min(), terrain_df['x'].max(), terrain_df['y'].min(), terrain_df['y'].max()]

# Initial terrain plot with a conventional colormap (e.g., 'terrain')
ax.imshow(terrain_matrix, cmap='terrain', origin='lower', extent=extent)

def animate(t):
    ax.clear()
    ax.imshow(terrain_matrix, cmap='terrain', origin='lower', extent=extent)

    current_positions = positions_df[positions_df['time'] == t]

    for _, row in current_positions.iterrows():
        img = tank_connected_img if row['connected'] else tank_disconnected_img
        img_extent = [row['x'] - 100, row['x'] + 100, row['y'] - 100, row['y'] + 100]
        ax.imshow(img, extent=img_extent, zorder=2)

    ax.set_title(f'Tank Positions at Time: {t}', fontsize=16)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.axis('off')

ani = animation.FuncAnimation(fig, animate, frames=times, interval=200, repeat=False)

# Save as MP4 video
ani.save('UGV_Scenario_Animation.mp4', writer='ffmpeg', fps=5)

plt.close()

print("Animation video 'UGV_Scenario_Animation.mp4' created successfully.")
