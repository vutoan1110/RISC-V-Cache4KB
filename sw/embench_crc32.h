#ifndef EMBENCH_CRC32_H
#define EMBENCH_CRC32_H

void embench_crc32_initialise(void);
void embench_crc32_warm_caches(int heat);
int  embench_crc32_run(void);
int  embench_crc32_verify(int result);

#endif
