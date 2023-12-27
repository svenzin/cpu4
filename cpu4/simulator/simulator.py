from typing import Optional
import math

# time
class Timestamp:
    def __init__(self, nanoseconds: int):
        self.t = nanoseconds
    
    def __iadd__(self, dt: 'Duration'):
        self.t += dt.d
        return self

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
UNDEFINED = 'U'

class System:
    def __init__(self, m=0.5) -> None:
        self.m = m
        self.clear()

    def register_element(self, element, name):
        assert name not in self.elements.keys()
        self.elements[name] = element
    
    def register_state(self, state, name):
        assert name not in self.states.keys()
        self.states[name] = state
    
    def clear(self):
        self.timestamp = Timestamp(0)
        self.elements = {}
        self.states = {}
    
    def update(self, dt: Duration):
        for element in self.elements.values():
            element.update(dt)
        self.timestamp += dt
    
    def step(self):
        dts = [element.next_update() for element in self.elements.values()]
        current_dt = min((dt.d for dt in dts if dt is not None))
        self.update(Duration(current_dt))

class State:
    def __init__(self) -> None:
        self.value = UNDEFINED
        self.is_driving = False
    
    def set(self, value, drive=False):
        self.is_driving = drive
        self.value = value
    
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
        assert 0 < duty < 1
        assert 0 <= phase < 360
        self.f = f
        self.p = f.to_duration()
        self.tt = tt or s(0)
        self.t_hi = duty * self.p
        self.t_lo = (1 - duty) * self.p
        self.clock = State()
        # apply phase using updates
        end_tmh = (1 - system.m) * self.tt
        end_hi = self.t_hi - (1 - system.m) * self.tt
        end_thm = self.t_hi
        end_tml = self.t_hi + system.m * self.tt
        end_lo = self.t_hi + self.t_lo - system.m * self.tt
        end_tlm = self.t_hi + self.t_lo
        self.dt = (1 - phase / 360) * self.p
        if self.dt <= end_tmh:
            self.dt = end_tmh - self.dt
            self.clock.set(TMH, True)
        elif self.dt <= end_hi:
            self.dt = end_hi - self.dt
            self.clock.set(HI, True)
        elif self.dt <= end_thm:
            self.dt = end_thm - self.dt
            self.clock.set(THM, True)
        elif self.dt <= end_tml:
            self.dt = end_tml - self.dt
            self.clock.set(TML, True)
        elif self.dt <= end_lo:
            self.dt = end_lo - self.dt
            self.clock.set(LO, True)
        elif self.dt <= end_tlm:
            self.dt = end_tlm - self.dt
            self.clock.set(TLM, True)
        assert self.dt >= Duration(0)
        assert self.clock.value in [TMH, HI, THM, TML, LO, TLM]
        system.register_element(self, 'clock')
        system.register_state(self.clock, 'clock.clock')

    def next_update(self):
        return self.dt

    def update(self, dt: Duration):
        assert dt <= self.dt
        self.dt -= dt
        while self.dt <= s(0):
            if self.clock.value == LO:
                self.clock.set(TLM, True)
                self.dt += self.tt * system.m
            elif self.clock.value == TLM:
                self.clock.set(TMH, True)
                self.dt += self.tt * (1 - system.m)
            elif self.clock.value == TMH:
                self.clock.set(HI, True)
                self.dt += self.t_hi - self.tt
            elif self.clock.value == HI:
                self.clock.set(THM, True)
                self.dt += self.tt * (1 - system.m)
            elif self.clock.value == THM:
                self.clock.set(TML, True)
                self.dt += self.tt * system.m
            elif self.clock.value == TML:
                self.clock.set(LO, True)
                self.dt += self.t_lo - self.tt
            else:
                assert False

class Buffer:
    def __init__(self, input: State, tp: Duration, tt: Duration):
        assert tt < tp
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
            if self.previous_output == UNDEFINED:
                # Initialization is "free"
                self.transitions.append((output, Duration(0)))
            elif output == LO:
                self.transitions.append((THM, self.tp - (1 - system.m) * self.tt))
                self.transitions.append((TML, self.tp))
                self.transitions.append((LO, self.tp + system.m * self.tt))
            elif output == HI:
                self.transitions.append((TLM, self.tp - (1 - system.m) * self.tt))
                self.transitions.append((TMH, self.tp))
                self.transitions.append((HI, self.tp + system.m * self.tt))
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
        assert tt < tp
        self.tp = tp
        self.tt = tt
        
        self.input = input
        
        self.output = State()
        self.output.set(UNDEFINED, True)
        self.previous_output = UNDEFINED
        
        self.transitions = []

        system.register_element(self, 'inverter')
        system.register_state(self.output, 'inverter.output')

    def next_update(self):
        i = self.input.logic_level()
        output = LO if i == HI else HI
        if self.previous_output != output:
            if output == LO:
                # Initialization is "free"
                if self.previous_output == UNDEFINED:
                    self.transitions.append((LO, Duration(0)))
                else:
                    self.transitions.append((THM, self.tp - (1 - system.m) * self.tt))
                    self.transitions.append((TML, self.tp))
                    self.transitions.append((LO, self.tp + system.m * self.tt))
            elif output == HI:
                # Initialization is "free"
                if self.previous_output == UNDEFINED:
                    self.transitions.append((HI, Duration(0)))
                else:
                    self.transitions.append((TLM, self.tp - (1 - system.m) * self.tt))
                    self.transitions.append((TMH, self.tp))
                    self.transitions.append((HI, self.tp + system.m * self.tt))
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


class And:
    def __init__(self, input_a: State, input_b: State, tp: Duration, tt: Duration):
        assert tt < tp
        self.tp = tp
        self.tt = tt
        
        self.a = input_a
        self.b = input_b
        
        self.output = State()
        self.output.set(UNDEFINED, True)
        self.previous_output = UNDEFINED
        
        self.transitions = []

        system.register_element(self, 'inverter')
        system.register_state(self.output, 'inverter.output')

    def next_update(self):
        a = self.a.logic_level()
        b = self.b.logic_level()
        output = HI if a == HI and b == HI else LO
        if self.previous_output != output:
            if output == LO:
                # Initialization is "free"
                if self.previous_output == UNDEFINED:
                    self.transitions.append((LO, Duration(0)))
                else:
                    self.transitions.append((THM, self.tp - (1 - system.m) * self.tt))
                    self.transitions.append((TML, self.tp))
                    self.transitions.append((LO, self.tp + system.m * self.tt))
            elif output == HI:
                # Initialization is "free"
                if self.previous_output == UNDEFINED:
                    self.transitions.append((HI, Duration(0)))
                else:
                    self.transitions.append((TLM, self.tp - (1 - system.m) * self.tt))
                    self.transitions.append((TMH, self.tp))
                    self.transitions.append((HI, self.tp + system.m * self.tt))
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

class ThreeState(Buffer):
    def __init__(self, input: State, n_oe: State, t_en: Duration, t_dis: Duration):
        self.input = input

        self.previous_n_oe = UNDEFINED
        self.n_oe = n_oe
        self.t_en = t_en
        self.t_dis = t_dis
        
        self.output_enabled = False
        self.output = State()
        self.output.set(UNDEFINED, True)
        
        self.transitions = []

        system.register_element(self, '3s')
        system.register_state(self.output, '3s.output')

    def append(self, output_enabled, dt):
        while len(self.transitions) > 0 and self.transitions[-1][1] > dt:
            self.transitions.pop()
        self.transitions.append((output_enabled, dt))

    def next_update(self):
        n_oe = self.n_oe.logic_level()
        if self.previous_n_oe != n_oe:
            if n_oe == HI:
                if self.previous_n_oe == UNDEFINED:
                    self.append(False, Duration(0))
                else:
                    self.append(False, self.t_dis)
            elif n_oe == LO:
                if self.previous_n_oe == UNDEFINED:
                    self.append(True, Duration(0))
                else:
                    self.append(True, self.t_en)
            else:
                assert False
            self.previous_n_oe = n_oe
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
        if self.output_enabled:
            self.output.set(self.input.value, True)
        else:
            self.output.set(Z, False)

class Buffer3S:
    def __init__(self, input: State, tp: Duration, tt: Duration, n_oe: State, t_en: Duration, t_dis: Duration):
        self.buffer = Buffer(input, tp, tt)
        self.three_state = ThreeState(self.buffer.output, n_oe, t_en, t_dis)
        self.output = self.three_state.output
