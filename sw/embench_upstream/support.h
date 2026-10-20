#ifndef SUPPORT_H
#define SUPPORT_H
/* Project-written stand-in for Embench-IoT's support/support.h (same declarations; the upstream file is
 * GPL-3.0 and is not copied). R14 upstream suite, RAM16K_CHANGES.md. main_upstream.c provides the board
 * hooks and drives initialise_benchmark / warm_caches / benchmark / verify_benchmark. */
void initialise_board(void);
void start_trigger(void);
void stop_trigger(void);
void initialise_benchmark(void);
void warm_caches(int temperature);
int benchmark(void) __attribute__((noinline));
int verify_benchmark(int res);
#include "beebsc.h"
#endif
