    j begin

scratcha: .dw 0
scratchx: .dw 0

s: .dw 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
is: .dw 0

.alias s0 s + 0
.alias s1 s+1
.alias s2 s+2
.alias s3 s+3
.alias s4 s+4

begin:
    ; start with acc=2 x=1
    ld #2
    ldx #1

    ; push a x
    st scratcha
    stx scratchx
    
    ldx is
    st s0+x  ; push a
    ld scratchx
    st s1+x  ; push x
    ld #._ret_0
    st s2+x
    ld #._ret_1
    st s3+x
    ld #._ret_2
    st s4+x
    addx #5
    stx is

    ; call with parameters
    ld scratcha
    ldx scratchx
    j foo

ret:
    ; pop x a
    ldx s1+x
    ld s0+x

    stop

check_foo: .dw 0 ; for validation
foo:
    ld #1       ; do work
    st check_foo
    ldx is     ; pre-decrement and jump back
    addx #-5
    stx is
    j (s2+x)
