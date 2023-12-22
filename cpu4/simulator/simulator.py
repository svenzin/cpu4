from typing import Optional

# time
class Timestamp:
    def __init__(self, seconds: float):
        self.t = seconds
    
    def __iadd__(self, dt: 'Duration'):
        self.t += dt.d
        return self

class Duration:
    def __init__(self, seconds: float) -> None:
        self.d = seconds
    
    def to_frequency(self) -> 'Frequency':
        return Frequency(1.0 / self.d)
    
    def __sub__(self, other: 'Duration'):
        return Duration(self.d - other.d)
    
    def __iadd__(self, other: 'Duration'):
        self.d += other.d
        return self

    def __eq__(self, other):
        return self.d == other.d

    def __lt__(self, other):
        return self.d < other.d

    def __le__(self, other):
        return self.d <= other.d

def s(t: float):
    return Duration(t)

def ms(t: float):
    return s(1e-3 * t)

def us(t: float):
    return s(1e-6 * t)

def ns(t: float):
    return s(1e-9 * t)

# frequency
class Frequency:
    def __init__(self, hertz: float) -> None:
        self.f = hertz
    
    def to_duration(self) -> Duration:
        return Duration(1.0 / self.f)

def hz(f: float):
    return Frequency(f)

def khz(f: float):
    return hz(1e3 * f)

def mhz(f: float):
    return hz(1e6 * f)

# bases
LO = 0
HI = 1
Z = 'Z'
T = 'T'
Tr = 'Tr'
Tf = 'Tf'
UNDEFINED = 'U'

class System:
    def __init__(self) -> None:
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
        current_dt = min((element.next_update().d for element in self.elements.values()))
        self.update(Duration(current_dt))

class State:
    def __init__(self) -> None:
        self.value = 'U'
        self.is_driving = False
    
    def set(self, value, drive=False):
        self.is_driving = drive
        self.value = value
system = System()

# clock
class Clock:
    def __init__(self,
                 f: Frequency,
                 t_rise: Optional[Duration]=None,
                 t_fall: Optional[Duration]=None) -> None:
        self.f = f
        self.t_rise = t_rise or s(0)
        self.t_fall = t_fall or s(0)
        self.t = f.to_duration()
        self.dt = Duration(0)
        self.clock = State()
        self.clock.set(LO, True)
        system.register_element(self, 'clock')
        system.register_state(self.clock, 'clock.clock')

    def next_update(self):
        return self.dt

    def update(self, dt: Duration):
        assert dt <= self.dt
        self.dt -= dt
        while self.dt <= s(0):
            if self.clock.value == LO:
                self.clock.set(Tr, True)
                self.dt += self.t_rise
            elif self.clock.value == Tr:
                self.clock.set(HI, True)
                self.dt += self.t - self.t_rise
            elif self.clock.value == HI:
                self.clock.set(Tf, True)
                self.dt += self.t_fall
            elif self.clock.value == Tf:
                self.clock.set(LO, True)
                self.dt += self.t - self.t_fall
            else:
                assert False
