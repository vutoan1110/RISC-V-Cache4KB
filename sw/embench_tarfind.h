#ifndef EMBENCH_TARFIND_H
#define EMBENCH_TARFIND_H

void embench_tarfind_initialise(void);
void embench_tarfind_warm_caches(int heat);
int  embench_tarfind_run(void);
int  embench_tarfind_verify(int result);

#endif
