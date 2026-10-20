/* A/B/C conflict microbenchmark for the two-way capacity boundary. */
.section .text
.globl _start
_start:
    li      t0, 0x00000000
    li      t1, 0x00000400
    li      t2, 0x00000800
    li      t3, 64
1:
    lw      a0, 0(t0)
    lw      a1, 0(t1)
    lw      a2, 0(t2)
    addi    t3, t3, -1
    bnez    t3, 1b
    li      t6, 1
2:
    j       2b
