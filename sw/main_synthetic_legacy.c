#include "platform.h"

#define DONE_MAGIC 0xB16B00B5u
#define FAIL_MAGIC 0xDEADFA11u

/* data_probe and bss_probe make startup initialization observable. */
static volatile unsigned int data_probe = 0x13579BDFu;
static volatile unsigned int bss_probe;
static volatile unsigned int buf[64];

int main(void)
{
    struct benchmark_snapshot perf;
    volatile unsigned int acc = 0u;
    unsigned int expected;
    unsigned int i;
    unsigned int r;
    int ram_ok;
    int counter_ok;
    int pass;

    UART_CFG   = UART_CFG_115200_8N1;
    DISP_VALUE = 0x1234ABCDu;
    DISP_LED   = 0x5Au;
    DISP_CTRL  = 0x00000000u;

    uart_puts("RISC-V boot\n");
    uart_puts("UART=PASS\n");

    ram_ok = (data_probe == 0x13579BDFu) && (bss_probe == 0u);
    for (i = 0u; i < 64u; ++i)
        buf[i] = (i * 17u) ^ (i << 4) ^ 0x12345678u;
    for (i = 0u; i < 64u; ++i) {
        expected = (i * 17u) ^ (i << 4) ^ 0x12345678u;
        if (buf[i] != expected)
            ram_ok = 0;
    }
    uart_puts(ram_ok ? "RAM=PASS\n" : "RAM=FAIL\n");

    timer_reset();
    timer_start();

    benchmark_measure_begin();
    for (r = 0u; r < 16u; ++r) {
        for (i = 1u; i < 64u; ++i) {
            unsigned int a = buf[i - 1u];
            unsigned int b = buf[i];
            unsigned int c = (a + (b ^ (i * 3u))) ^ (r + i);
            buf[i] = c;
            acc ^= c;
        }
    }
    benchmark_measure_end(&perf);

    counter_ok = benchmark_snapshot_invariants(&perf, 1);
    uart_puts(counter_ok ? "COUNTER=PASS\n" : "COUNTER=FAIL\n");
    pass = ram_ok && counter_ok && (acc != 0u);
    platform_report_benchmark("smoke", (int)acc, pass, &perf);

    if (pass) {
        DISP_VALUE = acc;
        DISP_LED   = 0xA5u;
        DISP_CTRL  = DONE_MAGIC;
    }
    else {
        DISP_VALUE = acc;
        DISP_LED   = 0xEEu;
        DISP_CTRL  = FAIL_MAGIC;
    }

    while (1) { }
}
