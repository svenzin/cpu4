import unittest

from cpu4.simulator import simulator as s
from cpu4.simulator.simulator import LO, HI


class TestClock(unittest.TestCase):
    def test_simple(self):
        s.system.clear()

        c = s.Clock(s.hz(1))
        c.update(s.s(0))
        self.assertEqual(HI, c.clock.value)
        
        c.update(s.s(1))
        self.assertEqual(LO, c.clock.value)
        
        c.update(s.s(1))
        self.assertEqual(HI, c.clock.value)
        
        c.update(s.s(0.5))
        self.assertEqual(HI, c.clock.value)
        c.update(s.s(0.5))
        self.assertEqual(LO, c.clock.value)
    
    def test_transition(self):
        s.system.clear()

        c = s.Clock(s.hz(1), s.ms(100), s.ms(200))
        c.update(s.s(0))
        self.assertEqual(TLH, c.clock.value)
        
        c.update(s.ms(100))
        self.assertEqual(HI, c.clock.value)
        
        c.update(s.ms(900))
        self.assertEqual(THL, c.clock.value)
        
        c.update(s.ms(200))
        self.assertEqual(LO, c.clock.value)
    
    def test_steps(self):
        s.system.clear()
        c = s.Clock(s.hz(1), s.ms(100), s.ms(200))

        s.system.step()
        self.assertEqual(s.s(0).d, s.system.timestamp.t)
        self.assertEqual(TLH, c.clock.value)
        
        s.system.step()
        self.assertEqual(s.s(0.1).d, s.system.timestamp.t)
        self.assertEqual(HI, c.clock.value)
        
        s.system.step()
        self.assertEqual(s.s(1).d, s.system.timestamp.t)
        self.assertEqual(THL, c.clock.value)
        
        s.system.step()
        self.assertEqual(s.s(1.2).d, s.system.timestamp.t)
        self.assertEqual(LO, c.clock.value)
