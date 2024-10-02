import unittest

from cpu4.simulator import simulator as s
from cpu4.simulator.simulator import LO, HI, TLM, TMH, THM, TML, UNDEFINED, Z, UNKNOWN, CONFLICT

class OperatorTestCase(unittest.TestCase):
    def assertStatesEqual(self, expected, actual):
        self.assertEqual(expected, [s.value() for s in actual])

    def assertTimestamp(self, d):
        self.assertEqual(d.d, s.system.timestamp.t)


class TestClock(OperatorTestCase):
    def test_init_phase_0(self):
        s.system.clear()
        c = s.Clock(s.hz(1), tt=s.ms(200), phase=0)
        self.assertEqual(HI, c.clock.value())
        self.assertEqual(s.s(0.5), c.next_update())
        c.update(s.s(0.5))
        self.assertEqual(LO, c.clock.value())

    def test_init_phase_180(self):
        s.system.clear()
        c = s.Clock(s.hz(1), tt=s.ms(200), phase=180)
        self.assertEqual(LO, c.clock.value())
        self.assertEqual(s.s(0.5), c.next_update())
        c.update(s.s(0.5))
        self.assertEqual(HI, c.clock.value())

    def test_clock(self):
        s.system.clear()
        c = s.Clock(s.hz(1), tt=s.ms(200), duty=0.4, phase=270)

        # step-by-step
        # freq 1hz   -> (HI>LO @ -0.5s) LO>HI @ 0s, HI>LO @ 0.5s
        # duty 40%   -> (HI>LO @ -0.6s) LO>HI @ 0s, HI>LO @ 0.4s
        # phase 270° -> HI>LO @ 0.15s, LO>HI @ 0.75s, HI>LO @ 1.15s
        def step(t, cv):
            s.system.step()
            self.assertTimestamp(s.s(t))
            self.assertEqual(cv, c.clock.value())

        self.assertTimestamp(s.s(0))
        self.assertEqual(HI, c.clock.value())

        step(0.15, LO)
        step(0.75, HI)
        step(1.15, LO)


class TestBuffer(unittest.TestCase):
    def test_init_lo(self):
        s.system.clear()
        i = s.State(UNDEFINED)
        
        b = s.Buffer(i, s.s(1), s.ms(100))
        self.assertEqual(UNDEFINED, b.output.value())
        self.assertEqual(None, b.next_update())
        
        # Initial state
        i.set(LO)
        self.assertEqual(s.s(1), b.next_update())
        
        b.update(s.s(1))
        self.assertEqual(LO, b.output.value())
        self.assertEqual(None, b.next_update())

    def test_init_hi(self):
        s.system.clear()
        i = s.State(UNDEFINED)
        
        b = s.Buffer(i, s.s(1), s.ms(100))
        self.assertEqual(UNDEFINED, b.output.value())
        self.assertEqual(None, b.next_update())
        
        # Initial state
        i.set(HI)
        self.assertEqual(s.s(1), b.next_update())
        
        b.update(s.s(1))
        self.assertEqual(HI, b.output.value())
        self.assertEqual(None, b.next_update())

    def init(self, level):
        s.system.clear()
        i = s.State(level)
        b = s.Buffer(i, s.s(1), s.ms(100))
        b.next_update()
        b.update(s.s(0))
        return i, b

    def test_simple(self):
        i, b = self.init(LO)
        i.set(HI)
        self.assertEqual(s.s(1), b.next_update())
        b.update(s.s(1))
        self.assertEqual(HI, b.output.value())

        i, b = self.init(HI)
        i.set(LO)
        self.assertEqual(s.s(1), b.next_update())
        b.update(s.s(1))
        self.assertEqual(LO, b.output.value())

    def test_multiple_changes(self):
        i, b = self.init(LO)

        i.set(HI)                                 # t=0, input LO>HI
        self.assertEqual(s.s(1), b.next_update())
        b.update(s.s(0.5))                              # t=0.5, input HI>LO
        i.set(LO)
        self.assertEqual(s.s(0.5), b.next_update())
        b.update(s.s(0.5))                             # t=1, output LO>HI
        self.assertEqual(HI, b.output.value())
        self.assertEqual(s.s(0.50), b.next_update())
        b.update(s.s(0.50))                             # t=1.5, output HI>LO
        self.assertEqual(LO, b.output.value())

class Test3State(unittest.TestCase):
    def test_simple(self):
        s.system.clear()
        
        i = s.State(LO)
        oe = s.State(HI)
        
        # b = s.Enabler(i, en, s.ms(100), s.ms(200), s.s(0), s.s(0), s.STATE_Z)
        b = s.OutputEnabler(i, oe, s.s(1), s.STATE_Z)
        self.assertEqual(UNDEFINED, b.output.value())
        # self.assertEqual(s.s(0.1), b.next_update())
        # b.update(s.s(0.1))
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.s(1))
        self.assertEqual(LO, b.output.value())
        self.assertEqual(None, s.system.next_update())

        oe.set(LO)
        # self.assertEqual(s.ms(200), b.next_update())
        # b.update(s.ms(200))
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.s(1))
        self.assertEqual(Z, b.output.value())
        self.assertEqual(None, s.system.next_update())

        oe.set(HI)
        # self.assertEqual(s.ms(100), b.next_update())
        # b.update(s.ms(100))
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.s(1))
        self.assertEqual(LO, b.output.value())
        self.assertEqual(None, s.system.next_update())

    def test_multiple_changes(self):
        s.system.clear()
        
        i = s.State(LO)
        en = s.State(HI)
        
        # b = s.Enabler(i, en, s.ms(100), s.ms(200), s.s(0), s.s(0), s.STATE_Z)
        b = s.OutputEnabler(i, en, s.s(1), s.STATE_Z)
        # self.assertEqual(s.s(0.1), b.next_update()) # initialization
        # b.update(s.s(0.1))
        self.assertEqual(s.s(1), s.system.next_update()) # initialization
        s.system.update(s.s(1))

        # disable then re-enable before fully disabled
        en.set(LO)
        # self.assertEqual(s.ms(200), b.next_update())
        # b.update(s.ms(150))
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.ms(950))
        en.set(HI)
        self.assertEqual(s.ms(50), s.system.next_update())
        s.system.update(s.ms(50))
        self.assertEqual(Z, b.output.value())
        # self.assertEqual(s.ms(50), b.next_update())
        # b.update(s.ms(50))
        self.assertEqual(s.ms(950), s.system.next_update())
        s.system.update(s.ms(950))
        self.assertEqual(LO, b.output.value())
        self.assertEqual(None, s.system.next_update())

        # disable then re-enable before disabling started
        en.set(LO)
        # self.assertEqual(s.ms(200), b.next_update())
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.ms(50))
        en.set(HI)
        # self.assertEqual(s.ms(100), b.next_update())
        # b.update(s.ms(100))
        self.assertEqual(s.ms(950), s.system.next_update())
        s.system.update(s.ms(950))
        self.assertEqual(Z, b.output.value())
        self.assertEqual(s.ms(50), s.system.next_update())
        s.system.update(s.ms(50))
        self.assertEqual(LO, b.output.value())
        self.assertEqual(None, s.system.next_update())

class TestAnd(unittest.TestCase):
    def test_simple(self):
        s.system.clear()
        
        i = s.State(LO)
        j = s.State(LO)
        
        b = s.And(i, j, s.s(1), s.ms(100))
        self.assertEqual(UNDEFINED, b.output.value())
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.s(1))
        self.assertEqual(LO, b.output.value())
        self.assertEqual(None, s.system.next_update())

        i.set(HI)
        self.assertEqual(None, s.system.next_update())

        i.set(LO)
        j.set(HI)
        self.assertEqual(None, s.system.next_update())

        i.set(HI)
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.s(1))
        self.assertEqual(HI, b.output.value())

        i.set(LO)
        j.set(LO)
        self.assertEqual(s.s(1), s.system.next_update())
        s.system.update(s.s(1))
        self.assertEqual(LO, b.output.value())

    def test_error(self):
        s.system.clear()
        
        i = s.State(LO)
        j = s.State(LO)
        
        b = s.And(i, j, s.s(1), s.ms(100))
        s.system.step()

        i.set(Z)
        s.system.step()
        self.assertEqual(UNKNOWN, b.output.value())

        i.set(LO)
        s.system.step()
        self.assertEqual(LO, b.output.value())
        i.set(CONFLICT)
        s.system.step()
        self.assertEqual(UNKNOWN, b.output.value())

        i.set(LO)
        s.system.step()
        i.set(UNKNOWN)
        s.system.step()
        self.assertEqual(UNKNOWN, b.output.value())

class TestDecoder(OperatorTestCase):
    def test_1_to_2(self):
        s.system.clear()

        en = s.State(LO)
        i0 = s.State(LO)
        
        d = s.Decoder([i0], en, s.s(1), s.s(0.5), s.s(0.1))
        self.assertEqual(2, len(d.outputs))
        self.assertStatesEqual([UNDEFINED, UNDEFINED], d.outputs)
        
        def step_until(t):
            target = s.Timestamp(0) + s.s(t)
            # loop over internal changes, check outputs are constant
            expected = [o.value() for o in d.outputs]
            while s.system.timestamp < target:
                for exp, act in zip(expected, d.outputs):
                    self.assertEqual(exp, act.value())
                s.system.step()
            while s.system.next_update() == s.Duration(0):
                s.system.step()
            self.assertTimestamp(s.s(t))

        step_until(0.5) # outputs are disabled by en
        self.assertStatesEqual([LO, LO], d.outputs)
        
        en.set(HI)
        step_until(1)
        self.assertStatesEqual([HI, LO], d.outputs)
        
        i0.set(HI)
        step_until(2)
        self.assertStatesEqual([LO, HI], d.outputs)
        
        en.set(LO)
        step_until(2.5)
        self.assertStatesEqual([LO, LO], d.outputs)
        
        en.set(UNKNOWN)
        step_until(3)
        self.assertStatesEqual([UNKNOWN, UNKNOWN], d.outputs)
        
        en.set(HI)
        step_until(3.5)
        self.assertStatesEqual([LO, HI], d.outputs)
        
        i0.set(UNKNOWN)
        step_until(4.5)
        self.assertStatesEqual([UNKNOWN, UNKNOWN], d.outputs)

class TestCombinations(OperatorTestCase):
    def test_buffered_clock(self):
        s.system.clear()

        c = s.Clock(s.hz(0.5), tt=s.ms(100))
        b = s.Buffer(c.clock, s.ms(500), s.ms(100))

        def step(t, cv, bv):
            s.system.step()
            self.assertTimestamp(s.s(t))
            self.assertEqual(cv, c.clock.value())
            self.assertEqual(bv, b.output.value())

        self.assertEqual(HI, c.clock.value())
        self.assertEqual(UNDEFINED, b.output.value())
        step(0.50, HI, HI)
        step(1.00, LO, HI)
        step(1.50, LO, LO)

    def test_3s_buffered_clock(self):
        s.system.clear()

        global c
        global b
        en = s.State(HI)
        c = s.Clock(s.hz(0.5), tt=s.ms(100))
        b = s.Buffer3S(c.clock, s.ms(500), s.ms(100), en, s.ms(100))

        def step_until(t, cv, bv):
            target = s.Timestamp(0) + s.s(t)
            # loop over internal changes
            #     states should not change
            # once the target timestamp is reached
            #     stabilise output at target timestamp
            #     perform checks
            initial_c = c.clock.value()
            initial_b = b.output.value()
            while s.system.timestamp < target:
                self.assertEqual(initial_c, c.clock.value())
                self.assertEqual(initial_b, b.output.value())
                s.system.step()
            while s.system.next_update() == s.Duration(0):
                s.system.step()
            self.assertEqual(cv, c.clock.value())
            self.assertEqual(bv, b.output.value())
            self.assertTimestamp(s.s(t))

        self.assertEqual(HI, c.clock.value())
        self.assertEqual(UNDEFINED, b.output.value())
        step_until(0.1, HI, UNDEFINED) # output enabler updates @ 0.1 but buffer propagates only after 0.5
        step_until(0.5, HI, HI)
        en.set(LO)
        step_until(0.6, HI, Z)
        step_until(1.0, LO, Z)
        en.set(HI)
        step_until(1.1, LO, HI)
        step_until(1.5, LO, LO)

    def test_inverted_clock(self):
        s.system.clear()

        c = s.Clock(s.hz(0.5), tt=s.ms(100))
        b = s.Inverter(c.clock, s.ms(500), s.ms(100))

        def step(t, cv, bv):
            s.system.step()
            self.assertTimestamp(s.s(t))
            self.assertEqual(cv, c.clock.value())
            self.assertEqual(bv, b.output.value())

        self.assertEqual(HI, c.clock.value())
        self.assertEqual(UNDEFINED, b.output.value())
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
            self.assertTimestamp(s.s(t))
            self.assertEqual(cv, c.clock.value())
            self.assertEqual(nv, bc.output.value())
            self.assertEqual(av, a.output.value())

        # initialization is unreliable because
        # clock starts at LO>HI transition
        # c.update(s.Duration(0))
        self.assertEqual(HI, c.clock.value())
        self.assertEqual(UNDEFINED, bc.output.value())
        self.assertEqual(UNDEFINED, a.output.value())
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

class TestMux(OperatorTestCase):
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

        self.assertEqual(UNDEFINED, m.output.value())
        s.system.step()
        self.assertEqual(LO, m.output.value())
        i0.set(HI)
        s.system.step()
        self.assertEqual(HI, m.output.value())
        is1.set(HI)
        s.system.step()
        self.assertEqual(LO, m.output.value())
        i2.set(HI)
        s.system.step()
        self.assertEqual(HI, m.output.value())

class TestAdder(OperatorTestCase):
    def test_2_bits(self):
        s.system.clear()

        a0, a1, b0, b1, cin = [s.State(LO) for _ in range(5)]
        a = s.Adder([a0, a1], [b0, b1], cin, s.s(1), s.s(0.1))

        def step():
            while s.system.step() is not None:
                pass
        
        self.assertStatesEqual([UNDEFINED, UNDEFINED], a.outputs)
        self.assertEqual(UNDEFINED, a.cout.value())
        step()
        self.assertStatesEqual([LO, LO], a.outputs)
        self.assertEqual(LO, a.cout.value())
        a0.set(HI)
        step()
        self.assertStatesEqual([LO, HI], a.outputs)
        self.assertEqual(LO, a.cout.value())
        b0.set(HI)
        step()
        self.assertStatesEqual([HI, LO], a.outputs)
        self.assertEqual(LO, a.cout.value())
        a1.set(HI)
        step()
        self.assertStatesEqual([LO, LO], a.outputs)
        self.assertEqual(HI, a.cout.value())
        cin.set(HI)
        step()
        self.assertStatesEqual([LO, HI], a.outputs)
        self.assertEqual(HI, a.cout.value())

class TestDtypeFlipFlop(OperatorTestCase):
    def init(self):
        s.system.clear()
        self.Tp = s.ms(20)
        self.Tt = s.ms(5)
        self.Tw = s.ms(7)
        self.Tr = s.ms(2)
        self.Ts = s.ms(13)
        self.Th = s.ms(6)
        self.Tshort = s.ms(1)
        self.Tmax = s.s(1)
        clock = s.State(LO)
        input = s.State(LO)
        reset = s.State(LO)
        enable = s.State(LO)
        ff = s.DtypeFlipFlop([input], clock, reset, enable, tp=self.Tp, tt=self.Tt, tw=self.Tw, tr=self.Tr, ts=self.Ts, th=self.Th)
        return clock, input, reset, enable, ff

    def test_load(self):
        clock, input, reset, enable, ff = self.init()
        self.assertStatesEqual([UNDEFINED], ff.outputs)
        self.assertEqual(None, s.system.next_update())

        # triggered on LO>HI transition
        enable.set(HI)
        s.system.next_update()
        s.system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tp)
        self.assertStatesEqual([LO], ff.outputs)
        self.assertEqual(None, s.system.next_update())
        
        # no output change outside of LO>HI trigger
        input.set(HI)
        self.assertEqual(None, s.system.next_update())

        # HI>LO does not trigger the flip flop
        clock.set(LO)
        self.assertEqual(None, s.system.next_update())

        # trigger the flip flop with HI input after enough time spent in LO
        s.system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(None, s.system.next_update())

    def test_load_inhibited(self):
        clock, input, reset, enable, ff = self.init()
        clock.set(HI)
        self.assertEqual(None, s.system.next_update())

    def test_load_lo_pulse_too_short(self):
        clock, input, reset, enable, ff = self.init()
        enable.set(HI)
        s.system.next_update()
        s.system.update(self.Tshort)
        clock.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, s.system.next_update())

    def test_load_hi_pulse_too_short(self):
        clock, input, reset, enable, ff = self.init()
        enable.set(HI)
        s.system.next_update()
        s.system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tshort)
        clock.set(LO)
        self.assertEqual(self.Tp - self.Tshort, s.system.next_update())
        s.system.update(self.Tp - self.Tshort)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, s.system.next_update())

    def test_load_enable_setup_too_short(self):
        clock, input, reset, enable, ff = self.init()
        s.system.next_update()
        s.system.update(self.Tw)
        enable.set(HI)
        s.system.next_update()
        s.system.update(self.Tshort)
        clock.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, s.system.next_update())

    def test_load_data_setup_too_short(self):
        clock, input, reset, enable, ff = self.init()
        enable.set(HI)
        s.system.next_update()
        s.system.update(self.Tmax)
        input.set(HI)
        s.system.next_update()
        s.system.update(self.Tshort)
        clock.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, s.system.next_update())

    def test_load_enable_hold_too_short(self):
        clock, input, reset, enable, ff = self.init()
        enable.set(HI)
        s.system.next_update()
        s.system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tshort)
        enable.set(LO)
        self.assertEqual(self.Tp - self.Tshort, s.system.next_update())
        s.system.update(self.Tp - self.Tshort)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, s.system.next_update())

    def test_load_data_hold_too_short(self):
        clock, input, reset, enable, ff = self.init()
        enable.set(HI)
        s.system.next_update()
        s.system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tshort)
        input.set(HI)
        self.assertEqual(self.Tp - self.Tshort, s.system.next_update())
        s.system.update(self.Tp - self.Tshort)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, s.system.next_update())

    def test_reset(self):
        clock, input, reset, enable, ff = self.init()
        enable.set(HI)
        input.set(HI)
        s.system.next_update()
        s.system.update(self.Tmax)
        clock.set(HI)
        s.system.next_update()
        s.system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(None, s.system.next_update())
        # reset contents
        reset.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tp)
        self.assertStatesEqual([LO], ff.outputs)
        self.assertEqual(None, s.system.next_update())
        # clock is inhibited
        clock.set(LO)
        s.system.next_update()
        s.system.update(self.Tw)
        clock.set(HI)
        self.assertEqual(None, s.system.next_update())
        s.system.update(self.Tw)
        # once reset is release, clock data in
        reset.set(LO)
        s.system.next_update()
        s.system.update(self.Tr)
        clock.set(LO)
        s.system.next_update()
        s.system.update(self.Tw)
        clock.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(None, s.system.next_update())

    def test_reset_pulse_too_short(self):
        clock, input, reset, enable, ff = self.init()
        enable.set(HI)
        input.set(HI)
        s.system.next_update()
        s.system.update(self.Tmax)
        clock.set(HI)
        s.system.next_update()
        s.system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(None, s.system.next_update())
        # reset pulse too short
        reset.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tshort)
        reset.set(LO)
        self.assertEqual(self.Tp - self.Tshort, s.system.next_update())
        s.system.update(self.Tp - self.Tshort)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, s.system.next_update())

    def test_reset_recovery_too_short(self):
        clock, input, reset, enable, ff = self.init()
        enable.set(HI)
        input.set(HI)
        s.system.next_update()
        s.system.update(self.Tmax)
        clock.set(HI)
        s.system.next_update()
        s.system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(None, s.system.next_update())
        # reset
        reset.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tp)
        self.assertStatesEqual([LO], ff.outputs)
        self.assertEqual(None, s.system.next_update())
        # cannot clock data in if before recovery time
        clock.set(LO)
        self.assertEqual(None, s.system.next_update())
        s.system.update(self.Tw)
        reset.set(LO)
        self.assertEqual(None, s.system.next_update())
        s.system.update(self.Tshort)
        clock.set(HI)
        self.assertEqual(self.Tp, s.system.next_update())
        s.system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)

class TestBinaryCounter(OperatorTestCase):
    def init(self):
        s.system.clear()
        self.Tp = s.ms(21)
        self.Tt = s.ms(7)
        self.Tw = s.ms(8)
        self.Tr = s.ms(7)
        self.Ts = s.ms(17)
        self.Th = s.ms(5)
        self.Tshort = s.us(1)
        self.Tmax = s.s(1)
        input = s.State(LO)
        clock = s.State(LO)
        reset = s.State(LO)
        count_enable = s.State(LO)
        load_enable = s.State(LO)
        ff = s.BinaryCounter([input], clock, reset, count_enable, load_enable, tp=self.Tp, tt=self.Tt, tw=self.Tw, tr=self.Tr, ts=self.Ts, th=self.Th)
        return input, clock, reset, count_enable, load_enable, ff, s.system

    def test_load(self):
        input, clock, reset, ce, le, ff, system = self.init()
        self.assertStatesEqual([UNDEFINED], ff.outputs)
        self.assertEqual(None, system.next_update())

        # triggered on LO>HI transition
        le.set(HI)
        self.assertEqual(None, system.next_update())
        system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([LO], ff.outputs)
        self.assertEqual(None, system.next_update())
        
        # no output change outside of LO>HI trigger
        input.set(HI)
        self.assertEqual(None, system.next_update())

        # HI>LO does not trigger the flip flop
        clock.set(LO)
        self.assertEqual(None, system.next_update())
        system.update(self.Tmax)

        # trigger the flip flop with HI input after enough time spent in LO
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(None, system.next_update())

    def test_hold(self):
        input, clock, reset, ce, le, ff, system = self.init()
        self.assertStatesEqual([UNDEFINED], ff.outputs)
        self.assertEqual(None, system.next_update())
        clock.set(HI)
        self.assertStatesEqual([UNDEFINED], ff.outputs)
        self.assertEqual(self.Tp, system.next_update())

    def test_load_lo_pulse_too_short(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        system.next_update()
        system.update(self.Tshort)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, system.next_update())

    def test_load_hi_pulse_too_short(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tshort)
        clock.set(LO)
        self.assertEqual(self.Tp - self.Tshort, system.next_update())
        system.update(self.Tp - self.Tshort)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, system.next_update())

    def test_load_enable_setup_too_short(self):
        input, clock, reset, ce, le, ff,system = self.init()
        system.next_update()
        system.update(self.Tmax)
        le.set(HI)
        system.next_update()
        system.update(self.Tshort)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, system.next_update())

    def test_load_data_setup_too_short(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        system.next_update()
        system.update(self.Tmax)
        input.set(HI)
        system.next_update()
        system.update(self.Tshort)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, system.next_update())

    def test_load_enable_hold_too_short(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tshort)
        le.set(LO)
        self.assertEqual(self.Tp - self.Tshort, system.next_update())
        system.update(self.Tp - self.Tshort)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, system.next_update())

    def test_load_data_hold_too_short(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tshort)
        input.set(HI)
        self.assertEqual(self.Tp - self.Tshort, system.next_update())
        system.update(self.Tp - self.Tshort)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, system.next_update())

    def test_reset(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        input.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        system.next_update()
        system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(None, system.next_update())
        # reset contents
        reset.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([LO], ff.outputs)
        self.assertEqual(None, system.next_update())
        # clock is inhibited
        clock.set(LO)
        system.next_update()
        system.update(self.Tw)
        clock.set(HI)
        self.assertEqual(None, system.next_update())
        system.update(self.Tw)
        # once reset is release, clock data in
        reset.set(LO)
        system.next_update()
        system.update(self.Tr)
        clock.set(LO)
        system.next_update()
        system.update(self.Tw)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(None, system.next_update())

    def test_reset_pulse_too_short(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        input.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        system.next_update()
        system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(None, system.next_update())
        # reset pulse too short
        reset.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tshort)
        reset.set(LO)
        self.assertEqual(self.Tp - self.Tshort, system.next_update())
        system.update(self.Tp - self.Tshort)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(None, system.next_update())

    def test_reset_recovery_too_short(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        input.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        system.next_update()
        system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(None, system.next_update())
        # reset
        reset.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([LO], ff.outputs)
        self.assertEqual(None, system.next_update())
        # cannot clock data in if before recovery time
        clock.set(LO)
        self.assertEqual(None, system.next_update())
        system.update(self.Tw)
        reset.set(LO)
        self.assertEqual(None, system.next_update())
        system.update(self.Tshort)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)

    def test_count(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        system.next_update()
        system.update(self.Tp)
        self.assertStatesEqual([LO], ff.outputs)
        self.assertEqual(LO, ff.terminal_count.value())
        
        clock.set(LO)
        le.set(LO)
        ce.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([HI], ff.outputs)
        self.assertEqual(HI, ff.terminal_count.value())
        self.assertEqual(None, system.next_update())
        
        clock.set(LO)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([LO], ff.outputs)
        self.assertEqual(LO, ff.terminal_count.value())
        self.assertEqual(None, system.next_update())

    def test_count_unknown_values(self):
        input, clock, reset, ce, le, ff, system = self.init()
        ce.set(HI)
        self.assertStatesEqual([UNDEFINED], ff.outputs)
        self.assertEqual(UNDEFINED, ff.terminal_count.value())
        self.assertEqual(None, system.next_update())
        system.update(self.Tmax)
        clock.set(HI)
        self.assertStatesEqual([UNDEFINED], ff.outputs)
        self.assertEqual(UNDEFINED, ff.terminal_count.value())
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(UNKNOWN, ff.terminal_count.value())
        self.assertEqual(None, system.next_update())
        clock.set(LO)
        self.assertEqual(None, system.next_update())
        system.update(self.Tmax)
        clock.set(HI)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(UNKNOWN, ff.terminal_count.value())
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(UNKNOWN, ff.terminal_count.value())
        self.assertEqual(None, system.next_update())

    def test_count_enable_setup_too_short(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        system.next_update()
        system.update(self.Tp)
        self.assertStatesEqual([LO], ff.outputs)
        self.assertEqual(LO, ff.terminal_count.value())
        
        clock.set(LO)
        le.set(LO)
        system.next_update()
        system.update(self.Tmax)
        ce.set(HI)
        system.next_update()
        system.update(self.Tshort)
        clock.set(HI)
        self.assertEqual(self.Tp, system.next_update())
        system.update(self.Tp)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(UNKNOWN, ff.terminal_count.value())

    def test_count_enable_hold_too_short(self):
        input, clock, reset, ce, le, ff, system = self.init()
        le.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        system.next_update()
        system.update(self.Tp)
        self.assertStatesEqual([LO], ff.outputs)
        self.assertEqual(LO, ff.terminal_count.value())
        
        clock.set(LO)
        le.set(LO)
        ce.set(HI)
        system.next_update()
        system.update(self.Tmax)
        clock.set(HI)
        system.next_update()
        system.update(self.Tshort)
        ce.set(LO)
        self.assertEqual(self.Tp - self.Tshort, system.next_update())
        system.update(self.Tp - self.Tshort)
        self.assertStatesEqual([UNKNOWN], ff.outputs)
        self.assertEqual(UNKNOWN, ff.terminal_count.value())
