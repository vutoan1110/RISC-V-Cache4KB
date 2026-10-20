OUTPUT_ARCH(riscv)
ENTRY(rvtest_entry_point)

SECTIONS
{
    . = 0x00000000;
    .text.init : { *(.text.init) }
    .text.rvtest : { *(.text.rvtest) *(.text.rvtest.*) }
    .data : { *(.data) *(.data.*) *(.rodata) *(.rodata.*) }
    .text.rvmodel : {
        *(.text.rvmodel)
        *(.text.rvmodel.*)
        *(.text)
        *(.text.*)
    }
    .bss : { *(.bss) *(.bss.*) *(COMMON) }
    /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}

/* 0x0000fffc is reserved for the testbench tohost pass/fail word. */
