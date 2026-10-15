/* Full-program snapshot is auxiliary; the score uses only the final timed
 * iterate interval recorded by the CoreMark timing port. RAM32KiB simulation. */
#include "platform.h"
int coremark_main(void);
int coremark_port_pass(void);
int main(void)
{
    struct benchmark_snapshot perf;
    int result, pass;
    UART_CFG = UART_CFG_115200_8N1;
    uart_puts("COREMARK_STANDARD_BEGIN\n");
    benchmark_measure_begin();
    result = coremark_main();
    benchmark_measure_end(&perf);
    pass = coremark_port_pass() && benchmark_snapshot_invariants(&perf, 1);
    platform_report_benchmark("coremark", result, pass, &perf);
    DISP_VALUE = perf.core.mcycle;
    DISP_LED = pass ? 0xA5u : 0xEEu;
    DISP_CTRL = pass ? 0xB16B00B5u : 0xDEADFA11u;
    for (;;) { }
}
