module axi_lite_to_apb (
    input  wire        clk,
    input  wire        reset_n,

    input  wire [31:0] s_axil_awaddr,
    input  wire        s_axil_awvalid,
    output wire        s_axil_awready,
    input  wire [31:0] s_axil_wdata,
    input  wire [3:0]  s_axil_wstrb,
    input  wire        s_axil_wvalid,
    output wire        s_axil_wready,
    output wire [1:0]  s_axil_bresp,
    output wire        s_axil_bvalid,
    input  wire        s_axil_bready,

    input  wire [31:0] s_axil_araddr,
    input  wire        s_axil_arvalid,
    output wire        s_axil_arready,
    output wire [31:0] s_axil_rdata,
    output wire [1:0]  s_axil_rresp,
    output wire        s_axil_rvalid,
    input  wire        s_axil_rready,

    output wire        PSEL,
    output wire        PENABLE,
    output wire        PWRITE,
    output wire [3:0]  PSTRB,
    output wire [31:0] PADDR,
    output wire [31:0] PWDATA,
    input  wire [31:0] PRDATA,
    input  wire        PREADY,
    input  wire        PSLVERR,

    output reg  [31:0] apb_transfer_count
);

localparam [2:0] ST_IDLE      = 3'd0;
localparam [2:0] ST_APB_SETUP = 3'd1;
localparam [2:0] ST_APB_ACCESS= 3'd2;
localparam [2:0] ST_AXI_BRESP = 3'd3;
localparam [2:0] ST_AXI_RRESP = 3'd4;

localparam [1:0] RESP_OKAY   = 2'b00;
localparam [1:0] RESP_SLVERR = 2'b10;

reg [2:0] state;
reg       aw_hold_q;
reg [31:0] awaddr_q;
reg       w_hold_q;
reg [31:0] wdata_q;
reg [3:0]  wstrb_q;

reg        apb_write_q;
reg [31:0] apb_addr_q;
reg [31:0] apb_wdata_q;
reg [3:0]  apb_wstrb_q;
reg [31:0] rdata_q;
reg [1:0]  rresp_q;
reg [1:0]  bresp_q;

wire write_candidate = s_axil_awvalid || s_axil_wvalid ||
                       aw_hold_q || w_hold_q;

// AW/W accepted independently; AR blocked while a write is pending so only
// one AXI-Lite transaction reaches APB at a time.
assign s_axil_awready = (state == ST_IDLE) && !aw_hold_q;
assign s_axil_wready  = (state == ST_IDLE) && !w_hold_q;
assign s_axil_arready = (state == ST_IDLE) && !write_candidate;

wire aw_fire = s_axil_awvalid && s_axil_awready;
wire w_fire  = s_axil_wvalid && s_axil_wready;
wire ar_fire = s_axil_arvalid && s_axil_arready;
wire b_fire  = s_axil_bvalid && s_axil_bready;
wire r_fire  = s_axil_rvalid && s_axil_rready;

wire write_pair_complete = (state == ST_IDLE) &&
                           (aw_hold_q || aw_fire) &&
                           (w_hold_q  || w_fire);

wire [31:0] selected_awaddr = aw_hold_q ? awaddr_q : s_axil_awaddr;
wire [31:0] selected_wdata  = w_hold_q  ? wdata_q  : s_axil_wdata;
wire [3:0]  selected_wstrb  = w_hold_q  ? wstrb_q  : s_axil_wstrb;

assign PSEL    = (state == ST_APB_SETUP) || (state == ST_APB_ACCESS);
assign PENABLE = (state == ST_APB_ACCESS);
assign PWRITE  = apb_write_q;
assign PSTRB   = apb_wstrb_q;
assign PADDR   = apb_addr_q;
assign PWDATA  = apb_wdata_q;

assign s_axil_bvalid = (state == ST_AXI_BRESP);
assign s_axil_bresp  = bresp_q;
assign s_axil_rvalid = (state == ST_AXI_RRESP);
assign s_axil_rdata  = rdata_q;
assign s_axil_rresp  = rresp_q;

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        state              <= ST_IDLE;
        aw_hold_q          <= 1'b0;
        awaddr_q           <= 32'h0000_0000;
        w_hold_q           <= 1'b0;
        wdata_q            <= 32'h0000_0000;
        wstrb_q            <= 4'b0000;
        apb_write_q        <= 1'b0;
        apb_addr_q         <= 32'h0000_0000;
        apb_wdata_q        <= 32'h0000_0000;
        apb_wstrb_q        <= 4'b0000;
        rdata_q            <= 32'h0000_0000;
        rresp_q            <= RESP_OKAY;
        bresp_q            <= RESP_OKAY;
        apb_transfer_count <= 32'h0000_0000;
    end
    else begin
        if(aw_fire) begin
            aw_hold_q <= 1'b1;
            awaddr_q  <= s_axil_awaddr;
        end

        if(w_fire) begin
            w_hold_q <= 1'b1;
            wdata_q  <= s_axil_wdata;
            wstrb_q  <= s_axil_wstrb;
        end

        case(state)
            ST_IDLE: begin
                if(write_pair_complete) begin
                    apb_write_q <= 1'b1;
                    apb_addr_q  <= selected_awaddr;
                    apb_wdata_q <= selected_wdata;
                    apb_wstrb_q <= selected_wstrb;
                    aw_hold_q   <= 1'b0;
                    w_hold_q    <= 1'b0;
                    state       <= ST_APB_SETUP;
                end
                else if(ar_fire) begin
                    apb_write_q <= 1'b0;
                    apb_addr_q  <= s_axil_araddr;
                    apb_wdata_q <= 32'h0000_0000;
                    apb_wstrb_q <= 4'b0000;
                    state       <= ST_APB_SETUP;
                end
            end

            ST_APB_SETUP: begin
                // PSEL=1 and PENABLE=0 for exactly one setup cycle.
                state <= ST_APB_ACCESS;
            end

            ST_APB_ACCESS: begin
                if(PREADY) begin
                    apb_transfer_count <= apb_transfer_count + 1'b1;
                    if(apb_write_q) begin
                        bresp_q <= PSLVERR ? RESP_SLVERR : RESP_OKAY;
                        state   <= ST_AXI_BRESP;
                    end
                    else begin
                        rdata_q <= PRDATA;
                        rresp_q <= PSLVERR ? RESP_SLVERR : RESP_OKAY;
                        state   <= ST_AXI_RRESP;
                    end
                end
            end

            ST_AXI_BRESP: begin
                if(b_fire)
                    state <= ST_IDLE;
            end

            ST_AXI_RRESP: begin
                if(r_fire)
                    state <= ST_IDLE;
            end

            default: state <= ST_IDLE;
        endcase
    end
end

endmodule
