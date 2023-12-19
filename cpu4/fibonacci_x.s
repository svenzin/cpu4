j begin

fibo: .dw 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0

begin:   ld #0
         st fibo
         ld #1
         ldx #1
         st fibo+x
fibloop: addx #-1
         add fibo+x
         addx #2
         jc fibdone
         st fibo+x
         j fibloop
fibdone:
         stop
