`timescale 1ns/1ps

module tb_axi_mmio;

reg clk;
reg reset_n;

reg         req_valid;
reg         req_write;
reg  [31:0] req_addr;
reg  [31:0] req_wdata;
reg  [3:0]  req_wstrb;
wire        req_ready;
wire        rsp_valid;
wire [31:0] rsp_rdata;
wire        rsp_error;

wire [31:0] master_awaddr;
wire        master_awvalid;
wire        master_awready;
wire [31:0] master_wdata;
wire [3:0]  master_wstrb;
wire        master_wvalid;
wire        master_wready;
wire [1:0]  master_bresp;
wire        master_bvalid;
wire        master_bready;
wire [31:0] master_araddr;
wire        master_arvalid;
wire        master_arready;
wire [31:0] master_rdata;
wire [1:0]  master_rresp;
wire        master_rvalid;
wire        master_rready;

reg allow_aw;
reg allow_w;
reg allow_ar;

wire [31:0] bridge_awaddr  = master_awaddr;
wire        bridge_awvalid = master_awvalid && allow_aw;
wire        bridge_awready;
wire [31:0] bridge_wdata   = master_wdata;
wire [3:0]  bridge_wstrb   = master_wstrb;
wire        bridge_wvalid  = master_wvalid && allow_w;
wire        bridge_wready;
wire [31:0] bridge_araddr  = master_araddr;
wire        bridge_arvalid = master_arvalid && allow_ar;
wire        bridge_arready;

assign master_awready = bridge_awready && allow_aw;
assign master_wready  = bridge_wready && allow_w;
assign master_arready = bridge_arready && allow_ar;

wire        PSEL;
wire        PENABLE;
wire        PWRITE;
wire [3:0]  PSTRB;
wire [31:0] PADDR;
wire [31:0] PWDATA;
wire [31:0] PRDATA;
wire        PREADY;
reg         PSLVERR;
wire [31:0] apb_transfer_count;

integer apb_wait_cfg;
integer apb_wait_remaining;
integer errors;
integer watchdog;
integer setup_count;
integer access_count;
integer access_wait_count;
integer aw_handshake_count;
integer w_handshake_count;
integer ar_handshake_count;
integer b_handshake_count;
integer r_handshake_count;
integer apb_complete_count;
integer response_count;
integer aw_cycle;
integer w_cycle;
integer apb_complete_cycle;
integer response_cycle;
integer cycle_count;

reg        previous_setup;
reg        apb_hold_active;
reg        apb_hold_write;
reg [31:0] apb_hold_addr;
reg [31:0] apb_hold_wdata;
reg [3:0]  apb_hold_wstrb;
reg        aw_hold_active;
reg [31:0] aw_hold_addr;
reg        w_hold_active;
reg [31:0] w_hold_data;
reg [3:0]  w_hold_strb;
reg        ar_hold_active;
reg [31:0] ar_hold_addr;

assign PREADY = (apb_wait_remaining == 0);
assign PRDATA = (PADDR == 32'h4000_0208) ? 32'h1357_9bdf :
                (PADDR == 32'h4000_0304) ? 32'h2468_ace0 :
                                           32'hdead_beef;

always #5 clk = ~clk;

native_axi_lite_master u_master (
    .clk(clk), .reset_n(reset_n),
    .req_valid(req_valid), .req_write(req_write), .req_addr(req_addr),
    .req_wdata(req_wdata), .req_wstrb(req_wstrb), .req_ready(req_ready),
    .rsp_valid(rsp_valid), .rsp_rdata(rsp_rdata), .rsp_error(rsp_error),
    .m_axil_awaddr(master_awaddr), .m_axil_awvalid(master_awvalid),
    .m_axil_awready(master_awready), .m_axil_wdata(master_wdata),
    .m_axil_wstrb(master_wstrb), .m_axil_wvalid(master_wvalid),
    .m_axil_wready(master_wready), .m_axil_bresp(master_bresp),
    .m_axil_bvalid(master_bvalid), .m_axil_bready(master_bready),
    .m_axil_araddr(master_araddr), .m_axil_arvalid(master_arvalid),
    .m_axil_arready(master_arready), .m_axil_rdata(master_rdata),
    .m_axil_rresp(master_rresp), .m_axil_rvalid(master_rvalid),
    .m_axil_rready(master_rready)
);

axi_lite_to_apb u_bridge (
    .clk(clk), .reset_n(reset_n),
    .s_axil_awaddr(bridge_awaddr), .s_axil_awvalid(bridge_awvalid),
    .s_axil_awready(bridge_awready), .s_axil_wdata(bridge_wdata),
    .s_axil_wstrb(bridge_wstrb), .s_axil_wvalid(bridge_wvalid),
    .s_axil_wready(bridge_wready), .s_axil_bresp(master_bresp),
    .s_axil_bvalid(master_bvalid), .s_axil_bready(master_bready),
    .s_axil_araddr(bridge_araddr), .s_axil_arvalid(bridge_arvalid),
    .s_axil_arready(bridge_arready), .s_axil_rdata(master_rdata),
    .s_axil_rresp(master_rresp), .s_axil_rvalid(master_rvalid),
    .s_axil_rready(master_rready),
    .PSEL(PSEL), .PENABLE(PENABLE), .PWRITE(PWRITE), .PSTRB(PSTRB),
    .PADDR(PADDR), .PWDATA(PWDATA), .PRDATA(PRDATA), .PREADY(PREADY),
    .PSLVERR(PSLVERR), .apb_transfer_count(apb_transfer_count)
);

task automatic fail(input string message);
    begin
        $error("%s", message);
        errors = errors + 1;
    end
endtask

task automatic expect32(
    input [31:0] actual,
    input [31:0] expected,
    input string label_text
);
    begin
        if(actual !== expected) begin
            $error("%s expected=%08h got=%08h", label_text, expected, actual);
            errors = errors + 1;
        end
    end
endtask

task automatic reset_case;
    begin
        reset_n = 0;
        req_valid = 0;
        req_write = 0;
        req_addr = 0;
        req_wdata = 0;
        req_wstrb = 0;
        allow_aw = 1;
        allow_w = 1;
        allow_ar = 1;
        PSLVERR = 0;
        apb_wait_cfg = 0;
        repeat(4) @(posedge clk);
        @(negedge clk);
        reset_n = 1;
        repeat(2) @(posedge clk);
    end
endtask

task automatic native_write(
    input [31:0] address,
    input [31:0] data,
    input [3:0]  strobe,
    input integer aw_delay,
    input integer w_delay,
    input integer wait_cycles,
    input expected_error
);
    begin
        allow_aw = (aw_delay == 0);
        allow_w = (w_delay == 0);
        apb_wait_cfg = wait_cycles;
        fork
            begin
                repeat(aw_delay) @(posedge clk);
                allow_aw = 1;
            end
            begin
                repeat(w_delay) @(posedge clk);
                allow_w = 1;
            end
        join_none

        @(negedge clk);
        req_write = 1;
        req_addr = address;
        req_wdata = data;
        req_wstrb = strobe;
        req_valid = 1;
        watchdog = 0;
        while(!req_ready) begin
            @(posedge clk); #1;
            watchdog = watchdog + 1;
            if(watchdog > 100) $fatal(1, "MMIO write request timeout");
        end
        @(posedge clk); #1;
        @(negedge clk); req_valid = 0;

        watchdog = 0;
        while(!rsp_valid) begin
            @(posedge clk); #1;
            watchdog = watchdog + 1;
            if(watchdog > 300) $fatal(1, "MMIO write response timeout");
        end
        if(rsp_error !== expected_error)
            fail($sformatf("MMIO write error expected=%0d got=%0d",
                           expected_error, rsp_error));
        @(posedge clk); #1;
        @(negedge clk);
    end
endtask

task automatic native_read(
    input [31:0] address,
    input [31:0] expected_data,
    input integer ar_delay,
    input integer wait_cycles,
    input expected_error
);
    begin
        allow_ar = (ar_delay == 0);
        apb_wait_cfg = wait_cycles;
        fork
            begin
                repeat(ar_delay) @(posedge clk);
                allow_ar = 1;
            end
        join_none

        @(negedge clk);
        req_write = 0;
        req_addr = address;
        req_wdata = 0;
        req_wstrb = 0;
        req_valid = 1;
        watchdog = 0;
        while(!req_ready) begin
            @(posedge clk); #1;
            watchdog = watchdog + 1;
            if(watchdog > 100) $fatal(1, "MMIO read request timeout");
        end
        @(posedge clk); #1;
        @(negedge clk); req_valid = 0;

        watchdog = 0;
        while(!rsp_valid) begin
            @(posedge clk); #1;
            watchdog = watchdog + 1;
            if(watchdog > 300) $fatal(1, "MMIO read response timeout");
        end
        if(!expected_error && (rsp_rdata !== expected_data))
            fail($sformatf("MMIO read expected=%08h got=%08h",
                           expected_data, rsp_rdata));
        if(rsp_error !== expected_error)
            fail($sformatf("MMIO read error expected=%0d got=%0d",
                           expected_error, rsp_error));
        @(posedge clk); #1;
        @(negedge clk);
    end
endtask

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        cycle_count <= 0;
        setup_count <= 0;
        access_count <= 0;
        access_wait_count <= 0;
        aw_handshake_count <= 0;
        w_handshake_count <= 0;
        ar_handshake_count <= 0;
        b_handshake_count <= 0;
        r_handshake_count <= 0;
        apb_complete_count <= 0;
        response_count <= 0;
        aw_cycle <= -1;
        w_cycle <= -1;
        apb_complete_cycle <= -1;
        response_cycle <= -1;
        apb_wait_remaining <= 0;
        previous_setup <= 0;
        apb_hold_active <= 0;
        aw_hold_active <= 0;
        w_hold_active <= 0;
        ar_hold_active <= 0;
    end
    else begin
        cycle_count <= cycle_count + 1;

        if(PSEL && !PENABLE) begin
            setup_count <= setup_count + 1;
            previous_setup <= 1;
            apb_wait_remaining <= apb_wait_cfg;
        end
        else begin
            if(previous_setup) begin
                assert(PSEL && PENABLE)
                    else $fatal(1, "APB ACCESS did not follow SETUP");
                previous_setup <= 0;
            end
            if(PSEL && PENABLE && !PREADY)
                apb_wait_remaining <= apb_wait_remaining - 1;
        end

        if(PSEL && PENABLE) begin
            access_count <= access_count + 1;
            if(!PREADY)
                access_wait_count <= access_wait_count + 1;
            if(PREADY) begin
                apb_complete_count <= apb_complete_count + 1;
                apb_complete_cycle <= cycle_count;
            end
        end

        if(PSEL && PENABLE && !PREADY) begin
            if(!apb_hold_active) begin
                apb_hold_active <= 1;
                apb_hold_write <= PWRITE;
                apb_hold_addr <= PADDR;
                apb_hold_wdata <= PWDATA;
                apb_hold_wstrb <= PSTRB;
            end
            else begin
                assert(PSEL && PENABLE && PWRITE == apb_hold_write &&
                       PADDR == apb_hold_addr && PWDATA == apb_hold_wdata &&
                       PSTRB == apb_hold_wstrb)
                    else $fatal(1, "APB payload changed during wait state");
            end
        end
        else if(apb_hold_active)
            apb_hold_active <= 0;

        if(aw_hold_active) begin
            assert(master_awvalid && master_awaddr == aw_hold_addr)
                else $fatal(1, "AXI-Lite AW changed under backpressure");
            if(master_awvalid && master_awready)
                aw_hold_active <= 0;
        end
        else if(master_awvalid && !master_awready) begin
            aw_hold_active <= 1;
            aw_hold_addr <= master_awaddr;
        end

        if(w_hold_active) begin
            assert(master_wvalid && master_wdata == w_hold_data &&
                   master_wstrb == w_hold_strb)
                else $fatal(1, "AXI-Lite W changed under backpressure");
            if(master_wvalid && master_wready)
                w_hold_active <= 0;
        end
        else if(master_wvalid && !master_wready) begin
            w_hold_active <= 1;
            w_hold_data <= master_wdata;
            w_hold_strb <= master_wstrb;
        end

        if(ar_hold_active) begin
            assert(master_arvalid && master_araddr == ar_hold_addr)
                else $fatal(1, "AXI-Lite AR changed under backpressure");
            if(master_arvalid && master_arready)
                ar_hold_active <= 0;
        end
        else if(master_arvalid && !master_arready) begin
            ar_hold_active <= 1;
            ar_hold_addr <= master_araddr;
        end

        if(master_awvalid && master_awready) begin
            aw_handshake_count <= aw_handshake_count + 1;
            aw_cycle <= cycle_count;
        end
        if(master_wvalid && master_wready) begin
            w_handshake_count <= w_handshake_count + 1;
            w_cycle <= cycle_count;
        end
        if(master_arvalid && master_arready)
            ar_handshake_count <= ar_handshake_count + 1;
        if(master_bvalid && master_bready)
            b_handshake_count <= b_handshake_count + 1;
        if(master_rvalid && master_rready)
            r_handshake_count <= r_handshake_count + 1;
        if(rsp_valid) begin
            assert(apb_complete_count > 0)
                else $fatal(1, "Native MMIO response occurred before APB completion");
            response_count <= response_count + 1;
            response_cycle <= cycle_count;
        end
    end
end

initial begin
    clk = 0;
    errors = 0;
    reset_n = 0;
    req_valid = 0;
    req_write = 0;
    req_addr = 0;
    req_wdata = 0;
    req_wstrb = 0;
    allow_aw = 1;
    allow_w = 1;
    allow_ar = 1;
    PSLVERR = 0;
    apb_wait_cfg = 0;

    $display("===== AXI-LITE / APB SELF-CHECKING TEST =====");

    // TEST 16: W is accepted before AW, followed by one APB setup/access.
    reset_case();
    $display("[TEST 16] MMIO write via AXI-Lite to APB");
    native_write(32'h4000_0100, 32'hcafe_babe, 4'b1111, 3, 0, 0, 0);
    expect32(aw_handshake_count, 1, "T16 AW handshakes");
    expect32(w_handshake_count, 1, "T16 W handshakes");
    if(!(w_cycle < aw_cycle)) fail("T16 independent W-before-AW not observed");
    expect32(setup_count, 1, "T16 APB setup cycles");
    expect32(apb_complete_count, 1, "T16 APB completions");
    expect32(apb_transfer_count, 1, "T16 bridge transfer counter");
    expect32(PADDR, 32'h4000_0100, "T16 APB address");
    expect32(PWDATA, 32'hcafe_babe, "T16 APB data");
    if(PSTRB !== 4'hf) fail("T16 APB PSTRB incorrect");
    expect32(b_handshake_count, 1, "T16 AXI B handshakes");

    // TEST 17: AR is deliberately stalled before the APB read.
    reset_case();
    $display("[TEST 17] MMIO read via AXI-Lite to APB");
    native_read(32'h4000_0208, 32'h1357_9bdf, 3, 0, 0);
    expect32(ar_handshake_count, 1, "T17 AR handshakes");
    expect32(r_handshake_count, 1, "T17 R handshakes");
    expect32(setup_count, 1, "T17 APB setup cycles");
    expect32(apb_complete_count, 1, "T17 APB completions");

    // TEST 18: APB access and all payload signals remain asserted/stable.
    reset_case();
    $display("[TEST 18] APB wait states");
    native_write(32'h4000_0004, 32'h0000_005a, 4'b0001, 0, 0, 5, 0);
    if(access_wait_count < 5)
        fail("T18 did not observe five APB wait cycles");
    expect32(apb_complete_count, 1, "T18 APB completion");
    expect32(response_count, 1, "T18 native response count");

    // Extra check: PSLVERR must become an AXI-Lite/native error.
    reset_case();
    $display("[TEST 19B] AXI-Lite/APB error propagation");
    PSLVERR = 1;
    native_read(32'h4000_0304, 32'h0, 0, 0, 1);

    if(errors != 0)
        $fatal(1, "[FAIL] AXI-Lite/APB tests: %0d error(s)", errors);

    $display("[PASS] AXI-Lite/APB tests 16-18 and MMIO error propagation");
    $display("[PASS] APB SETUP/ACCESS/wait-state and AXI-Lite stability assertions");
    $finish;
end

endmodule
