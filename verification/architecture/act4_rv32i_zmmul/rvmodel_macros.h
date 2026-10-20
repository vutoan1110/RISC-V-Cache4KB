#ifndef ACT4_RV32I_ZMMUL_RVMODEL_MACROS_H
#define ACT4_RV32I_ZMMUL_RVMODEL_MACROS_H

/*
 * ACT4 DUT macros for the reduced RV32I + Zmmul core.
 *
 * Do not define STANDARD_SM_SUPPORTED here. The current RTL has selected
 * machine CSRs and a timer-interrupt path, but not the complete synchronous
 * exception/privileged contract required by ACT4 Sm tests.
 */

#define RVMODEL_BOOT

/* ACT4 2e655961 includes sail_macros.h for the intermediate signature ELF
 * even when Spike is selected as the reference model. These two addresses
 * only satisfy that header contract; privileged/interrupt tests are excluded
 * and neither address is presented as a DUT memory-mapped device. */
#define SAIL_CLINT_BASE_ADDRESS 0x02000000
#define SAIL_SIMPLE_INTERRUPT_GENERATOR_BASE_ADDRESS 0x03000000

#define RVMODEL_DATA_SECTION                         \
  .pushsection .tohost,"aw",@progbits;               \
  .balign 4; .global tohost; tohost: .word 0;         \
  .balign 4; .global fromhost; fromhost: .word 0;     \
  .popsection

#define RVMODEL_HALT_PASS                            \
  li t0, 1;                                          \
  la t1, tohost;                                     \
1:                                                   \
  sw t0, 0(t1);                                      \
  j 1b

#define RVMODEL_HALT_FAIL                            \
  li t0, 3;                                          \
  la t1, tohost;                                     \
1:                                                   \
  sw t0, 0(t1);                                      \
  j 1b

#define RVMODEL_IO_INIT(_R1, _R2, _R3)
#define RVMODEL_IO_WRITE_STR(_R1, _R2, _R3, _STR_PTR)

/* Required interface macros; privileged tests are excluded, so these are
 * intentionally empty and no unsupported interrupt source is advertised. */
#define RVMODEL_INTERRUPT_LATENCY 4096
#define RVMODEL_TIMER_INT_SOON_DELAY 100
#define RVMODEL_MAX_CYCLES_PER_TIMER_TICK 1
#define RVMODEL_SET_MEXT_INT(_R1, _R2)
#define RVMODEL_CLR_MEXT_INT(_R1, _R2)
#define RVMODEL_SET_MSW_INT(_R1, _R2)
#define RVMODEL_CLR_MSW_INT(_R1, _R2)
#define RVMODEL_SET_SEXT_INT(_R1, _R2)
#define RVMODEL_CLR_SEXT_INT(_R1, _R2)
#define RVMODEL_SET_SSW_INT(_R1, _R2)
#define RVMODEL_CLR_SSW_INT(_R1, _R2)

#endif
