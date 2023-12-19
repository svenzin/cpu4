j begin
zero: .0
one: .1
two: .2
minus_one: .15

scratch: .0
fn: .0
fn1: .1
fibo: .0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
begin:
         lea zero
         ld
         swapax
         ld
         lea fibo+x
         st
         add #1
         addx #1
         lea fibo+x
         st
fibloop:
         addx #-1
         lea fibo+x
         add
         addx #2
         jc fibdone
         lea fibo+x
         st
         j fibloop
fibdone:
         stop