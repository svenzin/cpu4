from typing import Optional

# time
class Duration:
    def __init__(self, seconds: float) -> None:
        self.d = seconds

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

def hz(f: float):
    return Frequency(f)

def khz(f: float):
    return hz(1e3 * f)

def mhz(f: float):
    return hz(1e6 * f)

# conversions
def to_duration(f: Frequency):
    return Duration(1.0 / f.f)

def to_frequency(d: Duration):
    return Frequency(1.0 / d.d)

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
        self.elements = {}
        self.states = {}

    def register_element(self, element, name):
        assert name not in self.elements.keys()
        self.elements[name] = element
    
    def register_state(self, state, name):
        assert name not in self.states.keys()
        self.states[name] = state
    
    def clear(self):
        self.elements = {}
        self.states = {}
    
    def update(self, dt: Duration):
        for element in self.elements.values():
            element.update(dt)

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
        self.t = to_duration(f)
        self.dt = 0#self.t.d
        self.clock = State()
        self.clock.set(LO, True)
        system.register_element(self, 'clock')
        system.register_state(self.clock, 'clock.clock')

    def next_update(self):
        return self.dt

    def update(self, dt: Duration):
        assert dt.d <= self.dt
        self.dt -= dt.d
        while self.dt <= 0:
            if self.clock.value == LO:
                self.clock.set(Tr, True)
                self.dt += self.t_rise.d
            elif self.clock.value == Tr:
                self.clock.set(HI, True)
                self.dt += self.t.d - self.t_rise.d
            elif self.clock.value == HI:
                self.clock.set(Tf, True)
                self.dt += self.t_fall.d
            elif self.clock.value == Tf:
                self.clock.set(LO, True)
                self.dt += self.t.d - self.t_fall.d
            else:
                assert False
