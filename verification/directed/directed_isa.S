    # Directed RV32I and Zmmul architectural self-check program.
    .option norvc
    .section .text
    .globl _start

    .macro CHECK_REG reg, expected, code
        li      x27, \expected
        beq     \reg, x27, 1f
        li      x31, \code
        jal     x0, test_done
1:
    .endm

_start:
    li      x31, 1                  # pass marker unless a check overwrites it
    li      x30, 0x1000             # safe aligned data region, beyond code

    # RV32I register and immediate ALU operations.
    li      x5, 0x7fffffff
    li      x6, 1
    add     x7, x5, x6
    CHECK_REG x7, 0x80000000, 2
    sub     x7, x0, x6
    CHECK_REG x7, -1, 3
    and     x7, x5, x7
    CHECK_REG x7, 0x7fffffff, 4
    or      x7, x5, x6
    CHECK_REG x7, 0x7fffffff, 5
    xor     x7, x5, x6
    CHECK_REG x7, 0x7ffffffe, 6
    slt     x7, x7, x0
    CHECK_REG x7, 0, 7
    li      x5, 0x80000000
    slt     x7, x5, x6
    CHECK_REG x7, 1, 8
    sltu    x7, x5, x6
    CHECK_REG x7, 0, 9
    sll     x7, x6, x6
    CHECK_REG x7, 2, 10
    srl     x7, x5, x6
    CHECK_REG x7, 0x40000000, 11
    sra     x7, x5, x6
    CHECK_REG x7, 0xc0000000, 12

    addi    x7, x0, -1
    CHECK_REG x7, -1, 13
    slti    x7, x5, 0
    CHECK_REG x7, 1, 14
    sltiu   x7, x0, -1
    CHECK_REG x7, 1, 15
    xori    x7, x5, -1
    CHECK_REG x7, 0x7fffffff, 16
    ori     x7, x0, 0x55
    CHECK_REG x7, 0x55, 17
    andi    x7, x7, 0x0f
    CHECK_REG x7, 5, 18
    slli    x7, x6, 31
    CHECK_REG x7, 0x80000000, 19
    srli    x7, x7, 31
    CHECK_REG x7, 1, 20
    srai    x7, x5, 31
    CHECK_REG x7, -1, 21

    # Upper-immediate instructions.
    lui     x8, 0x12345
    CHECK_REG x8, 0x12345000, 22
auipc_site:
    auipc   x9, 0
    la      x10, auipc_site
    beq     x9, x10, 1f
    li      x31, 23
    jal     x0, test_done
1:

    # Zmmul instruction execution through the pipeline.
    li      x5, -1
    li      x6, -1
    mul     x7, x5, x6
    CHECK_REG x7, 1, 24
    mulh    x7, x5, x6
    CHECK_REG x7, 0, 25
    mulhu   x7, x5, x6
    CHECK_REG x7, 0xfffffffe, 26
    li      x6, 0x80000000
    mulhsu  x7, x5, x6
    CHECK_REG x7, 0xffffffff, 27

    # Little-endian loads, sign extension and byte strobes.
    li      x5, 0x80ff7f01
    sw      x5, 0(x30)
    lw      x6, 0(x30)
    CHECK_REG x6, 0x80ff7f01, 28
    lb      x6, 3(x30)
    CHECK_REG x6, 0xffffff80, 29
    lbu     x6, 3(x30)
    CHECK_REG x6, 0x00000080, 30
    lh      x6, 2(x30)
    CHECK_REG x6, 0xffff80ff, 31
    lhu     x6, 2(x30)
    CHECK_REG x6, 0x000080ff, 32
    li      x5, 0xaa
    sb      x5, 5(x30)
    lbu     x6, 5(x30)
    CHECK_REG x6, 0xaa, 33
    li      x5, 0x8123
    sh      x5, 6(x30)
    lhu     x6, 6(x30)
    CHECK_REG x6, 0x8123, 34
    li      x5, 0x12345678
    sw      x5, 8(x30)
    lw      x6, 8(x30)
    CHECK_REG x6, 0x12345678, 35
    lw      x5, 8(x30)
    add     x6, x5, x0              # intentional immediate load-use hazard
    CHECK_REG x6, 0x12345678, 53

    # All six conditional branch types, both outcomes, forward and backward.
    li      x5, -1
    li      x6, 1
    beq     x6, x6, 1f
    li      x31, 36
    jal     x0, test_done
1:  bne     x5, x6, 2f
    li      x31, 37
    jal     x0, test_done
2:  blt     x5, x6, 3f
    li      x31, 38
    jal     x0, test_done
3:  bge     x6, x5, 4f
    li      x31, 39
    jal     x0, test_done
4:  bltu    x6, x5, 5f
    li      x31, 40
    jal     x0, test_done
5:  bgeu    x5, x6, 6f
    li      x31, 41
    jal     x0, test_done
6:
    li      x24, 0
    beq     x5, x6, 7f             # expected not taken
    addi    x24, x24, 1
7:  CHECK_REG x24, 1, 42
    li      x24, 0
8:  addi    x24, x24, 1
    blt     x24, x6, 8b            # first outcome not taken: 1 < 1 is false
    CHECK_REG x24, 1, 43

    # Explicit not-taken outcome for every conditional branch type.
    li      x5, -1
    li      x6, 1
    li      x24, 0
    beq     x5, x6, 9f
    addi    x24, x24, 1
9:  bne     x6, x6, 10f
    addi    x24, x24, 1
10: blt     x6, x5, 11f
    addi    x24, x24, 1
11: bge     x5, x6, 12f
    addi    x24, x24, 1
12: bltu    x5, x6, 13f
    addi    x24, x24, 1
13: bgeu    x6, x5, 14f
    addi    x24, x24, 1
14: CHECK_REG x24, 6, 54

    # JAL link and wrong-path suppression.
    jal     x21, jal_target
jal_return:
    jal     x0, after_jal
    li      x31, 44
    jal     x0, test_done
jal_target:
    la      x23, jal_return
    bne     x21, x23, fail_jal_link
    jal     x0, jal_return
fail_jal_link:
    li      x31, 45
    jal     x0, test_done
after_jal:

    # JALR target bit zero clearing and link-register correctness.
    la      x22, jalr_target
    addi    x22, x22, 1
    jalr    x21, 0(x22)
jalr_return:
    jal     x0, after_jalr
jalr_target:
    la      x23, jalr_return
    bne     x21, x23, fail_jalr_link
    jal     x0, jalr_return
fail_jalr_link:
    li      x31, 46
    jal     x0, test_done
after_jalr:

    # Cold taken branches must suppress wrong-path RAM and MMIO stores.
    li      x5, 0x5a
    beq     x0, x0, 1f
    sw      x5, 12(x30)
1:  lw      x6, 12(x30)
    CHECK_REG x6, 0, 52
    li      x5, 0x40000100
    li      x6, 0x66
    beq     x0, x0, 2f
    sw      x6, 0(x5)
2:

    # Reduced machine CSR subset: register forms only.
    li      x5, 0x120
    csrrw   x6, mtvec, x5
    csrrs   x7, mtvec, x0
    CHECK_REG x7, 0x120, 47
    li      x5, 0x44
    csrrw   x0, mepc, x5
    csrrs   x7, mepc, x0
    CHECK_REG x7, 0x44, 48
    li      x5, 0x55
    csrrw   x0, mcause, x5
    csrrs   x7, mcause, x0
    CHECK_REG x7, 0x55, 49
    csrrs   x7, mcycle, x0
    beq     x7, x0, fail_mcycle
    csrrs   x7, minstret, x0
    beq     x7, x0, fail_minstret
    fence   rw, rw
    jal     x0, test_done
fail_mcycle:
    li      x31, 50
    jal     x0, test_done
fail_minstret:
    li      x31, 51

test_done:
    .word   0x0000006f              # supported JAL x0,0 stop loop; TB stops first retire
