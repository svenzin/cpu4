import unittest

from cpu4.simulator import simulator as s
from cpu4.simulator.simulator import LO, HI, TLM, TMH, THM, TML, UNDEFINED, Z, UNKNOWN, CONFLICT


class TestClock(unittest.TestCase):
    def test_init_phase_0(self):
        s.system.clear()
        c = s.Clock(s.hz(1), tt=s.ms(200), phase=0)
        self.assertEqual(TLM, c.clock.value)
        self.assertEqual(s.s(0), c.next_update())
        c.update(s.s(0))
        self.assertEqual(TMH, c.clock.value)

    def test_init_phase_180(self):
        s.system.clear()
        c = s.Clock(s.hz(1), tt=s.ms(200), phase=180)
        self.assertEqual(THM, c.clock.value)
        self.assertEqual(s.s(0), c.next_update())
        c.update(s.s(0))
        self.assertEqual(TML, c.clock.value)

    def test_clock(self):
        s.system.clear()
        c = s.Clock(s.hz(1), tt=s.ms(200), duty=0.4, phase=270)

        # step-by-step
        # freq 1hz   -> (HI>LO @ -0.5s) LO>HI @ 0s, HI>LO @ 0.5s
        # duty 40%   -> (HI>LO @ -0.6s) LO>HI @ 0s, HI>LO @ 0.4s
        # phase 270° -> HI>LO @ 0.15s, LO>HI @ 0.75s, HI>LO @ 1.15s
        # tt 200ms   -> HI>THM @ 0.05s, THM>TML @ 0.15s, TML>LO @ 0.25s
        #               LO>TLM @ 0.65s, TLM>TMH @ 0.75s, TMH>HI @ 0.85s
        #               HI>THM @ 1.05s, THM>TML @ 1.15s, TML>LO @ 1.25s
        def step(t, cv):
            s.system.step()
            self.assertEqual(s.s(t).d, s.system.timestamp.t)
            self.assertEqual(cv, c.clock.value)

        self.assertEqual(s.s(0).d, s.system.timestamp.t)
        self.assertEqual(HI, c.clock.value)

        step(0.05, THM)
        step(0.15, TML)
        step(0.25, LO)
        step(0.65, TLM)
        step(0.75, TMH)
        step(0.85, HI)
        step(1.05, THM)
        step(1.15, TML)
        step(1.25, LO)


class TestBuffer(unittest.TestCase):
    def test_init_lo(self):
        s.system.clear()
        i = s.State()
        
        b = s.Buffer(i, s.s(1), s.ms(100))
        self.assertEqual(UNDEFINED, b.output.value)
        self.assertEqual(None, b.next_update())
        
        # Initial state
        i.set(LO, True)
        self.assertEqual(s.s(0), b.next_update())
        
        b.update(s.s(0))
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
        self.assertEqual(s.s(0), b.next_update())
        
        b.update(s.s(0))
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
        # same-level states do not trigger changes
        i, b = self.init(LO)
        i.set(TLM, True)
        self.assertEqual(None, b.next_update())
        i.set(TML, True)
        self.assertEqual(None, b.next_update())
        
        i, b = self.init(HI)
        i.set(THM, True)
        self.assertEqual(None, b.next_update())
        i.set(TMH, True)
        self.assertEqual(None, b.next_update())
        
        # other-level states trigger changes
        i, b = self.init(LO)
        i.set(TMH, True)
        self.assertEqual(s.s(0.95), b.next_update())
        b.update(s.s(0.95))
        self.assertEqual(TLM, b.output.value)
        self.assertEqual(s.s(0.05), b.next_update())
        b.update(s.s(0.05))
        self.assertEqual(TMH, b.output.value)
        self.assertEqual(s.s(0.05), b.next_update())
        b.update(s.s(0.05))
        self.assertEqual(HI, b.output.value)

        i, b = self.init(HI)
        i.set(TML, True)
        self.assertEqual(s.s(0.95), b.next_update())
        b.update(s.s(0.95))
        self.assertEqual(THM, b.output.value)
        self.assertEqual(s.s(0.05), b.next_update())
        b.update(s.s(0.05))
        self.assertEqual(TML, b.output.value)
        self.assertEqual(s.s(0.05), b.next_update())
        b.update(s.s(0.05))
        self.assertEqual(LO, b.output.value)

    def test_multiple_changes(self):
        i, b = self.init(LO)

        i.set(HI, True)                                 # t=0, input LO>HI
        self.assertEqual(s.s(0.95), b.next_update())
        b.update(s.s(0.5))                              # t=0.5, input HI>LO
        i.set(LO, True)
        self.assertEqual(s.s(0.45), b.next_update())
        b.update(s.s(0.45))                             # t=0.95, output LO>TLM
        self.assertEqual(TLM, b.output.value)
        self.assertEqual(s.s(0.05), b.next_update())
        b.update(s.s(0.05))                             # t=1, output TLM>TMH
        self.assertEqual(TMH, b.output.value)
        self.assertEqual(s.s(0.05), b.next_update())
        b.update(s.s(0.05))                             # t=1.05, output TMH>HI
        self.assertEqual(HI, b.output.value)
        self.assertEqual(s.s(0.40), b.next_update())
        b.update(s.s(0.40))                             # t=1.45, output HI>THM
        self.assertEqual(THM, b.output.value)
        self.assertEqual(s.s(0.05), b.next_update())
        b.update(s.s(0.05))                             # t=1.5, output THM>TML
        self.assertEqual(TML, b.output.value)
        self.assertEqual(s.s(0.05), b.next_update())
        b.update(s.s(0.05))                             # t=1.55, output TML>LO
        self.assertEqual(LO, b.output.value)

class Test3State(unittest.TestCase):
    def test_simple(self):
        s.system.clear()
        
        i = s.State()
        i.set(LO, True)
        
        n_oe = s.State()
        n_oe.set(LO, True)
        
        b = s.ThreeState(i, n_oe, s.ms(100), s.ms(200))
        self.assertEqual(s.s(0), b.next_update())
        b.update(s.s(0))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, b.next_update())

        n_oe.set(HI, True)
        self.assertEqual(s.ms(200), b.next_update())
        b.update(s.ms(200))
        self.assertEqual(Z, b.output.value)
        self.assertEqual(None, b.next_update())

        n_oe.set(LO, True)
        self.assertEqual(s.ms(100), b.next_update())
        b.update(s.ms(100))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, b.next_update())

    def test_multiple_changes(self):
        s.system.clear()
        
        i = s.State()
        i.set(LO, True)
        
        n_oe = s.State()
        n_oe.set(LO, True)
        
        b = s.ThreeState(i, n_oe, s.ms(100), s.ms(200))
        self.assertEqual(s.ms(0), b.next_update()) # initialization
        b.update(s.s(0))

        # disable then re-enable before fully disabled
        n_oe.set(HI, True)
        self.assertEqual(s.ms(200), b.next_update())
        b.update(s.ms(150))
        n_oe.set(LO, True)
        self.assertEqual(s.ms(50), b.next_update())
        b.update(s.ms(50))
        self.assertEqual(Z, b.output.value)
        self.assertEqual(s.ms(50), b.next_update())
        b.update(s.ms(50))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, b.next_update())

        # disable then re-enable before disabling started
        n_oe.set(HI, True)
        self.assertEqual(s.ms(200), b.next_update())
        b.update(s.ms(50))
        n_oe.set(LO, True)
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
        self.assertEqual(s.s(0), s.system.next_update())
        s.system.update(s.s(0))
        self.assertEqual(LO, b.output.value)
        self.assertEqual(None, s.system.next_update())

        i.set(HI, True)
        self.assertEqual(None, s.system.next_update())

        i.set(LO, True)
        j.set(HI, True)
        self.assertEqual(None, s.system.next_update())

        i.set(HI, True)
        self.assertEqual(s.s(0.95), s.system.next_update())
        s.system.update(s.s(0.95))
        self.assertEqual(TLM, b.output.value)
        self.assertEqual(s.s(0.05), s.system.next_update())
        s.system.update(s.s(0.05))
        self.assertEqual(TMH, b.output.value)
        self.assertEqual(s.s(0.05), s.system.next_update())
        s.system.update(s.s(0.05))
        self.assertEqual(HI, b.output.value)

        i.set(LO, True)
        j.set(LO, True)
        self.assertEqual(s.s(0.95), s.system.next_update())
        s.system.update(s.s(0.95))
        self.assertEqual(THM, b.output.value)
        self.assertEqual(s.s(0.05), s.system.next_update())
        s.system.update(s.s(0.05))
        self.assertEqual(TML, b.output.value)
        self.assertEqual(s.s(0.05), s.system.next_update())
        s.system.update(s.s(0.05))
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
        
        s.system.step()
        self.assertTimestamp(s.s(0))
        self.assertStatesEqual([LO, LO], d.outputs)
        
        en.set(HI, True)
        s.system.step()
        self.assertTimestamp(s.s(0.45))
        self.assertStatesEqual([TLM, LO], d.outputs)
        s.system.step()
        self.assertTimestamp(s.s(0.5))
        self.assertStatesEqual([TMH, LO], d.outputs)
        s.system.step()
        self.assertTimestamp(s.s(0.55))
        self.assertStatesEqual([HI, LO], d.outputs)
        
        i0.set(HI, True)
        s.system.step()
        self.assertTimestamp(s.s(1.45))
        self.assertStatesEqual([THM, TLM], d.outputs)
        s.system.step()
        self.assertTimestamp(s.s(1.5))
        self.assertStatesEqual([TML, TMH], d.outputs)
        s.system.step()
        self.assertTimestamp(s.s(1.55))
        self.assertStatesEqual([LO, HI], d.outputs)
        
        en.set(LO, True)
        s.system.step()
        self.assertTimestamp(s.s(1.95))
        self.assertStatesEqual([LO, THM], d.outputs)
        s.system.step()
        self.assertTimestamp(s.s(2))
        self.assertStatesEqual([LO, TML], d.outputs)
        s.system.step()
        self.assertTimestamp(s.s(2.05))
        self.assertStatesEqual([LO, LO], d.outputs)
        
        en.set(UNKNOWN, True)
        s.system.step()
        self.assertStatesEqual([UNKNOWN, UNKNOWN], d.outputs)
        
        en.set(HI, True)
        s.system.step()
        self.assertStatesEqual([LO, HI], d.outputs)
        
        i0.set(UNKNOWN, True)
        s.system.step()
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

        step(0.00, TMH, LO)
        step(0.05, HI,  LO)
        step(0.45, HI, TLM)
        step(0.50, HI, TMH)
        step(0.55, HI,  HI)
        step(0.95, THM, HI)
        step(1.00, TML, HI)
        step(1.05, LO,  HI)
        step(1.45, LO, THM)
        step(1.50, LO, TML)
        step(1.55, LO,  LO)

    def test_3s_buffered_clock(self):
        s.system.clear()

        n_oe = s.State()
        n_oe.set(LO, True)
        c = s.Clock(s.hz(0.5), tt=s.ms(100))
        b = s.Buffer3S(c.clock, s.ms(500), s.ms(100), n_oe, s.ms(100), s.ms(100))

        def step(t, cv, bv):
            s.system.step()
            self.assertEqual(s.s(t).d, s.system.timestamp.t)
            self.assertEqual(cv, c.clock.value)
            self.assertEqual(bv, b.output.value)

        step(0.00, TMH, LO)
        step(0.05, HI,  LO)
        step(0.45, HI, TLM)
        step(0.50, HI, TMH)
        n_oe.set(HI, True)
        step(0.55, HI,  HI)
        step(0.60, HI,  Z)
        step(0.95, THM, Z)
        step(1.00, TML, Z)
        n_oe.set(LO, True)
        step(1.05, LO,  Z)
        step(1.10, LO,  HI)
        step(1.45, LO, THM)
        step(1.50, LO, TML)
        step(1.55, LO,  LO)

    def test_inverted_clock(self):
        s.system.clear()

        c = s.Clock(s.hz(0.5), tt=s.ms(100))
        b = s.Not(c.clock, s.ms(500), s.ms(100))

        def step(t, cv, bv):
            s.system.step()
            self.assertEqual(s.s(t).d, s.system.timestamp.t)
            self.assertEqual(cv, c.clock.value)
            self.assertEqual(bv, b.output.value)

        step(0.00, TMH, HI)
        step(0.05, HI,  HI)
        step(0.45, HI, THM)
        step(0.50, HI, TML)
        step(0.55, HI,  LO)
        step(0.95, THM, LO)
        step(1.00, TML, LO)
        step(1.05, LO,  LO)
        step(1.45, LO, TLM)
        step(1.50, LO, TMH)
        step(1.55, LO,  HI)
