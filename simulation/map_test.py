import unittest

from map import Map

import math

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

    def test_get_tank_dict(self):
        map = Map(10, 10, 5, (0,0), [(1,1.2), (2.4,2), (3,3), (4,4.1), (5,5)])

        out = {0:(1,1.2), 1:(2.4,2), 2:(3,3), 3:(4,4.1), 4:(5,5)}

        self.assertDictEqual(map.get_tank_pos_dict(), out)


    def test_delete_and_add_tank(self):
        map = Map(10, 10, 5, (0,0), [(1,1.2), (2.4,2), (3,3), (4,4.1), (5,5)])

        map.set_tank_destroyed_or_missing(2)
        out = {0:(1,1.2), 1:(2.4,2), 2:(4,4.1), 3:(5,5)}
        self.assertDictEqual(map.get_tank_pos_dict(), out)

        map.add_new_tank(3.3, 2.2)
        out = {0:(1,1.2), 1:(2.4,2), 2:(4,4.1), 3:(5,5), 4:(3.3, 2.2)}
        self.assertDictEqual(map.get_tank_pos_dict(), out)