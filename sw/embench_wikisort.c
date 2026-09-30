// Project-original kernel for RISCV-AHB-APB-UART. This is a fresh, ~120-line
// implementation of a stable, in-place, bottom-up merge sort: small blocks are
// insertion-sorted, then merged in place using the classic three-reversal
// rotation ("block swap") technique. It is NOT a copy of BonzaiThePenguin's
// WikiSort (that code is ~1000 lines and, in any case, Public Domain / the
// Unlicense) nor of the Embench-IoT "wikisort" port. The algorithms used
// (insertion sort; in-place merge by rotation) are textbook and not
// copyrightable.
//
// NOTE: an earlier revision of this file was mistakenly tagged with a
// GPL-3.0 SPDX identifier. That marking was wrong -- the file contains no
// third-party code -- and has been removed. This is project-original work.
// The kernel is named after the Embench-IoT "wikisort" (sorting) workload
// category; the numbers are NOT an official Embench score.
// See docs/guides/05_EXTENDED_EMBENCH_BENCHMARKS.md.

#include "embench_wikisort.h"

#ifdef WIKISORT_TRACE
#include "platform.h"
#endif

#define WIKISORT_VERIFY 0xa1af1446u
#define WIKISORT_ITER   16u
#define SORT_SIZE       48u
#ifdef WIKISORT_TRACE
#define TRACE_VISIBLE_ITEMS 8u
#endif

static int arr[SORT_SIZE];

#ifdef WIKISORT_TRACE
static void trace_array(const char *phase, const int *a, unsigned int n)
{
    unsigned int i;

    uart_puts("TRACE_PHASE=");
    uart_puts(phase);
    uart_putc('\n');
    for (i = 0u; i < n; ++i) {
        uart_puts("TRACE_ITEM INDEX=0x");
        uart_puthex(i);
        uart_puts(" VALUE=0x");
        uart_puthex((unsigned int)a[i]);
        uart_putc('\n');
    }
}
#endif

/* ------------------------------------------------------------------ */
/* Insertion sort for small sub-arrays                                */
/* ------------------------------------------------------------------ */
static void insertion_sort(int *a, unsigned int n)
{
    unsigned int i, j;
    for (i = 1u; i < n; ++i) {
        int key = a[i];
        j = i;
        while (j > 0u && a[j - 1] > key) {
            a[j] = a[j - 1];
            --j;
        }
        a[j] = key;
    }
}

/* ------------------------------------------------------------------ */
/* In-place merge of a[lo..mid-1] and a[mid..hi-1]                    */
/* Uses rotation (no extra buffer needed, O(1) extra space)           */
/* ------------------------------------------------------------------ */
static void rotate(int *a, unsigned int lo, unsigned int mid, unsigned int hi)
{
    unsigned int i, j;
    int tmp;
    /* Reverse a[lo..mid-1] */
    i = lo; j = mid - 1;
    while (i < j) { tmp = a[i]; a[i] = a[j]; a[j] = tmp; ++i; --j; }
    /* Reverse a[mid..hi-1] */
    i = mid; j = hi - 1;
    while (i < j) { tmp = a[i]; a[i] = a[j]; a[j] = tmp; ++i; --j; }
    /* Reverse a[lo..hi-1] */
    i = lo; j = hi - 1;
    while (i < j) { tmp = a[i]; a[i] = a[j]; a[j] = tmp; ++i; --j; }
}

static void merge_inplace(int *a, unsigned int lo, unsigned int mid,
                          unsigned int hi)
{
    unsigned int i = lo;
    unsigned int j = mid;

    while (i < j && j < hi) {
        if (a[i] <= a[j]) {
            ++i;
        } else {
            /* Find run of elements in right half that are less */
            unsigned int k = j + 1;
            while (k < hi && a[k] < a[i]) ++k;
            rotate(a, i, j, k);
            i += (k - j);
            j = k;
        }
    }
}

/* ------------------------------------------------------------------ */
/* Bottom-up merge sort (stable, in-place via rotation)               */
/* ------------------------------------------------------------------ */
static void wiki_sort(int *a, unsigned int n)
{
    unsigned int width, i;

    /* Start with insertion sort on blocks of 8 */
    for (i = 0u; i < n; i += 8u) {
        unsigned int end = i + 8u;
        if (end > n) end = n;
        insertion_sort(a + i, end - i);
    }

    /* Bottom-up merging */
    for (width = 8u; width < n; width <<= 1) {
        for (i = 0u; i + width < n; i += width << 1) {
            unsigned int mid = i + width;
            unsigned int hi  = mid + width;
            if (hi > n) hi = n;
            merge_inplace(a, i, mid, hi);
        }
    }
}

static int is_sorted(const int *a, unsigned int n)
{
    unsigned int i;
    for (i = 1u; i < n; ++i) {
        if (a[i - 1] > a[i]) return 0;
    }
    return 1;
}

/* ------------------------------------------------------------------ */
/* Embench interface                                                  */
/* ------------------------------------------------------------------ */

void embench_wikisort_initialise(void) { }
void embench_wikisort_warm_caches(int heat) { (void)heat; }

int embench_wikisort_run(void)
{
    unsigned int hash = 0u;
    unsigned int iter;

#ifdef WIKISORT_TRACE
    uart_put_key_hex("TRACE_ARRAY_SIZE", SORT_SIZE);
    uart_put_key_hex("TRACE_VALUES_SHOWN", TRACE_VISIBLE_ITEMS);
#endif

    for (iter = 0u; iter < WIKISORT_ITER; ++iter) {
        unsigned int i;
        unsigned int seed = 0x12345678u ^ (iter * 0x9E3779B9u);
        int sorted;

#ifdef WIKISORT_TRACE
        uart_put_key_hex("TRACE_ITER_BEGIN", iter);
#endif

        /* Fill with pseudo-random data */
        for (i = 0u; i < SORT_SIZE; ++i) {
            seed = (seed * 1103515245u + 12345u);
            arr[i] = (int)((seed >> 10) & 0xFFFFu) - 32768;
        }

#ifdef WIKISORT_TRACE
        if (iter == 0u)
            trace_array("INPUT_ITER0_FIRST8", arr, TRACE_VISIBLE_ITEMS);
#endif

        /* Sort */
        wiki_sort(arr, SORT_SIZE);

        /* Verify sorted and hash result */
        sorted = is_sorted(arr, SORT_SIZE);
#ifdef WIKISORT_TRACE
        if (iter == 0u)
            trace_array("SORTED_ITER0_FIRST8", arr, TRACE_VISIBLE_ITEMS);
        uart_puts("TRACE_SORT_OK=");
        uart_puts(sorted ? "PASS\n" : "FAIL\n");
#endif
        if (!sorted)
            return -1;

        for (i = 0u; i < SORT_SIZE; ++i)
            hash = ((hash * 131u) ^ (unsigned int)arr[i]);

#ifdef WIKISORT_TRACE
        uart_put_key_hex("TRACE_HASH_AFTER_ITER", hash);
#endif
    }

#ifdef WIKISORT_TRACE
    uart_put_key_hex("TRACE_FINAL_HASH", hash);
#endif

    return (int)hash;
}

int embench_wikisort_verify(int result)
{
    return ((unsigned int)result == WIKISORT_VERIFY);
}
