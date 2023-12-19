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
         ld zero
         swapax
         ld zero
         st fibo+x
         add one
         addx one
         st fibo+x
fibloop:
         st scratch
         addx minus_one
         ld fibo+x
         add scratch
         addx two
         jc fibdone
         st fibo+x
         j fibloop
fibdone:
         stop