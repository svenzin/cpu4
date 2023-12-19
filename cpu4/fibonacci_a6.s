j begin

.align 16
fibo: .dw 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0

zero: .dw 0
one: .dw 1

next: .@ fibo

n0: .dw 0
n1: .dw 1

begin:
    ld n0
    st (next)

    ldx #1 ; ldx one
    stx .@next_0

    ld n1
    st (next)

fibloop:
    addx #1 ; addx one
    jc fibdone
    stx .@next_0

    add n0
    st n0
    st (next)

    addx #1 ; addx one
    ; jc fibdone
    stx .@next_0

    add n1
    st n1
    st (next)

    j fibloop

fibdone:
    stop
