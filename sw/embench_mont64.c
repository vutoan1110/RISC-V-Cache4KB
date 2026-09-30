// Project-original kernel for RISCV-AHB-APB-UART. Not derived from Embench-IoT
// or Henry Warren's "Hacker's Delight" code. Implements 64-bit Montgomery
// modular multiplication (Montgomery, 1985 -- a published algorithm) built
// from 32-bit halves (RV32I has no 64-bit multiply), with a project-specific
// harness. Named after the Embench-IoT "aha-mont64" workload category; NOT an
// official Embench score. See docs/guides/05_EXTENDED_EMBENCH_BENCHMARKS.md.
#include "embench_mont64.h"

#define MONT64_VERIFY  0xda46d43eu
#define MONT64_ITER    16u

/* ------------------------------------------------------------------ */
/* 64-bit helpers built from 32-bit halves (hi:lo)                    */
/* ------------------------------------------------------------------ */

typedef struct { unsigned int lo; unsigned int hi; } u64_t;

static u64_t u64_from(unsigned int lo, unsigned int hi)
{
    u64_t r; r.lo = lo; r.hi = hi; return r;
}

static u64_t u64_add(u64_t a, u64_t b)
{
    u64_t r;
    r.lo = a.lo + b.lo;
    r.hi = a.hi + b.hi + (r.lo < a.lo ? 1u : 0u);
    return r;
}


/* Multiply two 32-bit numbers -> 64-bit result using RV32M MUL/MULHU */
static u64_t u32_mul64(unsigned int a, unsigned int b)
{
    u64_t r;
    r.lo = a * b;

    /* Use inline asm for MULHU if available, else portable: */
    unsigned int ahi = a >> 16, alo = a & 0xFFFFu;
    unsigned int bhi = b >> 16, blo = b & 0xFFFFu;
    unsigned int p0 = alo * blo;
    unsigned int p1 = alo * bhi;
    unsigned int p2 = ahi * blo;
    unsigned int p3 = ahi * bhi;
    unsigned int mid = p1 + p2;
    unsigned int carry1 = (mid < p1) ? 0x10000u : 0u;
    unsigned int upper = p3 + (mid >> 16) + carry1;
    unsigned int lower = p0 + (mid << 16);
    unsigned int carry2 = (lower < p0) ? 1u : 0u;
    r.lo = lower;
    r.hi = upper + carry2;
    return r;
}

/* ------------------------------------------------------------------ */
/* Montgomery reduction: compute  a*b * R^{-1}  mod m                 */
/*   R = 2^32, m is odd                                               */
/* ------------------------------------------------------------------ */

static unsigned int mont_inv(unsigned int m)
{
    /* Compute -m^{-1} mod 2^32  using Newton's method */
    unsigned int x = 1u;
    unsigned int i;
    for (i = 0; i < 5; ++i)
        x = x * (2u - m * x);
    return (unsigned int)(-(int)x);
}

static unsigned int mont_reduce(u64_t t, unsigned int m, unsigned int m_inv)
{
    unsigned int u = t.lo * m_inv;
    u64_t um = u32_mul64(u, m);
    u64_t s  = u64_add(t, um);
    /* result is s.hi (the upper word) */
    unsigned int res = s.hi;
    if (res >= m)
        res -= m;
    return res;
}

static unsigned int mont_mul(unsigned int a, unsigned int b,
                             unsigned int m, unsigned int m_inv)
{
    u64_t t = u32_mul64(a, b);
    return mont_reduce(t, m, m_inv);
}

/* Montgomery modular exponentiation: base^exp mod m */
static unsigned int mont_powmod(unsigned int base, unsigned int exp,
                                unsigned int m)
{
    unsigned int m_inv = mont_inv(m);
    /* R mod m = (2^32) mod m, computed as (-m) mod m ... simplified: */
    unsigned int r_mod_m = (unsigned int)(-(int)m) ;  /* 2^32 - m for m < 2^31 */
    /* We still need R mod m properly: try small subtraction loop */
    while (r_mod_m >= m) r_mod_m -= m;

    /* Convert base to Montgomery form: a_mont = base * R mod m */
    unsigned int a_mont = mont_reduce(u32_mul64(base, r_mod_m), m, m_inv);
    /* result = R mod m (= 1 in Montgomery form) */
    unsigned int result = mont_reduce(u32_mul64(1u, r_mod_m), m, m_inv);

    while (exp > 0u) {
        if (exp & 1u)
            result = mont_mul(result, a_mont, m, m_inv);
        a_mont = mont_mul(a_mont, a_mont, m, m_inv);
        exp >>= 1;
    }

    /* Convert back from Montgomery: result * 1 * R^{-1} mod m */
    result = mont_reduce(u64_from(result, 0u), m, m_inv);
    return result;
}

/* ------------------------------------------------------------------ */
/* Embench interface                                                  */
/* ------------------------------------------------------------------ */

void embench_mont64_initialise(void) { }
void embench_mont64_warm_caches(int heat) { (void)heat; }

int embench_mont64_run(void)
{
    static const unsigned int moduli[] = {
        0x7FFFFFEDu,  /* Curve25519 prime-like */
        0x7FFFFFFF,   /* Mersenne-like */
        0x01000003u,  /* small odd */
        0xFFFFFFFBu   /* large odd */
    };
    unsigned int hash = 0u;
    unsigned int iter;

    for (iter = 0u; iter < MONT64_ITER; ++iter) {
        unsigned int q;
        for (q = 0u; q < 4u; ++q) {
            unsigned int m = moduli[q];
            unsigned int base = 0x12345678u ^ (iter * 17u) ^ (q * 0x9Du);
            unsigned int exp  = 0x0000FFu + iter + q;
            /* Make sure base < m */
            if (base >= m) base = base - m;
            if (base == 0u) base = 1u;

            unsigned int res = mont_powmod(base, exp, m);
            hash = ((hash * 131u) ^ res ^ iter);
        }
    }

    return (int)hash;
}

int embench_mont64_verify(int result)
{
    return ((unsigned int)result == MONT64_VERIFY);
}
