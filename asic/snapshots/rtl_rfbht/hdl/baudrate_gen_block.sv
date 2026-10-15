module baudrate_gen_block 
#(
    parameter COUNT_BIT_WIDTH = 16 ,
    parameter OVERSAMPLE      = 16
)
(
    input        clk        ,
    input        reset_n    ,
    input        baud_tx_en ,
    input        baud_rx_en ,
    input  [1:0] set_baud   ,
    output       tick_tx_os ,
    output       tick_rx_os 
);

localparam BAUD24      = 2'b00              ;
localparam BAUD48      = 2'b01              ;
localparam BAUD96      = 2'b10              ;
localparam BAUD115_200 = 2'b11              ;
localparam OS_LOG2     = $clog2(OVERSAMPLE) ;
// The last oversample index is compared against a counter narrower than the
// expression that produces it. Sizing it once here is clearer than extending
// implicitly at every comparison.
localparam [OS_LOG2-1:0] OS_LAST = OS_LOG2'(OVERSAMPLE - 1) ;

// count_max is a signal, not a constant: it follows set_baud. It was spelled in
// capitals, which reads as a parameter and invites exactly the wrong code.
logic [COUNT_BIT_WIDTH-1:0]         count_max ;
// One oversample tick every count_max/OVERSAMPLE clocks. The shift is a plain
// part-select of the divisor, so the width is stated rather than truncated.
logic [COUNT_BIT_WIDTH-OS_LOG2-1:0] bit_period ;
logic [COUNT_BIT_WIDTH-OS_LOG2-1:0] tx_count  ;
logic [COUNT_BIT_WIDTH-OS_LOG2-1:0] rx_count  ;
logic [OS_LOG2-1:0]                 tx_os_cnt ;
logic                               tick_tx   ;

assign bit_period = count_max[COUNT_BIT_WIDTH-1:OS_LOG2] ;

always_comb begin
    case (set_baud)
     BAUD24:      count_max = 16'd20832 ;
     BAUD48:      count_max = 16'd10416 ;
     BAUD96:      count_max = 16'd5207  ;
     BAUD115_200: count_max = 16'd433   ;
     default:     count_max = 16'd5207  ;
    endcase
end

always_ff @(posedge clk, negedge reset_n) begin
    if (!reset_n) begin
        tx_count <= 0 ;
    end else begin
        if (baud_tx_en) begin
            if (tx_count == bit_period) begin
                tx_count <= 0 ;
            end
            else begin
                tx_count <= tx_count + 1 ;
            end
        end 
        else begin
            tx_count <= 0 ;
        end
    end
end

always_ff @(posedge clk, negedge reset_n) begin
    if (!reset_n) begin
        rx_count <= 0 ;
    end else begin
        if (baud_rx_en) begin
            if (rx_count == bit_period) begin
                rx_count <= 0 ;
            end
            else begin
                rx_count <= rx_count + 1 ;
            end
        end 
        else begin
            rx_count <= 0 ;
        end
    end
end

always_ff @(posedge clk, negedge reset_n) begin
    if (!reset_n) begin
        tx_os_cnt <= 0 ;
    end else begin
        if (!baud_tx_en) begin
            tx_os_cnt <= 0 ;
        end 
        else if (tick_tx) begin
            if (tx_os_cnt == OS_LAST) begin
                tx_os_cnt <= 0 ;
            end
            else begin
                tx_os_cnt <= tx_os_cnt + 1 ;
            end
        end
        else begin
            tx_os_cnt <= tx_os_cnt ;
        end
    end
end

assign tick_tx    = (tx_count == bit_period)               ;
assign tick_tx_os = tick_tx && (tx_os_cnt == OS_LAST)      ;
assign tick_rx_os = (rx_count == bit_period)               ;


endmodule
