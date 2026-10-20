// uvm_reg model of the APB peripherals.
//
// There is no external APB master: the CPU drives the bus through the
// AXI-Lite bridge. The model is therefore kept up to date by explicit
// prediction from the APB monitor, which is the standard arrangement when the
// stimulus comes from software rather than from the testbench. The mirrored
// values are reported at end of test.
//
// Address maps come from hdl/uart_apb.v, hdl/apb_timer.v and
// hdl/apb_performance_monitor.v.

// uvm_reg is abstract, so every register in the model is an instance of this
// one-field concrete register. Width and access are set before build().
class soc_generic_reg extends uvm_reg;

    rand uvm_reg_field value;

    int unsigned reg_width  = 32;
    string       reg_access = "RW";
    uvm_reg_data_t reg_reset = 0;

    `uvm_object_utils(soc_generic_reg)

    function new(string name = "soc_generic_reg");
        super.new(name, 32, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();
        value = uvm_reg_field::type_id::create("value");
        value.configure(this, reg_width, 0, reg_access, 0, reg_reset, 1, 0, 1);
    endfunction

endclass

// Shared helper: create, configure and map one register.
function automatic soc_generic_reg make_reg(uvm_reg_block blk, uvm_reg_map map,
                                            string name, int unsigned offset,
                                            string access, int unsigned width,
                                            uvm_reg_data_t reset = 0);
    soc_generic_reg r = soc_generic_reg::type_id::create(name);
    r.reg_width  = width;
    r.reg_access = access;
    r.reg_reset  = reset;
    r.configure(blk, null, "");
    r.build();
    map.add_reg(r, offset, access);
    return r;
endfunction

class uart_reg_block extends uvm_reg_block;

    rand soc_generic_reg tx_data;    // 0x00 W: byte to transmit
    rand soc_generic_reg rx_data;    // 0x04 R: received byte
    rand soc_generic_reg cfg;        // 0x08 RW: baud divider and framing
    rand soc_generic_reg ctrl;       // 0x0C RW: start and enable strobes
    rand soc_generic_reg status;     // 0x10 R: tx/rx done, parity error, [5] tx FIFO full, [6] rx FIFO empty

    `uvm_object_utils(uart_reg_block)

    function new(string name = "uart_reg_block");
        super.new(name, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();
        default_map = create_map("uart_map", 0, 4, UVM_LITTLE_ENDIAN);
        tx_data = make_reg(this, default_map, "tx_data", 32'h00, "WO", 8);
        rx_data = make_reg(this, default_map, "rx_data", 32'h04, "RO", 8);
        cfg     = make_reg(this, default_map, "cfg",     32'h08, "RW", 32);
        ctrl    = make_reg(this, default_map, "ctrl",    32'h0C, "RW", 32);
        // Reset value 0x40: the RX FIFO is empty out of reset.
        status  = make_reg(this, default_map, "status",  32'h10, "RO", 7, 7'h40);
        lock_model();
    endfunction

endclass

class timer_reg_block extends uvm_reg_block;

    rand soc_generic_reg ctrl;       // 0x00 RW
    rand soc_generic_reg cmp;        // 0x04 RW
    rand soc_generic_reg count;      // 0x08 RW
    rand soc_generic_reg status;     // 0x0C write-one-to-clear pending flag

    `uvm_object_utils(timer_reg_block)

    function new(string name = "timer_reg_block");
        super.new(name, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();
        default_map = create_map("timer_map", 0, 4, UVM_LITTLE_ENDIAN);
        ctrl   = make_reg(this, default_map, "ctrl",   32'h00, "RW", 32);
        cmp    = make_reg(this, default_map, "cmp",    32'h04, "RW", 32);
        count  = make_reg(this, default_map, "count",  32'h08, "RW", 32);
        status = make_reg(this, default_map, "status", 32'h0C, "RW", 32);
        lock_model();
    endfunction

endclass

class sysmon_reg_block extends uvm_reg_block;

    rand soc_generic_reg ident;      // 0x00 R: 0x53380002 (ABI v2: 0xAC/0xB0 bus write error)
    rand soc_generic_reg ctrl;       // 0x04 RW: command port and state
    rand soc_generic_reg seq_num;    // 0x08 R: snapshot sequence
    rand soc_generic_reg mcause;     // 0x0C R
    rand soc_generic_reg mcycle;     // 0x10 R
    rand soc_generic_reg bus_err;    // 0xAC R/W1C: posted-write BRESP error (ABI v2)
    rand soc_generic_reg bus_err_addr; // 0xB0 R: address of the first failing write

    `uvm_object_utils(sysmon_reg_block)

    function new(string name = "sysmon_reg_block");
        super.new(name, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();
        default_map = create_map("sysmon_map", 0, 4, UVM_LITTLE_ENDIAN);
        ident   = make_reg(this, default_map, "ident",   32'h00, "RO", 32);
        ctrl    = make_reg(this, default_map, "ctrl",    32'h04, "RW", 32);
        seq_num = make_reg(this, default_map, "seq_num", 32'h08, "RO", 32);
        mcause  = make_reg(this, default_map, "mcause",  32'h0C, "RO", 32);
        mcycle  = make_reg(this, default_map, "mcycle",  32'h10, "RO", 32);
        bus_err = make_reg(this, default_map, "bus_err", 32'hAC, "W1C", 1);
        bus_err_addr = make_reg(this, default_map, "bus_err_addr", 32'hB0, "RO", 32);
        lock_model();
    endfunction

endclass

// One block per APB page of hdl/bus/soc_address_decoder.v.
class soc_reg_model extends uvm_reg_block;

    rand uart_reg_block   uart;
    rand timer_reg_block  timer;
    rand sysmon_reg_block sysmon;

    `uvm_object_utils(soc_reg_model)

    function new(string name = "soc_reg_model");
        super.new(name, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();
        default_map = create_map("soc_map", 0, 4, UVM_LITTLE_ENDIAN);

        uart = uart_reg_block::type_id::create("uart");
        uart.configure(this);
        uart.build();
        default_map.add_submap(uart.default_map, 32'h4000_0000);

        timer = timer_reg_block::type_id::create("timer");
        timer.configure(this);
        timer.build();
        default_map.add_submap(timer.default_map, 32'h4000_0200);

        sysmon = sysmon_reg_block::type_id::create("sysmon");
        sysmon.configure(this);
        sysmon.build();
        default_map.add_submap(sysmon.default_map, 32'h4000_0300);

        lock_model();
    endfunction

endclass
