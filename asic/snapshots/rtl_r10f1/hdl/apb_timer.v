module apb_timer (
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
    output wire        irq
);

reg [31:0] ctrl_reg;
reg [31:0] cmp_reg;
reg [31:0] count_reg;
reg [31:0] status_reg;
wire apb_wr;
wire apb_rd;

assign PREADY  = 1'b1;
assign PSLVERR = 1'b0;
assign apb_wr  = PSEL && PENABLE && PWRITE;
assign apb_rd  = PSEL && PENABLE && !PWRITE;
assign irq     = status_reg[0] & ctrl_reg[1];

function automatic [31:0] apply_strb(input [31:0] oldv, input [31:0] newv, input [3:0] strb);
    begin
        apply_strb = oldv;
        if (strb[0]) apply_strb[ 7: 0] = newv[ 7: 0];
        if (strb[1]) apply_strb[15: 8] = newv[15: 8];
        if (strb[2]) apply_strb[23:16] = newv[23:16];
        if (strb[3]) apply_strb[31:24] = newv[31:24];
    end
endfunction

always @(posedge PCLK or negedge PRESETn) begin
    if(!PRESETn) begin
        ctrl_reg   <= 32'h0000_0000;
        cmp_reg    <= 32'd40;
        count_reg  <= 32'h0000_0000;
        status_reg <= 32'h0000_0000;
    end
    else begin
        if(ctrl_reg[0]) begin
            if(count_reg >= cmp_reg) begin
                status_reg[0] <= 1'b1;
                if(ctrl_reg[2]) count_reg <= 32'h0000_0000;
            end
            else begin
                count_reg <= count_reg + 1'b1;
            end
        end

        if(apb_wr) begin
            case(PADDR[7:0])
                8'h00: ctrl_reg  <= apply_strb(ctrl_reg,  PWDATA, PSTRB);
                8'h04: cmp_reg   <= apply_strb(cmp_reg,   PWDATA, PSTRB);
                8'h08: count_reg <= apply_strb(count_reg, PWDATA, PSTRB);
                8'h0C: if(PWDATA[0]) status_reg[0] <= 1'b0;
                default: ;
            endcase
        end
    end
end

always @(*) begin
    PRDATA = 32'h0000_0000;
    if(apb_rd) begin
        case(PADDR[7:0])
            8'h00: PRDATA = ctrl_reg;
            8'h04: PRDATA = cmp_reg;
            8'h08: PRDATA = count_reg;
            8'h0C: PRDATA = status_reg;
            default: PRDATA = 32'h0000_0000;
        endcase
    end
end

endmodule
