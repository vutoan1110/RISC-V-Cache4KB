#ifndef EMBENCH_INSERTSORT_H
#define EMBENCH_INSERTSORT_H

void embench_insertsort_initialise(void);
void embench_insertsort_warm_caches(int heat);
int  embench_insertsort_run(void);
int  embench_insertsort_verify(int result);

#endif
