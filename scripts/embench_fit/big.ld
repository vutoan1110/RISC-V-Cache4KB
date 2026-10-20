OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { RAM (rwx) : ORIGIN = 0x0, LENGTH = 1M }
SECTIONS {
  .text : { KEEP(*(.text.init)) *(.text .text.*) } > RAM
  .rodata : { *(.rodata .rodata.* .srodata .srodata.*) } > RAM
  .data : { *(.sdata .sdata.* .data .data.*) } > RAM
  .bss : { *(.sbss .sbss.* .bss .bss.* COMMON) } > RAM
  __stack_top = ORIGIN(RAM) + LENGTH(RAM);
}
