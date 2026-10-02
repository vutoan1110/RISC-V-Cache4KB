/* sw_metrics/irq/irq_entry.S -- machine-timer trap handlers for the interrupt-latency and
 * context-switch measurement (metric expansion, 2026-09-30). Entered through mtvec in direct mode,
 * so each handler is 4-byte aligned.
 *
 *   irq_min  the least a handler must do: free two registers, acknowledge the timer (its match
 *            flag clears, so the interrupt line falls), count, restore, mret.
 *   irq_ctx  an RTOS-style context switch without the scheduler decision: the interrupted task's
 *            x1, x3..x31 and mepc go to a 32-word frame on its own stack (the FreeRTOS RISC-V
 *            layout; this core has no mscratch), the stack pointer is published in current_sp as a
 *            task control block would hold it, the timer is acknowledged and counted, then the task
 *            is resumed from current_sp: mepc rewritten, every register reloaded, mret.
 *
 * Only register-form CSR instructions: the core implements csrrw/csrrs/csrrc, not the immediates.
 * mret sets mstatus.MIE again (datapath.v), so neither handler touches mstatus. */
    .equ TIMER_STATUS_ADDR, 0x4000020C

    .section .text.irq, "ax", @progbits

    .align 2
    .global irq_min
    .type irq_min, @function
irq_min:
    addi  sp, sp, -8
    sw    t0, 0(sp)
    sw    t1, 4(sp)
    li    t0, TIMER_STATUS_ADDR
    li    t1, 1
    sw    t1, 0(t0)
    la    t0, irq_count
    lw    t1, 0(t0)
    addi  t1, t1, 1
    sw    t1, 0(t0)
    lw    t0, 0(sp)
    lw    t1, 4(sp)
    addi  sp, sp, 8
    mret
    .size irq_min, .-irq_min

    .align 2
    .global irq_ctx
    .type irq_ctx, @function
irq_ctx:
    addi  sp, sp, -128
    sw    x1,    4(sp)
    sw    x3,   12(sp)
    sw    x4,   16(sp)
    sw    x5,   20(sp)
    sw    x6,   24(sp)
    sw    x7,   28(sp)
    sw    x8,   32(sp)
    sw    x9,   36(sp)
    sw    x10,  40(sp)
    sw    x11,  44(sp)
    sw    x12,  48(sp)
    sw    x13,  52(sp)
    sw    x14,  56(sp)
    sw    x15,  60(sp)
    sw    x16,  64(sp)
    sw    x17,  68(sp)
    sw    x18,  72(sp)
    sw    x19,  76(sp)
    sw    x20,  80(sp)
    sw    x21,  84(sp)
    sw    x22,  88(sp)
    sw    x23,  92(sp)
    sw    x24,  96(sp)
    sw    x25, 100(sp)
    sw    x26, 104(sp)
    sw    x27, 108(sp)
    sw    x28, 112(sp)
    sw    x29, 116(sp)
    sw    x30, 120(sp)
    sw    x31, 124(sp)
    csrr  t0, mepc
    sw    t0,    0(sp)
    la    t0, current_sp
    sw    sp, 0(t0)
    li    t0, TIMER_STATUS_ADDR
    li    t1, 1
    sw    t1, 0(t0)
    la    t0, irq_count
    lw    t1, 0(t0)
    addi  t1, t1, 1
    sw    t1, 0(t0)
    la    t0, current_sp
    lw    sp, 0(t0)
    lw    t0,    0(sp)
    csrw  mepc, t0
    lw    x1,    4(sp)
    lw    x3,   12(sp)
    lw    x4,   16(sp)
    lw    x5,   20(sp)
    lw    x6,   24(sp)
    lw    x7,   28(sp)
    lw    x8,   32(sp)
    lw    x9,   36(sp)
    lw    x10,  40(sp)
    lw    x11,  44(sp)
    lw    x12,  48(sp)
    lw    x13,  52(sp)
    lw    x14,  56(sp)
    lw    x15,  60(sp)
    lw    x16,  64(sp)
    lw    x17,  68(sp)
    lw    x18,  72(sp)
    lw    x19,  76(sp)
    lw    x20,  80(sp)
    lw    x21,  84(sp)
    lw    x22,  88(sp)
    lw    x23,  92(sp)
    lw    x24,  96(sp)
    lw    x25, 100(sp)
    lw    x26, 104(sp)
    lw    x27, 108(sp)
    lw    x28, 112(sp)
    lw    x29, 116(sp)
    lw    x30, 120(sp)
    lw    x31, 124(sp)
    addi  sp, sp, 128
    mret
    .size irq_ctx, .-irq_ctx
