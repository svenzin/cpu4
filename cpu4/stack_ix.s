    j begin

scratcha: .dw 0
scratchx: .dw 0

.align 16
s: .dw 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
is: ._s

.align 16
sp: .dw 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
isp: ._sp

begin:
    ; start with acc=2 x=1
    ld #2
    ldx #1

    ; push a x
    st scratcha
    stx scratchx

    st (is)  ; push a
    ld .@is_0
    add #1
    st .@is_0
    stx (is) ; push x
    ld .@is_0
    add #1
    st .@is_0

    ; push pc (computed by assembler)
    ld #._ret_0
    st (isp)
    ld .@isp_0
    add #1
    st .@isp_0
    ld #._ret_1
    st (isp)
    ld .@isp_0
    add #1
    st .@isp_0
    ld #._ret_2
    st (isp)
    ld .@isp_0
    add #1
    st .@isp_0

    ; call with parameters
    ld scratcha
    j foo

ret:
    ; pop x a
    ld .@is_0
    add #-1
    st .@is_0
    ldx (is)
    ld .@is_0
    add #-1
    st .@is_0
    ld (is)

    stop

check_foo: .dw 0 ; for validation
foo:
    ld #1       ; do work
    st check_foo
    ld .@isp_0     ; pre-decrement and jump back
    add #-3
    st .@isp_0
    j [isp]
