// Project-original kernel for RISCV-AHB-APB-UART. Not derived from Embench-IoT
// or MRTC/WCET source. Implements a deterministic 16x16 unsigned integer
// matrix multiply-accumulate with modulo-2^32 arithmetic and a checksum, with
// a project-specific harness (the MATMULT_VERIFY constant was reconstructed
// independently -- see the note below). Named after the Embench-IoT
// "matmult-int" (GEMM) workload category; NOT an official Embench score.
// See docs/guides/05_EXTENDED_EMBENCH_BENCHMARKS.md.
#include "embench_matmult.h"

typedef unsigned int matrix_t[16][16];

#define UPPERLIMIT     16u
#define MOD_SIZE       8095u
// Independently reconstructed from the deterministic 16x16 kernel with
// modulo-2^32 multiply/accumulate and checksum arithmetic. The previous
// 0x06A3E000 constant did not match this source algorithm and made the same
// binary fail on both the baseline and current RTL.
#define MATMULT_VERIFY 0xAA1C6419u

static unsigned int seed_matmult;
static matrix_t ArrayA_ref;
static matrix_t ArrayB_ref;
static matrix_t ResultArray;

static void init_seed(void)
{
    seed_matmult = 0u;
}

static unsigned int random_integer(void)
{
    seed_matmult = ((seed_matmult * 133u) + 81u) % MOD_SIZE;
    return seed_matmult;
}

static void initialise_matrix(matrix_t m)
{
    unsigned int i, j;
    for (i = 0; i < UPPERLIMIT; ++i) {
        for (j = 0; j < UPPERLIMIT; ++j) {
            m[i][j] = random_integer();
        }
    }
}

static void multiply(matrix_t A, matrix_t B, matrix_t Res)
{
    unsigned int i, j, k;
    unsigned int acc;

    for (i = 0; i < UPPERLIMIT; ++i) {
        for (j = 0; j < UPPERLIMIT; ++j) {
            acc = 0u;
            for (k = 0; k < UPPERLIMIT; ++k) {
                acc += A[i][k] * B[k][j];
            }
            Res[i][j] = acc;
        }
    }
}

static unsigned int checksum_result(void)
{
    unsigned int h = 0u;
    unsigned int i, j;

    for (i = 0; i < UPPERLIMIT; ++i) {
        for (j = 0; j < UPPERLIMIT; ++j) {
            h = (h * 131u) ^ ResultArray[i][j];
        }
    }

    return h;
}

void embench_matmult_initialise(void)
{
    init_seed();
    initialise_matrix(ArrayA_ref);
    initialise_matrix(ArrayB_ref);
}

void embench_matmult_warm_caches(int heat)
{
    (void)heat;
}

int embench_matmult_run(void)
{
    multiply(ArrayA_ref, ArrayB_ref, ResultArray);
    return (int)checksum_result();
}

int embench_matmult_verify(int result)
{
    return ((unsigned int)result == MATMULT_VERIFY);
}
