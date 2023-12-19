j begin
zero: .0
one: .1

scratch: .0
fn: .0
fn1: .1
fibo: .0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
begin:
         ld zero
         swapax
         ld zero
         st fn
         st fibo+x
         add one
         addx one
         st fibo+x
fibloop:
         addx one
         jc fibdone
         st scratch
         add fn
         st fibo+x
         ld scratch
         st fn
         ld fibo+x
         j fibloop
fibdone:
         stop