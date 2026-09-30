#ifndef EMBENCH_MATMULT_H
#define EMBENCH_MATMULT_H

void embench_matmult_initialise(void);
void embench_matmult_warm_caches(int heat);
int  embench_matmult_run(void);
int  embench_matmult_verify(int result);

#endif
