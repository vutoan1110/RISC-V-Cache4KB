#pragma once
#include <stddef.h>
int abs(int); void *malloc(size_t); void free(void *); void *calloc(size_t, size_t); void *realloc(void *, size_t);
int rand(void); void srand(unsigned); void exit(int); void abort(void); long strtol(const char *, char **, int); int atoi(const char *);
