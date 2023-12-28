from typing import Optional
import math

# time
class Timestamp:
    def __init__(self, nanoseconds: int):
        self.t = nanoseconds
    
    def __repr__(self):
        return f'Timestamp({repr(self.t / 1e9)})'
    
    def __iadd__(self, dt: 'Duration'):
        self.t += dt.d
        return self
    
    def __le__(self, other):
        return self.t <= other.t

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
        for element in self.elements.values():
            element.update(dt)
        self.timestamp += dt
    
    def step(self):
        current_dt = self.next_update()
        if current_dt is not None:
            self.update(current_dt)
        return current_dt

class State:
    def __init__(self) -> None:
        self.timeline = []
        self.set(UNDEFINED, False)
        
    def __repr__(self):
        return f'State({repr(self.value)}, {repr(self.is_driving)})'

    def set(self, value, drive=False):
        self.is_driving = drive
        self.value = value
        if len(self.timeline) > 0:
            assert self.timeline[-1][0] <= system.timestamp
        self.timeline.append((system.timestamp, self.value, self.is_driving))
    
    def logic_level(self):
        if self.value in [LO, TLM, TML]:
            return LO
        if self.value in [HI, THM, TMH]:
            return HI
        return self.value
system = System()

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
        self.f = f
        self.p = f.to_duration()
        self.tt = tt or s(0)
        self.t_hi = duty * self.p
        self.t_lo = (1 - duty) * self.p
        self.clock = State()
        # apply phase using updates
        end_hi = self.t_hi
        end_lo = self.t_hi + self.t_lo
        self.dt = (1 - phase / 360) * self.p
        if self.dt <= end_hi:
            self.dt = end_hi - self.dt
            self.clock.set(HI, True)
        elif self.dt <= end_lo:
            self.dt = end_lo - self.dt
            self.clock.set(LO, True)
        assert self.dt >= Duration(0)
        assert self.clock.value in [HI, LO]
        system.register_element(self, 'clock')
        system.register_state(self.clock, 'clock.clock')

    def next_update(self):
        return self.dt

    def update(self, dt: Duration):
        assert dt <= self.dt
        self.dt -= dt
        if self.dt <= s(0):
            if self.clock.value == LO:
                self.clock.set(HI, True)
                self.dt += self.t_hi
            elif self.clock.value == HI:
                self.clock.set(LO, True)
                self.dt += self.t_lo
            else:
                assert False

class Buffer:
    def __init__(self, input: State, tp: Duration, tt: Duration):
        assert tt <= tp
        self.tp = tp
        self.tt = tt
        
        self.input = input
        
        self.output = State()
        self.output.set(UNDEFINED, True)
        self.previous_output = UNDEFINED
        
        self.transitions = []

        system.register_element(self, 'buffer')
        system.register_state(self.output, 'buffer.output')

    def next_update(self):
        output = self.input.logic_level()
        if self.previous_output != output:
            if self.previous_output == UNDEFINED and output in [LO, HI, UNKNOWN]:
                # Initialization is "free"
                self.transitions.append((output, Duration(0)))
            elif output == LO:
                self.transitions.append((LO, self.tp))
            elif output == HI:
                self.transitions.append((HI, self.tp))
            elif output == UNKNOWN:
                self.transitions.append((UNKNOWN, self.tp))
            else:
                assert False
            self.previous_output = output
        if len(self.transitions) > 0:
            _, dt = self.transitions[0]
            return dt
        else:
            return None
    
    def update(self, dt: Duration):
        if len(self.transitions) == 0:
            return
        transitions = []
        for value, dt_transition in self.transitions:
            assert dt <= dt_transition
            dt_transition -= dt
            if dt_transition <= Duration(0):
                self.output.set(value, True)
            else:
                transitions.append((value, dt_transition))
        self.transitions = transitions


class Not:
    def __init__(self, input: State, tp: Duration, tt: Duration):
        self.input = input
        self._output = State()
        self._buffer = Buffer(self._output, tp, tt)
        self.output = self._buffer.output

        system.register_element(self, 'inverter')
        system.register_state(self.output, 'inverter.output')

    def next_update(self):
        i = self.input.logic_level()
        output = LO if i == HI else HI
        self._output.set(output, True)
        return self._buffer.next_update()
    
    def update(self, dt: Duration):
        return None


class BinaryOp:
    def __init__(self, op_table, input_a: State, input_b: State, tp: Duration, tt: Duration):
        self.op = op_table

        self.a = input_a
        self.b = input_b
        
        self._output = State()
        self._buffer = Buffer(self._output, tp, tt)
        self.output = self._buffer.output

        system.register_element(self, 'binop')
        system.register_state(self.output, 'binop.output')

    def next_update(self):
        a = self.a.logic_level()
        b = self.b.logic_level()
        try:
            output = self.op[a, b]
        except KeyError:
            output = UNKNOWN
        self._output.set(output, True)
        return self._buffer.next_update()
    
    def update(self, dt: Duration):
        return

class And(BinaryOp):
    def __init__(self, input_a: State, input_b: State, tp: Duration, tt: Duration):
        super().__init__({(LO, LO): LO,
                          (LO, HI): LO,
                          (HI, LO): LO,
                          (HI, HI): HI}, input_a, input_b, tp, tt)

class Or(BinaryOp):
    def __init__(self, input_a: State, input_b: State, tp: Duration, tt: Duration):
        super().__init__({(LO, LO): LO,
                          (LO, HI): HI,
                          (HI, LO): HI,
                          (HI, HI): HI}, input_a, input_b, tp, tt)

class Decoder:
    def __init__(self, inputs: list[State], en: State, tp_data: Duration, tp_en: Duration, tt: Duration):
        self.inputs = inputs

        self.output_count = 2 ** len(inputs)
        self._outputs = [State() for _ in range(self.output_count)]
        
        self._buffers = [Buffer(o, tp_data, tt) for o in self._outputs]

        disabled = State()
        disabled.set(LO, True)
        self._enablers = [Enabler(b.output, en, tp_en, tp_en, tt, tt, disabled) for b in self._buffers]
        
        self.outputs = [e.output for e in self._enablers]
    
        system.register_element(self, 'decoder')
        for o in self.outputs:
            system.register_state(o, 'decoder.output')

    def next_update(self):
        inputs = [i.logic_level() for i in self.inputs]
        try:
            value_map = {LO: 0, HI: 1}
            index = sum((2 ** i * value_map[value] for i, value in enumerate(inputs)))
        except KeyError:
            index = None
        if index is None:
            for o in self._outputs:
                o.set(UNKNOWN, True)
        else:
            for i, o in enumerate(self._outputs):
                if i == index:
                    o.set(HI, True)
                else:
                    o.set(LO, True)
        dt_buffers = [b.next_update() for b in self._buffers]
        dt_enablers = [e.next_update() for e in self._enablers]
        return min([dt for dt in dt_buffers + dt_enablers if dt is not None], default=None)
    
    def update(self, dt: Duration):
        return

class Enabler:
    def __init__(self, input: State, en: State, tp_en: Duration, tp_dis: Duration, tt_en: Duration, tt_dis: Duration, disabled: State):
        self.input = input

        self.en = en
        self.previous_en = UNDEFINED
        
        self.tp_en = tp_en
        self.tp_dis = tp_dis
        self.tt_en = tt_en
        self.tt_dis = tt_dis
        
        self.output_enabled = None
        self.output = State()
        self.output.set(UNDEFINED, True)
        
        self.disabled_state = disabled
        
        self.transitions = []

        system.register_element(self, 'enabler')
        system.register_state(self.output, 'enabler.output')

    def append(self, output_enabled, dt):
        while len(self.transitions) > 0 and self.transitions[-1][1] > dt:
            self.transitions.pop()
        self.transitions.append((output_enabled, dt))

    def next_update(self):
        en = self.en.logic_level()
        if self.previous_en != en:
            if en == HI:
                if self.previous_en == UNDEFINED:
                    self.append(True, Duration(0))
                else:
                    self.append(True, self.tp_en)
            elif en == LO:
                if self.previous_en == UNDEFINED:
                    self.append(False, Duration(0))
                else:
                    self.append(False, self.tp_dis)
            else:
                if self.previous_en == UNDEFINED:
                    self.append(None, Duration(0))
                elif self.previous_en == LO:
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
            self.output.set(UNKNOWN, True)
        elif self.output_enabled:
            self.output.set(self.input.value, True)
        else:
            self.output.set(self.disabled_state.value, False)

class Buffer3S:
    def __init__(self, input: State, tp: Duration, tt: Duration, en: State, t_en: Duration, t_dis: Duration):
        self.buffer = Buffer(input, tp, tt)
        self.disabled = State()
        self.disabled.set(Z)
        self.enabler = Enabler(self.buffer.output, en, t_en, t_dis, tt, tt, self.disabled)
        self.output = self.enabler.output
