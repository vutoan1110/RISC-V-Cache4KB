/* Separate trace build. The measured wikisort build remains unchanged because
 * WIKISORT_TRACE is defined only in this translation unit. */
#define WIKISORT_TRACE 1
#define embench_wikisort_initialise  embench_wikisort_trace_initialise
#define embench_wikisort_warm_caches embench_wikisort_trace_warm_caches
#define embench_wikisort_run         embench_wikisort_trace_run
#define embench_wikisort_verify      embench_wikisort_trace_verify
#include "embench_wikisort.c"
