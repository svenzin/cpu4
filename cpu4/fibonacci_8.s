j begin
zero: .dw 0
one: .dw 1
two: .dw 2
minus_one: .dw 15

scratch: .dw 0
fn: .dw 0
fn1: .dw 1
fibo: .dw 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
begin:
         lea zero
         ld
         swapax
         ld
         lea fibo+x
         st
         lea one
         add
         addx
         lea fibo+x
         st
fibloop:
         lea minus_one
         addx
         lea fibo+x
         add
         lea two
         addx
         jc fibdone
         lea fibo+x
         st
         j fibloop
fibdone:
         stop