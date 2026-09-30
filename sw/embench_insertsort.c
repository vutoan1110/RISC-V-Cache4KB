// Project-original store-bound sorting kernel for RISCV-AHB-APB-UART.
//
// PROVENANCE / LICENSE
//   This file is original code written for this project. It implements the
//   textbook insertion-sort algorithm (Knuth, TAOCP Vol. 3, Algorithm S;
//   an uncopyrightable published algorithm) with a project-specific harness.
//   It is NOT derived from Embench-IoT, BEEBS, MRTC/WCET or any third-party
//   benchmark source, and carries no third-party copyright. It follows the
//   same measurement contract as the other kernels in this directory so it
//   can be run on DM / SA2 / DM_VC4 through run_benchmark_snapshot.do.
//
// PURPOSE
//   The project's permissively-licensed store-bound workload. Insertion sort
//   on a reverse-sorted array performs ~n^2/2 array-element writes with almost
//   no cache misses (working set ~400 B), so mcycle is dominated by the
//   D-cache write-through path -- the exact behaviour the posted-write
//   buffer targets. It replaces an earlier BEEBS "bubblesort" port that
//   was removed for licensing reasons.
//
//
//
// PROPERTIES
//   - Pure RV32I + Zmmul: no division/modulo, no float, no libc, no heap.
//     The compiled object has zero undefined symbols under
//     -march=rv32i_zmmul (checked with `nm`).
//   - Deterministic: worst-case (reverse-sorted) input is re-applied before
//     every repeat, and the result checksum is folded ONCE after the repeat
//     loop, so INSERTSORT_REPEATS only sets how long the kernel runs -- it
//     cannot change INSERTSORT_VERIFY.

#include "embench_insertsort.h"

#define NUMELEMS 100
#define MAXDIM   (NUMELEMS + 1)

#define INSERTSORT_REPEATS 3u

/* Checksum of the ascending sorted array [1, 2, ..., 100]:
 *   h = 0; for v in Array: h = (h * 131) ^ (unsigned)v   (mod 2^32)
 * Computed independently in Python from the deterministic sorted sequence;
 * embench_insertsort_run() produces exactly this value regardless of
 * INSERTSORT_REPEATS. */
#define INSERTSORT_VERIFY 0xb4287fa4u

static int Array[MAXDIM];

/* Worst case for insertion sort: strictly descending input [100, 99, ..., 1].
 * Every key then has to travel the full distance to the front, so the inner
 * shift loop runs the maximum number of times. */
static void initialise_worstcase(void)
{
    int i;
    for (i = 0; i < NUMELEMS; ++i)
        Array[i] = NUMELEMS - i;      /* [100, 99, ..., 2, 1] */
    Array[NUMELEMS] = 0;              /* unused guard slot, kept for symmetry */
}

/* Textbook ascending insertion sort. The `a[j + 1] = a[j]` line in the inner
 * loop is the store-heavy part: on the worst-case input above it executes
 * 1 + 2 + ... + (n-1) = n*(n-1)/2 = 4950 times per sort. */
static void insertion_sort(int a[], int n)
{
    int i, j, key;

    for (i = 1; i < n; ++i) {
        key = a[i];
        j   = i - 1;
        while (j >= 0 && a[j] > key) {
            a[j + 1] = a[j];         /* shift one element right (a store) */
            --j;
        }
        a[j + 1] = key;             /* drop the key into its slot (a store) */
    }
}

/* ------------------------------------------------------------------ */
/* Benchmark interface (matches the other kernels in this directory)  */
/* ------------------------------------------------------------------ */

void embench_insertsort_initialise(void)
{
}

void embench_insertsort_warm_caches(int heat)
{
    int h;
    for (h = 0; h < heat; ++h) {
        initialise_worstcase();
        insertion_sort(Array, NUMELEMS);
    }
}

int embench_insertsort_run(void)
{
    unsigned int hash = 0u;
    unsigned int rep;
    int i;

    for (rep = 0u; rep < INSERTSORT_REPEATS; ++rep) {
        initialise_worstcase();
        insertion_sort(Array, NUMELEMS);
    }

    for (i = 0; i < NUMELEMS; ++i)
        hash = (hash * 131u) ^ (unsigned int)Array[i];

    return (int)hash;
}

int embench_insertsort_verify(int result)
{
    int i;

    /* structural check: strictly ascending [1, 2, ..., 100] */
    for (i = 0; i < NUMELEMS; ++i) {
        if (Array[i] != i + 1)
            return 0;
    }

    return ((unsigned int)result == INSERTSORT_VERIFY);
}
