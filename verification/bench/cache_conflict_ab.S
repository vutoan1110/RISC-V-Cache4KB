/* A/B conflict microbenchmark. A=0 and B=0x400 map to the same DM index. */
.section .text
.globl _start
_start:
    li      t0, 0x00000000
    li      t1, 0x00000400
    li      t2, 64
1:
    lw      a0, 0(t0)
    lw      a1, 0(t1)
    addi    t2, t2, -1
    bnez    t2, 1b
    li      t6, 1
2:
    j       2b
