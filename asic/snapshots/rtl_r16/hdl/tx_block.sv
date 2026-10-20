module tx_block 
#(
    parameter IDLE     = 2'b00 ,
    parameter START    = 2'b01 ,
    parameter TRANSMIT = 2'b10 ,
    parameter STOP     = 2'b11 
)
(
    input              clk             ,
    input              reset_n         ,
    input              tick_tx_os      ,
    input              start_tx        ,
    input        [1:0] data_bit_config ,
    input              parity_bit_en   ,
    input              parity_bit_type ,
    input              stop_bit_config ,
    input        [7:0] tx_data_i       ,
    input              tx_fifo_empty   ,
    input              cts_n           ,
    output logic       read_fifo       ,
    output             baud_tx_en      ,
    output logic       tx_done         ,
    output logic       tx
);

logic [1:0] current_state  ;
logic [1:0] next_state     ;

logic [3:0] data_bit_width ;
logic [3:0] data_bit_count ;

logic [1:0] stop_bit_width ;
logic [1:0] stop_bit_count ;

//data bit width
always_comb begin
    case(data_bit_config)
     2'b00:   data_bit_width = 5 ;
     2'b01:   data_bit_width = 6 ;
     2'b10:   data_bit_width = 7 ;
     2'b11:   data_bit_width = 8 ;
     default: data_bit_width = 8 ;
    endcase
end

//stop bit width
always_comb begin
    case({stop_bit_config, parity_bit_en})
    //  2'b00:   stop_bit_width = 0 ;
     2'b01:   stop_bit_width = 1 ;
     2'b10:   stop_bit_width = 1 ;
     2'b11:   stop_bit_width = 2 ;
     default: stop_bit_width = 1 ;
    endcase
end

//current state
always_ff @(posedge clk, negedge reset_n) begin
    if(!reset_n) current_state <= IDLE       ;
    else         current_state <= next_state ;
end

//next state
always_comb begin
    case(current_state)
     IDLE: begin
        if (!cts_n && start_tx && !tx_fifo_empty) next_state = START ;
        else                                      next_state = IDLE  ;
     end
     START: begin
        if(tick_tx_os) next_state = TRANSMIT ;
        else           next_state = START    ;
     end
     TRANSMIT: begin
        if(tick_tx_os && data_bit_count == data_bit_width - 1) next_state = STOP     ;
        else                                                   next_state = TRANSMIT ;
     end
     STOP: begin
        if(tick_tx_os && stop_bit_count == stop_bit_width - 1) next_state = IDLE ;
        else                                                   next_state = STOP ;
     end
     default: begin
        next_state = IDLE ; 
     end
    endcase
end

//output
always@(*) begin
    case(current_state)
     IDLE: begin
        tx_done = 0 ;
        tx      = 1 ;
        if(next_state == START) read_fifo = 1 ;
        else                    read_fifo = 0 ;
     end
     START: begin
        tx_done   = 0 ;
        tx        = 0 ;
        read_fifo = 0 ;
     end
     TRANSMIT: begin
        tx_done   = 0                         ;
        // The counter needs four bits because it reaches data_bit_width, up
        // to eight, on the cycle the state leaves TRANSMIT. The index into
        // the data is only ever 0..7, so it is three bits.
        tx        = tx_data_i[data_bit_count[2:0]] ;
        read_fifo = 0                         ;
     end
     STOP: begin
        read_fifo = 0 ;
        if(stop_bit_count == 0) begin
            if(parity_bit_en) begin
                case({parity_bit_type, data_bit_config})
                 3'b000: tx = ^(tx_data_i[4:0])    ;
                 3'b001: tx = ^(tx_data_i[5:0])    ;
                 3'b010: tx = ^(tx_data_i[6:0])    ;
                 3'b011: tx = ^(tx_data_i[7:0])    ;
                 3'b100: tx = ~(^(tx_data_i[4:0])) ;
                 3'b101: tx = ~(^(tx_data_i[5:0])) ;
                 3'b110: tx = ~(^(tx_data_i[6:0])) ;
                 3'b111: tx = ~(^(tx_data_i[7:0])) ;
                endcase
            end
            else tx = 1 ;
        end
        else if(stop_bit_count == 1) begin
            tx = 1;
        end
        else begin
            tx = 1;
        end
        if(next_state == IDLE) tx_done = 1 ;
        else                   tx_done = 0 ;
     end
     default: begin
        tx_done   = 0 ;
        tx        = 1 ;
        read_fifo = 0 ;
     end
    endcase
end

//data count, stop count
always_ff @(posedge clk, negedge reset_n) begin
    if(!reset_n) begin
        data_bit_count <= 0 ;
        stop_bit_count <= 0 ;
    end
    else begin
        case(current_state)
         IDLE: begin
            data_bit_count <= 0 ;
            stop_bit_count <= 0 ;
         end
         START: begin
            data_bit_count <= 0 ;
            stop_bit_count <= 0 ;
         end
         TRANSMIT: begin
            if(tick_tx_os) data_bit_count <= data_bit_count + 1 ;
            else           data_bit_count <= data_bit_count     ;
                           stop_bit_count <= 0                  ;
         end
         STOP: begin
            if(tick_tx_os) stop_bit_count <= stop_bit_count + 1 ;
            else           stop_bit_count <= stop_bit_count     ;
                           data_bit_count <= 0                  ;
         end
         default: begin
            data_bit_count <= 0 ;
            stop_bit_count <= 0 ;
         end
        endcase
    end
end

assign baud_tx_en = (current_state != IDLE) ;

endmodule
