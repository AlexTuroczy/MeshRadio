import unittest

from map import Map

import math
import scipy
import numpy as np

from constants import DEFAULT_RADIO_RADIUS


class MapTestCase(unittest.TestCase):

    def test_create(self):
        map = Map(10, 10, 5, (0,0))
        
    def test_create_positions(self):
        map = Map(10, 10, 5, (0,0), [(1,1), (2,2), (3,3), (4,4), (5,5)])

        for i in range(5):
            self.assertTupleEqual(map.get_tank_pos(i), (i+1,i+1))
            self.assertEqual(map.get_tank_radius(i), DEFAULT_RADIO_RADIUS)

    def test_set_position(self):
        map = Map(10, 10, 5, (0,0), [(1,1), (2,2), (3,3), (4,4), (5,5)])

        map.set_tank_pos(3, 9, 5)

        self.assertTupleEqual(map.get_tank_pos(3), (9,5))

    def test_get_distance(self):
        map = Map(10, 10, 5, (0,0), [(1,1), (2,2), (3,3), (4,4), (5,5)])

        self.assertAlmostEqual(map.get_tank_distance(0, 1), math.sqrt(2))
        

    def test_get_tank_altitude(self):

        map = Map(10, 10, 5, (0,0), [(1,1.2), (2.4,2), (3,3), (4,4.1), (5,5)])

        for i in range(5):
            map.set_altitude(i+1, i+1, i)

        for i in range(5):
            self.assertAlmostEqual(map.get_tank_altitude(i), i)

    def test_get_tank_altitude_with_gaussian(self):
        tank_positions = [(1,1.2), (2.4,2), (3,3), (4,4.1), (5,5)]
        center = [(0,0)]
        map = Map(10, 10, 5, (0,0), tank_positions, altitude_centers=center)

        rv = scipy.stats.multivariate_normal(mean=center[0], cov=map.sigma)
        for i in range(5):
            pos = self._round(tank_positions[i])
            self.assertAlmostEqual(map.get_tank_altitude(i), rv.pdf(np.array(pos)) * map.scale)

        center = [(0, 0), (2,2)]
        map = Map(10, 10, 5, (0, 0), tank_positions, altitude_centers=center)

        rv1 = scipy.stats.multivariate_normal(mean=center[0], cov=map.sigma)
        rv2 = scipy.stats.multivariate_normal(mean=center[1], cov=map.sigma)
        for i in range(5):
            pos = self._round(tank_positions[i])
            self.assertAlmostEqual(map.get_tank_altitude(i), (rv1.pdf(np.array((pos))) + rv2.pdf(np.array(pos))) * map.scale)

    def _round(self, tup):
        return (round(tup[0]), round(tup[1]))