.section .text.init, "ax", @progbits
.align 2
.global _start
.type _start, @function
_start:
    /* Avoid linker relaxation turning gp initialization into mv gp,gp. */
    .option push
    .option norelax
    la      gp, __global_pointer$
    .option pop

    la      sp, __stack_top

    /* Generic .data copy.  Current unified-RAM layout has equal LMA/VMA, so
     * the loop is skipped; keeping it makes the startup symbols truthful if a
     * future image deliberately separates load and run addresses. */
    la      t0, __data_load
    la      t1, __data_start
    la      t2, __data_end
    beq     t0, t1, 2f
1:
    bgeu    t1, t2, 2f
    lw      t3, 0(t0)
    sw      t3, 0(t1)
    addi    t0, t0, 4
    addi    t1, t1, 4
    j       1b

    /* Zero every BSS word before entering C. */
2:
    la      t0, __bss_start
    la      t1, __bss_end
3:
    bgeu    t0, t1, 4f
    sw      zero, 0(t0)
    addi    t0, t0, 4
    j       3b

4:
    call    main
5:
    j       5b
.size _start, .-_start
