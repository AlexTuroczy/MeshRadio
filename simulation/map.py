import numpy as np

from typing import List, Tuple, Optional

from constants import DEFAULT_RADIO_RADIUS
from utils import dist

from random import randint
import math

class MapObject:

    def __init__(self, x_pos: int, y_pos: int):
        self.x_pos = x_pos
        self.y_pos = y_pos

    def get_pos(self):
        return np.array([self.x_pos, self.y_pos])
    
    def set_pos(self, x: float, y: float):
        self.x_pos = x
        self.y_pos = y

class MiniTank(MapObject):

    def __init__(self, x_pos: float, y_pos: float, radar_radius: int):
        super().__init__( x_pos, y_pos)
        self.radar_radius = radar_radius

    def get_radius(self):
        return self.radar_radius
    

class MissingTank(MapObject):
    def __init__(self, x_pos: float, y_pos: float, radar_radius: int):
        super().__init__(x_pos, y_pos)
    

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
):
        self.x_size = map_x_size
        self.y_size = map_y_size
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

    def get_nb_tanks(self):
        return self.nb_nodes
    
    def get_tank_pos_dict(self):
        tanks = {}
        for idx, node in enumerate(self.nodes):
            tanks[idx] = node.get_pos()

        return tanks

    def set_tank_destroyed_or_missing(self, idx: int):
        if idx < 0 or idx >= self.nb_nodes:
            raise Exception("Index out of range.")
        self.nodes = [node for i, node in enumerate(self.nodes) if not i == idx]
        self.nb_nodes -= 1

    def add_new_tank(self, x_pos: float, y_pos: float, radius: Optional[float] = None):
        if radius is None:
            radius = DEFAULT_RADIO_RADIUS
        self.nodes.append(MiniTank(x_pos, y_pos, radar_radius=radius))
        self.nb_nodes += 1
    
