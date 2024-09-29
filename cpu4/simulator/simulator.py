from typing import Optional
import math
import itertools

from collections import namedtuple
from dataclasses import dataclass


# time
class Timestamp:
    def __init__(self, nanoseconds: int):
        self.t = nanoseconds
    
    def __repr__(self):
        return f'Timestamp({repr(self.t / 1e9)})'
    
    def __sub__(self, other: 'Timestamp'):
        return Duration(self.t - other.t)
    
    def __iadd__(self, dt: 'Duration'):
        self.t += dt.d
        return self
    
    def __eq__(self, other: 'Timestamp'):
        return self.t == other.t
    
    def __lt__(self, other: 'Timestamp'):
        return self.t < other.t
    
    def __le__(self, other: 'Timestamp'):
        return self.t <= other.t
    
    def copy(self):
        return Timestamp(self.t)

class Duration:
    def __init__(self, nanoseconds: int):
        self.d = nanoseconds
    
    def __repr__(self):
        return f'Duration({repr(self.d / 1e9)})'
    
    def to_frequency(self) -> 'Frequency':
        return Frequency(1e9 / self.d)
    
    def __sub__(self, other: 'Duration'):
        return Duration(self.d - other.d)
    
    def __add__(self, other: 'Duration'):
        return Duration(self.d + other.d)
    
    def __iadd__(self, other: 'Duration'):
        self.d += other.d
        return self
    
    def __mul__(self, other: float):
        return Duration(self.d * other)
    
    def __rmul__(self, other: float):
        return self * other

    def __eq__(self, other):
        return (other is not None) and (self.d == other.d)

    def __lt__(self, other):
        return self.d < other.d

    def __le__(self, other):
        return self.d <= other.d

def s(t: float):
    return ns(1e9 * t)

def ms(t: float):
    return ns(1e6 * t)

def us(t: float):
    return ns(1e3 * t)

def ns(t: float):
    return Duration(math.floor(t))

# frequency
class Frequency:
    def __init__(self, hertz: float) -> None:
        self.f = hertz
    
    def __repr__(self):
        return f'Frequency({repr(self.f)})'
    
    def to_duration(self) -> Duration:
        return s(1.0 / self.f)

def hz(f: float):
    return Frequency(f)

def khz(f: float):
    return hz(1e3 * f)

def mhz(f: float):
    return hz(1e6 * f)

# bases
BaseLevel = str
LO = 'LO'
HI = 'HI'
TLM = 'TLM'
TMH = 'TMH'
THM = 'THM'
TML = 'TML'
Z = 'Z'
CONFLICT = 'X'
UNKNOWN = '?'
UNDEFINED = 'U'
ERROR = '!'
PULL_UP = 'P_HI'
PULL_DOWN = 'P_LO'

LEVELS_LO = (LO, TLM, TML)
LEVELS_HI = (HI, THM, TMH)

def base_logic_level(base):
    if base in LEVELS_LO:
        return LO
    if base in LEVELS_HI:
        return HI
    return base

def base_is_driving(base):
    if base in (UNDEFINED, Z, PULL_UP, PULL_DOWN):
        return False
    return True

def logic_level(state):
    if state is None:
        return ERROR
    return base_logic_level(state.value())

def logic_levels(states):
    return tuple((base_logic_level(s.value()) for s in states))

@dataclass
class BaseState:
    value: BaseLevel
    t_begin: Timestamp
    t_end: Optional[Timestamp]
    
    def __init__(self, value):
        self.value = value
        self.t_begin = system.timestamp.copy()
        self.t_end = None

class State:
    def __init__(self, value: BaseLevel=None, *, other: 'State'=None, read_only=False):
        assert (value is not None) != (other is not None)
        self.read_only = read_only
        if value is not None:
            self.i = 0
            self.timeline = [BaseState(value)]
        elif other is not None:
            self.i = other.i
            self.timeline = other.timeline
    
    def value(self):
        return self.timeline[self.i].value

    def duration(self) -> Duration:
        desc = self.timeline[self.i]
        try:
            return desc.t_end - desc.t_begin
        except TypeError:
            return system.timestamp - desc.t_begin
    
    def set(self, value: BaseLevel):
        assert not self.read_only
        assert self.i == len(self.timeline) - 1
        desc = self.timeline[self.i]
        if value != desc.value:
            desc.t_end = system.timestamp.copy()
            self.i += 1
            self.timeline.append(BaseState(value))
    
    def has_changed(self) -> bool:
        assert self.i == len(self.timeline) - 1
        return self.timeline[self.i].t_begin == system.timestamp

    def _get(self, offset) -> 'State':
        s = State(other=self)
        s.i += offset
        return s
    
    def previous(self) -> 'State':
        return self._get(-1)
    
    def sample(self) -> 'State':
        return self._get(0)
    
    def setup(self, t: Timestamp) -> Duration:
        desc = self.timeline[self.i]
        assert desc.t_begin <= t
        assert desc.t_end is None or t <= desc.t_end
        return t - desc.t_begin
    
    def hold(self, t: Timestamp) -> Duration:
        desc = self.timeline[self.i]
        assert desc.t_begin <= t
        assert desc.t_end is None or t <= desc.t_end
        try:
            return desc.t_end - t
        except TypeError:
            return system.timestamp - t

# system

class System:
    def __init__(self, m=0.5) -> None:
        self._n = 0
        self.m = m
        self.clear()

    def register_element(self, element, name):
        uname = f'{name}_{self._n}'
        self._n += 1
        assert uname not in self.elements.keys()
        self.elements[uname] = element
    
    def register_state(self, state, name):
        uname = f'{name}_{self._n}'
        self._n += 1
        assert uname not in self.states.keys()
        self.states[uname] = state
    
    def clear(self):
        self.timestamp = Timestamp(0)
        self.elements = {}
        self.states = {}
        self.timeline = []
    
    def next_update(self):
        dts = [element.next_update() for element in self.elements.values()]
        dts = [dt for dt in dts if dt is not None]
        if len(dts) == 0:
            return None
        current_dt = min((dt.d for dt in dts if dt is not None))
        return Duration(current_dt)
    
    def update(self, dt: Duration):
        self.timestamp += dt
        for element in self.elements.values():
            element.update(dt)
    
    def step(self):
        current_dt = self.next_update()
        if current_dt is not None:
            self.update(current_dt)
        return current_dt

system = System()

STATE_UNDEFINED = State(UNDEFINED, read_only=True)
STATE_LO = State(LO, read_only=True)
STATE_HI = State(HI, read_only=True)
STATE_Z = State(Z, read_only=True)
STATE_UNKNOWN = State(UNKNOWN, read_only=True)
STATE_CONFLICT = State(CONFLICT, read_only=True)

# clock
class Clock:
    def __init__(self,
                 f: Frequency,
                 *,
                 tt: Optional[Duration]=None,
                 duty: float=0.5,
                 phase: float=0):
        super().__init__()
        assert 0 < duty < 1
        assert 0 <= phase < 360
        period = f.to_duration()
        self.tt = tt or s(0)
        self.t_hi = duty * period
        self.t_lo = (1 - duty) * period
        self.clock = State(UNDEFINED)
        dt_phase = phase / 360 * period
        if dt_phase == Duration(0):
            self.dt = self.t_hi
            self.clock.set(HI)
        elif dt_phase <= self.t_lo:
            self.dt = dt_phase
            self.clock.set(LO)
        else:
            self.dt = dt_phase - self.t_lo
            assert self.dt <= self.t_hi
            self.clock.set(HI)
        assert self.dt >= Duration(0)
        assert self.clock.value() in [HI, LO]
        system.register_element(self, 'clock')
        system.register_state(self.clock, 'clock.clock')

    def next_update(self):
        return self.dt

    def update(self, dt: Duration):
        assert dt <= self.dt
        self.dt -= dt
        if self.dt <= s(0):
            if self.clock.value() == LO:
                self.clock.set(HI)
                self.dt += self.t_hi
            elif self.clock.value() == HI:
                self.clock.set(LO)
                self.dt += self.t_lo
            else:
                assert False

class Operator:
    def __init__(self, inputs: list[State], op: dict[tuple[BaseLevel], tuple[State]], tp: Duration, tt: Duration, name='operator'):
        assert tt <= tp
        self.tp = tp
        self.tt = tt
        
        self.input_count = len(inputs)
        assert all(self.input_count == len(o) for o in op.keys())
        self.inputs = inputs

        self.op = op

        self.output_count = len(next(iter(op.values())))
        assert all(self.output_count == len(o) for o in op.values())
        self.outputs = [State(UNDEFINED) for _ in range(self.output_count)]
        self.previous_outputs = None
        
        self.transitions = []

        system.register_element(self, name)
        for o in self.outputs:
            system.register_state(o, f'{name}.output')

    def next_update(self):
        inputs = logic_levels(self.inputs)
        if (self.previous_outputs is not None
            or len(inputs) == 0
            or any((i != UNDEFINED for i in inputs))):
            try:
                outputs = logic_levels(self.op[inputs])
            except KeyError:
                outputs = self.output_count * [UNKNOWN]
            if self.previous_outputs != outputs:
                self.transitions.append((outputs, self.tp))
                self.previous_outputs = outputs
        if len(self.transitions) > 0:
            _, dt = self.transitions[0]
            return dt
        else:
            return None
    
    def update(self, dt: Duration):
        if len(self.transitions) == 0:
            return
        transitions = []
        for values, dt_transition in self.transitions:
            assert dt <= dt_transition
            dt_transition -= dt
            if dt_transition <= Duration(0):
                for output, value in zip(self.outputs, values):
                    output.set(value)
            else:
                transitions.append((values, dt_transition))
        self.transitions = transitions

class Buffer(Operator):
    def __init__(self, input: State, tp: Duration, tt: Duration):
        super().__init__([input], {(LO,): (STATE_LO,),
                                   (HI,): (STATE_HI,)}, tp, tt, 'buffer')
        self.output = self.outputs[0]

class Inverter(Operator):
    def __init__(self, input: State, tp: Duration, tt: Duration):
        super().__init__([input], {(LO,): (STATE_HI,),
                                   (HI,): (STATE_LO,)}, tp, tt, 'inverter')
        self.output = self.outputs[0]

class And(Operator):
    def __init__(self, input_a: State, input_b: State, tp: Duration, tt: Duration):
        super().__init__([input_a, input_b], {(LO, LO): (STATE_LO,),
                                              (LO, HI): (STATE_LO,),
                                              (HI, LO): (STATE_LO,),
                                              (HI, HI): (STATE_HI,)}, tp, tt, 'and')
        self.output = self.outputs[0]

class Or(Operator):
    def __init__(self, input_a: State, input_b: State, tp: Duration, tt: Duration):
        super().__init__([input_a, input_b], {(LO, LO): (STATE_LO,),
                                              (LO, HI): (STATE_HI,),
                                              (HI, LO): (STATE_HI,),
                                              (HI, HI): (STATE_HI,)}, tp, tt, 'or')
        self.output = self.outputs[0]

class Muxer(Operator):
    def __init__(self, inputs: list[State], sel: list[State], tp: Duration, tt: Duration):
        # mux_map example for 4>1 mux
        # { (LO, LO): (inputs[0],),
        #   (LO, HI): (inputs[1],),
        #   (HI, LO): (inputs[2],),
        #   (HI, HI): (inputs[3],) }
        mux_map = {}
        coordinates = len(sel) * [[LO, HI]]
        for index, select in enumerate(itertools.product(*coordinates)):
            mux_map[select] = [inputs[index]]
        
        # selection bits need to be reversed because of the way itertools.product produces items
        super().__init__(list(reversed(sel)), mux_map, tp, tt, 'muxer')

        assert len(self.outputs) == 1
        self.output = self.outputs[0]

class Demuxer(Operator):
    def __init__(self, input: State, sel: list[State], tp: Duration, tt: Duration):
        # demux_map example for 1>4 demux
        # { (LO, LO): (input,    STATE_LO, STATE_LO, STATE_LO),
        #   (LO, HI): (STATE_LO, input,    STATE_LO, STATE_LO),
        #   (HI, LO): (STATE_LO, STATE_LO, input,    STATE_LO),
        #   (HI, HI): (STATE_LO, STATE_LO, STATE_LO, input) }
        demux_map = {}
        coordinates = len(sel) * [[LO, HI]]
        for index, select in enumerate(itertools.product(*coordinates)):
            output = 2 ** len(sel) * [STATE_LO]
            output[index] = input
            demux_map[select] = output
        
        # selection bits need to be reversed because of the way itertools.product produces items
        super().__init__(list(reversed(sel)), demux_map, tp, tt, 'demuxer')

class Adder:
    def __init__(self, inputs_a: list[State], inputs_b: list[State], cin: State, tp: Duration, tt: Duration):
        # add_map example for 1 bit adder
        # { (LO, LO, LO): (STATE_LO, STATE_LO),
        #   (LO, LO, HI): (STATE_LO, STATE_HI),
        #   (LO, HI, LO): (STATE_LO, STATE_HI),
        #   (LO, HI, HI): (STATE_HI, STATE_LO),
        #   (HI, LO, LO): (STATE_LO, STATE_HI),
        #   (HI, LO, HI): (STATE_HI, STATE_LO),
        #   (HI, HI, LO): (STATE_HI, STATE_LO),
        #   (HI, HI, HI): (STATE_HI, STATE_HI) }
        bit_count = len(inputs_a)
        assert bit_count == len(inputs_b)
        
        # input_values contain 'bit_count' bits
        coordinates = bit_count * [[LO, HI]]
        input_values = list(itertools.product(*coordinates))
        
        # output_values contain 'bit_count + 1' bits : (cout, *result)
        coordinates = (bit_count + 1) * [[STATE_LO, STATE_HI]]
        output_states = list(itertools.product(*coordinates))
        
        add_map = {}
        for a_value, a_input in enumerate(input_values):
            for b_value, b_input in enumerate(input_values):
                for c_value, c_input in enumerate([(LO,), (HI,)]):
                    select = c_input + b_input + a_input
                    output = a_value + b_value + c_value
                    add_map[select] = output_states[output]
        self.adder = Operator([cin] + list(reversed(inputs_b)) + list(reversed(inputs_a)), add_map, tp, tt, 'adder')
        
        self.cout = self.adder.outputs[0]
        self.outputs = self.adder.outputs[1:]

class Decoder:
    def __init__(self, inputs: list[State], en: State, tp_data: Duration, tp_en: Duration, tt: Duration):
        self.decoder = Demuxer(STATE_HI, inputs, tp_data, tt)
        self.enablers = [Enabler(o, en, tp_en, tp_en, tt, tt, STATE_LO) for o in self.decoder.outputs]
        self.outputs = [e.output for e in self.enablers]

class EnablerOperator(Operator):
    def __init__(self, input: State, en: State, tp: Duration, tt: Duration, disabled: State):
        super().__init__([en], {(LO,): (disabled,),
                                (HI,): (input,)}, tp, tt, 'enabler')
        self.output = self.outputs[0]

class Enabler:
    def __init__(self, input: State, en: State, tp_en: Duration, tp_dis: Duration, tt_en: Duration, tt_dis: Duration, disabled: State):
        self.input = input

        self.en = en
        self.previous_en = UNDEFINED
        
        assert tt_en <= tp_en
        self.tp_en = tp_en
        self.tt_en = tt_en
        
        assert tt_dis <= tp_dis
        self.tp_dis = tp_dis
        self.tt_dis = tt_dis
        
        self.output_enabled = None
        self.output = State(UNDEFINED)
        
        self.disabled_state = disabled
        
        self.transitions = []

        system.register_element(self, 'enabler')
        system.register_state(self.output, 'enabler.output')

    def append(self, output_enabled, dt):
        while len(self.transitions) > 0 and self.transitions[-1][1] > dt:
            self.transitions.pop()
        self.transitions.append((output_enabled, dt))

    def next_update(self):
        en = logic_level(self.en)
        if self.previous_en != en:
            if en == HI:
                self.append(True, self.tp_en)
            elif en == LO:
                self.append(False, self.tp_dis)
            else:
                if self.previous_en == LO:
                    self.append(None, self.tp_en)
                elif self.previous_en == HI:
                    self.append(None, self.tp_dis)
                else:
                    assert False
            self.previous_en = en
        if len(self.transitions) > 0:
            _, dt = self.transitions[0]
            return dt
        else:
            return None
    
    def update(self, dt: Duration):
        if len(self.transitions) > 0:
            transitions = []
            for value, dt_transition in self.transitions:
                assert dt <= dt_transition
                dt_transition -= dt
                if dt_transition <= Duration(0):
                    self.output_enabled = value
                else:
                    transitions.append((value, dt_transition))
            self.transitions = transitions
        if self.output_enabled is None:
            self.output.set(UNKNOWN)
        elif self.output_enabled:
            self.output.set(self.input.value())
        else:
            self.output.set(self.disabled_state.value())

class Buffer3S:
    def __init__(self, input: State, tp: Duration, tt: Duration, en: State, t_en: Duration, t_dis: Duration):
        self.buffer = Buffer(input, tp, tt)
        self.enabler = Enabler(self.buffer.output, en, t_en, t_dis, tt, tt, STATE_Z)
        self.output = self.enabler.output

class Transition:
    def __init__(self, t: Timestamp, dt: Duration, *payload):
        self.timestamp = t
        self.remaining_dt = dt
        self.elapsed_dt = Duration(0)
        self.payload = list(payload)

class Base:
    def __init__(self):
        self.transitions: list[Transition] = []
        system.register_element(self, "")
    
    def transition(self, payload):
        raise NotImplementedError()

    def append_transition(self, dt, *payload):
        self.transitions.append(Transition(system.timestamp.copy(), dt, *payload))

    def next_update(self):
        if len(self.transitions) > 0:
            return self.transitions[0].remaining_dt
        return None
    
    def update(self, dt):
        for transition in self.transitions:
            assert Duration(0) <= dt <= transition.remaining_dt
            transition.remaining_dt -= dt
            transition.elapsed_dt += dt
        
        if len(self.transitions) > 0 and self.transitions[0].remaining_dt <= Duration(0):
            transition = self.transitions.pop(0)
            self.transition(transition)

class DtypeFlipFlop(Base):
    def __init__(self, inputs, clock, reset, enable, tp, tt, tw, tr, ts, th):
        super().__init__()
        assert tt <= tp
        assert tw <= tp
        assert th <= tp
        assert tr <= tp
        self.inputs = inputs
        self.clock = clock
        self.reset = reset
        self.enable = enable

        self.tp = tp
        self.tt = tt
        self.tw = tw
        self.tr = tr
        self.ts = ts
        self.th = th

        self.outputs = [State(UNDEFINED) for _ in inputs]

    def next_update(self):
        now = system.timestamp
        snapshot = [s.sample() for s in [self.clock, self.reset, self.enable] + self.inputs]
        clock, reset, enable, *inputs = snapshot
        previous_clock = clock.previous()
        is_clocked = (clock.has_changed()
                      and logic_level(clock) == HI
                      and logic_level(previous_clock) == LO
                      # inhibit clock during ~enable or reset
                      and logic_level(reset) == LO
                      and logic_level(enable) == HI)
        if is_clocked:
            if (previous_clock.duration() >= self.tw
                and logic_level(enable) == HI
                and enable.setup(now) >= self.ts
                and reset.setup(now) >= self.tr
                and all((input.setup(now) >= self.ts for input in self.inputs))):
                desired_outputs = logic_levels(self.inputs)
            else:
                desired_outputs = [UNKNOWN for _ in self.inputs]
            self.append_transition(self.tp,
                                   desired_outputs,
                                   snapshot,
                                   'load')
        if reset.has_changed():
            reset = logic_level(reset)
            if reset == LO:
                pass
            else:
                if reset == HI:
                    desired_outputs = [LO for _ in self.inputs]
                else:
                    desired_outputs = [UNKNOWN for _ in self.inputs]
                self.append_transition(self.tp,
                                       desired_outputs,
                                       snapshot,
                                       'reset')
        return super().next_update()

    def transition(self, transition: Transition):
        t = transition.timestamp
        output_levels, snapshot, scenario = transition.payload
        clock, reset, enable, *inputs = snapshot
        assert len(output_levels) == len(self.outputs)
        is_stable = True
        if scenario == 'reset':
            is_stable = (is_stable
                         and logic_level(reset) == HI
                         and reset.hold(t) >= self.th)
        elif scenario == 'load':
            is_stable = (is_stable
                        and logic_level(clock) == HI
                        and clock.hold(t) >= self.tw
                        and logic_level(enable) == HI
                        and enable.hold(t) >= self.th)
            for input in inputs:
                is_stable = (is_stable
                            and input.hold(t) >= self.th)
        else:
            is_stable = False

        if is_stable:
            for o, l in zip(self.outputs, output_levels):
                o.set(l)
        else:
            for o, l in zip(self.outputs, output_levels):
                o.set(UNKNOWN)

class BinaryCounter(Base):
    def __init__(self, inputs, clock, reset, ce, le, tp, tt, tw, tr, ts, th):
        super().__init__()
        assert tt <= tp
        assert tw <= tp
        assert th <= tp
        assert tr <= tp
        self.inputs = inputs
        self.clock = clock
        self.reset = reset
        self.ce = ce
        self.le = le

        self.tp = tp
        self.tt = tt
        self.tw = tw
        self.tr = tr
        self.ts = ts
        self.th = th

        self.outputs = [State(UNDEFINED) for _ in inputs]
        self.terminal_count = State(UNDEFINED)

    def next_update(self):
        now = system.timestamp
        snapshot = [s.sample() for s in [self.clock, self.reset, self.ce, self.le] + self.inputs]
        clock, reset, ce, le, *inputs = snapshot
        previous_clock = clock.previous()
        is_clocked = (clock.has_changed()
                      and logic_level(clock) == HI
                      and logic_level(previous_clock) == LO
                      # inhibit clock during reset
                      and logic_level(reset) == LO)
        if is_clocked:
            if (previous_clock.duration() >= self.tw
                and logic_level(le) == HI):
                if (reset.setup(now) >= self.tr
                    and le.setup(now) >= self.ts
                    and all((input.setup(now) >= self.ts for input in inputs))):
                    desired_outputs = logic_levels(self.inputs)
                else:
                    desired_outputs = [UNKNOWN for _ in self.inputs]
                self.append_transition(self.tp,
                                       desired_outputs,
                                       snapshot,
                                       'load')
            elif (previous_clock.duration() >= self.tw
                  and logic_level(ce) == HI):
                if(reset.setup(now) >= self.tr
                  and ce.setup(now) >= self.ts):
                    carry = HI
                    desired_outputs = []
                    for bit in self.outputs:
                        b = bit.value()
                        if b == LO:
                            desired_outputs.append(carry)
                            carry = LO
                        elif b == HI and carry == LO:
                            desired_outputs.append(HI)
                        elif b == HI and carry == HI:
                            desired_outputs.append(LO)
                        else:
                            desired_outputs.append(UNKNOWN)
                else:
                    desired_outputs = [UNKNOWN for _ in self.outputs]
                self.append_transition(self.tp,
                                       desired_outputs,
                                       snapshot,
                                       'count')
            else:
                desired_outputs = [UNKNOWN for _ in self.outputs]
                self.append_transition(self.tp,
                                       desired_outputs,
                                       snapshot,
                                       'invalid')
        if reset.has_changed():
            reset = logic_level(reset)
            if reset == LO:
                pass
            else:
                if reset == HI:
                    desired_outputs = [LO for _ in self.inputs]
                else:
                    desired_outputs = [UNKNOWN for _ in self.inputs]
                self.append_transition(self.tp,
                                        desired_outputs,
                                        snapshot,
                                        'reset')
        return super().next_update()
    
    def transition(self, transition: Transition):
        t = transition.timestamp
        output_levels, snapshot, scenario = transition.payload
        clock, reset, ce, le, *inputs = snapshot
        assert len(output_levels) == len(self.outputs)
        is_stable = True
        if scenario == 'reset':
            is_stable = (is_stable
                         and logic_level(reset) == HI
                         and reset.hold(t) >= self.tw)
        elif scenario == 'load':
            is_stable = (is_stable
                        and logic_level(le) == HI
                        and le.hold(t) >= self.th
                        and logic_level(clock) == HI
                        and clock.hold(t) >= self.tw)
            for input in inputs:
                is_stable = (is_stable
                            and input.hold(t) >= self.th)
        elif scenario == 'count':
            is_stable = (is_stable
                        and logic_level(ce) == HI
                        and ce.hold(t) >= self.th
                        and logic_level(clock) == HI
                        and clock.hold(t) >= self.tw)
        elif scenario == 'invalid':
            is_stable = False
        if is_stable:
            if all((o == HI for o in output_levels)):
                self.terminal_count.set(HI)
            elif all((o in [LO, HI] for o in output_levels)):
                self.terminal_count.set(LO)
            else:
                self.terminal_count.set(UNKNOWN)
            for o, l in zip(self.outputs, output_levels):
                o.set(l)
        else:
            self.terminal_count.set(UNKNOWN)
            for o, l in zip(self.outputs, output_levels):
                o.set(UNKNOWN)
