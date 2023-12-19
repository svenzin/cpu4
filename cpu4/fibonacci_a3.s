j begin

.align 16
fibo: .dw 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0

zero: .dw 0
one: .dw 1
two: .dw 2
three: .dw 3

curr: .@ fibo
prev: .@ fibo

begin:   ld #0
         st .@prev_0
         st (prev)

         ld #1
         st .@curr_0
         st (curr)

fibloop:  add (prev)
          ldx .@prev_0
          addx #2
          jc fibdone
          stx .@prev_0
          st (prev)

          add (curr)
          ldx .@curr_0
          addx #2
          ; jc fibdone
          stx .@curr_0
          st (curr)

          j fibloop

fibdone:
         stop
