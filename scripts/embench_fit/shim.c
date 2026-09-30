/* Minimal freestanding pieces the upstream Embench sources need on this SoC (no libc for rv32i/ilp32 in
   the toolchain). Size-measurement harness only (FLOW_JOURNAL / Embench fit study, 2026-09-29). */
#include <stddef.h>
void initialise_board(void) {}
void start_trigger(void) {}
void stop_trigger(void) {}
void *memcpy(void *d, const void *s, size_t n) { unsigned char *a = d; const unsigned char *b = s; while (n--) *a++ = *b++; return d; }
void *memmove(void *d, const void *s, size_t n) { unsigned char *a = d; const unsigned char *b = s; if (a < b) { while (n--) *a++ = *b++; } else { a += n; b += n; while (n--) *--a = *--b; } return d; }
void *memset(void *d, int c, size_t n) { unsigned char *a = d; while (n--) *a++ = (unsigned char)c; return d; }
int memcmp(const void *x, const void *y, size_t n) { const unsigned char *a = x, *b = y; for (; n; n--, a++, b++) if (*a != *b) return *a - *b; return 0; }
size_t strlen(const char *s) { size_t n = 0; while (s[n]) n++; return n; }
int strcmp(const char *a, const char *b) { while (*a && *a == *b) { a++; b++; } return (unsigned char)*a - (unsigned char)*b; }
int strncmp(const char *a, const char *b, size_t n) { for (; n; n--, a++, b++) { if (*a != *b || !*a) return (unsigned char)*a - (unsigned char)*b; } return 0; }
char *strcpy(char *d, const char *s) { char *r = d; while ((*d++ = *s++)); return r; }
char *strchr(const char *s, int c) { for (; *s; s++) if (*s == (char)c) return (char *)s; return c ? 0 : (char *)s; }
int abs(int x) { return x < 0 ? -x : x; }
void abort(void) { for (;;) ; }
double sqrt(double x) { double r = x > 1 ? x / 2 : 1; for (int i = 0; i < 30; i++) r = 0.5 * (r + x / r); return x <= 0 ? 0 : r; }
