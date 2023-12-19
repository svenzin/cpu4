    j begin

scratcha: .dw 0
scratchx: .dw 0

s: .dw 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
is: .dw 0

begin:
    ; start with acc=2 x=1
    ld #2
    ldx #1

    ; push a
    stx scratchx
    ldx is
    st s+x
    addx #1
    stx is
    ldx scratchx

    ; push x
    swapax
    ; push a
    stx scratchx
    ldx is
    st s+x
    addx #1
    stx is
    ldx scratchx
    swapax

    ; push pc (computed by assembler)
    st scratcha
    stx scratchx

    ; push ret[0]
    ld #._ret_0
    ldx is
    st s+x
    addx #1
    stx is

    ; push ret[1]
    ld #._ret_1
    ldx is
    st s+x
    addx #1
    stx is

    ; push ret[2]
    ld #._ret_2
    ldx is
    st s+x
    addx #1
    stx is

    ldx scratchx
    ld scratcha

    ; call with parameters a, x
    j foo

ret:
    ; pop x
    ldx is
    addx #-1
    stx is
    ldx s+x

    ; pop a
    swapax
    ldx is
    addx #-1
    stx is
    ldx s+x
    swapax

    stop

check_foo: .dw 0 ; for validation
foo:
    ld #1       ; do work
    st check_foo
    ldx is     ; pre-decrement and jump back
    addx #-3
    stx is
    j (s+x)
