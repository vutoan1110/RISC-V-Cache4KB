#include "platform.h"
#include "embench_wikisort_trace.h"
#include "embench_beebs.h"

#define DONE_MAGIC 0xB16B00B5u
#define FAIL_MAGIC 0xDEADFA11u
#define HEAP_SIZE  128u

static unsigned char beebs_heap[HEAP_SIZE];

int main(void)
{
    struct benchmark_snapshot perf;
    int result;
    int pass;

    UART_CFG   = UART_CFG_115200_8N1;
    DISP_VALUE = 0xE8BEF001u;
    DISP_LED   = 0xE1u;
    DISP_CTRL  = 0x00000000u;

    uart_puts("RISC-V boot\n");
    uart_puts("TRACE_MODE=WIKISORT_VERBOSE\n");
    uart_puts("PERF_VALID=0\n");
    uart_puts("NOTE=UART_TRACE_IS_INSIDE_MEASURED_REGION\n");

    init_heap_beebs(beebs_heap, sizeof(beebs_heap));
    timer_reset();
    timer_start();
    embench_wikisort_trace_initialise();
    embench_wikisort_trace_warm_caches(0);

    benchmark_measure_begin();
    result = embench_wikisort_trace_run();
    benchmark_measure_end(&perf);

    pass = embench_wikisort_trace_verify(result);
    platform_report_benchmark("wikisort_trace", result, pass, &perf);
    pass = pass && benchmark_snapshot_invariants(&perf, 1);

    if (pass) {
        DISP_VALUE = (unsigned int)result;
        DISP_LED   = 0xA5u;
        DISP_CTRL  = DONE_MAGIC;
    }
    else {
        DISP_VALUE = (unsigned int)result;
        DISP_LED   = 0xEEu;
        DISP_CTRL  = FAIL_MAGIC;
    }

    while (1) {
    }
}
