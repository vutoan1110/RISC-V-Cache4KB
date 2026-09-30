// Project-original kernel for RISCV-AHB-APB-UART. Not derived from BEEBS,
// MRTC/WCET, or the Independent JPEG Group code. Implements an 8x8 integer
// forward DCT using Chen's butterfly decomposition (Chen, Smith & Fralick,
// 1977 -- a published algorithm) with project-chosen Q12 coefficients and a
// project-specific harness. Named after the "fdct" (JPEG/DCT) workload
// category; NOT an official Embench score.
// See docs/guides/05_EXTENDED_EMBENCH_BENCHMARKS.md.
#include "embench_fdct.h"

#define FDCT_VERIFY  0x8be7296bu
#define FDCT_ITER    64u
#define BLOCK_SIZE   8u

/* Q12 fixed-point cosine coefficients for 8-point DCT
   c[k] = cos(k*pi/16) * 4096 */
#define C1  4017   /* cos(1*pi/16) * 4096 = 4017 */
#define C2  3784   /* cos(2*pi/16) * 4096 = 3784 */
#define C3  3406   /* cos(3*pi/16) * 4096 = 3406 */
#define C5  2276   /* cos(5*pi/16) * 4096 = 2276 */
#define C6  1567   /* cos(6*pi/16) * 4096 = 1567 */
#define C7   799   /* cos(7*pi/16) * 4096 =  799 */

/* 1D 8-point FDCT using Chen's butterfly decomposition (integer) */
static void fdct_1d(int *data)
{
    int s0, s1, s2, s3, s4, s5, s6, s7;
    int d0, d1, d2, d3;
    int t0, t1, t2, t3;

    /* Stage 1: add/sub pairs */
    s0 = data[0] + data[7];
    s1 = data[1] + data[6];
    s2 = data[2] + data[5];
    s3 = data[3] + data[4];
    s4 = data[0] - data[7];
    s5 = data[1] - data[6];
    s6 = data[2] - data[5];
    s7 = data[3] - data[4];

    /* Stage 2: even part */
    d0 = s0 + s3;
    d1 = s1 + s2;
    d2 = s0 - s3;
    d3 = s1 - s2;

    /* DC and Nyquist */
    data[0] = d0 + d1;
    data[4] = d0 - d1;

    /* Rotations using C2, C6 */
    data[2] = (C2 * d2 + C6 * d3) >> 12;
    data[6] = (C6 * d2 - C2 * d3) >> 12;

    /* Stage 2: odd part - rotations using C1,C3,C5,C7 */
    t0 = C7 * s4 + C1 * s7;
    t1 = C5 * s5 + C3 * s6;
    t2 = C3 * s5 - C5 * s6;
    t3 = C1 * s4 - C7 * s7;

    data[1] = (t3) >> 12;
    data[3] = (t2) >> 12;
    data[5] = (t1) >> 12;
    data[7] = (t0) >> 12;
}

/* 2D 8x8 block FDCT (rows then columns) */
static void fdct_2d(int block[BLOCK_SIZE][BLOCK_SIZE])
{
    unsigned int i, j;

    /* Transform rows */
    for (i = 0; i < BLOCK_SIZE; ++i)
        fdct_1d(block[i]);

    /* Transpose */
    for (i = 0; i < BLOCK_SIZE; ++i) {
        for (j = i + 1; j < BLOCK_SIZE; ++j) {
            int tmp = block[i][j];
            block[i][j] = block[j][i];
            block[j][i] = tmp;
        }
    }

    /* Transform columns (now rows after transpose) */
    for (i = 0; i < BLOCK_SIZE; ++i)
        fdct_1d(block[i]);
}

void embench_fdct_initialise(void) { }
void embench_fdct_warm_caches(int heat) { (void)heat; }

int embench_fdct_run(void)
{
    static int block[BLOCK_SIZE][BLOCK_SIZE];
    unsigned int hash = 0u;
    unsigned int iter, i, j;

    for (iter = 0u; iter < FDCT_ITER; ++iter) {
        /* Fill block with pseudo-random pixel values */
        unsigned int seed = 0x13579BDFu + iter * 23u;
        for (i = 0; i < BLOCK_SIZE; ++i) {
            for (j = 0; j < BLOCK_SIZE; ++j) {
                seed = (seed * 1103515245u + 12345u);
                block[i][j] = (int)((seed >> 16) & 0xFFu);  /* 0..255 */
            }
        }

        /* Perform 2D DCT */
        fdct_2d(block);

        /* Hash the result */
        for (i = 0; i < BLOCK_SIZE; ++i) {
            for (j = 0; j < BLOCK_SIZE; ++j) {
                hash = ((hash * 131u) ^ (unsigned int)block[i][j]);
            }
        }
    }

    return (int)hash;
}

int embench_fdct_verify(int result)
{
    return ((unsigned int)result == FDCT_VERIFY);
}
