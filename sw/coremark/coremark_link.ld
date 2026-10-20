OUTPUT_ARCH(riscv)
ENTRY(_start)

/* The hardware has one unified AXI backing RAM; this CoreMark build raises it to 8192 words.  The address
 * decoder exposes a larger cacheable window, but axi_ram_32 returns SLVERR for
 * every word above this physical 32-KiB range. */
MEMORY
{
    RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 32K
}

__ram_base     = ORIGIN(RAM);
__ram_size     = LENGTH(RAM);
__stack_size   = 0x400;                 /* 1 KiB, reserved and checked */
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
       "firmware data/BSS overlaps the reserved 1-KiB stack")
