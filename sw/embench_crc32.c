// Project-original kernel for RISCV-AHB-APB-UART. Not derived from Embench-IoT
// or BEEBS source. Implements a bit-serial CRC-32 (ISO 3309 / IEEE 802.3,
// reversed polynomial 0xEDB88320) -- a published standard, not copyrightable --
// with a project-specific measurement harness. Named after the Embench-IoT
// "crc32" workload category; the numbers are NOT an official Embench score.
// See docs/guides/05_EXTENDED_EMBENCH_BENCHMARKS.md.
#include "embench_crc32.h"

#define CRC32_LOCAL_SCALE_FACTOR  4u
#define CRC32_GLOBAL_SCALE_FACTOR 1u
#define CRC32_VERIFY_RESULT       12901

static unsigned int crc32_step(unsigned int crc, unsigned char data)
{
    int k;

    crc ^= (unsigned int)data;
    for (k = 0; k < 8; ++k) {
        if (crc & 1u)
            crc = (crc >> 1) ^ 0xEDB88320u;
        else
            crc = (crc >> 1);
    }

    return crc;
}

static int benchmark_body(unsigned int local_scale_factor,
                          unsigned int global_scale_factor)
{
    unsigned int crc;
    unsigned int i;
    unsigned int j;
    unsigned char b;

    crc = 0xFFFFFFFFu;

    for (i = 0; i < local_scale_factor; ++i) {
        for (j = 0; j < (64u * global_scale_factor); ++j) {
            b = (unsigned char)((j ^ (j << 1) ^ (i << 2) ^ 0x5Au) & 0xFFu);
            crc = crc32_step(crc, b);
        }
    }

    return (int)((~crc) & 0x7FFFu);
}

void embench_crc32_initialise(void)
{
}

void embench_crc32_warm_caches(int heat)
{
    (void)heat;
}

int embench_crc32_run(void)
{
    return benchmark_body(CRC32_LOCAL_SCALE_FACTOR,
                          CRC32_GLOBAL_SCALE_FACTOR);
}

int embench_crc32_verify(int result)
{
    return (result == CRC32_VERIFY_RESULT);
}