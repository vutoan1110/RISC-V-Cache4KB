#ifndef EMBENCH_EDN_H
#define EMBENCH_EDN_H

void embench_edn_initialise(void);
void embench_edn_warm_caches(int heat);
int  embench_edn_run(void);
int  embench_edn_verify(int result);

#endif
