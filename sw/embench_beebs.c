#include "embench_beebs.h"

static unsigned long seed = 0;
static unsigned char *heap_ptr = (unsigned char *)0;
static unsigned char *heap_end = (unsigned char *)0;
static size_t heap_requested = 0;

static void *memset_beebs(void *dst, int value, size_t n) {
    unsigned char *p = (unsigned char *)dst;
    size_t i;
    for (i = 0; i < n; ++i)
        p[i] = (unsigned char)value;
    return dst;
}

int rand_beebs(void) {
    seed = (seed * 1103515245UL + 12345UL) & ((1UL << 31) - 1UL);
    return (int)(seed >> 16);
}

void srand_beebs(unsigned int new_seed) {
    seed = (unsigned long)new_seed;
}

void init_heap_beebs(void *heap, size_t heap_size) {
    heap_ptr = (unsigned char *)heap;
    heap_end = heap_ptr + heap_size;
    heap_requested = 0;
}

int check_heap_beebs(void *heap) {
    return (((unsigned char *)heap) + heap_requested) <= heap_end;
}

void *malloc_beebs(size_t size) {
    const size_t alignment = sizeof(void *);
    unsigned char *next_heap_ptr;
    size_t padding;
    void *new_ptr;

    if (size == 0 || heap_ptr == (unsigned char *)0)
        return (void *)0;

    next_heap_ptr = heap_ptr + size;
    heap_requested += size;

    if (((uintptr_t)next_heap_ptr % alignment) != 0U) {
        padding = alignment - ((uintptr_t)next_heap_ptr % alignment);
        next_heap_ptr += padding;
        heap_requested += padding;
    }

    if (next_heap_ptr > heap_end)
        return (void *)0;

    new_ptr = (void *)heap_ptr;
    heap_ptr = next_heap_ptr;
    return new_ptr;
}

void *calloc_beebs(size_t nmemb, size_t size) {
    void *new_ptr = malloc_beebs(nmemb * size);
    if (new_ptr != (void *)0)
        memset_beebs(new_ptr, 0, nmemb * size);
    return new_ptr;
}

void *realloc_beebs(void *ptr, size_t size) {
    unsigned char *dst;
    unsigned char *src;
    void *new_ptr;
    size_t i;

    if (ptr == (void *)0)
        return (void *)0;

    new_ptr = malloc_beebs(size);
    if (new_ptr == (void *)0)
        return (void *)0;

    dst = (unsigned char *)new_ptr;
    src = (unsigned char *)ptr;
    for (i = 0; i < size; ++i)
        dst[i] = src[i];

    return new_ptr;
}

void free_beebs(void *ptr) {
    (void)ptr;
}