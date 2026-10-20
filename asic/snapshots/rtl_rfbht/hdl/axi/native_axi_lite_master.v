module native_axi_lite_master (
    input  wire        clk,
    input  wire        reset_n,

    input  wire        req_valid,
    input  wire        req_write,
    input  wire [31:0] req_addr,
    input  wire [31:0] req_wdata,
    input  wire [3:0]  req_wstrb,
    output wire        req_ready,
    output wire        rsp_valid,
    output wire [31:0] rsp_rdata,
    output wire        rsp_error,

    output wire [31:0] m_axil_awaddr,
    output wire        m_axil_awvalid,
    input  wire        m_axil_awready,
    output wire [31:0] m_axil_wdata,
    output wire [3:0]  m_axil_wstrb,
    output wire        m_axil_wvalid,
    input  wire        m_axil_wready,
    input  wire [1:0]  m_axil_bresp,
    input  wire        m_axil_bvalid,
    output wire        m_axil_bready,

    output wire [31:0] m_axil_araddr,
    output wire        m_axil_arvalid,
    input  wire        m_axil_arready,
    input  wire [31:0] m_axil_rdata,
    input  wire [1:0]  m_axil_rresp,
    input  wire        m_axil_rvalid,
    output wire        m_axil_rready
);

localparam [2:0] ST_IDLE       = 3'd0;
localparam [2:0] ST_READ_ADDR  = 3'd1;
localparam [2:0] ST_READ_DATA  = 3'd2;
localparam [2:0] ST_WRITE_SEND = 3'd3;
localparam [2:0] ST_WRITE_RESP = 3'd4;
localparam [2:0] ST_CPU_RESP   = 3'd5;

reg [2:0]  state;
reg [31:0] addr_q;
reg [31:0] wdata_q;
reg [3:0]  wstrb_q;
reg        aw_done_q;
reg        w_done_q;
reg [31:0] rsp_data_q;
reg        rsp_error_q;

wire req_fire = req_valid && req_ready;
wire ar_fire  = m_axil_arvalid && m_axil_arready;
wire r_fire   = m_axil_rvalid && m_axil_rready;
wire aw_fire  = m_axil_awvalid && m_axil_awready;
wire w_fire   = m_axil_wvalid && m_axil_wready;
wire b_fire   = m_axil_bvalid && m_axil_bready;
wire write_channels_done = (aw_done_q || aw_fire) &&
                           (w_done_q  || w_fire);

assign req_ready = (state == ST_IDLE);
assign rsp_valid = (state == ST_CPU_RESP);
assign rsp_rdata = rsp_data_q;
assign rsp_error = rsp_error_q;

assign m_axil_awaddr  = addr_q;
assign m_axil_awvalid = (state == ST_WRITE_SEND) && !aw_done_q;
assign m_axil_wdata   = wdata_q;
assign m_axil_wstrb   = wstrb_q;
assign m_axil_wvalid  = (state == ST_WRITE_SEND) && !w_done_q;
assign m_axil_bready  = (state == ST_WRITE_RESP);

assign m_axil_araddr  = addr_q;
assign m_axil_arvalid = (state == ST_READ_ADDR);
assign m_axil_rready  = (state == ST_READ_DATA);

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        state       <= ST_IDLE;
        addr_q      <= 32'h0000_0000;
        wdata_q     <= 32'h0000_0000;
        wstrb_q     <= 4'b0000;
        aw_done_q   <= 1'b0;
        w_done_q    <= 1'b0;
        rsp_data_q  <= 32'h0000_0000;
        rsp_error_q <= 1'b0;
    end
    else begin
        case(state)
            ST_IDLE: begin
                aw_done_q   <= 1'b0;
                w_done_q    <= 1'b0;
                rsp_data_q  <= 32'h0000_0000;
                rsp_error_q <= 1'b0;
                if(req_fire) begin
                    addr_q  <= req_addr;
                    wdata_q <= req_wdata;
                    wstrb_q <= req_wstrb;
                    state   <= req_write ? ST_WRITE_SEND : ST_READ_ADDR;
                end
            end

            ST_READ_ADDR: begin
                if(ar_fire)
                    state <= ST_READ_DATA;
            end

            ST_READ_DATA: begin
                if(r_fire) begin
                    rsp_data_q  <= m_axil_rdata;
                    rsp_error_q <= (m_axil_rresp != 2'b00);
                    state       <= ST_CPU_RESP;
                end
            end

            ST_WRITE_SEND: begin
                if(aw_fire)
                    aw_done_q <= 1'b1;
                if(w_fire)
                    w_done_q <= 1'b1;
                if(write_channels_done)
                    state <= ST_WRITE_RESP;
            end

            ST_WRITE_RESP: begin
                if(b_fire) begin
                    rsp_error_q <= (m_axil_bresp != 2'b00);
                    state       <= ST_CPU_RESP;
                end
            end

            ST_CPU_RESP: state <= ST_IDLE;

            default: state <= ST_IDLE;
        endcase
    end
end

endmodule
