from typing import Optional
import math
import itertools

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

class BaseState:
    def __init__(self, value, drive):
        self.value = value
        self.is_driving = drive

    def __repr__(self):
        return f'BaseState({repr(self.value)}, {repr(self.is_driving)})'
    
    def logic_level(self):
        if self.value in [LO, TLM, TML]:
            return LO
        if self.value in [HI, THM, TMH]:
            return HI
        return self.value

class State(BaseState):
    def __init__(self, value=UNDEFINED, drive=False):
        self.timeline = []
        self.set(value, drive)
        
    def __repr__(self):
        return f'State({repr(self.value)}, {repr(self.is_driving)})'

    def set(self, value, drive=False):
        self.is_driving = drive
        self.value = value
        if len(self.timeline) > 0:
            assert self.timeline[-1][0] <= system.timestamp
        self.timeline.append((system.timestamp, self.value, self.is_driving))

STATE_UNDEFINED = BaseState(UNDEFINED, False)
STATE_LO = BaseState(LO, True)
STATE_HI = BaseState(HI, True)
STATE_Z = BaseState(Z, False)
STATE_UNKOWN = BaseState(UNKNOWN, True)

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
        period = f.to_duration()
        self.tt = tt or s(0)
        self.t_hi = duty * period
        self.t_lo = (1 - duty) * period
        self.clock = State()
        dt_phase = phase / 360 * period
        if dt_phase == Duration(0):
            self.dt = self.t_hi
            self.clock.set(HI, True)
        elif dt_phase <= self.t_lo:
            self.dt = dt_phase
            self.clock.set(LO, True)
        else:
            self.dt = dt_phase - self.t_lo
            assert self.dt <= self.t_hi
            self.clock.set(HI, True)
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

class Operator:
    def __init__(self, inputs: list[State], op: dict[tuple, tuple], tp: Duration, tt: Duration, name='operator'):
        assert tt <= tp
        self.tp = tp
        self.tt = tt
        
        self.input_count = len(inputs)
        assert all(self.input_count == len(o) for o in op.keys())
        self.inputs = inputs

        self.op = op

        self.output_count = len(next(iter(op.values())))
        assert all(self.output_count == len(o) for o in op.values())
        self.outputs = [State() for _ in range(self.output_count)]
        self.previous_outputs = UNDEFINED
        
        self.transitions = []

        system.register_element(self, name)
        for o in self.outputs:
            system.register_state(o, f'{name}.output')

    def next_update(self):
        inputs = tuple((i.logic_level() for i in self.inputs))
        if any((i != UNDEFINED for i in inputs)) or self.previous_outputs != UNDEFINED:
            try:
                outputs = self.op[inputs]
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
                    output.set(value, True)
            else:
                transitions.append((values, dt_transition))
        self.transitions = transitions

class StateOperator:
    def __init__(self, inputs: list[State], op: dict[tuple, tuple], tp: Duration, tt: Duration, name='operator'):
        assert tt <= tp
        self.tp = tp
        self.tt = tt
        
        self.input_count = len(inputs)
        assert all(self.input_count == len(o) for o in op.keys())
        self.inputs = inputs

        self.op = op

        self.output_count = len(next(iter(op.values())))
        assert all(self.output_count == len(o) for o in op.values())
        self.outputs = [State() for _ in range(self.output_count)]
        self.previous_outputs = UNDEFINED
        
        self.transitions = []

        system.register_element(self, name)
        for o in self.outputs:
            system.register_state(o, f'{name}.output')

    def next_update(self):
        inputs = tuple((i.logic_level() for i in self.inputs))
        if (self.previous_outputs != UNDEFINED
            or len(inputs) == 0
            or any((i != UNDEFINED for i in inputs))):
            try:
                outputs = self.op[inputs]
            except KeyError:
                outputs = self.output_count * [STATE_UNKOWN]
            if self.previous_outputs != outputs:
                self.transitions.append((outputs, self.tp))
                self.previous_outputs = tuple((o.logic_level() for o in outputs))
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
                    output.set(value.value, value.is_driving)
            else:
                transitions.append((values, dt_transition))
        self.transitions = transitions

class Buffer(Operator):
    def __init__(self, input: State, tp: Duration, tt: Duration):
        super().__init__([input], {(LO,): (LO,),
                                   (HI,): (HI,)}, tp, tt, 'buffer')
        self.output = self.outputs[0]

class Inverter(Operator):
    def __init__(self, input: State, tp: Duration, tt: Duration):
        super().__init__([input], {(LO,): (HI,),
                                   (HI,): (LO,)}, tp, tt, 'inverter')
        self.output = self.outputs[0]

class And(Operator):
    def __init__(self, input_a: State, input_b: State, tp: Duration, tt: Duration):
        super().__init__([input_a, input_b], {(LO, LO): (LO,),
                                              (LO, HI): (LO,),
                                              (HI, LO): (LO,),
                                              (HI, HI): (HI,)}, tp, tt, 'and')
        self.output = self.outputs[0]

class Or(Operator):
    def __init__(self, input_a: State, input_b: State, tp: Duration, tt: Duration):
        super().__init__([input_a, input_b], {(LO, LO): (LO,),
                                              (LO, HI): (HI,),
                                              (HI, LO): (HI,),
                                              (HI, HI): (HI,)}, tp, tt, 'or')
        self.output = self.outputs[0]

class MuxerDemuxer:
    def __init__(self, i_sel: list[State], inputs: list[State], o_sel: list[State], tp: Duration, tt: Duration):
        mux_map = {}
        coordinates = len(i_sel) * [[LO, HI]]
        for index, input in enumerate(itertools.product(*coordinates)):
            mux_map[input] = [inputs[index]]
        # selection bits need to be reversed because of the way itertools.product produces items
        self.muxer = StateOperator(list(reversed(i_sel)), mux_map, tp, tt, 'muxer_demuxer.muxer')

        demux_map = {}
        coordinates = len(o_sel) * [[LO, HI]]
        for index, input in enumerate(itertools.product(*coordinates)):
            output = 2 ** len(o_sel) * [STATE_LO]
            output[index] = self.muxer.outputs[0]
            demux_map[input] = output
        # selection bits need to be reversed because of the way itertools.product produces items
        self.demuxer = StateOperator(list(reversed(o_sel)), demux_map, tp, tt, 'muxer_demuxer.demuxer')

        self.outputs = self.demuxer.outputs

class DecoderBase(Operator):
    def __init__(self, inputs: list[State], tp: Duration, tt: Duration):
        self.input_count = len(inputs)
        self.output_count = 2 ** self.input_count
        
        decoder_map = {}
        coordinates = self.input_count * [[LO, HI]]
        for index, input in enumerate(itertools.product(*coordinates)):
            output = self.output_count * [LO]
            output[index] = HI
            decoder_map[input] = output

        super().__init__(inputs, decoder_map, tp, tt, 'decoder')

class Decoder(DecoderBase):
    def __init__(self, inputs: list[State], en: State, tp_data: Duration, tp_en: Duration, tt: Duration):
        self.decoder = DecoderBase(inputs, tp_data, tt)
        self.enablers = [Enabler(o, en, tp_en, tp_en, tt, tt, STATE_LO) for o in self.decoder.outputs]
        self.outputs = [e.output for e in self.enablers]

class Enabler:
    def __init__(self, input: State, en: State, tp_en: Duration, tp_dis: Duration, tt_en: Duration, tt_dis: Duration, disabled: BaseState):
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
        self.output = State()
        
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
            self.output.set(UNKNOWN, True)
        elif self.output_enabled:
            self.output.set(self.input.value, True)
        else:
            self.output.set(self.disabled_state.value, False)

class Buffer3S:
    def __init__(self, input: State, tp: Duration, tt: Duration, en: State, t_en: Duration, t_dis: Duration):
        self.buffer = Buffer(input, tp, tt)
        self.enabler = Enabler(self.buffer.output, en, t_en, t_dis, tt, tt, STATE_Z)
        self.output = self.enabler.output
