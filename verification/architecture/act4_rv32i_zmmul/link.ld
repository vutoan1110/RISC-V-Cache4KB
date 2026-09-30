/* ACT4 core-verification linker map. The 512 KiB external harness RAM is
 * testbench-only; it does not change the active SoC/FPGA memory map. */
/* 0x0000-0x1fff remains a NOP trampoline in the DUT harness. Spike reserves
 * these pages for its debug module and boot ROM, so both models load the ELF
 * at the first non-overlapping page, 0x2000. */
RAM_ORIGIN = 0x00002000;
RAM_LENGTH = 0x00080000;
TEST_BASE = RAM_ORIGIN;
NUM_HARTS = 1;
STACK_SIZE = 0x800;
TOHOST_BASE = 0x00081ff0;

OUTPUT_ARCH("riscv")
ENTRY(rvtest_entry_point)

MEMORY
{
  ram (rwx) : ORIGIN = RAM_ORIGIN, LENGTH = RAM_LENGTH
}

PROVIDE(__stack_size = STACK_SIZE);
PROVIDE(__num_harts = NUM_HARTS);

SECTIONS
{
  .text.init TEST_BASE : { *(.text.init) } > ram
  .text.rvtest . : { *(.text.rvtest) *(.text.rvtest.*) } > ram

  . = ALIGN(16);
  .rodata . : { *(.rodata) *(.rodata.*) *(.srodata) *(.srodata.*) } > ram
  .data . : { *(.data) *(.data.*) *(.sdata) *(.sdata.*) } > ram

  . = ALIGN(16);
  .bss . (NOLOAD) :
  {
    __bss_start = .;
    *(.sbss) *(.sbss.*) *(.bss) *(.bss.*) *(COMMON)
    . = ALIGN(16);
    __bss_end = .;
  } > ram

  . = ALIGN(16);
  __stack_bottom = .;
  . += __stack_size * __num_harts;
  __stack_top = .;

  . = ALIGN(16);
  .text.rvmodel . : { *(.text.rvmodel) *(.text.rvmodel.*) *(.text) *(.text.*) } > ram

  _act_payload_end = .;
  ASSERT(_act_payload_end <= TOHOST_BASE,
         "ACT4 ELF exceeds the 512 KiB architecture-test RAM before tohost")

  .tohost TOHOST_BASE : { KEEP(*(.tohost)) } > ram
  ASSERT(SIZEOF(.tohost) <= 16, "tohost/fromhost section is larger than 16 bytes")

  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
