#ifndef EMBENCH_WIKISORT_TRACE_H
#define EMBENCH_WIKISORT_TRACE_H

void embench_wikisort_trace_initialise(void);
void embench_wikisort_trace_warm_caches(int heat);
int  embench_wikisort_trace_run(void);
int  embench_wikisort_trace_verify(int result);

#endif
