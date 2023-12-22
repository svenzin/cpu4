import unittest

from cpu4.simulator import simulator as s
from cpu4.simulator.simulator import LO, HI, TLO, THI, UNDEFINED


class TestClock(unittest.TestCase):
    def test_clock(self):
        s.system.clear()
        c = s.Clock(s.hz(1), s.ms(100), s.ms(200))

        self.assertEqual(0, s.system.timestamp.t)
        self.assertEqual(LO, c.clock.value)

        s.system.step()
        self.assertEqual(0, s.system.timestamp.t)
        self.assertEqual(TLO, c.clock.value)

        s.system.step()
        self.assertEqual(0.1, s.system.timestamp.t)
        self.assertEqual(HI, c.clock.value)

        s.system.step()
        self.assertEqual(1, s.system.timestamp.t)
        self.assertEqual(THI, c.clock.value)

        s.system.step()
        self.assertEqual(1.2, s.system.timestamp.t)
        self.assertEqual(LO, c.clock.value)

        s.system.step()
        self.assertEqual(2, s.system.timestamp.t)
        self.assertEqual(TLO, c.clock.value)


class TestBuffer(unittest.TestCase):
    def test_simple(self):
        s.system.clear()
        i = s.State()
        i.set(LO, True)
        b = s.Buffer(i, s.ms(100), s.ms(10))

        self.assertEqual(UNDEFINED, b.output.value)
        self.assertEqual(s.Duration(0.1), b.next_update())
        
        b.update(s.s(0.1))
        self.assertEqual(TLO, b.output.value)
        self.assertEqual(s.Duration(0.01), b.next_update())
        
        b.update(s.s(0.01))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, b.next_update())

        i.set(HI, True)
        self.assertEqual(LO, b.output.value)
        self.assertEqual(s.Duration(0.1), b.next_update())

        b.update(s.s(0.1))
        self.assertEqual(THI, b.output.value)
        self.assertEqual(s.Duration(0.01), b.next_update())
        
        b.update(s.s(0.01))
        self.assertEqual(HI, b.output.value)
        self.assertEqual(None, b.next_update())

    def test_multiple_changes(self):
        s.system.clear()
        i = s.State()
        i.set(LO, True)

        b = s.Buffer(i, s.ms(100), s.ms(0))
        b.next_update()
        b.update(s.s(0.1))
        b.next_update()
        b.update(s.s(0))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, b.next_update())

        i.set(HI, True)
        self.assertEqual(s.s(0.1), b.next_update())
        b.update(s.s(0.05))
        i.set(LO, True)
        self.assertRaises(AssertionError, lambda: b.next_update())
