#ifndef EMBENCH_MD5SUM_H
#define EMBENCH_MD5SUM_H

void embench_md5sum_initialise(void);
void embench_md5sum_warm_caches(int heat);
int  embench_md5sum_run(void);
int  embench_md5sum_verify(int result);

#endif
