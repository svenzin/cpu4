import unittest

from cpu4.simulator import simulator as s
from cpu4.simulator.simulator import LO, HI, TLM, TMH, THM, TML, UNDEFINED, Z, UNKNOWN, CONFLICT


class TestClock(unittest.TestCase):
    def test_init_phase_0(self):
        s.system.clear()
        c = s.Clock(s.hz(1), tt=s.ms(200), phase=0)
        self.assertEqual(HI, c.clock.value)
        self.assertEqual(s.s(0.5), c.next_update())
        c.update(s.s(0.5))
        self.assertEqual(LO, c.clock.value)

    def test_init_phase_180(self):
        s.system.clear()
        c = s.Clock(s.hz(1), tt=s.ms(200), phase=180)
        self.assertEqual(LO, c.clock.value)
        self.assertEqual(s.s(0.5), c.next_update())
        c.update(s.s(0.5))
        self.assertEqual(HI, c.clock.value)

    def test_clock(self):
        s.system.clear()
        c = s.Clock(s.hz(1), tt=s.ms(200), duty=0.4, phase=270)

        # step-by-step
        # freq 1hz   -> (HI>LO @ -0.5s) LO>HI @ 0s, HI>LO @ 0.5s
        # duty 40%   -> (HI>LO @ -0.6s) LO>HI @ 0s, HI>LO @ 0.4s
        # phase 270° -> HI>LO @ 0.15s, LO>HI @ 0.75s, HI>LO @ 1.15s
        def step(t, cv):
            s.system.step()
            self.assertEqual(s.s(t).d, s.system.timestamp.t)
            self.assertEqual(cv, c.clock.value)

        self.assertEqual(s.s(0).d, s.system.timestamp.t)
        self.assertEqual(HI, c.clock.value)

        step(0.15, LO)
        step(0.75, HI)
        step(1.15, LO)


class TestBuffer(unittest.TestCase):
    def test_init_lo(self):
        s.system.clear()
        i = s.State()
        
        b = s.Buffer(i, s.s(1), s.ms(100))
        self.assertEqual(UNDEFINED, b.output.value)
        self.assertEqual(None, b.next_update())
        
        # Initial state
        i.set(LO, True)
        self.assertEqual(s.s(1), b.next_update())
        
        b.update(s.s(1))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, b.next_update())

    def test_init_hi(self):
        s.system.clear()
        i = s.State()
        
        b = s.Buffer(i, s.s(1), s.ms(100))
        self.assertEqual(UNDEFINED, b.output.value)
        self.assertEqual(None, b.next_update())
        
        # Initial state
        i.set(HI, True)
        self.assertEqual(s.s(1), b.next_update())
        
        b.update(s.s(1))
        self.assertEqual(HI, b.output.value)
        self.assertEqual(None, b.next_update())

    def init(self, level):
        s.system.clear()
        i = s.State()
        b = s.Buffer(i, s.s(1), s.ms(100))
        i.set(level, True)
        b.next_update()
        b.update(s.s(0))
        return i, b

    def test_simple(self):
        i, b = self.init(LO)
        i.set(HI, True)
        self.assertEqual(s.s(1), b.next_update())
        b.update(s.s(1))
        self.assertEqual(HI, b.output.value)

        i, b = self.init(HI)
        i.set(LO, True)
        self.assertEqual(s.s(1), b.next_update())
        b.update(s.s(1))
        self.assertEqual(LO, b.output.value)

    def test_multiple_changes(self):
        i, b = self.init(LO)

        i.set(HI, True)                                 # t=0, input LO>HI
        self.assertEqual(s.s(1), b.next_update())
        b.update(s.s(0.5))                              # t=0.5, input HI>LO
        i.set(LO, True)
        self.assertEqual(s.s(0.5), b.next_update())
        b.update(s.s(0.5))                             # t=1, output LO>HI
        self.assertEqual(HI, b.output.value)
        self.assertEqual(s.s(0.50), b.next_update())
        b.update(s.s(0.50))                             # t=1.5, output HI>LO
        self.assertEqual(LO, b.output.value)

class Test3State(unittest.TestCase):
    def test_simple(self):
        s.system.clear()
        
        i = s.State()
        i.set(LO, True)
        
        en = s.State()
        en.set(HI, True)
        
        # b = s.Enabler(i, en, s.ms(100), s.ms(200), s.s(0), s.s(0), s.STATE_Z)
        b = s.EnablerOperator(i, en, s.s(1), s.ms(100), s.STATE_Z)
        self.assertEqual(UNDEFINED, b.output.value)
        # self.assertEqual(s.s(0.1), b.next_update())
        # b.update(s.s(0.1))
        self.assertEqual(s.s(1), b.next_update())
        b.update(s.s(1))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, b.next_update())

        en.set(LO, True)
        # self.assertEqual(s.ms(200), b.next_update())
        # b.update(s.ms(200))
        self.assertEqual(s.s(1), b.next_update())
        b.update(s.s(1))
        self.assertEqual(Z, b.output.value)
        self.assertEqual(None, b.next_update())

        en.set(HI, True)
        # self.assertEqual(s.ms(100), b.next_update())
        # b.update(s.ms(100))
        self.assertEqual(s.s(1), b.next_update())
        b.update(s.s(1))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, b.next_update())

    def test_multiple_changes(self):
        s.system.clear()
        
        i = s.State()
        i.set(LO, True)
        
        en = s.State()
        en.set(HI, True)
        
        b = s.Enabler(i, en, s.ms(100), s.ms(200), s.s(0), s.s(0), s.STATE_Z)
        self.assertEqual(s.s(0.1), b.next_update()) # initialization
        b.update(s.s(0.1))

        # disable then re-enable before fully disabled
        en.set(LO, True)
        self.assertEqual(s.ms(200), b.next_update())
        b.update(s.ms(150))
        en.set(HI, True)
        self.assertEqual(s.ms(50), b.next_update())
        b.update(s.ms(50))
        self.assertEqual(Z, b.output.value)
        self.assertEqual(s.ms(50), b.next_update())
        b.update(s.ms(50))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, b.next_update())

        # disable then re-enable before disabling started
        en.set(LO, True)
        self.assertEqual(s.ms(200), b.next_update())
        b.update(s.ms(50))
        en.set(HI, True)
        self.assertEqual(s.ms(100), b.next_update())
        b.update(s.ms(100))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, b.next_update())

class TestAnd(unittest.TestCase):
    def test_simple(self):
        s.system.clear()
        
        i = s.State()
        i.set(LO, True)
        
        j = s.State()
        j.set(LO, True)
        
        b = s.And(i, j, s.s(1), s.ms(100))
        self.assertEqual(UNDEFINED, b.output.value)
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.s(1))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, s.system.next_update())

        i.set(HI, True)
        self.assertEqual(None, s.system.next_update())

        i.set(LO, True)
        j.set(HI, True)
        self.assertEqual(None, s.system.next_update())

        i.set(HI, True)
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.s(1))
        self.assertEqual(HI, b.output.value)

        i.set(LO, True)
        j.set(LO, True)
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.s(1))
        self.assertEqual(LO, b.output.value)

    def test_error(self):
        s.system.clear()
        
        i = s.State()
        i.set(LO, True)
        
        j = s.State()
        j.set(LO, True)
        
        b = s.And(i, j, s.s(1), s.ms(100))
        s.system.step()

        i.set(Z)
        s.system.step()
        self.assertEqual(UNKNOWN, b.output.value)

        i.set(LO)
        s.system.step()
        self.assertEqual(LO, b.output.value)
        i.set(CONFLICT)
        s.system.step()
        self.assertEqual(UNKNOWN, b.output.value)

        i.set(LO)
        s.system.step()
        i.set(UNKNOWN)
        s.system.step()
        self.assertEqual(UNKNOWN, b.output.value)

class TestDecoder(unittest.TestCase):
    def assertStatesEqual(self, expected, actual):
        self.assertEqual(expected, [s.value for s in actual])

    def assertTimestamp(self, d):
        self.assertEqual(d.d, s.system.timestamp.t)

    def test_1_to_2(self):
        s.system.clear()

        en = s.State()
        en.set(LO, True)
        
        i0 = s.State()
        i0.set(LO, True)
        
        d = s.Decoder([i0], en, s.s(1), s.s(0.5), s.s(0.1))
        self.assertEqual(2, len(d.outputs))
        self.assertStatesEqual([UNDEFINED, UNDEFINED], d.outputs)
        
        s.system.step() # outputs are disabled by en
        self.assertTimestamp(s.s(0.5))
        self.assertStatesEqual([LO, LO], d.outputs)
        
        en.set(HI, True)
        s.system.step()
        self.assertTimestamp(s.s(1))
        self.assertStatesEqual([HI, LO], d.outputs)
        
        i0.set(HI, True)
        s.system.step()
        self.assertTimestamp(s.s(2))
        self.assertStatesEqual([LO, HI], d.outputs)
        
        en.set(LO, True)
        s.system.step()
        self.assertTimestamp(s.s(2.5))
        self.assertStatesEqual([LO, LO], d.outputs)
        
        en.set(UNKNOWN, True)
        s.system.step()
        self.assertTimestamp(s.s(3))
        self.assertStatesEqual([UNKNOWN, UNKNOWN], d.outputs)
        
        en.set(HI, True)
        s.system.step()
        self.assertTimestamp(s.s(3.5))
        self.assertStatesEqual([LO, HI], d.outputs)
        
        i0.set(UNKNOWN, True)
        s.system.step()
        self.assertTimestamp(s.s(4.5))
        self.assertStatesEqual([UNKNOWN, UNKNOWN], d.outputs)

class TestCombinations(unittest.TestCase):
    def test_buffered_clock(self):
        s.system.clear()

        c = s.Clock(s.hz(0.5), tt=s.ms(100))
        b = s.Buffer(c.clock, s.ms(500), s.ms(100))

        def step(t, cv, bv):
            s.system.step()
            self.assertEqual(s.s(t).d, s.system.timestamp.t)
            self.assertEqual(cv, c.clock.value)
            self.assertEqual(bv, b.output.value)

        self.assertEqual(HI, c.clock.value)
        self.assertEqual(UNDEFINED, b.output.value)
        step(0.50, HI, HI)
        step(1.00, LO, HI)
        step(1.50, LO, LO)

    def test_3s_buffered_clock(self):
        s.system.clear()

        en = s.State()
        en.set(HI, True)
        c = s.Clock(s.hz(0.5), tt=s.ms(100))
        b = s.Buffer3S(c.clock, s.ms(500), s.ms(100), en, s.ms(100), s.ms(100))

        def step(t, cv, bv):
            # take a step, stabilize outputs, perform checks
            s.system.step()
            while s.system.next_update() == s.Duration(0):
                s.system.step()
            self.assertEqual(s.s(t).d, s.system.timestamp.t)
            self.assertEqual(cv, c.clock.value)
            self.assertEqual(bv, b.output.value)

        self.assertEqual(HI, c.clock.value)
        self.assertEqual(UNDEFINED, b.output.value)
        step(0.1, HI, UNDEFINED) # output enabler updates @ 0.1 but buffer propagates only after 0.5
        step(0.5, HI, HI)
        en.set(LO, True)
        step(0.6, HI, Z)
        step(1.0, LO, Z)
        en.set(HI, True)
        step(1.1, LO, HI)
        step(1.5, LO, LO)

    def test_inverted_clock(self):
        s.system.clear()

        c = s.Clock(s.hz(0.5), tt=s.ms(100))
        b = s.Inverter(c.clock, s.ms(500), s.ms(100))

        def step(t, cv, bv):
            s.system.step()
            self.assertEqual(s.s(t).d, s.system.timestamp.t)
            self.assertEqual(cv, c.clock.value)
            self.assertEqual(bv, b.output.value)

        self.assertEqual(HI, c.clock.value)
        self.assertEqual(UNDEFINED, b.output.value)
        step(0.50, HI, LO)
        step(1.00, LO, LO)
        step(1.50, LO, HI)

    def test_gated_clock(self):
        s.system.clear()
        c = s.Clock(s.hz(0.5), tt=s.ms(100))
        bc = s.Buffer(c.clock, s.ms(200), s.ms(100))
        a = s.And(c.clock, bc.output, s.ms(100), s.ms(100))
        
        def step(t, cv, nv, av):
            s.system.step()
            self.assertEqual(s.s(t).d, s.system.timestamp.t)
            self.assertEqual(cv, c.clock.value)
            self.assertEqual(nv, bc.output.value)
            self.assertEqual(av, a.output.value)

        # initialization is unreliable because
        # clock starts at LO>HI transition
        # c.update(s.Duration(0))
        self.assertEqual(HI, c.clock.value)
        self.assertEqual(UNDEFINED, bc.output.value)
        self.assertEqual(UNDEFINED, a.output.value)
        step(0.10, HI, UNDEFINED, UNKNOWN)
        step(0.20, HI, HI, UNKNOWN)
        step(0.30, HI, HI, HI)
        step(1.00, LO, HI, HI)
        step(1.10, LO, HI, LO)
        step(1.20, LO, LO, LO)
        step(2.00, HI, LO, LO)
        step(2.20, HI, HI, LO)
        step(2.30, HI, HI, HI)
        step(3.00, LO, HI, HI)
        step(3.10, LO, HI, LO)

class TestMux(unittest.TestCase):
    def assertStatesEqual(self, expected, actual):
        self.assertEqual(expected, [s.value for s in actual])

    def test_4_to_2(self):
        s.system.clear()

        is0, is1 = s.State(LO), s.State(LO)
        os0 = s.State(LO)
        i0, i1, i2, i3 = [s.State(LO) for _ in range(4)]
        m = s.Muxer([i0, i1, i2, i3], [is0, is1], s.s(1), s.s(0.1))
        d = s.Demuxer(m.output, [os0], s.s(1), s.s(0.1))

        def step():
            while s.system.step() is not None:
                pass
        
        self.assertStatesEqual([UNDEFINED, UNDEFINED], d.outputs)
        step()
        self.assertStatesEqual([LO, LO], d.outputs)
        i0.set(HI)
        step()
        self.assertStatesEqual([HI, LO], d.outputs)
        os0.set(HI)
        step()
        self.assertStatesEqual([LO, HI], d.outputs)
        is1.set(HI)
        step()
        self.assertStatesEqual([LO, LO], d.outputs)
        i2.set(HI)
        step()
        self.assertStatesEqual([LO, HI], d.outputs)

    def test_1_to_2(self):
        s.system.clear()

        os0 = s.State(LO)
        i0 = s.State(LO)
        md = s.Demuxer(i0, [os0], s.s(1), s.s(0.1))

        self.assertStatesEqual([UNDEFINED, UNDEFINED], md.outputs)
        s.system.step()
        self.assertStatesEqual([LO, LO], md.outputs)
        i0.set(HI)
        s.system.step()
        self.assertStatesEqual([HI, LO], md.outputs)
        os0.set(HI)
        s.system.step()
        self.assertStatesEqual([LO, HI], md.outputs)

    def test_4_to_1(self):
        s.system.clear()

        is0, is1 = s.State(LO), s.State(LO)
        i0, i1, i2, i3 = [s.State(LO) for _ in range(4)]
        m = s.Muxer([i0, i1, i2, i3], [is0, is1], s.s(1), s.s(0.1))

        self.assertEqual(UNDEFINED, m.output.value)
        s.system.step()
        self.assertEqual(LO, m.output.value)
        i0.set(HI)
        s.system.step()
        self.assertEqual(HI, m.output.value)
        is1.set(HI)
        s.system.step()
        self.assertEqual(LO, m.output.value)
        i2.set(HI)
        s.system.step()
        self.assertEqual(HI, m.output.value)

class TestAdder(unittest.TestCase):
    def assertStatesEqual(self, expected, actual):
        self.assertEqual(expected, [s.value for s in actual])

    def test_2_bits(self):
        s.system.clear()

        a0, a1, b0, b1, cin = [s.State(LO) for _ in range(5)]
        a = s.Adder([a0, a1], [b0, b1], cin, s.s(1), s.s(0.1))

        def step():
            while s.system.step() is not None:
                pass
        
        self.assertStatesEqual([UNDEFINED, UNDEFINED], a.outputs)
        self.assertEqual(UNDEFINED, a.cout.value)
        step()
        self.assertStatesEqual([LO, LO], a.outputs)
        self.assertEqual(LO, a.cout.value)
        a0.set(HI)
        step()
        self.assertStatesEqual([LO, HI], a.outputs)
        self.assertEqual(LO, a.cout.value)
        b0.set(HI)
        step()
        self.assertStatesEqual([HI, LO], a.outputs)
        self.assertEqual(LO, a.cout.value)
        a1.set(HI)
        step()
        self.assertStatesEqual([LO, LO], a.outputs)
        self.assertEqual(HI, a.cout.value)
        cin.set(HI)
        step()
        self.assertStatesEqual([LO, HI], a.outputs)
        self.assertEqual(HI, a.cout.value)
