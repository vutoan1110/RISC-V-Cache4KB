// Project-original kernel for RISCV-AHB-APB-UART. Not derived from Embench-IoT
// or MRTC/WCET source. Implements textbook fixed-point DSP filters (a 16-tap
// FIR and an IIR biquad, Q15) over a deterministic pseudo-random signal, with
// a project-specific harness. Named after the Embench-IoT "edn" (signal
// processing) workload category; NOT an official Embench score.
// See docs/guides/05_EXTENDED_EMBENCH_BENCHMARKS.md.
#include "embench_edn.h"

#define EDN_VERIFY  0x66c22c29
#define EDN_ITER    32u
#define N_TAPS      16u
#define N_DATA      32u

/* Fixed-point Q15 coefficients for a low-pass FIR filter */
static const int fir_coeffs[N_TAPS] = {
     158,   478,  1062,  1980,  3206,  4634,  6090,  7352,
    7352,  6090,  4634,  3206,  1980,  1062,   478,   158
};

/* IIR biquad coefficients (Q15 fixed-point) */
static const int iir_b[3] = {  4096,  8192,  4096 };
static const int iir_a[3] = { 16384, -24576, 10240 };

static int data_buf[N_DATA];

static void init_data(unsigned int seed)
{
    unsigned int i;
    for (i = 0u; i < N_DATA; ++i) {
        seed = (seed * 1103515245u + 12345u);
        data_buf[i] = (int)((seed >> 16) & 0x7FFFu) - 16384;
    }
}

/* ------------------------------------------------------------------ */
/* FIR filter: y[n] = sum(h[k] * x[n-k])                             */
/* ------------------------------------------------------------------ */
static int fir_filter(const int *input, int *output, unsigned int n_data,
                      const int *coeffs, unsigned int n_taps)
{
    unsigned int n, k;
    int checksum = 0;

    for (n = n_taps - 1u; n < n_data; ++n) {
        int acc = 0;
        for (k = 0u; k < n_taps; ++k) {
            acc += coeffs[k] * input[n - k];  /* uses MUL */
        }
        output[n] = acc >> 15;  /* Q15 -> integer */
        checksum ^= output[n];
    }
    return checksum;
}

/* ------------------------------------------------------------------ */
/* IIR biquad filter: Direct Form I                                   */
/* ------------------------------------------------------------------ */
static int iir_filter(const int *input, int *output, unsigned int n_data)
{
    int x1 = 0, x2 = 0, y1 = 0, y2 = 0;
    unsigned int n;
    int checksum = 0;

    for (n = 0u; n < n_data; ++n) {
        int x0 = input[n];
        int acc = iir_b[0] * x0 + iir_b[1] * x1 + iir_b[2] * x2
                - iir_a[1] * y1 - iir_a[2] * y2;
        int y0 = acc >> 14;

        x2 = x1; x1 = x0;
        y2 = y1; y1 = y0;
        output[n] = y0;
        checksum ^= y0;
    }
    return checksum;
}

/* ------------------------------------------------------------------ */
/* Dot product of two arrays                                          */
/* ------------------------------------------------------------------ */
static int dot_product(const int *a, const int *b, unsigned int n)
{
    int acc = 0;
    unsigned int i;
    for (i = 0u; i < n; ++i) {
        acc += a[i] * b[i];
    }
    return acc;
}

/* ------------------------------------------------------------------ */
/* Embench interface                                                  */
/* ------------------------------------------------------------------ */

void embench_edn_initialise(void) { }
void embench_edn_warm_caches(int heat) { (void)heat; }

int embench_edn_run(void)
{
    static int out_buf[N_DATA];
    unsigned int hash = 0u;
    unsigned int iter;

    for (iter = 0u; iter < EDN_ITER; ++iter) {
        int cs;

        init_data(0x5A5A5A5Au + iter * 31u);

        /* FIR */
        cs = fir_filter(data_buf, out_buf, N_DATA, fir_coeffs, N_TAPS);
        hash = ((hash * 131u) ^ (unsigned int)cs);

        /* IIR */
        cs = iir_filter(data_buf, out_buf, N_DATA);
        hash = ((hash * 17u) ^ (unsigned int)cs);

        /* Dot product */
        cs = dot_product(data_buf, out_buf, N_DATA);
        hash = ((hash * 65u) ^ (unsigned int)cs);
    }

    return (int)hash;
}

int embench_edn_verify(int result)
{
    return ((unsigned int)result == EDN_VERIFY);
}
