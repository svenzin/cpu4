j begin
zero: .0
one: .1

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
         swapax
         add one
         swapax
         st fn1
         st fibo+x
fibloop: swapax  ; next index
         add one
         swapax
         jc fibdone
         ld fn
         add fn1
         st fibo+x
         ld fn1
         st fn
         ld fibo+x
         st fn1
         j fibloop
fibdone:
         stop