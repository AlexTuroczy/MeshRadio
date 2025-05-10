import numpy as np

from typing import List, Tuple, Optional

from constants import DEFAULT_RADIO_RADIUS
from utils import dist

from random import randint
import math
import scipy

class MapObject:

    def __init__(self, x_pos: int, y_pos: int):
        self.x_pos = x_pos
        self.y_pos = y_pos

    def get_pos(self):
        return self.x_pos, self.y_pos
    
    def set_pos(self, x: float, y: float):
        self.x_pos = x
        self.y_pos = y

class MiniTank(MapObject):

    def __init__(self, x_pos: float, y_pos: float, radar_radius: int):
        super().__init__( x_pos, y_pos)
        self.radar_radius = radar_radius

    def get_radius(self):
        return self.radar_radius


class Target(MapObject):

    def __init__(self, x_pos: float, y_pos: float):
        super().__init__(x_pos, y_pos)


class Map:

    def __init__(self,
            map_x_size: int,
            map_y_size: int,
            nb_nodes: int,
            hq_pos: Tuple[float],
            init_positions: Optional[List[Tuple[float]]] = None,
            targets: Optional[List[Tuple[float]]] = None,
            altitude_centers: Optional[List[List[float]]] = None
):
        sigma_x = 1
        sigma_y = 1
        self.sigma = np.array([[sigma_x ** 2, 0], [0, sigma_y ** 2]])
        self.scale = 100
        self.x_size = map_x_size
        self.y_size = map_y_size
        if altitude_centers:
            self.altitude = self._generate_altitudes(altitude_centers)
        else:
            self.altitude = np.zeros((map_x_size, map_y_size))

        self.nb_nodes = nb_nodes

        if init_positions:
            assert len(init_positions) == nb_nodes
            self.nodes = [MiniTank(x, y, DEFAULT_RADIO_RADIUS) for x,y in init_positions]
        else:
            self.nodes = []
            for _ in range(nb_nodes):
                x = randint(0, self.x_size)
                y = randint(0, self.y_size)
                self.nodes.append(MiniTank(x, y, DEFAULT_RADIO_RADIUS))
        
        self.hq = MapObject(hq_pos[0], hq_pos[1])

        targets = []
        if targets:
            self.targets = [Target(x,y) for x,y in targets]

    def _generate_altitudes(self, altitude_centers):
        alt_matrix = np.zeros((self.x_size, self.y_size))
        x_values, y_values = np.meshgrid(np.linspace(0, self.x_size, self.x_size), np.linspace(0, self.y_size, self.y_size))

        for x in range(self.x_size):
            for y in range(self.y_size):
                alt_matrix[x, y] = self._evaluate_altitude(x, y, altitude_centers)
        return alt_matrix

    def _evaluate_altitude(self, x, y, altitude_centers):
        sum = 0
        for center in altitude_centers:
            rv = scipy.stats.multivariate_normal(mean=center, cov=self.sigma)
            altitude = rv.pdf(np.array([x, y])) * self.scale
            sum += altitude
        return sum

    def get_tank_pos(self, idx: int):
        if idx < 0 or idx >= self.nb_nodes:
            raise Exception("Index out of range.")
        return self.nodes[idx].get_pos()
    
    def set_tank_pos(self, idx: int, x_pos, y_pos):
        if idx < 0 or idx >= self.nb_nodes:
            raise Exception("Index out of range.")
        if x_pos < 0 or x_pos >= self.x_size:
            raise Exception("Map position out of range")
        if y_pos < 0 or y_pos >= self.y_size:
            raise Exception("Map position out of range")
        self.nodes[idx].set_pos(x_pos, y_pos)

    def get_tank_radius(self, idx: int):
        if idx < 0 or idx >= self.nb_nodes:
            raise Exception("Index out of range.")
        # TODO: possible larger radius for higher altitude?
        return self.nodes[idx].get_radius()
    
    def get_tank_altitude(self, idx: int):
        if idx < 0 or idx >= self.nb_nodes:
            raise Exception("Index out of range.")
        x,y = self.get_tank_pos(idx)
        return self.get_altitude(x,y)

    def get_altitude(self, x: float, y: float):
        if x < 0 or x > self.x_size - 1:
            raise Exception("Map position out of range")
        if y < 0 or y > self.y_size - 1:
            raise Exception("Map position out of range")
        x_rounded = round(x)
        y_rounded = round(y)
        return self.altitude[x_rounded,y_rounded]
    
    def set_altitude(self, x: float, y: float, altitude: float):
        if x < 0 or x > self.x_size - 1:
            raise Exception("Map position out of range")
        if y < 0 or y > self.y_size - 1:
            raise Exception("Map position out of range")
        x_rounded = round(x)
        y_rounded = round(y)
        self.altitude[x_rounded,y_rounded] = altitude
    
    def get_hq_pos(self):
        return self.hq.get_pos()
    
    def set_hq_pos(self, x: int, y: int):
        if x < 0 or x >= self.x_size:
            raise Exception("Map position out of range")
        if y < 0 or y >= self.y_size:
            raise Exception("Map position out of range")
        self.hq.set_pos(x, y)

    def get_tank_distance(self, idx1: int, idx2: int):
        """ Distance between 2 tanks """
        if idx1 < 0 or idx1 >= self.nb_nodes:
            raise Exception("Index out of range.")
        if idx2 < 0 or idx2 >= self.nb_nodes:
            raise Exception("Index out of range.")
        pos1 = self.get_tank_pos(idx1)
        pos2 = self.get_tank_pos(idx2)
        return dist(pos1, pos2)
    
    def tank_can_radio_location(self, idx: int, x_pos: float, y_pos: float):
        if idx < 0 or idx >= self.nb_nodes:
            raise Exception("Index out of range.")

        tank_pos = self.get_tank_pos(idx)
        return dist(tank_pos, (x_pos, y_pos)) < self.get_tank_radius(idx)
    
    def get_tank_distance_from_hq(self, idx: int):
        if idx < 0 or idx >= self.nb_nodes:
            raise Exception("Index out of range.")
        pos1 = self.get_tank_pos(idx)
        pos2 = self.get_hq_pos()
        return dist(pos1, pos2)
    
    def get_targets_pos(self):
        """ Get all target positions """
        positions = []
        for target in self.targets:
            positions.append(target.get_pos())
        return positions

    def get_tank_distance_to_position(self, idx: int, x: float, y: float):
        if idx < 0 or idx >= self.nb_nodes:
            raise Exception("Index out of range.")
        if x < 0 or x >= self.x_size:
            raise Exception("Map position out of range")
        if y < 0 or y >= self.y_size:
            raise Exception("Map position out of range")
        pos = self.get_tank_pos(idx)
        return dist(pos, (x,y))

    
