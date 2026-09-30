// ASIC drop-in replacement for hdl/axi/axi_ram_32.v, backed by four real
// Sky130 SRAM hard macros (sky130_sram_2kbyte_1rw1r_32x512_8, pre-built by
// OpenRAM, from github.com/VLSIDA/sky130_sram_macros) instead of a
// behavioral register array.
//
// STATUS: written but NOT YET SIMULATED against tb/axi_memory_tb.sv or any
// other testbench in this repository. The port list is byte-for-byte
// identical to hdl/axi/axi_ram_32.v so it can be swapped in with no other
// RTL changes, but the internal FSM timing (in particular: exact cycle at
// which s_axi_arready/s_axi_rvalid/s_axi_rlast assert) has only been
// reasoned through on paper against the macro's documented 1-cycle
// synchronous read latency. Do not treat this as verified until it has
// been run through the project's own axi_memory_tb.sv (same golden
// checks: 4-beat INCR burst, RLAST on beat 4, one active read transaction,
// AW/W independent acceptance, B only after both AW and W).
//
// Address mapping: word address = {araddr,awaddr}[31:2]. Four banks of
// 512 words each cover the required 2048-word (8 KiB) depth:
//   bank_sel  = word_addr[10:9]   (selects among the 4 macro instances)
//   bank_addr = word_addr[8:0]    (9-bit address INTO the selected macro)
// A 4-word INCR burst is always 16-byte (4-word) aligned in this design
// (see docs/reference/01_RTL_ARCHITECTURE.md: refill is always aligned),
// and 512 is an exact multiple of 4, so a burst can never straddle a bank
// boundary -- the bank is decoded once from the AR address and held for
// all 4 beats.
//
// The macro's read port (port 0, the read/write port) has a fixed 1-cycle
// synchronous latency: address+csb0+web0 presented at edge N -> dout0
// valid at edge N+1. This is the same latency class as the LINE_COUNT
// M9K read path already used throughout hdl/cache/*_data_ram.v, so the
// same "register the index, consume next cycle" discipline applies here.

// The module keeps the name axi_ram_32. The ASIC file list leaves out
// hdl/axi/axi_ram_32.v and supplies this file instead, so hdl/soc_top.v is
// used unmodified -- the same substitution cache_data_ram_sram4.v makes for
// the cache arrays. The ASIC flow previously used a hand-copied
// soc_top_asic.v to reach a differently named module, and that copy drifted
// 66 lines away from hdl/soc_top.v without anything noticing.
module axi_ram_32 #(
    parameter DEPTH_WORDS = 2048,   // must equal 4 * 512 for this bank count
    parameter MEMFILE     = "riscv_full.hex"  // unused: macros are not
                                               // preloaded by a MIF at
                                               // synthesis time; see NOTE
                                               // below on initialization.
)(
    input  wire        clk,
    input  wire        reset_n,

    input  wire [31:0] s_axi_araddr,
    input  wire [7:0]  s_axi_arlen,
    input  wire [2:0]  s_axi_arsize,
    input  wire [1:0]  s_axi_arburst,
    input  wire        s_axi_arvalid,
    output wire        s_axi_arready,

    output wire [31:0] s_axi_rdata,
    output wire [1:0]  s_axi_rresp,
    output wire        s_axi_rlast,
    output wire        s_axi_rvalid,
    input  wire        s_axi_rready,

    input  wire [31:0] s_axi_awaddr,
    input  wire [7:0]  s_axi_awlen,
    input  wire [2:0]  s_axi_awsize,
    input  wire [1:0]  s_axi_awburst,
    input  wire        s_axi_awvalid,
    output wire        s_axi_awready,

    input  wire [31:0] s_axi_wdata,
    input  wire [3:0]  s_axi_wstrb,
    input  wire        s_axi_wlast,
    input  wire        s_axi_wvalid,
    output wire        s_axi_wready,

    output wire [1:0]  s_axi_bresp,
    output wire        s_axi_bvalid,
    input  wire        s_axi_bready,

    // Simulation-only backpressure/error injection on the original
    // axi_ram_32. The original module's own comment says to tie these
    // low in synthesis; this ASIC replacement does not implement them at
    // all (ties are implicit -- the ports exist only so the surrounding
    // soc_top_asic.v instantiation can stay byte-identical to soc_top.v).
    input  wire [7:0]  test_ar_stall_cycles,
    input  wire [7:0]  test_r_first_delay_cycles,
    input  wire [7:0]  test_r_gap_cycles,
    input  wire [7:0]  test_aw_stall_cycles,
    input  wire [7:0]  test_w_stall_cycles,
    input  wire [7:0]  test_b_delay_cycles,
    input  wire        test_rresp_error,
    input  wire        test_bresp_error,

    output reg  [31:0] read_burst_count,
    output reg  [31:0] write_txn_count
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

    // Silence "unused input" lint warnings for the intentionally-ignored
    // test/injection ports without affecting synthesis.
    wire _unused_test_ports = &{1'b0,
        test_ar_stall_cycles, test_r_first_delay_cycles, test_r_gap_cycles,
        test_aw_stall_cycles, test_w_stall_cycles, test_b_delay_cycles,
        test_rresp_error, test_bresp_error, 1'b0};

    localparam [1:0] RESP_OKAY = 2'b00;

    // ------------------------------------------------------------------
    // Four SRAM macro banks, port 0 (RW) used; port 1 (R-only) unused and
    // held disabled (csb1=1).
    // ------------------------------------------------------------------
    // csb0 on the macro is one bit. This was declared two bits wide, so every
    // instance connection truncated silently; only bit 0 was ever wired, which
    // is why the behaviour was right by accident.
    reg         bank_csb0   [0:3]; // active-low chip select, one per bank
    reg         bank_web0   [0:3]; // active-low write enable
    reg  [3:0]  bank_wmask0 [0:3];
    reg  [8:0]  bank_addr0  [0:3];
    reg  [31:0] bank_din0   [0:3];
    wire [31:0] bank_dout0  [0:3];

    genvar gi;
    generate
        for (gi = 0; gi < 4; gi = gi + 1) begin : g_bank
            sky130_sram_2kbyte_1rw1r_32x512_8 u_bank (
`ifdef USE_POWER_PINS
                .vccd1 (vccd1),
                .vssd1 (vssd1),
`endif
                .clk0  (clk),
                .csb0  (bank_csb0[gi]),
                .web0  (bank_web0[gi]),
                .wmask0(bank_wmask0[gi]),
                .addr0 (bank_addr0[gi]),
                .din0  (bank_din0[gi]),
                .dout0 (bank_dout0[gi]),
                .clk1  (clk),
                .csb1  (1'b1),      // port 1 unused: always deselected
                .addr1 (9'd0),
                .dout1 ()           // left open, port 1 not read
            );
        end
    endgenerate

    // ------------------------------------------------------------------
    // Read side: 4-beat INCR burst, ARLEN fixed at 3 by this project's
    // cache_axi_master (see hdl/axi/cache_axi_master.v). One beat per
    // cycle once the pipeline is filled, matching the macro's one-word-
    // per-cycle synchronous read.
    // ------------------------------------------------------------------
    localparam [1:0] RD_IDLE  = 2'd0;
    localparam [1:0] RD_FETCH = 2'd1; // address driven to macro this cycle
    localparam [1:0] RD_SEND  = 2'd2; // macro dout valid, drive on AXI R

    reg [1:0]  rd_state;
    reg [7:0]  rd_len_q;
    reg [7:0]  rd_beat_q;
    reg [1:0]  rd_bank_q;
    reg [8:0]  rd_bank_addr_q;

    wire        rd_accept = (rd_state == RD_IDLE) && s_axi_arvalid;
    wire [10:0] rd_word_addr = s_axi_araddr[12:2]; // 11 bits: 2048 words
    wire [1:0]  rd_bank_sel  = rd_word_addr[10:9];
    wire [8:0]  rd_bank_off  = rd_word_addr[8:0];

    assign s_axi_arready = (rd_state == RD_IDLE);

    // Write-side state, declared here because the combinational bank drive
    // below reads it. It used to be declared after that block, which Yosys
    // and the linter accept but Questa rejects; this file had never been
    // through Questa until the ASIC-view simulation.
    localparam [1:0] WR_IDLE   = 2'd0;
    localparam [1:0] WR_COMMIT = 2'd1; // address+data+wmask driven this cycle
    localparam [1:0] WR_RESP   = 2'd2;

    reg [1:0]  wr_state;
    reg        aw_have_q, w_have_q;
    reg [31:0] aw_addr_q;
    reg [31:0] w_data_q;
    reg [3:0]  w_strb_q;

    reg [1:0]  wr_bank_r;
    reg [8:0]  wr_bank_off_r;
    reg [31:0] wr_data_r;
    reg [3:0]  wr_strb_r;

    integer rb;
    always @(*) begin
        for (rb = 0; rb < 4; rb = rb + 1) begin
            bank_csb0[rb]   = 1'b1;
            bank_web0[rb]   = 1'b1;
            bank_wmask0[rb] = 4'b0000;
            bank_addr0[rb]  = 9'd0;
            bank_din0[rb]   = 32'd0;
        end

        // Read-side drive (RD_FETCH presents the address for THIS beat).
        if (rd_state == RD_FETCH) begin
            bank_csb0[rd_bank_q] = 1'b0;
            bank_web0[rd_bank_q] = 1'b1; // read
            bank_addr0[rd_bank_q] = rd_bank_addr_q;
        end

        // Write-side drive (WR_COMMIT presents address+data+wmask).
        if (wr_state == WR_COMMIT) begin
            bank_csb0[wr_bank_r]   = 1'b0;
            bank_web0[wr_bank_r]   = 1'b0; // write
            bank_wmask0[wr_bank_r] = wr_strb_r;
            bank_addr0[wr_bank_r]  = wr_bank_off_r;
            bank_din0[wr_bank_r]   = wr_data_r;
        end
    end

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            rd_state       <= RD_IDLE;
            rd_len_q       <= 8'd0;
            rd_beat_q      <= 8'd0;
            rd_bank_q      <= 2'd0;
            rd_bank_addr_q <= 9'd0;
            read_burst_count <= 32'd0;
        end else begin
            case (rd_state)
                RD_IDLE: begin
                    if (rd_accept) begin
                        rd_len_q       <= s_axi_arlen;
                        rd_beat_q      <= 8'd0;
                        rd_bank_q      <= rd_bank_sel;
                        rd_bank_addr_q <= rd_bank_off;
                        rd_state       <= RD_FETCH;
                    end
                end
                RD_FETCH: begin
                    // Address+csb+web presented this cycle; macro dout
                    // valid next cycle -> move to RD_SEND.
                    rd_state <= RD_SEND;
                end
                RD_SEND: begin
                    if (s_axi_rready) begin
                        if (rd_beat_q == rd_len_q) begin
                            read_burst_count <= read_burst_count + 32'd1;
                            rd_state <= RD_IDLE;
                        end else begin
                            rd_beat_q      <= rd_beat_q + 8'd1;
                            rd_bank_addr_q <= rd_bank_addr_q + 9'd1;
                            rd_state       <= RD_FETCH;
                        end
                    end
                    // else: hold rvalid, wait for consumer (rready) --
                    // the macro's dout0 for THIS beat's address must stay
                    // stable, which it does since we do not re-drive a new
                    // address into the same bank until rd_state advances.
                end
                default: rd_state <= RD_IDLE;
            endcase
        end
    end

    assign s_axi_rvalid = (rd_state == RD_SEND);
    assign s_axi_rdata  = bank_dout0[rd_bank_q];
    assign s_axi_rresp  = RESP_OKAY;
    assign s_axi_rlast  = (rd_state == RD_SEND) && (rd_beat_q == rd_len_q);

    // ------------------------------------------------------------------
    // Write side: single-beat writes only (this project's cache_axi_master
    // never issues multi-beat writes -- see hdl/axi/cache_axi_master.v).
    // AW and W are accepted independently as soon as both have arrived at
    // least once (matching the "AW-first, W-first, same-cycle AW/W" cases
    // the project's own axi_memory_tb.sv exercises against axi_ram_32).
    // ------------------------------------------------------------------

    // The write fires in the cycle both halves are present. When AW arrives in
    // that same cycle, aw_addr_q still holds the PREVIOUS write's address --
    // the non-blocking update lands at this edge -- so the address needs the
    // same bypass the data already has. Without it every write whose AW and W
    // arrived together was committed to the previous write's address, and the
    // first write after reset to address 0: 91 of 115 writes in the first
    // ASIC-view run. hdl/axi/axi_ram_32.v has had this bypass all along
    // (selected_awaddr); the macro wrapper had never been simulated.
    wire [31:0] wr_sel_addr  = aw_have_q ? aw_addr_q : s_axi_awaddr;
    wire [10:0] wr_word_addr = wr_sel_addr[12:2];

    assign s_axi_awready = (wr_state == WR_IDLE) && !aw_have_q;
    assign s_axi_wready  = (wr_state == WR_IDLE) && !w_have_q;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            wr_state      <= WR_IDLE;
            aw_have_q     <= 1'b0;
            w_have_q      <= 1'b0;
            aw_addr_q     <= 32'd0;
            w_data_q      <= 32'd0;
            w_strb_q      <= 4'd0;
            wr_bank_r     <= 2'd0;
            wr_bank_off_r <= 9'd0;
            wr_data_r     <= 32'd0;
            wr_strb_r     <= 4'd0;
            write_txn_count <= 32'd0;
        end else begin
            case (wr_state)
                WR_IDLE: begin
                    if (s_axi_awvalid && s_axi_awready) begin
                        aw_addr_q <= s_axi_awaddr;
                        aw_have_q <= 1'b1;
                    end
                    if (s_axi_wvalid && s_axi_wready) begin
                        w_data_q <= s_axi_wdata;
                        w_strb_q <= s_axi_wstrb;
                        w_have_q <= 1'b1;
                    end
                    // Fire once both halves have arrived (this cycle or a
                    // previous one).
                    if ((aw_have_q || (s_axi_awvalid && s_axi_awready)) &&
                        (w_have_q  || (s_axi_wvalid  && s_axi_wready))) begin
                        wr_bank_r     <= wr_word_addr[10:9];
                        wr_bank_off_r <= wr_word_addr[8:0];
                        wr_data_r     <= w_have_q ? w_data_q : s_axi_wdata;
                        wr_strb_r     <= w_have_q ? w_strb_q : s_axi_wstrb;
                        wr_state      <= WR_COMMIT;
                        aw_have_q     <= 1'b0;
                        w_have_q      <= 1'b0;
                    end
                end
                WR_COMMIT: begin
                    // Address+wmask+data presented to the macro this
                    // cycle (see combinational block above); the write
                    // itself completes synchronously at this same edge,
                    // so the response can be offered next cycle.
                    wr_state <= WR_RESP;
                end
                WR_RESP: begin
                    if (s_axi_bready) begin
                        write_txn_count <= write_txn_count + 32'd1;
                        wr_state <= WR_IDLE;
                    end
                end
                default: wr_state <= WR_IDLE;
            endcase
        end
    end

    assign s_axi_bvalid = (wr_state == WR_RESP);
    assign s_axi_bresp  = RESP_OKAY;

// ASIC-view simulation only. The macros have no initialisation port, so the
// program is written straight into their storage, the way the FPGA RAM's
// $readmemh fills its arrays. Bank b holds words b*512 .. b*512+511, the same
// split as bank_sel = word_addr[10:9] above. ASIC_VIEW_SIM is defined only by
// tb/compile_asic_view.do; synthesis and lint never see this block.
`ifdef ASIC_VIEW_SIM
reg [31:0] asic_view_init [0:2047];
integer    asic_view_i;
initial begin
    for (asic_view_i = 0; asic_view_i < 2048; asic_view_i = asic_view_i + 1)
        asic_view_init[asic_view_i] = 32'h0000_0000;
    if (MEMFILE != "") $readmemh(MEMFILE, asic_view_init);
    for (asic_view_i = 0; asic_view_i < 512; asic_view_i = asic_view_i + 1) begin
        g_bank[0].u_bank.mem[asic_view_i] = asic_view_init[asic_view_i];
        g_bank[1].u_bank.mem[asic_view_i] = asic_view_init[512  + asic_view_i];
        g_bank[2].u_bank.mem[asic_view_i] = asic_view_init[1024 + asic_view_i];
        g_bank[3].u_bank.mem[asic_view_i] = asic_view_init[1536 + asic_view_i];
    end
end
`endif

endmodule
