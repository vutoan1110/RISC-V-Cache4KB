/* sw_metrics/conflict/link_probe.ld -- sw/link.ld with a 512-byte stack (0x3E00-0x3FFF) and the image
 * kept below 0x0C00, so the conflict probe owns 0x0C00-0x3DFF (conflict_probe.c). */
OUTPUT_ARCH(riscv)
ENTRY(_start)

/* The hardware has one unified 4096-word AXI backing RAM (R14, 2026-09-29: was 2048 words; RAM16K_CHANGES.md).  The address
 * decoder exposes a larger cacheable window, but axi_ram_32 returns SLVERR for
 * every word above this physical 16-KiB range. */
MEMORY
{
    RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 16K
}

__ram_base     = ORIGIN(RAM);
__ram_size     = LENGTH(RAM);
__stack_size   = 0x200;                 /* 512 B: the probe region ends at 0x3E00 */
__stack_top    = ORIGIN(RAM) + LENGTH(RAM);
__stack_bottom = __stack_top - __stack_size;
_stack_top     = __stack_top;           /* preserve the original symbol */

SECTIONS
{
    . = ORIGIN(RAM);

    .text : ALIGN(4)
    {
        KEEP(*(.text.init))
        *(.text .text.*)
    } > RAM

    .rodata : ALIGN(4)
    {
        *(.rodata .rodata.*)
        *(.srodata .srodata.*)
    } > RAM

    .data : ALIGN(4)
    {
        __data_start = .;
        *(.sdata .sdata.*)
        *(.data .data.*)
        . = ALIGN(4);
        __data_end = .;
    } > RAM
    __data_load = LOADADDR(.data);

    .bss (NOLOAD) : ALIGN(4)
    {
        __bss_start = .;
        *(.sbss .sbss.*)
        *(.bss .bss.*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > RAM

    __image_end = ALIGN(4);
    __heap_start = __image_end;
    __heap_end = __stack_bottom;

    /* C is built with -msmall-data-limit=0, but startup still initializes gp
     * so hand-written code and future compatible objects have a valid value. */
    PROVIDE(__global_pointer$ = __data_start + 0x800);

    /DISCARD/ :
    {
        *(.comment)
        *(.note .note.*)
    }
}

ASSERT(_start == ORIGIN(RAM), "firmware entry is not at reset vector 0x00000000")
ASSERT(__image_end <= __stack_bottom,
       "firmware data/BSS overlaps the reserved stack")
ASSERT(__image_end <= 0x0C00,
       "conflict probe image reaches the probe region at 0x0C00")
