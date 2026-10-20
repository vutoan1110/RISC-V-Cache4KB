#ifndef EMBENCH_BEEBS_H
#define EMBENCH_BEEBS_H

#include <stddef.h>
#include <stdint.h>

#ifndef RAND_MAX
#define RAND_MAX ((1U << 15) - 1U)
#endif

int rand_beebs(void);
void srand_beebs(unsigned int new_seed);
void init_heap_beebs(void *heap, size_t heap_size);
int check_heap_beebs(void *heap);
void *malloc_beebs(size_t size);
void *calloc_beebs(size_t nmemb, size_t size);
void *realloc_beebs(void *ptr, size_t size);
void free_beebs(void *ptr);

#endif
