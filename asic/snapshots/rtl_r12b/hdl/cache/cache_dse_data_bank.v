// Single-way cache data bank.
// Synchronous full-line read -> M9K inference; a per-controller hot buffer
// gives the same-cycle response.
module cache_dse_data_bank #(
    parameter SET_COUNT   = 64,
    parameter INDEX_WIDTH = 6,
    parameter LINE_WORDS  = 4
)(
    input  wire                        clk,
    // The bank is read only when the controller will consume the result.
    // Every other cycle rd_line holds, which removes the M9K read on idle
    // and L0-hit cycles without changing any value the controller sees.
    input  wire                        rd_en,
    input  wire [INDEX_WIDTH-1:0]      rd_index,
    output wire [(32*LINE_WORDS)-1:0]  rd_line,
    input  wire                        wr_en,
    input  wire [INDEX_WIDTH-1:0]      wr_index,
    input  wire [3:0]                  wr_word,
    input  wire [31:0]                 wr_data
);

// Separate 32-bit banks, one per word of the line (not one wide word with a
// partial write): Quartus 20.1 infers M9K only for this pattern. The generate
// keeps that shape at any line length, and each slice of rd_line has exactly
// one driver.
//
// wr_word is a fixed four bits, so the port width never depends on LINE_WORDS
// and LINE_WORDS may be up to 16. Drivers must be four bits wide too: a
// narrower connection leaves the top bit unresolved, every comparison below
// goes X, and no bank is ever written. A driver wider than the port silently
// truncates instead, aliasing the upper words onto the lower ones.
genvar w;
generate
    for(w = 0; w < LINE_WORDS; w = w + 1) begin : g_bank
        localparam integer W_IDX = w;
        (* ramstyle = "M9K, no_rw_check" *) reg [31:0] data_mem [0:SET_COUNT-1];
        reg [31:0] rd_word;
        always @(posedge clk) begin
            if(rd_en)
                rd_word <= data_mem[rd_index];
            // W_IDX is an integer parameter; the part-select states which
            // four bits the four-bit selector is actually compared against.
            if(wr_en && (wr_word == W_IDX[3:0]))
                data_mem[wr_index] <= wr_data;
        end
        assign rd_line[(w*32)+31 -: 32] = rd_word;
    end
endgenerate


// synthesis translate_off
initial begin
    if((LINE_WORDS < 2) || (LINE_WORDS > 16) ||
       ((LINE_WORDS & (LINE_WORDS - 1)) != 0))
        $fatal(1, "cache_dse_data_bank: LINE_WORDS=%0d is unsupported. It must be a power of two from 2 to 16; the bank word selector is four bits, so wider lines would alias their upper words onto the lower ones without any other symptom.", LINE_WORDS);
end
// synthesis translate_on

endmodule
