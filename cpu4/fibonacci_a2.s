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
         ld #0
         st .@prev_0
         st (prev)

         ld #1
         st .@curr_0
         st (curr)

         ldx #2
         stx .@next_0

fibloop:
         add (prev)
         st (next)
         ldx .@prev_0
         addx #3
         stx .@prev_0

         ; jc fibdone

         add (curr)
         st (prev)
         ldx .@curr_0
         addx #3
         stx .@curr_0

         jc fibdone

         add (next)
         st (curr)
         ldx .@next_0
         addx #3
         stx .@next_0

         ;jc fibdone
         j fibloop
fibdone:
         stop
