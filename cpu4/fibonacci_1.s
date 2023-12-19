      j begin

zero: .0
one:  .1

scratch: .0

temp: .0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0

begin:
      ld zero
      swapax
      ld zero
      st temp+x
      add one
      swapax
      add one
      st temp+x
loop: swapax    ; go to Fn-1
      sub one
      swapax
      ld temp+x ; load Fn-1
      swapax    ; go to Fn
      add one
      swapax
      st scratch ; add Fn
      ld temp+x
      add scratch
      swapax     ; go to Fn+1
      add one
      jc done
      swapax
      st temp+x  ; store Fn+1
      j loop
done: ld zero
      sub one

      stop