#ifndef EMBENCH_WIKISORT_H
#define EMBENCH_WIKISORT_H

void embench_wikisort_initialise(void);
void embench_wikisort_warm_caches(int heat);
int  embench_wikisort_run(void);
int  embench_wikisort_verify(int result);

#endif
