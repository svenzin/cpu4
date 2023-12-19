import unittest

from simulator.signals import Group, Value, make_groups


class TestValue(unittest.TestCase):
    def test_single(self):
        self.assertRaises(ValueError, lambda: Value(0, 0))
        self.assertRaises(ValueError, lambda: Value(2, 1))

    def test_combination(self):
        self.assertRaises(ValueError, lambda: Value(0, 1) | Value(0, 3))
        x = Value(0b0001, 0b0001) | Value(0b0100, 0b1100)
        
        self.assertEqual(0b0101, x.value)
        self.assertEqual(0b1101, x.mask)


class TestGroup(unittest.TestCase):
    def test_single(self):
        self.assertRaises(ValueError, lambda: Group(0, 0))
        self.assertRaises(ValueError, lambda: Group(1, -1))
        
        g = Group(1, 0)
        self.assertEqual(0b1, g.mask)
        self.assertSequenceEqual((0, 1), g.all())
        
        g = Group(2, 3)
        self.assertEqual(0b11000, g.mask)
        self.assertSequenceEqual((0b00000, 0b01000, 0b10000, 0b11000),
                                 g.all())


class TestSignals(unittest.TestCase):
    def test_make_groups(self):
        self.assertSequenceEqual([], make_groups())

        self.assertRaises(ValueError, lambda: make_groups(0))

        g1, g2, g3 = make_groups(1, 2, 3)
        self.assertEqual(0b000001, g1.mask)
        self.assertEqual(0b000110, g2.mask)
        self.assertEqual(0b111000, g3.mask)
