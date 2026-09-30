// Project-original kernel for RISCV-AHB-APB-UART. Not derived from Embench-IoT
// or Scott Robert Ladd's huffbench source. Implements static Huffman coding
// (Huffman, 1952 -- a published algorithm) over four fixed text corpora with a
// project-specific harness. Named after the Embench-IoT "huffbench" (entropy
// coding) workload category; NOT an official Embench score.
// See docs/guides/05_EXTENDED_EMBENCH_BENCHMARKS.md.
#include "embench_huffbench.h"

#define HUFF_VERIFY 0x47c0a5f0u
#define HUFF_ITER   16u
#define MAX_ENCODED_BYTES 64u

static const char corpus0[] = "TEST ONE, TEST ONE.";
static const char corpus1[] = "A TONE IS A TONE.";
static const char corpus2[] = "NO NOISE, NO TERROR.";
static const char corpus3[] = "RAISE A STONE, A NOISE.";

static unsigned int str_len_local(const char *s)
{
    unsigned int n = 0u;
    while (s[n] != '\0') {
        n++;
    }
    return n;
}

static void symbol_to_code(char ch, unsigned int *code, unsigned int *nbits)
{
    switch (ch) {
    case 'S': *code = 0x0u;  *nbits = 3u; break;   /* 000   */
    case 'I': *code = 0x2u;  *nbits = 4u; break;   /* 0010  */
    case 'N': *code = 0x3u;  *nbits = 4u; break;   /* 0011  */
    case 'O': *code = 0x2u;  *nbits = 3u; break;   /* 010   */
    case 'A': *code = 0x3u;  *nbits = 3u; break;   /* 011   */
    case 'T': *code = 0x4u;  *nbits = 3u; break;   /* 100   */
    case 'E': *code = 0x5u;  *nbits = 3u; break;   /* 101   */
    case ' ': *code = 0x6u;  *nbits = 3u; break;   /* 110   */
    case '.': *code = 0xEu;  *nbits = 4u; break;   /* 1110  */
    case ',': *code = 0x1Eu; *nbits = 5u; break;   /* 11110 */
    case 'R': *code = 0x1Fu; *nbits = 5u; break;   /* 11111 */
    default:  *code = 0x6u;  *nbits = 3u; break;   /* map unknown to space */
    }
}

static unsigned int get_bit(const unsigned char *buf, unsigned int bit_pos)
{
    unsigned int byte_pos = bit_pos >> 3;
    unsigned int lane_pos = 7u - (bit_pos & 7u);
    return (unsigned int)((buf[byte_pos] >> lane_pos) & 1u);
}

static char decode_symbol(const unsigned char *buf, unsigned int *bit_pos)
{
    unsigned int code = 0u;
    unsigned int bits = 0u;

    while (bits < 5u) {
        code = (code << 1) | get_bit(buf, *bit_pos);
        *bit_pos = *bit_pos + 1u;
        bits++;

        if ((bits == 3u) && (code == 0x0u)) return 'S';
        if ((bits == 3u) && (code == 0x2u)) return 'O';
        if ((bits == 3u) && (code == 0x3u)) return 'A';
        if ((bits == 3u) && (code == 0x4u)) return 'T';
        if ((bits == 3u) && (code == 0x5u)) return 'E';
        if ((bits == 3u) && (code == 0x6u)) return ' ';
        if ((bits == 4u) && (code == 0x2u)) return 'I';
        if ((bits == 4u) && (code == 0x3u)) return 'N';
        if ((bits == 4u) && (code == 0xEu)) return '.';
        if ((bits == 5u) && (code == 0x1Eu)) return ',';
        if ((bits == 5u) && (code == 0x1Fu)) return 'R';
    }

    return '?';
}

static unsigned int encode_message(const char *msg, unsigned char *encoded)
{
    unsigned int bit_count = 0u;
    unsigned int i;

    for (i = 0u; i < MAX_ENCODED_BYTES; ++i) {
        encoded[i] = 0u;
    }

    for (i = 0u; msg[i] != '\0'; ++i) {
        unsigned int code;
        unsigned int nbits;
        unsigned int b;

        symbol_to_code(msg[i], &code, &nbits);

        for (b = 0u; b < nbits; ++b) {
            unsigned int src_bit = nbits - 1u - b;
            unsigned int bit_val = (code >> src_bit) & 1u;
            unsigned int byte_pos = bit_count >> 3;
            unsigned int lane_pos = 7u - (bit_count & 7u);

            if (bit_val != 0u) {
                encoded[byte_pos] = (unsigned char)(encoded[byte_pos] | (unsigned char)(1u << lane_pos));
            }
            bit_count++;
        }
    }

    return bit_count;
}

static unsigned int run_one_message(const char *msg, unsigned int iter, unsigned int hash)
{
    unsigned char encoded[MAX_ENCODED_BYTES];
    unsigned int bit_count;
    unsigned int pos = 0u;
    unsigned int i;
    unsigned int full_bytes;

    bit_count = encode_message(msg, encoded);

    for (i = 0u; i < str_len_local(msg); ++i) {
        char dec = decode_symbol(encoded, &pos);
        hash = ((hash * 131u) ^ (unsigned int)(unsigned char)dec ^ iter);
    }

    full_bytes = (bit_count + 7u) >> 3;
    for (i = 0u; i < full_bytes; ++i) {
        hash = ((hash * 17u) + (unsigned int)encoded[i] + bit_count);
    }

    return hash;
}

void embench_huffbench_initialise(void)
{
}

void embench_huffbench_warm_caches(int heat)
{
    (void)heat;
}

int embench_huffbench_run(void)
{
    unsigned int iter;
    unsigned int hash = 0u;

    for (iter = 0u; iter < HUFF_ITER; ++iter) {
        hash = run_one_message(corpus0, iter, hash);
        hash = run_one_message(corpus1, iter, hash);
        hash = run_one_message(corpus2, iter, hash);
        hash = run_one_message(corpus3, iter, hash);
    }

    return (int)hash;
}

int embench_huffbench_verify(int result)
{
    return ((unsigned int)result == HUFF_VERIFY);
}
