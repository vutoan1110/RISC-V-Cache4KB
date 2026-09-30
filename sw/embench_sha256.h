#ifndef EMBENCH_SHA256_H
#define EMBENCH_SHA256_H

void embench_sha256_initialise(void);
void embench_sha256_warm_caches(int heat);
int  embench_sha256_run(void);
int  embench_sha256_verify(int result);

#endif
