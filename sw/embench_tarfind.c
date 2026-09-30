// Project-original kernel for RISCV-AHB-APB-UART. Implements a linear search
// over a small in-project file-name table (a trivial, uncopyrightable loop);
// not a copy of Julian Kunkel's Embench-IoT "tarfind" (which is MIT-licensed
// in any case). Named after the Embench-IoT "tarfind" (archive search)
// workload category; NOT an official Embench score.
// See docs/guides/05_EXTENDED_EMBENCH_BENCHMARKS.md.
#include "embench_tarfind.h"

#define TARFIND_VERIFY 0x4ecf0600u
#define TARFIND_ITER    64u

typedef struct {
    const char *name;
    unsigned int size;
} tar_entry_t;

static const tar_entry_t entries[] = {
    { "boot.bin",    4096u  },
    { "soc_top.v",   18234u },
    { "main.c",      2048u  },
    { "cache.cfg",   64u    },
    { "uart.log",    1200u  },
    { "report.pdf",  65536u },
    { "result.txt",  512u   },
    { "image.hex",   8192u  },
    { "timer.map",   256u   },
    { "notes.md",    900u   },
    { "embench.crc", 128u   },
    { "matrix.dat",  4096u  }
};

static const char *queries[] = {
    "main.c",
    "uart.log",
    "missing.bin",
    "report.pdf",
    "image.hex",
    "x.bin",
    "notes.md",
    "boot.bin",
    "cache.cfg",
    "matrix.dat",
    "none",
    "result.txt"
};

static int strcmp_local(const char *a, const char *b)
{
    while ((*a != '\0') && (*b != '\0')) {
        if (*a != *b) {
            return (int)((unsigned char)*a) - (int)((unsigned char)*b);
        }
        a++;
        b++;
    }
    return (int)((unsigned char)*a) - (int)((unsigned char)*b);
}

static int search_one(const char *name, unsigned int *size_out)
{
    unsigned int i;
    for (i = 0u; i < (sizeof(entries) / sizeof(entries[0])); ++i) {
        if (strcmp_local(name, entries[i].name) == 0) {
            *size_out = entries[i].size;
            return (int)i;
        }
    }
    *size_out = 0u;
    return -1;
}

void embench_tarfind_initialise(void)
{
}

void embench_tarfind_warm_caches(int heat)
{
    (void)heat;
}

int embench_tarfind_run(void)
{
    unsigned int hash = 0u;
    unsigned int iter;

    for (iter = 0u; iter < TARFIND_ITER; ++iter) {
        unsigned int q;
        for (q = 0u; q < (sizeof(queries) / sizeof(queries[0])); ++q) {
            unsigned int size;
            int idx = search_one(queries[q], &size);
            if (idx >= 0) {
                hash = ((hash * 131u) ^ (unsigned int)((idx + 1) * 257) ^ size ^ iter);
            }
            else {
                hash = ((hash * 131u) ^ 0xDEADu ^ iter);
            }
        }
    }

    return (int)hash;
}

int embench_tarfind_verify(int result)
{
    return ((unsigned int)result == TARFIND_VERIFY);
}
