`timescale 1ns/1ps

// UART serial pins of soc_top. The environment drives uart_rx and observes
// uart_tx; framing is 8N1 at the baud rate the firmware configured.
interface uart_if (input logic clk, input logic reset_n);

    logic uart_rx;   // driven by the environment into the DUT
    logic uart_tx;   // driven by the DUT

    modport driver  (output uart_rx, input clk, input reset_n);
    modport passive (input uart_rx, input uart_tx, input clk, input reset_n);

endinterface
