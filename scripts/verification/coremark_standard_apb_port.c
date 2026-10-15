/* Isolated standard CoreMark timing port, based on sw/coremark/core_portme.c.
 * The timer saturates at CMP; configure UINT32_MAX before the timed interval.
 * Algorithms and hardware are unchanged. RAM32KiB simulation, HAS_FLOAT=0. */
#include "coremark.h"
#include "platform.h"
volatile ee_s32 seed1_volatile = VALIDATION_RUN ? 0x3415 : 0;
volatile ee_s32 seed2_volatile = VALIDATION_RUN ? 0x3415 : 0;
volatile ee_s32 seed3_volatile = 0x66;
volatile ee_s32 seed4_volatile = ITERATIONS;
volatile ee_s32 seed5_volatile = 0;
ee_u32 default_num_contexts = 1;
int coremark_validated;
struct sample { ee_u32 start, stop; };
static struct sample samples[16];
static ee_u32 sample_count, timer_open, timer_error;

void start_time(void)
{
    if (timer_open || sample_count >= 16) { timer_error = 1; return; }
    timer_reset();
    TIMER_CMP = 0xffffffffu;
    timer_start();
    timer_open = 1;
    samples[sample_count].start = TIMER_COUNT;
}
void stop_time(void)
{
    ee_u32 stop_ticks = TIMER_COUNT;
    if (!timer_open || sample_count >= 16) { timer_error = 1; return; }
    samples[sample_count++].stop = stop_ticks;
    timer_open = 0;
}
CORE_TICKS get_time(void)
{
    if (!sample_count || timer_open || timer_error) return 0;
    return samples[sample_count - 1].stop - samples[sample_count - 1].start;
}
secs_ret time_in_secs(CORE_TICKS ticks) { return ticks / 50000000u; }
void portable_init(core_portable *p, int *argc, char *argv[])
{ (void)argc; (void)argv; p->portable_id = 1; }
void portable_fini(core_portable *p)
{
    ee_u32 i;
    ee_printf("COREMARK_TIMER clock_hz=50000000 bits=32 samples=%u error=%u open=%u\n",
              sample_count, timer_error, timer_open);
    for (i = 0; i < sample_count; i++)
        ee_printf("COREMARK_INTERVAL index=%u start=0x%08x stop=0x%08x ticks=%u\n",
                  i, samples[i].start, samples[i].stop,
                  samples[i].stop - samples[i].start);
    p->portable_id = 0;
}
int coremark_port_pass(void)
{
    return coremark_validated && !timer_error && !timer_open && sample_count &&
           get_time() >= 500000000u;
}
void uart_send_char(char c) { uart_putc(c); }
