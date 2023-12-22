import unittest

from cpu4.simulator import simulator as s
from cpu4.simulator.simulator import LO, HI, Tr, Tf


class TestClock(unittest.TestCase):
    def test_clock(self):
        s.system.clear()
        c = s.Clock(s.hz(1), s.ms(100), s.ms(200))

        self.assertEqual(0, s.system.timestamp.t)
        self.assertEqual(LO, c.clock.value)

        s.system.step()
        self.assertEqual(0, s.system.timestamp.t)
        self.assertEqual(Tr, c.clock.value)

        s.system.step()
        self.assertEqual(0.1, s.system.timestamp.t)
        self.assertEqual(HI, c.clock.value)

        s.system.step()
        self.assertEqual(1, s.system.timestamp.t)
        self.assertEqual(Tf, c.clock.value)

        s.system.step()
        self.assertEqual(1.2, s.system.timestamp.t)
        self.assertEqual(LO, c.clock.value)

        s.system.step()
        self.assertEqual(2, s.system.timestamp.t)
        self.assertEqual(Tr, c.clock.value)
