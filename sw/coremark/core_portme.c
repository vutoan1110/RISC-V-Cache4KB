/* CoreMark porting layer for the RV32I+Zmmul SoC (review item A6).
 * Timing comes from the APB timer at 50 MHz; output goes to the UART.
 */
#include "coremark.h"
#include "../platform.h"

#if VALIDATION_RUN
volatile ee_s32 seed1_volatile = 0x3415;
volatile ee_s32 seed2_volatile = 0x3415;
volatile ee_s32 seed3_volatile = 0x66;
#endif
#if PERFORMANCE_RUN
volatile ee_s32 seed1_volatile = 0x0;
volatile ee_s32 seed2_volatile = 0x0;
volatile ee_s32 seed3_volatile = 0x66;
#endif
#if PROFILE_RUN
volatile ee_s32 seed1_volatile = 0x8;
volatile ee_s32 seed2_volatile = 0x8;
volatile ee_s32 seed3_volatile = 0x8;
#endif
volatile ee_s32 seed4_volatile = ITERATIONS;
volatile ee_s32 seed5_volatile = 0;

#define CORE_CLOCK_HZ 50000000u

static CORE_TICKS start_ticks;
static CORE_TICKS stop_ticks;

void
start_time(void)
{
    timer_reset();
    timer_start();
    start_ticks = TIMER_COUNT;
}

void
stop_time(void)
{
    stop_ticks = TIMER_COUNT;
}

CORE_TICKS
get_time(void)
{
    return (CORE_TICKS)(stop_ticks - start_ticks);
}

secs_ret
time_in_secs(CORE_TICKS ticks)
{
    /* HAS_FLOAT is 0, so secs_ret is an integer count of seconds. At one
     * iteration in simulation this is always zero; the cycle counters, not
     * this value, are what the paper reports. */
    return (secs_ret)(ticks / CORE_CLOCK_HZ);
}

ee_u32 default_num_contexts = 1;

void
portable_init(core_portable *p, int *argc, char *argv[])
{
    (void)argc;
    (void)argv;
    p->portable_id = 1;
}

void
portable_fini(core_portable *p)
{
    p->portable_id = 0;
}

/* ee_printf.c calls this for every character. */
void
uart_send_char(char c)
{
    uart_putc(c);
}
