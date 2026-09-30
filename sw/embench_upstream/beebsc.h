#ifndef BEEBSC_H
#define BEEBSC_H
/* Project-written stand-in for Embench-IoT's beebsc.h: the project's embench_beebs.c implements the
 * same rand/heap API. */
#include "embench_beebs.h"
/* Upstream kernels stop on a failed internal check; the harness then never reports DONE. */
#define assert_beebs(expr) do { if (!(expr)) { for (;;) { } } } while (0)
#endif
