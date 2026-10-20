`timescale 1ns/1ps

// UVM top level for hdl/soc_top.v. The SoC has no external bus port, so the
// environment observes the retirement record, the counter bank and the
// internal APB bus through continuous assignments, and drives only the pins
// that exist: uart_rx and key1_n.
module tb_soc_top #(
    // Cache capacity is LINE_COUNT * 4 words * 4 bytes. 64 is the published
    // 1 KiB; the benchmark matrix also measures 256 (4 KiB), and the UVM
    // environment has to be able to reach the same point.
    parameter integer CACHE_LINE_COUNT = 64
);

    import uvm_pkg::*;
`include "uvm_macros.svh"
    import soc_uvm_pkg::*;

    localparam integer RESET_CYCLES = 5;

    logic clk;
    logic reset_n;
    logic key1_n;

    wire       uart_tx;
    wire [6:0] HEX0, HEX1, HEX2, HEX3, HEX4, HEX5, HEX6, HEX7;
    wire [7:0] LEDR;
    wire [7:0] LCD_DATA;
    wire       LCD_EN, LCD_RS, LCD_RW, LCD_ON, LCD_BLON;

    soc_obs_if obs_if  (.clk(clk), .reset_n(reset_n));
    apb_if     apb_bus (.clk(clk), .reset_n(reset_n));
    uart_if    serial  (.clk(clk), .reset_n(reset_n));

    assign serial.uart_tx = uart_tx;

    wire [31:0] core_assert_checks;
    wire [31:0] axi_assert_checks;
    wire [31:0] cache_assert_checks;

    soc_top #(
        .MEMFILE               ("verification/directed/directed_isa.hex"),
        .IMEM_DEPTH            (2048),   // R14 2026-09-29: 16 KiB unified RAM, was 1024+1024 words (RAM16K_CHANGES.md)
        .DMEM_DEPTH            (2048),
        .ICACHE_LINE_COUNT     (CACHE_LINE_COUNT),
        .DCACHE_LINE_COUNT     (CACHE_LINE_COUNT),
        .BRANCH_PREDICT_ENABLE (1),
        .BHT_ENTRIES           (256)
    ) dut (
        .clk(clk), .reset_n(reset_n), .key1_n(key1_n),
        .uart_rx(serial.uart_rx), .uart_tx(uart_tx),
        .HEX0(HEX0), .HEX1(HEX1), .HEX2(HEX2), .HEX3(HEX3),
        .HEX4(HEX4), .HEX5(HEX5), .HEX6(HEX6), .HEX7(HEX7),
        .LEDR(LEDR), .LCD_DATA(LCD_DATA), .LCD_EN(LCD_EN),
        .LCD_RS(LCD_RS), .LCD_RW(LCD_RW), .LCD_ON(LCD_ON), .LCD_BLON(LCD_BLON)
    );

    // ------------------------------------------------------------------
    // Observation wiring. Everything below is read-only.
    // ------------------------------------------------------------------
    assign obs_if.retire_valid     = dut.retire_valid;
    assign obs_if.retire_order     = dut.retire_order;
    assign obs_if.retire_pc        = dut.retire_pc;
    assign obs_if.retire_pc_next   = dut.retire_pc_next;
    assign obs_if.retire_instr     = dut.retire_instr;
    assign obs_if.retire_rd_addr   = dut.retire_rd_addr;
    assign obs_if.retire_rd_wdata  = dut.retire_rd_wdata;
    assign obs_if.retire_rd_we     = dut.retire_rd_we;
    assign obs_if.retire_mem_valid = dut.retire_mem_valid;
    assign obs_if.retire_mem_write = dut.retire_mem_write;
    assign obs_if.retire_mem_addr  = dut.retire_mem_addr;
    assign obs_if.retire_mem_wdata = dut.retire_mem_wdata;
    assign obs_if.retire_mem_wstrb = dut.retire_mem_wstrb;
    assign obs_if.retire_trap      = dut.retire_trap;
    assign obs_if.retire_interrupt = dut.retire_interrupt;

    assign obs_if.cycle_reason_onehot          = dut.cycle_reason_onehot_dbg;
    assign obs_if.mcycle_count                 = dut.perf_mcycle_count_dbg;
    assign obs_if.minstret_count               = dut.perf_minstret_count_dbg;
    assign obs_if.retire_cycle_count           = dut.u_observability.retire_cycle_count;
    assign obs_if.load_use_cycle_count         = dut.u_observability.load_use_cycle_count;
    assign obs_if.icache_wait_cycle_count      = dut.u_observability.icache_wait_cycle_count;
    assign obs_if.dcache_wait_cycle_count      = dut.u_observability.dcache_wait_cycle_count;
    assign obs_if.control_redirect_cycle_count = dut.u_observability.control_redirect_cycle_count;
    assign obs_if.trap_redirect_cycle_count    = dut.u_observability.trap_redirect_cycle_count;
    assign obs_if.mmio_wait_cycle_count        = dut.u_observability.mmio_wait_cycle_count;
    assign obs_if.pipe_fill_drain_cycle_count  = dut.u_observability.pipe_fill_drain_cycle_count;
    assign obs_if.other_cycle_count            = dut.u_observability.other_cycle_count;

    assign obs_if.icache_access_count     = dut.icache_access_count;
    assign obs_if.icache_hit_count        = dut.icache_hit_count;
    assign obs_if.icache_miss_count       = dut.icache_miss_count;
    assign obs_if.icache_main_hit_count   = dut.icache_main_hit_count;
    assign obs_if.icache_victim_hit_count = dut.icache_victim_hit_count;
    assign obs_if.icache_true_miss_count  = dut.icache_true_miss_count;
    assign obs_if.dcache_access_count     = dut.dcache_access_count;
    assign obs_if.dcache_read_count       = dut.dcache_read_count;
    assign obs_if.dcache_write_count      = dut.dcache_write_count;
    assign obs_if.dcache_read_hit_count   = dut.dcache_read_hit_count;
    assign obs_if.dcache_read_miss_count  = dut.dcache_read_miss_count;
    assign obs_if.dcache_write_hit_count  = dut.dcache_write_hit_count;
    assign obs_if.dcache_write_miss_count = dut.dcache_write_miss_count;
    assign obs_if.dcache_main_hit_count   = dut.dcache_main_hit_count;
    assign obs_if.dcache_victim_hit_count = dut.dcache_victim_hit_count;
    assign obs_if.dcache_true_miss_count  = dut.dcache_true_miss_count;

    assign obs_if.conditional_branch_count        = dut.u_observability.conditional_branch_count;
    assign obs_if.branch_taken_count              = dut.u_observability.branch_taken_count;
    assign obs_if.branch_not_taken_count          = dut.u_observability.branch_not_taken_count;
    assign obs_if.branch_prediction_count         = dut.u_observability.branch_prediction_count;
    assign obs_if.branch_correct_prediction_count = dut.u_observability.branch_correct_prediction_count;
    assign obs_if.mispredict_event_count          = dut.u_observability.mispredict_event_count;

    assign obs_if.apb_transfer_count = dut.apb_transfer_count;
    assign obs_if.irq_timer          = dut.irq_timer;
    assign obs_if.trap_taken         = dut.u_core.trap_taken;

    assign apb_bus.psel    = dut.PSEL_bus;
    assign apb_bus.penable = dut.PENABLE_bus;
    assign apb_bus.pwrite  = dut.PWRITE_bus;
    assign apb_bus.pstrb   = dut.PSTRB_bus;
    assign apb_bus.paddr   = dut.PADDR_bus;
    assign apb_bus.pwdata  = dut.PWDATA_bus;
    assign apb_bus.prdata  = dut.PRDATA_bus;
    assign apb_bus.pready  = dut.PREADY_bus;
    assign apb_bus.pslverr = dut.PSLVERR_bus;

    // ------------------------------------------------------------------
    // All three reusable checkers apply at this level.
    // ------------------------------------------------------------------
    core_assertion_bind u_core_assertion_bind ();

    axi_assertions u_axi_assertions (
        .clk(clk), .reset_n(reset_n),
        .araddr(dut.axi_araddr), .arlen(dut.axi_arlen),
        .arsize(dut.axi_arsize), .arburst(dut.axi_arburst),
        .arvalid(dut.axi_arvalid), .arready(dut.axi_arready),
        .rdata(dut.axi_rdata), .rlast(dut.axi_rlast),
        .rvalid(dut.axi_rvalid), .rready(dut.axi_rready),
        .awaddr(dut.axi_awaddr), .awlen(dut.axi_awlen),
        .awsize(dut.axi_awsize), .awburst(dut.axi_awburst),
        .awvalid(dut.axi_awvalid), .awready(dut.axi_awready),
        .wdata(dut.axi_wdata), .wstrb(dut.axi_wstrb), .wlast(dut.axi_wlast),
        .wvalid(dut.axi_wvalid), .wready(dut.axi_wready),
        .bvalid(dut.axi_bvalid), .bready(dut.axi_bready),
        .native_write_rsp_valid(dut.dcache_mem_wr_rsp_valid),
        .assertion_checks(axi_assert_checks)
    );

    cache_assertions u_cache_assertions (
        .clk(clk), .reset_n(reset_n),
        .i_access(dut.icache_access_count), .i_hit(dut.icache_hit_count),
        .i_miss(dut.icache_miss_count),
        .d_access(dut.dcache_access_count), .d_read(dut.dcache_read_count),
        .d_write(dut.dcache_write_count), .d_hit(dut.dcache_hit_count),
        .d_miss(dut.dcache_miss_count),
        .d_read_hit(dut.dcache_read_hit_count),
        .d_read_miss(dut.dcache_read_miss_count),
        .d_write_hit(dut.dcache_write_hit_count),
        .d_write_miss(dut.dcache_write_miss_count),
        .d_write_miss_event(dut.dcache_write_miss_event),
        .d_refill_req_valid(dut.dcache_refill_req_valid),
        .d_tag_write_enable(dut.u_dcache.g_dm_baseline.u_controller.tag_wr_en),
        .assertion_checks(cache_assert_checks)
    );

    assign core_assert_checks = dut.u_core.u_pipeline.u_core_assertions.assertion_checks;

    initial clk = 1'b0;
    always #5 clk = ~clk;

    // The program normally comes from the MEMFILE parameter, which is fixed at
    // elaboration. +SOC_HEX replaces it during reset, after the RAM has run its
    // own initialisation, so one build can run several programs.
    task automatic backdoor_load(string path);
        int        fd;
        int        code;
        int        idx;
        bit [31:0] word;

        fd = $fopen(path, "r");
        if (fd == 0) begin
            $display("[FAIL] cannot open +SOC_HEX image %s", path);
            $finish;
        end
        idx = 0;
        forever begin
            code = $fscanf(fd, "%h", word);
            if (code != 1)
                break;
            dut.u_axi_ram.RAM0[idx] = word[7:0];
            dut.u_axi_ram.RAM1[idx] = word[15:8];
            dut.u_axi_ram.RAM2[idx] = word[23:16];
            dut.u_axi_ram.RAM3[idx] = word[31:24];
            idx++;
        end
        $fclose(fd);
        $display("[INFO] backdoor-loaded %0d words from %s", idx, path);
    endtask

    initial begin
        string hex_path;
        reset_n = 1'b0;
        key1_n  = 1'b1;
        repeat (2) @(posedge clk);
        if ($value$plusargs("SOC_HEX=%s", hex_path))
            backdoor_load(hex_path);
        repeat (RESET_CYCLES - 2) @(posedge clk);
        @(negedge clk);
        reset_n = 1'b1;
    end

    initial begin
        uvm_config_db #(virtual soc_obs_if)::set(null, "uvm_test_top", "obs_vif", obs_if);
        uvm_config_db #(virtual apb_if)::set(null, "uvm_test_top", "apb_vif", apb_bus);
        uvm_config_db #(virtual uart_if)::set(null, "uvm_test_top", "uart_vif", serial);

        if ($test$plusargs("UVM_WAVE")) begin
            $dumpfile("verification/uvm/out/tb_soc_top.vcd");
            $dumpvars(0, tb_soc_top);
        end

        run_test("soc_directed_test");
    end

    // Every bound checker calls $fatal on a violation, so reaching this point
    // means all three sampled cleanly.
    initial begin
        static uvm_event report_e = uvm_event_pool::get_global("soc_assert_report");
        report_e.wait_trigger();
        $display({"[COVERAGE] assertions sampled with no failure:",
                  " core %0d cycles, axi %0d cycles, cache %0d cycles"},
                 core_assert_checks, axi_assert_checks, cache_assert_checks);
    end

endmodule
