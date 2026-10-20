#ifndef RVMODEL_MACROS_H
#define RVMODEL_MACROS_H

/* Adapter fragment for the flat-memory architecture harness.
 * The surrounding ACT4 configuration must describe the reduced DUT exactly.
 */
#define RVMODEL_BOOT
#define RVMODEL_DATA_SECTION
#define RVMODEL_IO_INIT(_R1, _R2, _R3)
#define RVMODEL_IO_WRITE_STR(_R1, _R2, _R3, _STR_PTR)

#define RVMODEL_HALT_PASS          \
    li t0, 0x0000fffc;             \
    li t1, 1;                      \
    sw t1, 0(t0);                  \
1:  j 1b

#define RVMODEL_HALT_FAIL          \
    li t0, 0x0000fffc;             \
    li t1, 2;                      \
    sw t1, 0(t0);                  \
1:  j 1b

#endif
