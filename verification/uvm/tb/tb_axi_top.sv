`timescale 1ns/1ps

// UVM top level for hdl/axi/cache_axi_master.v. The three native channels are
// driven by initiator agents, the AXI4 side by a slave agent.
module tb_axi_top #(
    // One knob for the whole environment: it parameterises the DUT and is
    // published to the checkers, so the design and the checkers cannot be told
    // different burst lengths.
    parameter integer LINE_WORDS = 4
);

    import uvm_pkg::*;
`include "uvm_macros.svh"
    import axi_uvm_pkg::*;

    localparam integer RESET_CYCLES = 5;

    logic clk;
    logic reset_n;

    refill_if i_refill_if (.clk(clk), .reset_n(reset_n));
    refill_if d_refill_if (.clk(clk), .reset_n(reset_n));
    wthru_if  wthru_if_i  (.clk(clk), .reset_n(reset_n));
    axi4_if   axi_if      (.clk(clk), .reset_n(reset_n));

    wire [31:0] assertion_checks;

    cache_axi_master #(.LINE_WORDS(LINE_WORDS)) dut (
        .clk     (clk),
        .reset_n (reset_n),

        .i_refill_req_valid (i_refill_if.req_valid),
        .i_refill_req_addr  (i_refill_if.req_addr),
        .i_refill_req_ready (i_refill_if.req_ready),
        .i_refill_rsp_valid (i_refill_if.rsp_valid),
        .i_refill_rsp_data  (i_refill_if.rsp_data),
        .i_refill_rsp_last  (i_refill_if.rsp_last),
        .i_refill_rsp_error (i_refill_if.rsp_error),

        .d_refill_req_valid (d_refill_if.req_valid),
        .d_refill_req_addr  (d_refill_if.req_addr),
        .d_refill_req_ready (d_refill_if.req_ready),
        .d_refill_rsp_valid (d_refill_if.rsp_valid),
        .d_refill_rsp_data  (d_refill_if.rsp_data),
        .d_refill_rsp_last  (d_refill_if.rsp_last),
        .d_refill_rsp_error (d_refill_if.rsp_error),

        .d_write_req_valid (wthru_if_i.req_valid),
        .d_write_req_addr  (wthru_if_i.req_addr),
        .d_write_req_data  (wthru_if_i.req_data),
        .d_write_req_strb  (wthru_if_i.req_strb),
        .d_write_req_ready (wthru_if_i.req_ready),
        .d_write_rsp_valid (wthru_if_i.rsp_valid),
        .d_write_rsp_error (wthru_if_i.rsp_error),

        .m_axi_araddr  (axi_if.araddr),
        .m_axi_arlen   (axi_if.arlen),
        .m_axi_arsize  (axi_if.arsize),
        .m_axi_arburst (axi_if.arburst),
        .m_axi_arvalid (axi_if.arvalid),
        .m_axi_arready (axi_if.arready),

        .m_axi_rdata  (axi_if.rdata),
        .m_axi_rresp  (axi_if.rresp),
        .m_axi_rlast  (axi_if.rlast),
        .m_axi_rvalid (axi_if.rvalid),
        .m_axi_rready (axi_if.rready),

        .m_axi_awaddr  (axi_if.awaddr),
        .m_axi_awlen   (axi_if.awlen),
        .m_axi_awsize  (axi_if.awsize),
        .m_axi_awburst (axi_if.awburst),
        .m_axi_awvalid (axi_if.awvalid),
        .m_axi_awready (axi_if.awready),

        .m_axi_wdata  (axi_if.wdata),
        .m_axi_wstrb  (axi_if.wstrb),
        .m_axi_wlast  (axi_if.wlast),
        .m_axi_wvalid (axi_if.wvalid),
        .m_axi_wready (axi_if.wready),

        .m_axi_bresp  (axi_if.bresp),
        .m_axi_bvalid (axi_if.bvalid),
        .m_axi_bready (axi_if.bready),

        .busy                (),
        .active_source       (),
        .axi_read_txn_count  (),
        .axi_write_txn_count (),
        .axi_read_txn_event  (),
        .axi_write_txn_event (),
        // Error capture is exercised by tb/axi_memory_tb.sv T19; held idle
        // here so the input is never X.
        .wr_err              (),
        .wr_err_addr         (),
        .wr_err_clear        (1'b0)
    );

    // The AXI protocol and store-ordering checks from
    // verification/assertions/axi_assertions.sv, reused as is.
    axi_assertions #(.LINE_WORDS(LINE_WORDS)) u_axi_assertions (
        .clk(clk), .reset_n(reset_n),
        .araddr(axi_if.araddr), .arlen(axi_if.arlen),
        .arsize(axi_if.arsize), .arburst(axi_if.arburst),
        .arvalid(axi_if.arvalid), .arready(axi_if.arready),
        .rdata(axi_if.rdata), .rlast(axi_if.rlast),
        .rvalid(axi_if.rvalid), .rready(axi_if.rready),
        .awaddr(axi_if.awaddr), .awlen(axi_if.awlen),
        .awsize(axi_if.awsize), .awburst(axi_if.awburst),
        .awvalid(axi_if.awvalid), .awready(axi_if.awready),
        .wdata(axi_if.wdata), .wstrb(axi_if.wstrb), .wlast(axi_if.wlast),
        .wvalid(axi_if.wvalid), .wready(axi_if.wready),
        .bvalid(axi_if.bvalid), .bready(axi_if.bready),
        .native_write_rsp_valid(wthru_if_i.rsp_valid),
        .assertion_checks(assertion_checks)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        reset_n = 1'b0;
        repeat (RESET_CYCLES) @(posedge clk);
        @(negedge clk);
        reset_n = 1'b1;
    end

    initial begin
        uvm_config_db #(virtual refill_if)::set(null, "uvm_test_top", "i_refill_vif", i_refill_if);
        uvm_config_db #(virtual refill_if)::set(null, "uvm_test_top", "d_refill_vif", d_refill_if);
        uvm_config_db #(virtual wthru_if)::set(null, "uvm_test_top", "wthru_vif", wthru_if_i);
        uvm_config_db #(virtual axi4_if)::set(null, "uvm_test_top", "axi_vif", axi_if);
        uvm_config_db #(int unsigned)::set(null, "uvm_test_top", "refill_beats",
                                           LINE_WORDS);

        if ($test$plusargs("UVM_WAVE")) begin
            $dumpfile("verification/uvm/out/tb_axi_top.vcd");
            $dumpvars(0, tb_axi_top);
        end

        run_test("axi_smoke_test");
    end

    // axi_assertions calls $fatal on a violation, so reaching the end of the
    // run means every sampled cycle passed.
    initial begin
        static uvm_event report_e = uvm_event_pool::get_global("axi_assert_report");
        report_e.wait_trigger();
        $display("[COVERAGE] axi_assertions sampled %0d cycles with no failure",
                 assertion_checks);
    end

endmodule
