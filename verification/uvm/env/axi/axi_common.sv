// Shared configuration and transaction records for the cache_axi_master
// environment.

// Which native channel a request came from, matching the arbiter encoding in
// hdl/axi/cache_axi_master.v.
typedef enum bit [1:0] {
    SRC_ICACHE = 2'd0,
    SRC_DREAD  = 2'd1,
    SRC_DWRITE = 2'd2
} axi_src_e;

// One refill request and the four beats it produced.
class refill_item extends uvm_sequence_item;

    rand bit [31:0]  addr;
    bit [31:0]       beat[$];
    bit              error;
    bit              is_icache;
    longint unsigned accept_cycle;
    longint unsigned done_cycle;

    // The line is 16 bytes, so a refill address is always 16-byte aligned.
    constraint c_aligned { addr[3:0] == 4'h0; }

    `uvm_object_utils_begin(refill_item)
        `uvm_field_int(addr,      UVM_ALL_ON | UVM_HEX)
        `uvm_field_int(error,     UVM_ALL_ON)
        `uvm_field_int(is_icache, UVM_ALL_ON)
    `uvm_object_utils_end

    function new(string name = "refill_item");
        super.new(name);
    endfunction

    function string convert2string();
        return $sformatf("%s refill addr=0x%08h beats=%0d err=%0b",
                         is_icache ? "I" : "D", addr, beat.size(), error);
    endfunction

endclass

// One write-through request.
class wthru_item extends uvm_sequence_item;

    rand bit [31:0]  addr;
    rand bit [31:0]  data;
    rand bit [3:0]   strb;
    bit              error;
    longint unsigned accept_cycle;
    longint unsigned rsp_cycle;

    // hdl/axi/cache_axi_master.v takes a word-aligned address and a byte
    // strobe; an all-zero strobe would be a write with no effect.
    constraint c_aligned { addr[1:0] == 2'b00; }
    constraint c_strb    { strb != 4'h0; }

    `uvm_object_utils_begin(wthru_item)
        `uvm_field_int(addr, UVM_ALL_ON | UVM_HEX)
        `uvm_field_int(data, UVM_ALL_ON | UVM_HEX)
        `uvm_field_int(strb, UVM_ALL_ON | UVM_BIN)
    `uvm_object_utils_end

    function new(string name = "wthru_item");
        super.new(name);
    endfunction

    function string convert2string();
        return $sformatf("write addr=0x%08h data=0x%08h strb=%4b", addr, data, strb);
    endfunction

endclass

// What the AXI monitor saw on the bus.
typedef enum bit [1:0] {
    AXI_READ_BURST,
    AXI_WRITE
} axi_kind_e;

class axi_item extends uvm_sequence_item;

    axi_kind_e       kind;
    bit [31:0]       addr;
    bit [7:0]        len;
    bit [2:0]        size;
    bit [1:0]        burst;
    bit [31:0]       data[$];      // read beats, or the single write beat
    bit [3:0]        strb;
    bit [1:0]        resp;
    longint unsigned start_cycle;
    longint unsigned end_cycle;

    `uvm_object_utils(axi_item)

    function new(string name = "axi_item");
        super.new(name);
    endfunction

    function string convert2string();
        return $sformatf("%s addr=0x%08h len=%0d size=%0d burst=%0d beats=%0d resp=%0d",
                         kind.name(), addr, len, size, burst, data.size(), resp);
    endfunction

endclass

// Counters the scoreboard evaluates at end of test.
class axi_stats extends uvm_object;

    longint unsigned i_refill_req;
    longint unsigned i_refill_done;
    longint unsigned d_refill_req;
    longint unsigned d_refill_done;
    longint unsigned wthru_req;
    longint unsigned wthru_rsp;

    longint unsigned axi_read_burst;
    longint unsigned axi_write;
    longint unsigned axi_read_beats;

    longint unsigned max_outstanding_reads;
    longint unsigned posted_rsp_before_b;   // response ahead of the AXI B beat

    `uvm_object_utils(axi_stats)

    function new(string name = "axi_stats");
        super.new(name);
    endfunction

endclass

class axi_cfg extends uvm_object;

    virtual refill_if i_refill_vif;
    virtual refill_if d_refill_vif;
    virtual wthru_if  wthru_vif;
    virtual axi4_if   axi_vif;

    native_mem_model mem;          // the memory behind the AXI slave
    axi_stats        stats;

    int unsigned mem_size_bytes = 8192;

    // Words per cache line, which is also the refill burst length. The DUT
    // derives ARLEN from it, so the checkers must be told the same value
    // rather than assuming the four-word default.
    int unsigned refill_beats = 4;

    // AXI slave backpressure, in percent of cycles where the channel is not
    // ready. 0 keeps the slave always ready.
    int unsigned ar_stall_pct = 0;
    int unsigned r_stall_pct  = 0;
    int unsigned aw_stall_pct = 0;
    int unsigned w_stall_pct  = 0;
    int unsigned b_delay_max  = 0;

    int unsigned timeout_cycles = 100000;

    `uvm_object_utils(axi_cfg)

    function new(string name = "axi_cfg");
        super.new(name);
    endfunction

endclass
