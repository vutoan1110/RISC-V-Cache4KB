// ASIC drop-in replacement for hdl/cache/cache_dse_data_bank.v, the per-way data
// bank of icache_dse_core.v and dcache_dse_core.v (CACHE_CONFIG 1 = SA2 and
// 2 = DM_VC4), backed by Sky130 OpenRAM hard macros instead of register arrays.
// Same module name, parameters and ports: the ASIC file list supplies this file
// in place of the hdl/ one, exactly as asic/soc_dm_4kb/cache_data_ram_sram4.v
// supplies icache_data_ram / dcache_data_ram for the DM build. No hdl/ file is
// changed (2026-09-30, FLOW_JOURNAL: SA2 and DM_VC4 ASIC builds).
//
// GEOMETRY. sky130_sram_1kbyte_1rw1r_32x256_8 macros, LINE_WORDS = 4 lanes:
//
//   SET_COUNT 256 (DM_VC4, 4 KiB)  g_full: one macro per lane, rows = sets.
//                                  Port 1 reads, port 0 writes. 4 macros.
//   SET_COUNT 128 (SA2, 4 KiB)     g_pair: two lanes per macro. Lane 2j lives in
//                                  rows 0..127 and is read on port 1; lane 2j+1
//                                  lives in rows 128..255 and is read on port 0
//                                  whenever port 0 is not writing. 2 macros.
//
// SA2 at 4 KiB is 2 ways x 128 sets, so this gives 4 macros per cache -- the
// same count as DM and DM_VC4, and every macro full. Ways cannot share a macro:
// they are separate instances of this module and are read in the same cycle.
// In DM_VC4 the way-1 bank is never written (refill_way and store_way_latched
// are constant 0 there) and its rd_line is never selected, so synthesis is
// expected to remove its macros; the synthesised netlist is checked for that.
//
// READ-DURING-WRITE AND THE HOLD. The register bank returns the OLD word when a
// lane is read and written at one index in the same cycle, and holds rd_line
// while rd_en is low. Here a lane's read is replaced by that lane's last live
// read whenever the macro cannot perform it:
//   - the lane being written, at the same row (port 1 has no defined value
//     while port 0 writes that address);
//   - in g_pair, the port-0 lane of a macro that port 0 is writing.
// Why the kept word is the register bank's word: in both DSE cores every write
// happens outside ST_IDLE, where bank_rd_en is 1 and bank_rd_index equals the
// write index, and every writing state is entered from a state that read the
// same index; a lane is written at most once per refill (beats 0,1,2,3), once
// per swap and once per store commit. So the last live read of the lane was at
// the same index and nothing wrote that lane since -- the old word.
//
// That argument is checked, not trusted: the simulation-only shadow at the end
// of this file keeps the register-bank model on the same inputs and stops the
// simulation on the first cycle where rd_line differs from it, X included.
module cache_dse_data_bank #(
    parameter SET_COUNT   = 64,
    parameter INDEX_WIDTH = 6,
    parameter LINE_WORDS  = 4
)(
    input  wire                        clk,
    input  wire                        rd_en,
    input  wire [INDEX_WIDTH-1:0]      rd_index,
    output wire [(32*LINE_WORDS)-1:0]  rd_line,
    input  wire                        wr_en,
    input  wire [INDEX_WIDTH-1:0]      wr_index,
    input  wire [3:0]                  wr_word,
    input  wire [31:0]                 wr_data
);

// Macro power pins, as in cache_data_ram_sram4.v (R8): local supplies under
// USE_POWER_PINS only; the physical connection is OpenLane's PDN
// (PDN_MACRO_CONNECTIONS '.*u_bank VPWR VGND vccd1 vssd1'), checked by LVS.
`ifdef USE_POWER_PINS
    supply1 vccd1;
    supply0 vssd1;
`endif

// Simulation-only geometry guard (hidden from every OpenLane tool, whose
// frontends cannot all resolve $fatal; see cache_data_ram_sram4.v).
`ifndef __openlane__
initial begin
    if (LINE_WORDS != 4 || !(INDEX_WIDTH == 8 || INDEX_WIDTH == 7) ||
        SET_COUNT != (1 << INDEX_WIDTH)) begin
        $display("cache_dse_data_bank (ASIC): SET_COUNT=%0d INDEX_WIDTH=%0d LINE_WORDS=%0d",
                 SET_COUNT, INDEX_WIDTH, LINE_WORDS);
        $fatal(1, "cache_dse_data_bank (ASIC): supports 4 lanes of 256 or 128 sets only");
    end
end
`endif

genvar gi;
generate
if (INDEX_WIDTH == 8) begin : g_full
    for (gi = 0; gi < 4; gi = gi + 1) begin : g_bank
        localparam integer LANE = gi;
        wire sel_wr   = wr_en && (wr_word == LANE[3:0]);
        wire conflict = sel_wr && rd_en && (rd_index == wr_index);
        wire bank_rd  = rd_en && !conflict;
        wire [31:0] bank_dout_raw;

        sky130_sram_1kbyte_1rw1r_32x256_8 u_bank (
`ifdef USE_POWER_PINS
            .vccd1 (vccd1),
            .vssd1 (vssd1),
`endif
            // port 0: write (wmask0 per byte; every write here is a full word)
            .clk0  (clk),
            .csb0  (~sel_wr),
            .web0  (1'b0),
            .wmask0(4'b1111),
            .addr0 (wr_index),
            .din0  (wr_data),
            .dout0 (),
            // port 1: read
            .clk1  (clk),
            .csb1  (~bank_rd),
            .addr1 (rd_index),
            .dout1 (bank_dout_raw)
        );

        // dout is driven only in the cycle after a read (the vendor model makes
        // it X from T_HOLD after every other edge): keep the last live read.
        reg        rd_live_q;
        reg [31:0] rd_hold_q;
        always @(posedge clk) begin
            if (rd_live_q)
                rd_hold_q <= bank_dout_raw;
            rd_live_q <= bank_rd;
        end
        assign rd_line[(gi*32)+31 -: 32] = rd_live_q ? bank_dout_raw : rd_hold_q;
    end
end else begin : g_pair
    for (gi = 0; gi < 2; gi = gi + 1) begin : g_bank
        localparam integer LANE_A = 2 * gi;       // port 1, rows 0..127
        localparam integer LANE_B = 2 * gi + 1;   // port 0, rows 128..255
        wire wr_a   = wr_en && (wr_word == LANE_A[3:0]);
        wire wr_b   = wr_en && (wr_word == LANE_B[3:0]);
        wire wr_any = wr_a || wr_b;
        // Lane A: suppressed only when port 0 writes its row.
        wire rd_a   = rd_en && !(wr_a && (rd_index == wr_index));
        // Lane B: port 0 reads it whenever port 0 is not writing.
        wire rd_b   = rd_en && !wr_any;
        wire [7:0] addr0 = wr_any ? {wr_b, wr_index} : {1'b1, rd_index};
        wire [31:0] dout_a_raw;
        wire [31:0] dout_b_raw;

        sky130_sram_1kbyte_1rw1r_32x256_8 u_bank (
`ifdef USE_POWER_PINS
            .vccd1 (vccd1),
            .vssd1 (vssd1),
`endif
            // port 0: the write of either lane, otherwise the read of lane B
            .clk0  (clk),
            .csb0  (~(wr_any || rd_b)),
            .web0  (~wr_any),
            .wmask0(4'b1111),
            .addr0 (addr0),
            .din0  (wr_data),
            .dout0 (dout_b_raw),
            // port 1: the read of lane A
            .clk1  (clk),
            .csb1  (~rd_a),
            .addr1 ({1'b0, rd_index}),
            .dout1 (dout_a_raw)
        );

        reg        live_a_q;
        reg        live_b_q;
        reg [31:0] hold_a_q;
        reg [31:0] hold_b_q;
        always @(posedge clk) begin
            if (live_a_q)
                hold_a_q <= dout_a_raw;
            if (live_b_q)
                hold_b_q <= dout_b_raw;
            live_a_q <= rd_a;
            live_b_q <= rd_b;
        end
        assign rd_line[(LANE_A*32)+31 -: 32] = live_a_q ? dout_a_raw : hold_a_q;
        assign rd_line[(LANE_B*32)+31 -: 32] = live_b_q ? dout_b_raw : hold_b_q;
    end
end
endgenerate

// ---------------------------------------------------------------------------
// Simulation-only equivalence shadow: the register bank of
// hdl/cache/cache_dse_data_bank.v on the same inputs. rd_line must equal its
// rd_line in EVERY cycle (!==, so X must match X), not only in the cycles the
// core consumes it. Hidden from Quartus by translate_off and from OpenLane by
// __openlane__; it drives nothing.
// ---------------------------------------------------------------------------
`ifndef __openlane__
// synthesis translate_off
reg [31:0] shadow_mem [0:(4*SET_COUNT)-1];
reg [31:0] shadow_rd  [0:3];
reg [63:0] shadow_cycles;
reg [63:0] shadow_conflicts;
integer    sk;
// 32-bit copies of the indices, so the address arithmetic below has one width.
wire [31:0] shadow_rd_idx = {{(32-INDEX_WIDTH){1'b0}}, rd_index};
wire [31:0] shadow_wr_idx = {{(32-INDEX_WIDTH){1'b0}}, wr_index};
initial begin
    shadow_cycles    = 64'd0;
    shadow_conflicts = 64'd0;
end
always @(posedge clk) begin
    for (sk = 0; sk < 4; sk = sk + 1) begin
        if (rd_line[(sk*32)+31 -: 32] !== shadow_rd[sk])
            $fatal(1, "DSE_BANK_EQUIV %m cycle %0d lane %0d: macro view %h, register bank %h",
                   shadow_cycles, sk, rd_line[(sk*32)+31 -: 32], shadow_rd[sk]);
    end
    shadow_cycles <= shadow_cycles + 64'd1;
    if (rd_en && wr_en && (rd_index == wr_index))
        shadow_conflicts <= shadow_conflicts + 64'd1;
    for (sk = 0; sk < 4; sk = sk + 1) begin
        if (rd_en)
            shadow_rd[sk] <= shadow_mem[(sk*SET_COUNT) + shadow_rd_idx];
        if (wr_en && (wr_word == sk[3:0]))
            shadow_mem[(sk*SET_COUNT) + shadow_wr_idx] <= wr_data;
    end
end
final
    $display("DSE_BANK_EQUIV %m: %0d cycles matched, %0d same-index read/write cycles",
             shadow_cycles, shadow_conflicts);
// synthesis translate_on
`endif

endmodule
