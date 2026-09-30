// Project-original kernel for RISCV-AHB-APB-UART. Not derived from Nettle,
// the Embench-IoT "nettle-sha256" port, or any other implementation. A fresh
// implementation of SHA-256 exactly as specified in FIPS PUB 180-4 (a public
// U.S. government standard; the K constants and Sigma/sigma functions are part
// of that spec and are not copyrightable), with a project-specific harness.
// Named after the "sha256" (cryptographic hash) workload category; NOT an
// official Embench score. See docs/guides/05_EXTENDED_EMBENCH_BENCHMARKS.md.
#include "embench_sha256.h"

#define SHA256_VERIFY     0xE2E6EE70u
#define SHA256_ITER       4u

#define ROTR(n, x)  (((x) >> (n)) | ((x) << (32 - (n))))
#define SHR(n, x)   ((x) >> (n))

#define Ch(x,y,z)    (((x) & (y)) ^ ((~(x)) & (z)))
#define Maj(x,y,z)   (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define Sigma0(x)    (ROTR(2,(x))  ^ ROTR(13,(x)) ^ ROTR(22,(x)))
#define Sigma1(x)    (ROTR(6,(x))  ^ ROTR(11,(x)) ^ ROTR(25,(x)))
#define sigma0(x)    (ROTR(7,(x))  ^ ROTR(18,(x)) ^ SHR(3,(x)))
#define sigma1(x)    (ROTR(17,(x)) ^ ROTR(19,(x)) ^ SHR(10,(x)))

static const unsigned int K[64] = {
    0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u,
    0x3956c25bu, 0x59f111f1u, 0x923f82a4u, 0xab1c5ed5u,
    0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u,
    0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u,
    0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu,
    0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
    0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u,
    0xc6e00bf3u, 0xd5a79147u, 0x06ca6351u, 0x14292967u,
    0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u,
    0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u,
    0xa2bfe8a1u, 0xa81a664bu, 0xc24b8b70u, 0xc76c51a3u,
    0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
    0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u,
    0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu, 0x682e6ff3u,
    0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u,
    0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u
};

static const unsigned int H0[8] = {
    0x6a09e667u, 0xbb67ae85u, 0x3c6ef372u, 0xa54ff53au,
    0x510e527fu, 0x9b05688cu, 0x1f83d9abu, 0x5be0cd19u
};

static void sha256_compress(unsigned int state[8], unsigned int W[64])
{
    unsigned int a, b, c, d, e, f, g, h;
    unsigned int i;

    /* Expand message schedule */
    for (i = 16; i < 64; ++i) {
        W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];
    }

    a = state[0]; b = state[1]; c = state[2]; d = state[3];
    e = state[4]; f = state[5]; g = state[6]; h = state[7];

    /* 64 rounds */
    for (i = 0; i < 64; ++i) {
        unsigned int T1 = h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i];
        unsigned int T2 = Sigma0(a) + Maj(a, b, c);
        h = g; g = f; f = e; e = d + T1;
        d = c; c = b; b = a; a = T1 + T2;
    }

    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
    state[4] += e; state[5] += f; state[6] += g; state[7] += h;
}

static void sha256_hash(const unsigned int *msg_words, unsigned int msg_len, unsigned int digest[8])
{
    unsigned int W[64];
    unsigned int i;
    unsigned int bit_len;
    unsigned int num_words = msg_len / 4;
    unsigned int rem_bytes = msg_len % 4;
    unsigned int last_word;

    for (i = 0; i < 8; ++i) digest[i] = H0[i];
    for (i = 0; i < 16; ++i) W[i] = 0;

    for (i = 0; i < num_words; ++i) W[i] = msg_words[i];

    last_word = msg_words[num_words];
    if (rem_bytes == 0)      W[num_words] = 0x80000000u;
    else if (rem_bytes == 1) W[num_words] = (last_word & 0xFF000000u) | 0x00800000u;
    else if (rem_bytes == 2) W[num_words] = (last_word & 0xFFFF0000u) | 0x00008000u;
    else if (rem_bytes == 3) W[num_words] = (last_word & 0xFFFFFF00u) | 0x00000080u;

    bit_len = msg_len * 8u;
    W[15] = bit_len;

    sha256_compress(digest, W);
}

void embench_sha256_initialise(void) { }
void embench_sha256_warm_caches(int heat) { (void)heat; }

int embench_sha256_run(void)
{
    /* Test vectors packed into 32-bit big-endian words to avoid char arrays */
    static const unsigned int msg0_words[4] = { 0x61626300, 0, 0, 0 }; // "abc"
    static const unsigned int msg1_words[4] = { 0x52495343, 0x562D536F, 0x432D4441, 0x544E0000 }; // "RISCV-SoC-DATN"
    static const unsigned int msg2_words[4] = { 0x656D6265, 0x6E63682D, 0x696F742D, 0x73686100 }; // "embench-iot-sha"
    static const unsigned int msg3_words[4] = { 0x74657374, 0x31323334, 0x35363738, 0x39302100 }; // "test1234567890!"

    const unsigned int *msgs[]  = { msg0_words, msg1_words, msg2_words, msg3_words };
    const unsigned int  lens[]  = { 3, 14, 15, 15 };

    unsigned int hash = 0u;
    unsigned int digest[8];
    unsigned int iter, m, i;

    for (iter = 0u; iter < SHA256_ITER; ++iter) {
        for (m = 0u; m < 4u; ++m) {
            sha256_hash(msgs[m], lens[m], digest);

            for (i = 0; i < 8; ++i) {
                hash = ((hash * 131u) ^ digest[i] ^ iter);
            }
        }
    }

    return (int)hash;
}

int embench_sha256_verify(int result)
{
    return ((unsigned int)result == SHA256_VERIFY);
}
