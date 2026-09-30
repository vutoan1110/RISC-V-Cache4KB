#ifndef EMBENCH_MONT64_H
#define EMBENCH_MONT64_H

void embench_mont64_initialise(void);
void embench_mont64_warm_caches(int heat);
int  embench_mont64_run(void);
int  embench_mont64_verify(int result);

#endif
