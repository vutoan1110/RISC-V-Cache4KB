#ifndef EMBENCH_FDCT_H
#define EMBENCH_FDCT_H

void embench_fdct_initialise(void);
void embench_fdct_warm_caches(int heat);
int  embench_fdct_run(void);
int  embench_fdct_verify(int result);

#endif
