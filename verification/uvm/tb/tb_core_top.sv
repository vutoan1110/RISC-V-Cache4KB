`timescale 1ns/1ps
`include "tb/rf_bht_backdoor.svh"

// UVM top level for riscv_core_native. Clock and reset are generated here;
// everything else is driven from the environment through the two native
// interfaces. The retirement port is observed only.
module tb_core_top;

    import uvm_pkg::*;
`include "uvm_macros.svh"
    import core_uvm_pkg::*;

    localparam integer BRANCH_PREDICT_ENABLE = 1;
    localparam integer BHT_ENTRIES           = 256;
    localparam integer RESET_CYCLES          = 5;

    logic clk;
    logic reset_n;
    logic irq_timer;

    native_if imem_if (.clk(clk), .reset_n(reset_n));
    native_if dmem_if (.clk(clk), .reset_n(reset_n));
    rvfi_if   retire_if (.clk(clk), .reset_n(reset_n));

    // The instruction port is read only.
    assign imem_if.req_write = 1'b0;
    assign imem_if.req_wdata = 32'h0;
    assign imem_if.req_wstrb = 4'h0;

    // Milestone 1 keeps the timer interrupt low; IRQ belongs to phase 5.
    assign irq_timer = 1'b0;

    riscv_core_native #(
        .BRANCH_PREDICT_ENABLE (BRANCH_PREDICT_ENABLE),
        .BHT_ENTRIES           (BHT_ENTRIES)
    ) dut (
        .clk          (clk),
        .reset_n      (reset_n),
        .irq_timer    (irq_timer),

        .if_req_valid (imem_if.req_valid),
        .if_req_addr  (imem_if.req_addr),
        .if_req_ready (imem_if.req_ready),
        .if_rsp_valid (imem_if.rsp_valid),
        .if_rsp_data  (imem_if.rsp_rdata),
        .if_rsp_error (imem_if.rsp_error),

        .d_req_valid  (dmem_if.req_valid),
        .d_req_write  (dmem_if.req_write),
        .d_req_addr   (dmem_if.req_addr),
        .d_req_wdata  (dmem_if.req_wdata),
        .d_req_wstrb  (dmem_if.req_wstrb),
        .d_req_ready  (dmem_if.req_ready),
        .d_rsp_valid  (dmem_if.rsp_valid),
        .d_rsp_rdata  (dmem_if.rsp_rdata),
        .d_rsp_error  (dmem_if.rsp_error),

        .trap_taken   (retire_if.trap_taken),
        .mcause_dbg   (),
        .mepc_dbg     (),
        .mtvec_dbg    (),
        .mcycle_dbg   (retire_if.mcycle_dbg),
        .minstret_dbg (retire_if.minstret_dbg),
        .load_stall_dbg       (),
        .branch_flush_dbg     (),
        .control_redirect_dbg (),

        .retire_event_dbg                    (retire_if.retire_event_dbg),
        .load_use_stall_event_dbg            (retire_if.load_use_stall_event_dbg),
        .control_redirect_event_dbg          (retire_if.control_redirect_event_dbg),
        .mispredict_event_dbg                (retire_if.mispredict_event_dbg),
        .conditional_branch_event_dbg        (retire_if.conditional_branch_event_dbg),
        .branch_taken_event_dbg              (retire_if.branch_taken_event_dbg),
        .branch_not_taken_event_dbg          (retire_if.branch_not_taken_event_dbg),
        .branch_prediction_event_dbg         (retire_if.branch_prediction_event_dbg),
        .branch_correct_prediction_event_dbg (retire_if.branch_correct_prediction_event_dbg),
        .pipeline_nonempty_dbg               (retire_if.pipeline_nonempty_dbg),

        .retire_valid     (retire_if.retire_valid),
        .retire_order     (retire_if.retire_order),
        .retire_pc        (retire_if.retire_pc),
        .retire_pc_next   (retire_if.retire_pc_next),
        .retire_instr     (retire_if.retire_instr),
        .retire_rs1_addr  (retire_if.retire_rs1_addr),
        .retire_rs1_rdata (retire_if.retire_rs1_rdata),
        .retire_rs2_addr  (retire_if.retire_rs2_addr),
        .retire_rs2_rdata (retire_if.retire_rs2_rdata),
        .retire_rd_addr   (retire_if.retire_rd_addr),
        .retire_rd_wdata  (retire_if.retire_rd_wdata),
        .retire_rd_we     (retire_if.retire_rd_we),
        .retire_mem_valid (retire_if.retire_mem_valid),
        .retire_mem_write (retire_if.retire_mem_write),
        .retire_mem_addr  (retire_if.retire_mem_addr),
        .retire_mem_wdata (retire_if.retire_mem_wdata),
        .retire_mem_wstrb (retire_if.retire_mem_wstrb),
        .retire_trap      (retire_if.retire_trap),
        .retire_interrupt (retire_if.retire_interrupt),

        .pc_f_dbg     (),
        .if_wait_dbg  (retire_if.if_wait_dbg),
        .d_wait_dbg   (retire_if.d_wait_dbg),
        .if_error_dbg (retire_if.if_error_dbg),
        .d_error_dbg  (retire_if.d_error_dbg)
    );

    // Pipeline assertions from verification/assertions/core_assertions.sv.
    core_assertion_bind u_core_assertion_bind ();

    // Procedural functional coverage reused from verification/coverage. The
    // cache, AXI and IRQ inputs do not exist at the core boundary, so those
    // bins stay empty until the SoC-level environment of phase 5.
    core_coverage u_coverage (
        .clk                (clk),
        .reset_n            (reset_n),
        .retire_valid       (retire_if.retire_valid),
        .retire_instr       (retire_if.retire_instr),
        .forward_a_e        (dut.u_pipeline.datapath.forward_a_e),
        .forward_b_e        (dut.u_pipeline.datapath.forward_b_e),
        .load_use_hazard    (dut.u_pipeline.datapath.load_use_hazard),
        .branch_resolve_fire(dut.u_pipeline.datapath.branch_resolve_fire),
        .branch_funct3      (dut.u_pipeline.datapath.instr_e[14:12]),
        .branch_taken       (dut.u_pipeline.datapath.branch_taken_e),
        .predicted_taken    (dut.u_pipeline.datapath.predict_taken_e),
        .branch_mispredict  (dut.u_pipeline.datapath.mispredict_e),
        .icache_hit_event       (1'b0),
        .icache_miss_event      (1'b0),
        .dcache_read_hit_event  (1'b0),
        .dcache_read_miss_event (1'b0),
        .dcache_write_hit_event (1'b0),
        .dcache_write_miss_event(1'b0),
        .arvalid (1'b0), .arready (1'b0),
        .rvalid  (1'b0), .rready  (1'b0),
        .awvalid (1'b0), .awready (1'b0),
        .wvalid  (1'b0), .wready  (1'b0),
        .bvalid  (1'b0), .bready  (1'b0),
        .irq_accept (dut.u_pipeline.datapath.irq_accept),
        .cache_wait (retire_if.if_wait_dbg || retire_if.d_wait_dbg),
        .axi_busy   (1'b0)
    );

    // 100 MHz simulation clock, as in every testbench under tb/.
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // hdl/regfile.v has no reset, so in simulation the register file starts as
    // X. A program that reads a register before writing it then propagates X
    // into branch_taken_e, mispredict_e and finally pc_f. Every testbench that
    // runs such a program initialises the array here; tb/random_trace_tb.sv
    // does exactly the same thing.
    initial begin
        reset_n = 1'b0;
        for (int r = 0; r < 32; r++)
            `RF_SET(dut.u_pipeline.datapath.regfile, r, 32'h0);
        repeat (RESET_CYCLES) @(posedge clk);
        @(negedge clk);
        reset_n = 1'b1;
    end

    initial begin
        uvm_config_db #(virtual native_if)::set(null, "uvm_test_top", "imem_vif", imem_if);
        uvm_config_db #(virtual native_if)::set(null, "uvm_test_top", "dmem_vif", dmem_if);
        uvm_config_db #(virtual rvfi_if)::set(null, "uvm_test_top", "rvfi_vif", retire_if);

        if ($test$plusargs("UVM_WAVE")) begin
            $dumpfile("verification/uvm/out/tb_core_top.vcd");
            $dumpvars(0, tb_core_top);
        end

        run_test("core_smoke_test");
    end

    // Cycle-accurate fetch/pipeline trace for debugging a divergence.
    // +PCTRACE_TO=<cycle> turns it on; it is off by default.
    int unsigned dbg_cycle;
    int unsigned dbg_from;
    int unsigned dbg_to;

    initial begin
        dbg_from = 0;
        dbg_to   = 0;
        void'($value$plusargs("PCTRACE_FROM=%d", dbg_from));
        void'($value$plusargs("PCTRACE_TO=%d", dbg_to));
    end

    always @(posedge clk) begin
        if (!reset_n)
            dbg_cycle <= 0;
        else begin
            dbg_cycle <= dbg_cycle + 1;
            if ((dbg_to != 0) && (dbg_cycle >= dbg_from) && (dbg_cycle <= dbg_to))
                $display({"[PCTRACE] c=%0d pc_f=%08h instr=%08h | req v=%0b a=%08h r=%0b",
                          " | rsp v=%0b d=%08h | pend=%0b buf=%0b | stall=%0b",
                          " | pc_src_e=%0b mispred=%0b flush_d=%0b flush_e=%0b",
                          " | v_defw=%0b%0b%0b%0b pc_d=%08h instr_d=%08h",
                          " | ret v=%0b pc=%08h instr=%08h we=%0b"},
                    dbg_cycle,
                    dut.u_pipeline.datapath.pc_f, dut.instr,
                    imem_if.req_valid, imem_if.req_addr, imem_if.req_ready,
                    imem_if.rsp_valid, imem_if.rsp_rdata,
                    dut.if_pending, dut.if_buffer_valid, dut.stall_pipe,
                    dut.u_pipeline.datapath.pc_src_e,
                    dut.u_pipeline.datapath.mispredict_e,
                    dut.u_pipeline.datapath.flush_d, dut.u_pipeline.datapath.flush_e,
                    dut.u_pipeline.datapath.valid_d, dut.u_pipeline.datapath.valid_e,
                    dut.u_pipeline.datapath.valid_m, dut.u_pipeline.datapath.valid_w,
                    dut.u_pipeline.datapath.pc_d, dut.u_pipeline.datapath.instr_d,
                    retire_if.retire_valid, retire_if.retire_pc,
                    retire_if.retire_instr, retire_if.retire_rd_we);
        end
    end

    // core_coverage prints its bins procedurally; there is no covergroup
    // database to merge until phase 6. core_base_test::report_phase triggers
    // this event, which keeps the task call out of a final procedure.
    initial begin
        static uvm_event report_e = uvm_event_pool::get_global("core_coverage_report");
        report_e.wait_trigger();
        u_coverage.report();
        // core_assertions calls $fatal on any violation, so reaching this line
        // means every sampled cycle passed.
        $display("[COVERAGE] core_assertions sampled %0d cycles with no failure",
                 dut.u_pipeline.u_core_assertions.assertion_checks);
    end

endmodule
