#include "embench_ramsweep.h"

/* R14 (2026-09-29, RAM16K_CHANGES.md). The free region runs from the end of the image (__heap_start)
 * to the bottom of the reserved stack (__heap_end), rounded in to 16-byte lines. With the 16 KiB RAM it
 * is far larger than the 4 KiB D-cache, so the read-back of each pass comes from the physical RAM, and it
 * crosses every 512-word SRAM bank that the stack and the image do not already occupy. */
extern unsigned char __heap_start[];
extern unsigned char __heap_end[];

static volatile unsigned int *region_lo;
static volatile unsigned int *region_hi;

static unsigned int pattern(unsigned int addr, unsigned int pass) {
    return (addr * 0x9E3779B1u) ^ (0xA5A5A5A5u + pass * 0x01010101u);
}

void embench_ramsweep_initialise(void) {
    unsigned int lo = ((unsigned int)__heap_start + 15u) & ~15u;
    unsigned int hi = (unsigned int)__heap_end & ~15u;
    region_lo = (volatile unsigned int *)lo;
    region_hi = (volatile unsigned int *)hi;
}

void embench_ramsweep_warm_caches(int heat) {
    (void)heat;
}

unsigned int embench_ramsweep_words(void) {
    return (unsigned int)(region_hi - region_lo);
}

static int check_all(unsigned int pass) {
    volatile unsigned int *p;
    int bad = 0;
    for (p = region_lo; p < region_hi; p++) {
        if (*p != pattern((unsigned int)p, pass)) {
            bad++;
        }
    }
    return bad;
}

int embench_ramsweep_run(void) {
    volatile unsigned int *p;
    int bad = 0;

    /* pass 0: word stores */
    for (p = region_lo; p < region_hi; p++) {
        *p = pattern((unsigned int)p, 0u);
    }
    bad += check_all(0u);

    /* pass 1: byte stores, one per lane, over the previous contents */
    for (p = region_lo; p < region_hi; p++) {
        volatile unsigned char *b = (volatile unsigned char *)p;
        unsigned int v = pattern((unsigned int)p, 1u);
        b[0] = (unsigned char)v;
        b[1] = (unsigned char)(v >> 8);
        b[2] = (unsigned char)(v >> 16);
        b[3] = (unsigned char)(v >> 24);
    }
    bad += check_all(1u);

    /* pass 2: halfword stores */
    for (p = region_lo; p < region_hi; p++) {
        volatile unsigned short *h = (volatile unsigned short *)p;
        unsigned int v = pattern((unsigned int)p, 2u);
        h[0] = (unsigned short)v;
        h[1] = (unsigned short)(v >> 16);
    }
    bad += check_all(2u);

    return bad;
}

int embench_ramsweep_verify(int result) {
    /* every word checked three times, none may differ, and the region must reach past 8 KiB */
    return result == 0 && (unsigned int)region_hi > 0x2000u;
}
