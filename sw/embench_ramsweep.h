#ifndef EMBENCH_RAMSWEEP_H
#define EMBENCH_RAMSWEEP_H

/* R14 (2026-09-29, RAM16K_CHANGES.md): memory test, not a benchmark. It writes and reads back every
 * free word of the 16 KiB unified RAM (image end .. stack bottom) with word, byte and halfword stores,
 * so that all eight SRAM banks of the ASIC RAM wrapper and every byte lane are exercised. */
void embench_ramsweep_initialise(void);
void embench_ramsweep_warm_caches(int heat);
int  embench_ramsweep_run(void);
int  embench_ramsweep_verify(int result);
unsigned int embench_ramsweep_words(void);

#endif
