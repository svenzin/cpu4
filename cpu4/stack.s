    j begin

one: .1
two: .2
three: .3

stack: . 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
stack_x: .0

stackp: . 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
stackp_x: .0

stack_tmp: .0

begin:
    ; start with acc=2 x=1
    ld one
    swapax
    ld two

    ; push x
    ; push a
    st stack_tmp    ; t = a
    ld stack_x
    swapax
    st stack+x      ; push x
    swapax
    add one
    swapax
    ld stack_tmp    ; a = t
    st stack+x      ; push a
    swapax
    add one
    st stack_x      ; stack index

    ; push pc (computed by assembler)
    ld stackp_x
    swapax
    ld #._ret_0
    st stackp+x
    swapax
    add one
    swapax
    ld #._ret_1
    st stackp+x
    swapax
    add one
    swapax
    ld #._ret_2
    st stackp+x
    swapax
    add one
    st stackp_x

    ; do the call
    j foo
ret:
    ld stack_x
    sub one
    swapax
    ld stack+x
    st stack_tmp
    swapax
    sub one
    swapax
    ld stack+x
    swapax
    st stack_x
    ld stack_tmp

    stop

check_foo: . 0 ; for validation
foo:
    ld one
    st check_foo
    ld stackp_x
    sub three
    st stackp_x
    swapax
    j (stackp+x)
