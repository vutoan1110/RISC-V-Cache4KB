module icache_data_ram #(
    parameter LINE_COUNT  = 64,
    parameter INDEX_WIDTH = 6
)(
    input  wire                   clk,

    // Reads are enabled only in the cycles whose result the controller
    // consumes. Every other cycle the banks hold, which is the point.
    input  wire                   rd_en,
    input  wire [INDEX_WIDTH-1:0] rd_index,
    output reg  [127:0]           rd_line,

    input  wire                   wr_en,
    input  wire [INDEX_WIDTH-1:0] wr_index,
    input  wire [1:0]             wr_word,
    input  wire [31:0]            wr_data
);

// Four 32-bit banks -> four M9Ks; controller sees a registered full line.
(* ramstyle = "M9K, no_rw_check" *) reg [31:0] data_mem0 [0:LINE_COUNT-1];
(* ramstyle = "M9K, no_rw_check" *) reg [31:0] data_mem1 [0:LINE_COUNT-1];
(* ramstyle = "M9K, no_rw_check" *) reg [31:0] data_mem2 [0:LINE_COUNT-1];
(* ramstyle = "M9K, no_rw_check" *) reg [31:0] data_mem3 [0:LINE_COUNT-1];

always @(posedge clk) begin
    if(rd_en) begin
        rd_line[31:0]   <= data_mem0[rd_index];
        rd_line[63:32]  <= data_mem1[rd_index];
        rd_line[95:64]  <= data_mem2[rd_index];
        rd_line[127:96] <= data_mem3[rd_index];
    end
    if(wr_en) begin
        case(wr_word)
            2'd0: data_mem0[wr_index] <= wr_data;
            2'd1: data_mem1[wr_index] <= wr_data;
            2'd2: data_mem2[wr_index] <= wr_data;
            default: data_mem3[wr_index] <= wr_data;
        endcase
    end
end

endmodule
