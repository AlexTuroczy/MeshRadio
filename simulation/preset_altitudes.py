import numpy as np

from math import sin, cos, pi

def sine_map(x_size: int, y_size: int, freq_x: float, freq_y: float):
    altitude = np.ndarray((x_size, y_size))
    for x in range(x_size):
        for y in range(y_size):
            altitude[x,y] = sin(2*pi*(x * freq_x / x_size)) * sin(2*pi*(y * freq_y / y_size))

    return altitude

def one_valley(x_size: int, y_size:int):
    altitude = np.ndarray((x_size, y_size))
    for x in range(x_size):
        for y in range(y_size):
            altitude[x,y] = sin(2*pi*(x * 1.5 / x_size))

    return altitude