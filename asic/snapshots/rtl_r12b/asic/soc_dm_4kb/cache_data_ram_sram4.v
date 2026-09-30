// ASIC drop-in replacements for hdl/cache/icache_data_ram.v and
// hdl/cache/dcache_data_ram.v, backed by real Sky130 SRAM hard macros instead
// of register arrays.
//
// WHY THIS EXISTS. On the FPGA a capacity change is free: the arrays carry
// (* ramstyle = "M9K" *) and Quartus puts them in block RAM, so 64 to 256 lines
// costs block memory bits rather than logic. Yosys has no equivalent, so on the
// ASIC those `reg [31:0]` arrays synthesise to flip-flops:
//
//                            bits per cache      both caches
//     LINE_COUNT =  64    4 x  64 x 32 =  8,192      16,384 flops
//     LINE_COUNT = 256    4 x 256 x 32 = 32,768      65,536 flops
//
// Post-route at 1 KiB the whole chip has 27,642 sequential cells, so the two
// data arrays are already about 59% of every flop on the die. Taking them to
// 4 KiB in flip-flops would put the count near 77,000. That is not a design
// point worth measuring, which is what makes the macro mandatory rather than an
// optimisation.
//
// THE MACRO. A 4 KiB cache bank is exactly 32 bits x 256 words, which is
// sky130_sram_1kbyte_1rw1r_32x256_8 -- shipped in the PDK at
// libs.ref/sky130_sram_macros with LEF, GDS, lib, spice and verilog views. Four
// banks per cache, eight across instruction and data, alongside the four 2 KiB
// macros already used for main memory: twelve macros on the die.
//
// PORT MAPPING. The macro is 1rw1r, which is what this array needs: a full-line
// read across four banks while at most one bank is written.
//
//     port 1 (read only)   -> the read path. csb1 is the read enable, and
//                             dout1 is ALREADY REGISTERED by the macro, so
//                             rd_line becomes a wire and the one-cycle latency
//                             the controller expects is unchanged.
//     port 0 (read/write)  -> the write path. One bank at a time, selected by
//                             wr_word, so three of the four are deselected on
//                             any given write.
//
// Both csb signals are active low, as is web0.
//
// SAME-INDEX READ DURING WRITE. In the register-array version a read and a
// write to one index in the same cycle both use non-blocking assignment, so the
// read returns the OLD contents. An OpenRAM 1rw1r macro does not define what
// port 1 returns while port 0 writes the same address.
//
// The first draft of this file said the controller "is not believed to" do
// that. Checking instead of believing disproves it for the data cache:
//
//     dcache_controller.v:251   data_rd_en = ... || (state == ST_REFILL_DATA) || ...
//     dcache_controller.v:255   data_wr_en = ((state == ST_REFILL_DATA) && ...
//     dcache_controller.v:245   data_rd_index = (state == ST_IDLE) ? ... : request_index
//     dcache_controller.v:257   data_wr_index = request_index
//
// In ST_REFILL_DATA both enables assert and both indices are `request_index`.
// Every refill beat reads and writes the same row. The instruction cache is
// clear -- `data_rd_en = request_fire && !hot_hit` and `req_ready = (state ==
// ST_IDLE)`, while `data_wr_en = refill_write_beat` only outside ST_IDLE, so
// the two are mutually exclusive by state -- but the data cache is not.
//
// So the conflict is real and happens on every refill beat. This wrapper gives
// it a DEFINED behaviour: the read is suppressed on a same-index conflict, and
// dout1 holds its previous value rather than returning something undefined.
// That is not identical to the register model, which would have returned the
// old memory contents, and the difference is only harmless if no consumer uses
// the line read during ST_REFILL_DATA. The controller's own comment says the
// line is re-read in ST_CPU_RESP one cycle after the last write, which would
// make it harmless -- but that is again reasoning, not evidence.
//
// CONFLICT_REPORT counts the conflicts in simulation so the testbench can say
// how often this fires with real traffic. It must be run through
// tb/dcache_tb.sv and the directed regression before any number measured with
// this file is quoted.
//
// STATUS: written, NOT YET SIMULATED. The port list is identical to the modules
// it replaces so it drops in with no other RTL change, but nothing here has run
// yet. Treat every number produced from it as unverified until the full chain
// -- lint, 126 directed tests, UVM, the 48-run Embench matrix, each twice -- is
// clean on this file.

// ---------------------------------------------------------------------------
// Shared implementation. Both caches present byte-for-byte the same interface,
// so they differ only in the wrapper name.
// ---------------------------------------------------------------------------
module cache_data_ram_sram4 #(
    parameter LINE_COUNT  = 256,
    parameter INDEX_WIDTH = 8
)(
    input  wire                   clk,

    input  wire                   rd_en,
    input  wire [INDEX_WIDTH-1:0] rd_index,
    output wire [127:0]           rd_line,

    input  wire                   wr_en,
    input  wire [INDEX_WIDTH-1:0] wr_index,
    input  wire [1:0]             wr_word,
    input  wire [31:0]            wr_data
);

// R8 (NHAT_KY_RTL 2026-09-25): the macro's power pins, connected in the RTL
// view. Only under USE_POWER_PINS, which synthesis does not define, so the
// gate netlist is unchanged; the physical connection is made by OpenLane's PDN
// (PDN_MACRO_CONNECTIONS '.*u_bank VPWR VGND vccd1 vssd1') and LVS checks it on
// the powered netlist. Local supply nets rather than power ports threaded up
// through soc_top: the RTL above this wrapper is shared with the FPGA build.
`ifdef USE_POWER_PINS
    supply1 vccd1;
    supply0 vssd1;
`endif

// The macro is fixed at 256 words of 32 bits. Anything else silently maps the
// wrong depth, so refuse to elaborate rather than produce a wrong chip.
//
// The guard is simulation-only. Yosys reads this file happily during synthesis,
// but EQY invokes its Verilog frontend differently and cannot resolve $fatal:
//
//   cache_data_ram_sram4.v:105: ERROR: Can't resolve task name `$fatal'
//
// which failed read_gold and stopped the equivalence check before it started.
// `__openlane__` is defined by every OpenLane Yosys invocation and by none of
// the simulator runs, so this keeps the hard check where it can run and hides
// it where it cannot. It describes no hardware -- an `initial` block that only
// calls $display and $fatal drives nothing -- so the netlist is unchanged, and
// EQY itself is now the proof of that.
`ifndef __openlane__
initial begin
    if (LINE_COUNT != 256 || INDEX_WIDTH != 8) begin
        $display("cache_data_ram_sram4: LINE_COUNT=%0d INDEX_WIDTH=%0d, but ",
                 LINE_COUNT, INDEX_WIDTH,
                 "sky130_sram_1kbyte_1rw1r_32x256_8 is 32x256 (INDEX_WIDTH=8)");
        $fatal(1, "cache_data_ram_sram4: geometry does not match the macro");
    end
end
`endif

wire [31:0] bank_dout [0:3];
genvar gi;
generate
    for (gi = 0; gi < 4; gi = gi + 1) begin : g_bank
        // Write this bank only when the controller names it. csb0 and web0 are
        // active low; wmask0 is per-byte and every write here is full-word.
        wire sel_wr = wr_en && (wr_word == gi[1:0]);

        // Suppress this bank's read when it is the bank being written at the
        // same row: port 1 has no defined value while port 0 writes that
        // address. Only the written bank is suppressed -- the other three
        // still return their contents, so the line is three quarters fresh.
        wire conflict = sel_wr && rd_en && (rd_index == wr_index);
        wire bank_rd  = rd_en && !conflict;
        wire [31:0] bank_dout_raw;

        sky130_sram_1kbyte_1rw1r_32x256_8 u_bank (
`ifdef USE_POWER_PINS
            .vccd1 (vccd1),
            .vssd1 (vssd1),
`endif
            // port 0: write
            .clk0  (clk),
            .csb0  (~sel_wr),
            .web0  (1'b0),
            .wmask0(4'b1111),
            .addr0 (wr_index),
            .din0  (wr_data),
            .dout0 (),            // never read through port 0
            // port 1: read
            .clk1  (clk),
            .csb1  (~bank_rd),
            .addr1 (rd_index),
            .dout1 (bank_dout_raw)
        );

        // The macro drives dout1 only in the cycle after a read: the vendor
        // model makes it X from T_HOLD after every other clock edge, and a
        // read suppressed on a same-index conflict above never happens at
        // all. The cache controllers were designed and verified against a
        // registered read that HOLDS its value until the next read and
        // returns the old word on a same-index read-during-write, and the
        // data cache relies on it: dcache_controller.v switches the read off in
        // ST_WRITE_REQ and then, on the store commit, merges the stored word
        // into data_rd_line (store_line_next) to fill the L0 buffer. Measured
        // without this, on edn: the L0 line became
        //     xxxxxxxx_xxxxxxxx_xxxxxxxx_0000048b
        // where the FPGA view holds ffffc132_ffffde39_fffffb9c_0000048b, and
        // the next load returned X. Each bank therefore keeps the last value
        // it read: live dout1 in the cycle after a read, that value otherwise.
        // No cycle of latency is added.
        reg        rd_live_q;
        reg [31:0] rd_hold_q;
        always @(posedge clk) begin
            if (rd_live_q)
                rd_hold_q <= bank_dout_raw;
            rd_live_q <= bank_rd;
        end
        assign bank_dout[gi] = rd_live_q ? bank_dout_raw : rd_hold_q;
    end
endgenerate

// dout1 already carries the one-cycle synchronous read the controller expects,
// and holds its last value while csb1 is deasserted -- the same behaviour as
// `if (rd_en) rd_line <= ...` in the register-array version.
assign rd_line = {bank_dout[3], bank_dout[2], bank_dout[1], bank_dout[0]};

// Simulation-only instrumentation. The point is to find out whether the
// same-index conflict ever reaches a consumer, rather than to argue about it.
// Synthesis ignores this block.
`ifndef SYNTHESIS
// Declared and reset separately, and assigned non-blocking: an initialiser on
// the declaration trips PROCASSINIT and `=` inside a clocked process trips
// BLKSEQ, both of which this project treats as correctness-class failures. The
// first version of this counter introduced two of them.
integer conflict_count;
initial conflict_count = 0;
always @(posedge clk) begin
    if (rd_en && wr_en && (rd_index == wr_index)) begin
        conflict_count <= conflict_count + 1;
    end
end
`endif

endmodule


module icache_data_ram #(
    parameter LINE_COUNT  = 256,
    parameter INDEX_WIDTH = 8
)(
    input  wire                   clk,
    input  wire                   rd_en,
    input  wire [INDEX_WIDTH-1:0] rd_index,
    output wire [127:0]           rd_line,
    input  wire                   wr_en,
    input  wire [INDEX_WIDTH-1:0] wr_index,
    input  wire [1:0]             wr_word,
    input  wire [31:0]            wr_data
);
cache_data_ram_sram4 #(.LINE_COUNT(LINE_COUNT), .INDEX_WIDTH(INDEX_WIDTH)) u_ram (
    .clk(clk),
    .rd_en(rd_en), .rd_index(rd_index), .rd_line(rd_line),
    .wr_en(wr_en), .wr_index(wr_index), .wr_word(wr_word), .wr_data(wr_data)
);
endmodule


module dcache_data_ram #(
    parameter LINE_COUNT  = 256,
    parameter INDEX_WIDTH = 8
)(
    input  wire                   clk,
    input  wire                   rd_en,
    input  wire [INDEX_WIDTH-1:0] rd_index,
    output wire [127:0]           rd_line,
    input  wire                   wr_en,
    input  wire [INDEX_WIDTH-1:0] wr_index,
    input  wire [1:0]             wr_word,
    input  wire [31:0]            wr_data
);
cache_data_ram_sram4 #(.LINE_COUNT(LINE_COUNT), .INDEX_WIDTH(INDEX_WIDTH)) u_ram (
    .clk(clk),
    .rd_en(rd_en), .rd_index(rd_index), .rd_line(rd_line),
    .wr_en(wr_en), .wr_index(wr_index), .wr_word(wr_word), .wr_data(wr_data)
);
endmodule
