module fifo 
#(
    parameter DEPTH = 16
)
(
    input              clk        ,
    input              reset_n    ,
    input              write      ,
    input        [7:0] write_data ,
    input              read       ,
    output logic [7:0] read_data  ,
    output             empty      ,
    output             full       
);

localparam BIT_WIDTH = $clog2(DEPTH) ;

logic [DEPTH-1:0]   [7:0] mem      ;
logic [BIT_WIDTH:0]       wr_index ;
logic [BIT_WIDTH:0]       rd_index ;

assign empty = (wr_index == rd_index) ;
assign full  = (wr_index[BIT_WIDTH] != rd_index[BIT_WIDTH] && wr_index[BIT_WIDTH-1:0] == rd_index[BIT_WIDTH-1:0]) ;

always_ff @(posedge clk, negedge reset_n) begin
    if (!reset_n) begin
        wr_index <= 0 ;
        mem      <= 0 ;
    end 
    else if (write && !full) begin
        mem[wr_index[BIT_WIDTH-1:0]] <= write_data   ;
        wr_index                     <= wr_index + 1 ;
    end
end

always_ff @(posedge clk, negedge reset_n) begin
    if (!reset_n) begin
        rd_index  <= 0 ;
        read_data <= 0 ;
    end 
    else if (read && !empty) begin
        read_data <= mem[rd_index[BIT_WIDTH-1:0]] ;
        rd_index  <= rd_index + 1                 ;
    end
end

endmodule
