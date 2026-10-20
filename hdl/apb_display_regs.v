module apb_display_regs (
    input  wire        PCLK,
    input  wire        PRESETn,
    input  wire        PSEL,
    input  wire        PENABLE,
    input  wire        PWRITE,
    input  wire [3:0]  PSTRB,
    input  wire [11:0] PADDR,
    input  wire [31:0] PWDATA,
    output reg  [31:0] PRDATA,
    output wire        PREADY,
    output wire        PSLVERR,

    output reg  [31:0] disp_value,
    output reg  [7:0]  disp_led,
    output reg  [31:0] disp_ctrl,

    // KEY1 (active-low: 0 = pressed)
    input  wire        key1_n
);

assign PREADY  = 1'b1;
assign PSLVERR = 1'b0;

wire apb_wr = PSEL && PENABLE && PWRITE;
wire apb_rd = PSEL && PENABLE && !PWRITE;

function automatic [31:0] apply_strb(input [31:0] oldv, input [31:0] newv, input [3:0] strb);
    apply_strb = oldv;
    if (strb[0]) apply_strb[ 7: 0] = newv[ 7: 0];
    if (strb[1]) apply_strb[15: 8] = newv[15: 8];
    if (strb[2]) apply_strb[23:16] = newv[23:16];
    if (strb[3]) apply_strb[31:24] = newv[31:24];
endfunction

always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
        disp_value <= 32'h0000_0000;
        disp_led   <= 8'h00;
        disp_ctrl  <= 32'h0000_0000;
    end else if (apb_wr) begin
        case (PADDR[7:0])
            8'h00: disp_value <= apply_strb(disp_value, PWDATA, PSTRB);
            8'h04: disp_led   <= PWDATA[7:0];
            8'h08: disp_ctrl  <= apply_strb(disp_ctrl,  PWDATA, PSTRB);
            default: ;
        endcase
    end
end

always @(*) begin
    PRDATA = 32'h0000_0000;
    if (apb_rd) begin
        case (PADDR[7:0])
            8'h00: PRDATA = disp_value;
            8'h04: PRDATA = {24'h0, disp_led};
            8'h08: PRDATA = disp_ctrl;
            8'h0C: PRDATA = {31'h0, key1_n};  // bit0=1: not pressed, 0: pressed
            default: PRDATA = 32'h0000_0000;
        endcase
    end
end

endmodule
