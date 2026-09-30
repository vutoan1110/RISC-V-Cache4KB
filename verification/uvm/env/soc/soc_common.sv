// Configuration, counters and transaction records for the SoC environment.

class apb_item extends uvm_sequence_item;

    bit [31:0]       addr;
    bit              write;
    bit [3:0]        strb;
    bit [31:0]       wdata;
    bit [31:0]       rdata;
    bit              slverr;
    longint unsigned cycle;

    `uvm_object_utils(apb_item)

    function new(string name = "apb_item");
        super.new(name);
    endfunction

    function string convert2string();
        return $sformatf("APB %s addr=0x%08h wdata=0x%08h rdata=0x%08h strb=%4b err=%0b",
                         write ? "WR" : "RD", addr, wdata, rdata, strb, slverr);
    endfunction

endclass

// One byte seen on, or to be sent over, the serial line.
class uart_byte_item extends uvm_sequence_item;

    rand bit [7:0]   data;
    bit              framing_error;
    longint unsigned cycle;

    `uvm_object_utils(uart_byte_item)

    function new(string name = "uart_byte_item");
        super.new(name);
    endfunction

    function string convert2string();
        return $sformatf("uart byte 0x%02h%s", data, framing_error ? " (framing error)" : "");
    endfunction

endclass

class soc_stats extends uvm_object;

    longint unsigned n_retire;
    longint unsigned n_retire_before_halt;
    bit              halt_seen;
    uvm_event        halt_e;

    longint unsigned n_cycle;
    longint unsigned onehot_violations;

    longint unsigned apb_read;
    longint unsigned apb_write;
    longint unsigned uart_tx_bytes;
    longint unsigned uart_rx_bytes;
    longint unsigned irq_taken;

    bit [31:0] arch_regs[32];

    `uvm_object_utils(soc_stats)

    function new(string name = "soc_stats");
        super.new(name);
        halt_e = new("halt_e");
        foreach (arch_regs[i]) arch_regs[i] = 32'h0;
    endfunction

endclass

class soc_cfg extends uvm_object;

    virtual soc_obs_if obs_vif;
    virtual apb_if     apb_vif;
    virtual uart_if    uart_vif;

    soc_stats     stats;
    soc_reg_model regs;

    bit [31:0]   halt_instr      = 32'h0000_006f;
    int unsigned expected_retire = 0;
    int unsigned timeout_cycles  = 200000;

    // 8N1 framing; the bit period is taken from the firmware's baud divider,
    // in clock cycles.
    int unsigned uart_bit_cycles = 434;   // 50 MHz / 115200

    `uvm_object_utils(soc_cfg)

    function new(string name = "soc_cfg");
        super.new(name);
    endfunction

endclass
