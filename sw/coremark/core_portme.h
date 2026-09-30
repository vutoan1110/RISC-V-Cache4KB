/* CoreMark port for the RV32I+Zmmul SoC (review item A6).
 *
 * No FPU, no libc time, no stdio: the SoC has a 32-bit APB timer and a UART.
 * Memory comes from a static block, because the 8-KiB RAM has no heap and the
 * stack is small. ITERATIONS is fixed at one: an official CoreMark score needs
 * a run of at least ten seconds, which is not reachable in RTL simulation, so
 * this build is used for its cycle counts and is not reported as a score.
 */
#ifndef CORE_PORTME_H
#define CORE_PORTME_H

#define HAS_FLOAT 0
#define HAS_TIME_H 0
#define USE_CLOCK 0
#define HAS_STDIO 0
#define HAS_PRINTF 0

#define COMPILER_VERSION "GCC" __VERSION__
#define COMPILER_FLAGS "-O2 -march=rv32i_zmmul -mabi=ilp32"
#define MEM_LOCATION "STATIC"

typedef signed short   ee_s16;
typedef unsigned short ee_u16;
typedef signed int     ee_s32;
typedef double         ee_f32;
typedef unsigned char  ee_u8;
typedef unsigned int   ee_u32;
typedef unsigned int   ee_ptr_int;
typedef unsigned int   ee_size_t;

#ifndef NULL
#define NULL ((void *)0)
#endif

#define align_mem(x) (void *)(4 + (((ee_ptr_int)(x)-1) & ~3))

#define SEED_METHOD SEED_VOLATILE
#define MEM_METHOD  MEM_STATIC

#define MULTITHREAD 1
#define USE_PTHREAD 0
#define USE_FORK    0
#define USE_SOCKET  0

#define MAIN_HAS_NOARGC   1
#define MAIN_HAS_NORETURN 0

typedef ee_u32 CORE_TICKS;

/* HAS_PRINTF is 0, so the suite uses the bundled ee_printf. */
extern int ee_printf(const char *fmt, ...);
extern void uart_send_char(char c);

extern ee_u32 default_num_contexts;

typedef struct CORE_PORTABLE_S
{
    ee_u8 portable_id;
} core_portable;

void portable_init(core_portable *p, int *argc, char *argv[]);
void portable_fini(core_portable *p);

#if !defined(PROFILE_RUN) && !defined(PERFORMANCE_RUN) && !defined(VALIDATION_RUN)
#define PERFORMANCE_RUN 1
#endif

#ifndef ITERATIONS
#define ITERATIONS 1
#endif

#ifndef TOTAL_DATA_SIZE
#define TOTAL_DATA_SIZE 1200
#endif

#endif /* CORE_PORTME_H */
