from typing import Optional

from .. import simulator as op
from ..simulator import State, Duration


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
        self.adder = op.Adder(inputs_a,
                              inputs_b,
                              cin,
                              tp or op.ns(46),  # worst @ 4.5V max 25c CL 50pF
                              tt or op.ns(15))  # @ 4.5V max 25c CL 50pF


# logic

class HC00_Nand:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 4
        assert len(inputs_b) == 4
        self.adder = op.Nand(inputs_a,
                             inputs_b,
                             tp or op.ns(9),  # worst @ 4.5V max 25c CL 50pF
                             tt or op.ns(7))  # @ 4.5V max 25c CL 50pF

class HC02_Nor:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 4
        assert len(inputs_b) == 4
        self.adder = op.Nor(inputs_a,
                            inputs_b,
                            tp or op.ns(18),  # worst @ 4.5V max 25c CL 50pF
                            tt or op.ns(15))  # @ 4.5V max 25c CL 50pF

class HC04_Inverter:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 6
        assert len(inputs_b) == 6
        self.adder = op.Inverter(inputs_a,
                                 inputs_b,
                                 tp or op.ns(17),  # worst @ 4.5V max 25c CL 50pF
                                 tt or op.ns(15))  # @ 4.5V max 25c CL 50pF

class HC08_And:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 4
        assert len(inputs_b) == 4
        self.adder = op.And(inputs_a,
                            inputs_b,
                            tp or op.ns(18),  # worst @ 4.5V max 25c CL 50pF
                            tt or op.ns(15))  # @ 4.5V max 25c CL 50pF

class HC32_Or:
    def __init__(self,
                 inputs_a: list[State],
                 inputs_b: list[State],
                 tp: Optional[Duration],
                 tt: Optional[Duration]):
        assert len(inputs_a) == 4
        assert len(inputs_b) == 4
        self.adder = op.Or(inputs_a,
                           inputs_b,
                           tp or op.ns(18),  # worst @ 4.5V max 25c CL 50pF
                           tt or op.ns(15))  # @ 4.5V max 25c CL 50pF
