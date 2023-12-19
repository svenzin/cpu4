j begin

.align 16
fibo: .dw 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0

zero: .dw 0
one: .dw 1

next: .@ fibo

n0: .dw 0
n1: .dw 1
n2: .dw 0

begin:
    ld zero
    st (next)

    ld one
    st .@next_0
    st (next)
    add one
    st .@next_0

fibloop:
    ld n0
    st n2
    ld n1
    st n0
    add n2
    st n1

    st (next)
    ld .@next_0
    add one
    st .@next_0

    jc fibdone
    j fibloop

fibdone:
    stop
