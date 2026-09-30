#ifndef EMBENCH_HUFFBENCH_H
#define EMBENCH_HUFFBENCH_H

void embench_huffbench_initialise(void);
void embench_huffbench_warm_caches(int heat);
int  embench_huffbench_run(void);
int  embench_huffbench_verify(int result);

#endif
