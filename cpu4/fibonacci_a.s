j begin

.align 16
fibo: .dw 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0

zero: .dw 0
one: .dw 1
two: .dw 2
three: .dw 3

next: .@ fibo
curr: .@ fibo
prev: .@ fibo

begin:
         ld zero
         st .@prev_0
         st (prev)

         ld one
         st .@curr_0
         st (curr)

         ld two
         st .@next_0

fibloop:
         ld (prev)
         add (curr)
         st (next)
         ld .@curr_0
         st .@prev_0
         ld .@next_0
         st .@curr_0
         add one
         st .@next_0

         jc fibdone
         j fibloop
fibdone:
         stop
