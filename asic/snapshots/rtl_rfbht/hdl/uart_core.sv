module uart_core
(
    input              clk                ,
    input              reset_n            ,
    input        [1:0] set_baud           ,
    //tx fifo
    input              write_tx_fifo      ,
    //rx fifo
    input              read_rx_fifo       ,
    //tx
    input              start_tx           ,
    input              parity_bit_tx_en   ,
    input              parity_bit_tx_type ,
    input        [1:0] data_bit_tx_config ,
    input              stop_bit_tx_config ,
    input        [7:0] tx_data_i          ,
    input              cts_n              ,
    output             logic tx           ,
    output             logic tx_done      ,
    //rx      
    input              parity_bit_rx_en   ,
    input              parity_bit_rx_type ,
    input        [1:0] data_bit_rx_config ,
    input              stop_bit_rx_config ,
    input              rx                 ,
    output       [7:0] rx_data_o          ,
    output             parity_bit_error   ,
    output logic       rx_done            ,
    // FIFO state for software flow control: write only while the TX FIFO
    // is not full, read only while the RX FIFO is not empty.
    output             tx_fifo_full_o     ,
    output             rx_fifo_empty_o    ,
    output             rts_n              
);

//baud
logic       tick_tx_os   ;
logic       tick_rx_os   ;
logic       baud_tx_en   ;
logic       baud_rx_en   ;

//tx fifo
logic [7:0] tx_data_fifo  ;
logic       read_tx_fifo  ;
logic       tx_fifo_full  ;
logic       tx_fifo_empty ;

//rx fifo
logic [7:0] rx_data_fifo  ;
logic       write_rx_fifo ;
logic       rx_fifo_full  ;
logic       rx_fifo_empty ;

assign tx_fifo_full_o  = tx_fifo_full  ;
assign rx_fifo_empty_o = rx_fifo_empty ;

baudrate_gen_block baudrate_gen_block (
    .clk        (clk)        ,
    .reset_n    (reset_n)    ,
    .baud_tx_en (baud_tx_en) ,
    .baud_rx_en (baud_rx_en) ,
    .set_baud   (set_baud)   ,
    .tick_tx_os (tick_tx_os) ,
    .tick_rx_os (tick_rx_os) 
);

fifo tx_fifo (
    .clk        (clk)           ,
    .reset_n    (reset_n)       ,
    .write      (write_tx_fifo) ,
    .write_data (tx_data_i)     , 
    .read       (read_tx_fifo)  ,
    .read_data  (tx_data_fifo)  ,
    .empty      (tx_fifo_empty) ,
    .full       (tx_fifo_full)
);

fifo rx_fifo (
    .clk        (clk)           ,
    .reset_n    (reset_n)       ,
    .write      (write_rx_fifo) ,
    .write_data (rx_data_fifo)  , 
    .read       (read_rx_fifo)  ,
    .read_data  (rx_data_o)     ,
    .empty      (rx_fifo_empty) ,
    .full       (rx_fifo_full)
);


tx_block tx_block (
    .clk             (clk)                ,
    .reset_n         (reset_n)            ,
    .tick_tx_os      (tick_tx_os)         ,
    .start_tx        (start_tx)           ,
    .data_bit_config (data_bit_tx_config) ,
    .parity_bit_en   (parity_bit_tx_en)   ,
    .parity_bit_type (parity_bit_tx_type) ,
    .stop_bit_config (stop_bit_tx_config) ,
    .tx_data_i       (tx_data_fifo)       ,
    .tx_fifo_empty   (tx_fifo_empty)      ,
    .cts_n           (cts_n)              ,
    .read_fifo       (read_tx_fifo)       ,
    .baud_tx_en      (baud_tx_en)         ,
    .tx_done         (tx_done)            ,
    .tx              (tx)
);

rx_block rx_block (
    .clk              (clk)                ,
    .reset_n          (reset_n)            ,
    .tick_rx_os       (tick_rx_os)         ,
    .data_bit_config  (data_bit_rx_config) ,
    .parity_bit_en    (parity_bit_rx_en)   ,
    .parity_bit_type  (parity_bit_rx_type) ,
    .stop_bit_config  (stop_bit_rx_config) ,
    .rx               (rx)                 ,
    .rx_fifo_full     (rx_fifo_full)       ,
    .baud_rx_en       (baud_rx_en)         , 
    .write_fifo       (write_rx_fifo)      ,
    .rx_data_o        (rx_data_fifo)       ,
    .rx_done          (rx_done)            ,
    .parity_bit_error (parity_bit_error)   ,
    .rts_n            (rts_n)
);

endmodule
