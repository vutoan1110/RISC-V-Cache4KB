// Parameterized 2-bit conditional-branch history table.
// No tags are stored: different PCs with the same index intentionally alias.
module bht_2bit #(
    parameter integer BHT_ENTRIES    = 256,
    parameter [1:0]   BHT_RESET_STATE = 2'b01,
    parameter integer BHT_INDEX_BITS = $clog2(BHT_ENTRIES)
) (
    input  wire                        clk,
    input  wire                        reset_n,
    input  wire [31:0]                 fetch_pc,
`ifndef __openlane__
    input  wire [31:0]                 fetch_pc_next,    // FPGA: pc_f at the next edge (read-ahead address)
    input  wire [31:0]                 update_pc_next,   // FPGA: pc_e at the next edge
`endif
    output wire [BHT_INDEX_BITS-1:0]   fetch_index,
    output wire [1:0]                  fetch_state,
    output wire                        predict_taken,
    input  wire                        update_en,
    input  wire [31:0]                 update_pc,
    input  wire                        actual_taken
);

wire [BHT_INDEX_BITS-1:0] update_index;
`ifdef __openlane__
reg  [1:0] bht_mem [0:BHT_ENTRIES-1];
`endif

assign fetch_index  = fetch_pc[BHT_INDEX_BITS+1:2];
assign update_index = update_pc[BHT_INDEX_BITS+1:2];
`ifdef __openlane__
assign fetch_state  = bht_mem[fetch_index];
`endif
assign predict_taken = fetch_state[1];

function [1:0] next_counter_state;
    input [1:0] state;
    input       taken;
    begin
        case(state)
            2'b00: next_counter_state = taken ? 2'b01 : 2'b00;
            2'b01: next_counter_state = taken ? 2'b10 : 2'b00;
            2'b10: next_counter_state = taken ? 2'b11 : 2'b01;
            2'b11: next_counter_state = taken ? 2'b11 : 2'b10;
            default: next_counter_state = BHT_RESET_STATE;
        endcase
    end
endfunction

`ifdef __openlane__
// Generated per-entry update: one sequential driver each, and the whole
// table resets to BHT_RESET_STATE.
genvar entry;
generate
    for(entry = 0; entry < BHT_ENTRIES; entry = entry + 1) begin : g_entry
        localparam [BHT_INDEX_BITS-1:0] ENTRY_INDEX = entry;
        always @(posedge clk or negedge reset_n) begin
            if(!reset_n)
                bht_mem[entry] <= BHT_RESET_STATE;
            else if(update_en && (update_index == ENTRY_INDEX))
                bht_mem[entry] <= next_counter_state(bht_mem[entry], actual_taken);
        end
    end
endgenerate
`else
// FPGA (2026-10-08, review A1): counters in two M9K copies (fetch read, update read) instead of 512 flip-flops. The
// read addresses registered at an edge are the indices pc_f / pc_e take at that edge; q* = contents before the write
// of that edge, which is bypassed from upd_*_q. valid[] (flip-flops, asynchronous reset) makes an entry not written
// since reset read BHT_RESET_STATE, as the reset of the old table did. Same value as the old table in every cycle.
(* ramstyle = "M9K" *) reg [1:0] cnt_f [0:BHT_ENTRIES-1];
(* ramstyle = "M9K" *) reg [1:0] cnt_u [0:BHT_ENTRIES-1];
reg  [BHT_ENTRIES-1:0]    valid;
reg  [1:0]                qf, qu;
reg                       upd_q;
reg  [BHT_INDEX_BITS-1:0] upd_idx_q;
reg  [1:0]                upd_val_q;
wire [BHT_INDEX_BITS-1:0] fetch_index_next  = fetch_pc_next[BHT_INDEX_BITS+1:2];
wire [BHT_INDEX_BITS-1:0] update_index_next = update_pc_next[BHT_INDEX_BITS+1:2];
wire [1:0] cur_u = !valid[update_index] ? BHT_RESET_STATE :
                   (upd_q && upd_idx_q == update_index) ? upd_val_q : qu;
wire [1:0] new_u = next_counter_state(cur_u, actual_taken);

assign fetch_state = !valid[fetch_index] ? BHT_RESET_STATE :
                     (upd_q && upd_idx_q == fetch_index) ? upd_val_q : qf;

always @(posedge clk) begin
    if(update_en) begin
        cnt_f[update_index] <= new_u;
        cnt_u[update_index] <= new_u;
    end
    qf <= cnt_f[fetch_index_next];
    qu <= cnt_u[update_index_next];
end

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        valid     <= {BHT_ENTRIES{1'b0}};
        upd_q     <= 1'b0;
        upd_idx_q <= {BHT_INDEX_BITS{1'b0}};
        upd_val_q <= 2'b00;
    end
    else begin
        if(update_en)
            valid[update_index] <= 1'b1;
        upd_q     <= update_en;
        upd_idx_q <= update_index;
        upd_val_q <= new_u;
    end
end

// synthesis translate_off
// Checker: the old table beside the new one (same reset, same update); a difference stops the simulation. Compared
// at the edge that consumes the values, inside the reset structure of the table, so reset_n stays an asynchronous
// reset only (a level test of reset_n in a clocked block is SYNCASYNCNET in lint_asic).
reg [1:0] ref_mem [0:BHT_ENTRIES-1];
integer ref_i;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        for(ref_i = 0; ref_i < BHT_ENTRIES; ref_i = ref_i + 1)
            ref_mem[ref_i] <= BHT_RESET_STATE;
    end
    else begin
        if(fetch_state !== ref_mem[fetch_index] || (update_en && cur_u !== ref_mem[update_index]))
            $fatal(1, "bht_2bit M9K checker: fetch %b / %b (index %0d), update %b / %b (index %0d) at %0t",
                   fetch_state, ref_mem[fetch_index], fetch_index, cur_u, ref_mem[update_index], update_index, $time);
        if(update_en)
            ref_mem[update_index] <= next_counter_state(ref_mem[update_index], actual_taken);
    end
end
// synthesis translate_on
`endif

// synthesis translate_off
initial begin
    if(BHT_ENTRIES < 2)
        $fatal(1, "BHT_ENTRIES must be at least 2");
    if((BHT_ENTRIES & (BHT_ENTRIES - 1)) != 0)
        $fatal(1, "BHT_ENTRIES must be a power of two");
end
// synthesis translate_on

endmodule
