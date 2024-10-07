from typing import Optional

from .. import simulator as op
from ..simulator import State, Duration


from typing import Optional

from .. import simulator as op
from ..simulator import State, Duration

################################################################################
# adder


class HC283_Adder:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 cin: State,
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 4
        assert len(inputs_b) == 4
        self._adder = op.Adder(inputs_a,
                               inputs_b,
                               cin,
                               tp or op.ns(46),  # worst @ 4.5V max 25c CL 50pF
                               tt or op.ns(15))  # @ 4.5V max 25c CL 50pF
        self.outputs = self._adder.outputs
        self.cout = self._adder.cout


################################################################################
# logic


class HC00_Nand:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 4
        assert len(inputs_b) == 4
        self._op = op.Nand(inputs_a,
                           inputs_b,
                           tp or op.ns(9),  # worst @ 4.5V max 25c CL 50pF
                           tt or op.ns(7))  # @ 4.5V max 25c CL 50pF
        self.outputs = self._op.outputs


class HC02_Nor:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 4
        assert len(inputs_b) == 4
        self._op = op.Nor(inputs_a,
                          inputs_b,
                          tp or op.ns(18),  # worst @ 4.5V max 25c CL 50pF
                          tt or op.ns(15))  # @ 4.5V max 25c CL 50pF
        self.outputs = self._op.outputs


class HC04_Inverter:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 6
        assert len(inputs_b) == 6
        self._op = op.Inverter(inputs_a,
                               inputs_b,
                               tp or op.ns(17),  # worst @ 4.5V max 25c CL 50pF
                               tt or op.ns(15))  # @ 4.5V max 25c CL 50pF
        self.outputs = self._op.outputs


class HC08_And:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 4
        assert len(inputs_b) == 4
        self._op = op.And(inputs_a,
                          inputs_b,
                          tp or op.ns(18),  # worst @ 4.5V max 25c CL 50pF
                          tt or op.ns(15))  # @ 4.5V max 25c CL 50pF
        self.outputs = self._op.outputs


class HC32_Or:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 4
        assert len(inputs_b) == 4
        self._op = op.Or(inputs_a,
                         inputs_b,
                         tp or op.ns(18),  # worst @ 4.5V max 25c CL 50pF
                         tt or op.ns(15))  # @ 4.5V max 25c CL 50pF
        self.outputs = self._op.outputs


################################################################################
# memory


class HC161_Counter:
    def __init__(self,
                 inputs: list[State],
                 count_enable: State,
                 count_enable_carry: State,
                 n_load: State,
                 n_reset: State,
                 clock: State,
                 tp: Optional[Duration],
                 tt: Optional[Duration],
                 tw: Optional[Duration],
                 tr: Optional[Duration],
                 ts: Optional[Duration],
                 th: Optional[Duration]) -> None:
        assert len(inputs) == 4
        d0 = Duration(0)
        self._reset = op.Inverter(n_reset, d0, d0)
        self._load = op.Inverter(n_load, d0, d0)
        self._count = op.And(count_enable,
                             count_enable_carry,
                             d0, d0)
        self._counter = op.BinaryCounter(inputs,
                                         clock,
                                         self._reset,
                                         self._count,
                                         self._load,
                                         # worst @ 4.5V max 25c CL 50pF
                                         tp or op.ns(44),   # /MR to TC
                                         tt or op.ns(15),   #
                                         tw or op.ns(16),   #
                                         tr or op.ns(20),   #
                                         ts or op.ns(34),   # CEP, CET to CLK
                                         th or op.ns(5))    # -5 ns
        self.outputs = self._counter.outputs
        self.terminal_count = self._counter.terminal_count


class HC244_Buffer:
    def __init__(self,
                 inputs_a: list[State],
                 n_output_enable_a: State,
                 inputs_b: list[State],
                 n_output_enable_b: State,
                 tp: Optional[Duration],
                 tt: Optional[Duration]) -> None:
        d0 = Duration(0)
        assert len(inputs_a) == 4
        self._oe_a = op.Inverter(n_output_enable_a, d0, d0)
        self._buffers_a = [op.Buffer3S(i, tp, tt, self._oe_a, d0) for i in inputs_a]
        self.outputs_a = [b.output for b in self._buffers_a]
        assert len(inputs_b) == 4
        self._oe_b = op.Inverter(n_output_enable_b, d0, d0)
        self._buffers_b = [op.Buffer3S(i, tp, tt, self._oe_b, d0) for i in inputs_b]
        self.outputs_b = [b.output for b in self._buffers_b]


class HC173_Register:
    def __init__(self,
                 inputs: list[State],
                 n_enable_1: State,
                 n_enable_2: State,
                 n_output_enable_1: State,
                 n_output_enable_2: State,
                 reset: State,
                 clock: State,
                 tp: Optional[Duration],
                 tt: Optional[Duration],
                 tw: Optional[Duration],
                 tr: Optional[Duration],
                 ts: Optional[Duration],
                 th: Optional[Duration],
                 t_en: Optional[Duration]) -> None:
        d0 = Duration(0)
        assert len(inputs) == 4
        self._enable = op.Nor(n_enable_1,
                              n_enable_2,
                              d0, d0)
        self._output_enable = op.Nor(n_output_enable_1,
                                     n_output_enable_2,
                                     d0, d0)
        self._register = op.DtypeFlipFlop(inputs,
                                          clock,
                                          reset,
                                          self._enable,
                                          # worst @ 4.5V max 25c CL 50pF
                                          tp or op.ns(35), #
                                          tt or op.ns(12), #
                                          tw or op.ns(16), #
                                          tr or op.ns(12), #
                                          ts or op.ns(20), # /EN to CLK
                                          th or op.ns(1)) # Dn to CLK
        # TODO
        # Handle t_en properly
        self._3s = [op.OutputEnabler(o, self._output_enable, d0, d0) for o in self._register.outputs]
        self.outputs = [o.output for o in self._3s]
