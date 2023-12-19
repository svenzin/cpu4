    lea begin
    j

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
    lea #2
    ld
    lea #1
    ldx

    ; push a x
    lea scratcha
    st
    lea scratchx
    stx
    
    lea is
    ldx
    lea s0+x  ; push a
    st
    lea scratchx
    ld
    lea s1+x  ; push x
    st
    lea #._ret_0 ; push pc
    ld
    lea s2+x
    st
    lea #._ret_1
    ld
    lea s3+x
    st
    lea #._ret_2
    ld
    lea s4+x
    st
    lea #5
    addx
    lea is
    stx

    ; call with parameters
    lea scratcha
    ld
    lea scratchx
    ldx
    lea foo
    j

ret:
    ; pop x a
    lea s1+x
    ldx
    lea s0+x
    ld

    stop

check_foo: .dw 0 ; for validation
foo:
    lea #1       ; do work
    ld
    lea check_foo
    st
    lea is     ; pre-decrement and jump back
    ldx
    lea #-5
    addx
    lea is
    stx
    lea (s2+x)
    j
