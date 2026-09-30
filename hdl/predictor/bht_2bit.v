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
    output wire [BHT_INDEX_BITS-1:0]   fetch_index,
    output wire [1:0]                  fetch_state,
    output wire                        predict_taken,
    input  wire                        update_en,
    input  wire [31:0]                 update_pc,
    input  wire                        actual_taken
);

wire [BHT_INDEX_BITS-1:0] update_index;
reg  [1:0] bht_mem [0:BHT_ENTRIES-1];

assign fetch_index  = fetch_pc[BHT_INDEX_BITS+1:2];
assign update_index = update_pc[BHT_INDEX_BITS+1:2];
assign fetch_state  = bht_mem[fetch_index];
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

// synthesis translate_off
initial begin
    if(BHT_ENTRIES < 2)
        $fatal(1, "BHT_ENTRIES must be at least 2");
    if((BHT_ENTRIES & (BHT_ENTRIES - 1)) != 0)
        $fatal(1, "BHT_ENTRIES must be a power of two");
end
// synthesis translate_on

endmodule
