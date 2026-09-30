#ifndef EMBENCH_DEPTHCONV_H
#define EMBENCH_DEPTHCONV_H

void embench_depthconv_initialise(void);
void embench_depthconv_warm_caches(int heat);
int  embench_depthconv_run(void);
int  embench_depthconv_verify(int result);

#endif
