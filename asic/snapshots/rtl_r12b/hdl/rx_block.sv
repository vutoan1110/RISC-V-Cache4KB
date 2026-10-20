module rx_block
#
(
    parameter IDLE     = 2'b00 ,
    parameter RECEIVE  = 2'b01 ,
    parameter STOP     = 2'b10 
)
(
    input              clk              ,
    input              reset_n          ,
    input              tick_rx_os       ,
    input        [1:0] data_bit_config  ,
    input              parity_bit_en    ,
    input              parity_bit_type  ,
    input              stop_bit_config  ,
    input              rx               ,
    input              rx_fifo_full     ,
    output logic       baud_rx_en       ,
    output logic       write_fifo       ,
    output logic [7:0] rx_data_o        ,
    output logic       rx_done          ,
    output             parity_bit_error ,
    output             rts_n
);

logic [1:0] current_state  ;
logic [1:0] next_state     ;
                 
logic [3:0] data_bit_width ;
logic [3:0] data_bit_count ;
                 
logic [1:0] stop_bit_width ;
logic [1:0] stop_bit_count ;
 
logic [3:0] count_tick     ;
logic       parity_bit_ref ;
logic       parity_bit_i   ;
logic [7:0] rx_data_reg    ;
 
logic       parity_bit;    

//data bit width
always_comb begin
    case(data_bit_config)
     2'b00: data_bit_width = 5 ;
     2'b01: data_bit_width = 6 ;
     2'b10: data_bit_width = 7 ;
     2'b11: data_bit_width = 8 ;
    endcase
end

//stop bit width
always_comb begin
    case({stop_bit_config, parity_bit_en})
    //  2'b00: stop_bit_width = 0 ;
     2'b01:    stop_bit_width = 1 ;
     2'b10:    stop_bit_width = 1 ;
     2'b11:    stop_bit_width = 2 ;
     default : stop_bit_width = 1;
    endcase
end

//current state
always_ff @(posedge clk, negedge reset_n) begin
    if(!reset_n) current_state <= IDLE       ;
    else         current_state <= next_state ;
end

//next state 
always@(*) begin
    case(current_state)
     IDLE: begin
        if(~rx && count_tick == 15 && tick_rx_os) next_state = RECEIVE ;
        else                                      next_state = IDLE    ;
     end
     RECEIVE: begin
        if((count_tick == 15) && (data_bit_count == data_bit_width-1) && tick_rx_os) next_state = STOP    ;
        else                                                                         next_state = RECEIVE ;
     end
     STOP: begin
        if((count_tick == 15) && (stop_bit_count == stop_bit_width-1) && tick_rx_os) next_state = IDLE ;
        else                                                                         next_state = STOP ;
     end
     default: begin
        next_state = IDLE ;
     end
    endcase
end

always@(*) begin
    if(parity_bit_en) begin
        case(parity_bit_type)
         1'b0: parity_bit_ref = ^rx_data_reg    ;
         1'b1: parity_bit_ref = ~(^rx_data_reg) ;
        endcase
    end
    else parity_bit_ref = 0 ;
end

assign parity_bit       = parity_bit_en ? parity_bit_i : 0 ;
assign parity_bit_error = ~(parity_bit == parity_bit_ref) ;

always_ff @(posedge clk, negedge reset_n) begin
    if(!reset_n) begin
        data_bit_count <= 0 ;
        stop_bit_count <= 0 ;
        count_tick     <= 0 ;
        rx_data_reg    <= 0 ;
        parity_bit_i   <= 0 ;
    end
    else begin
        case(current_state)
         IDLE: begin
            rx_data_reg    <= 0 ;
            data_bit_count <= 0 ;
            stop_bit_count <= 0 ;
            parity_bit_i   <= 0 ;
            if(next_state == RECEIVE) count_tick <= 0 ;
            else if(tick_rx_os) begin
                if(count_tick != 15) count_tick <= count_tick + 1 ;
                else                 count_tick <= 0              ;
            end 
            else count_tick <= count_tick ;
         end
         RECEIVE: begin
            if(next_state == STOP) count_tick <= 0 ;
            else if(tick_rx_os) begin
                if(count_tick == 7) begin
                    // Three bits address the byte; see tx_block.sv.
                    rx_data_reg[data_bit_count[2:0]] <= rx        ;
                    count_tick                  <= count_tick + 1 ; 
                end
                else if(count_tick == 15) begin
                    data_bit_count <= data_bit_count + 1 ;
                    count_tick     <= 0                  ;
                end
                else begin
                    count_tick <= count_tick + 1 ;
                end 
            end
            else begin
                count_tick <= count_tick ;
            end
         end
         STOP: begin
            if(next_state == IDLE) count_tick <= 0 ;
            else if (tick_rx_os) begin
                if(count_tick == 7) begin
                    count_tick   <= count_tick + 1 ; 
                    if(stop_bit_count == 0) parity_bit_i <= rx           ;
                    else                    parity_bit_i <= parity_bit_i ;
                end
                else if(count_tick == 15) begin
                    stop_bit_count <= stop_bit_count + 1 ;
                    count_tick     <= 0                  ;
                end
                else begin
                    count_tick <= count_tick + 1 ;
                end 
            end
            else begin
                count_tick <= count_tick ;
            end
         end
         default: begin
            data_bit_count <= 0 ;
            stop_bit_count <= 0 ;
            count_tick     <= 0 ;
            parity_bit_i   <= 0 ;
         end
        endcase
    end
end

//rx_data_o
always@(*) begin
    case(data_bit_config)
     2'b00: rx_data_o = {3'b111, rx_data_reg[4:0]} ;
     2'b01: rx_data_o = {2'b11,  rx_data_reg[5:0]} ;
     2'b10: rx_data_o = {1'b1,   rx_data_reg[6:0]} ;
     2'b11: rx_data_o = {        rx_data_reg[7:0]} ;
    endcase
end

always@(*) begin
    case(current_state) 
     IDLE: begin
        rx_done    = 0 ;
        write_fifo = 0 ;
        if(~rx) baud_rx_en = 1 ;
        else    baud_rx_en = 0 ;
     end
     RECEIVE: begin
        rx_done    = 0 ;
        write_fifo = 0 ; 
        baud_rx_en = 1 ;
     end
     STOP: begin
        baud_rx_en = 1;
        if(next_state == IDLE && !rx_fifo_full) write_fifo = 1 ;
        else                                    write_fifo = 0 ;
        if(next_state == IDLE) rx_done = 1 ;
        else                   rx_done = 0 ;
     end
     // current_state is two bits and only IDLE/RECEIVE/STOP are ever loaded, so
     // this branch is unreachable. It must still assign every output of the
     // block: leaving write_fifo and baud_rx_en out made synthesis infer a
     // transparent latch for each (two sky130_fd_sc_hd__dlxtn_1 on the ASIC).
     default: begin
        rx_done    = 0 ;
        write_fifo = 0 ;
        baud_rx_en = 0 ;
     end
    endcase
end

assign rts_n = ((current_state==IDLE) & (next_state==IDLE)) ? 0 : 1 ;

endmodule
