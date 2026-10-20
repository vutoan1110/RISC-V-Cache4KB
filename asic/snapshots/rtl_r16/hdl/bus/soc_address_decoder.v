module soc_address_decoder (
    input  wire [31:0] addr,
    output wire        sel_cacheable,
    output wire        sel_mmio,
    output wire        sel_uart,
    output wire        sel_display,
    output wire        sel_timer,
    output wire        sel_sysmon,
    output wire        sel_unmapped
);

// 64 KiB low window is cacheable; each APB peripheral owns a 256-byte page
// in 0x4000_0000.
assign sel_cacheable = (addr[31:16] == 16'h0000);
assign sel_uart      = (addr[31:8]  == 24'h4000_00);
assign sel_display   = (addr[31:8]  == 24'h4000_01);
assign sel_timer     = (addr[31:8]  == 24'h4000_02);
assign sel_sysmon    = (addr[31:8]  == 24'h4000_03);
assign sel_mmio      = sel_uart || sel_display || sel_timer || sel_sysmon;
assign sel_unmapped  = !sel_cacheable && !sel_mmio;

endmodule
