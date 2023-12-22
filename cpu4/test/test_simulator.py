import unittest

from simulator import simulator as s
from simulator.simulator import LO, HI, TLO, THI


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
        self.assertEqual(TLO, c.clock.value)
        
        c.update(s.ms(100))
        self.assertEqual(HI, c.clock.value)
        
        c.update(s.ms(900))
        self.assertEqual(THI, c.clock.value)
        
        c.update(s.ms(200))
        self.assertEqual(LO, c.clock.value)
    
    def test_steps(self):
        s.system.clear()
        c = s.Clock(s.hz(1), s.ms(100), s.ms(200))

        s.step()
        self.assertEqual(0, s.timestamp.t)
        self.assertEqual(TLO, c.clock.value)
        
        s.step()
        self.assertEqual(0.1, s.timestamp.t)
        self.assertEqual(HI, c.clock.value)
        
        s.step()
        self.assertEqual(1, s.timestamp.t)
        self.assertEqual(THI, c.clock.value)
        
        s.step()
        self.assertEqual(1.2, s.timestamp.t)
        self.assertEqual(LO, c.clock.value)
