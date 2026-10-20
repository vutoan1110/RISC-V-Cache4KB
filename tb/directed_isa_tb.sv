`timescale 1ns/1ps

module tb_directed_isa #(
    // 64 is the directed regression's geometry. The ASIC view runs this
    // bench at 256, the only geometry its SRAM-backed cache arrays accept;
    // the checks are architectural, so they do not depend on it.
    parameter integer TB_LINE_COUNT = 64
);

localparam [31:0] HALT_INSTR = 32'h0000_006f; // JAL x0,0

reg clk;
reg reset_n;
reg key1_n;
reg uart_rx;
wire uart_tx;
wire [6:0] HEX0, HEX1, HEX2, HEX3, HEX4, HEX5, HEX6, HEX7;
wire [7:0] LEDR;
wire [7:0] LCD_DATA;
wire LCD_EN, LCD_RS, LCD_RW, LCD_ON, LCD_BLON;

reg [31:0] architectural_regs [0:31];
integer i;
integer trace_fd;
integer retired_before_halt;
integer cycle_count;
reg done;
wire [31:0] core_assertion_checks;
wire [31:0] axi_assertion_checks;
wire [31:0] cache_assertion_checks;

wire actual_regfile_write =
    dut.u_core.u_pipeline.reg_wr_w &&
    dut.u_core.u_pipeline.datapath.valid_w &&
    !dut.u_core.stall_pipe &&
    (dut.u_core.u_pipeline.datapath.instr_w[11:7] != 5'd0);

soc_top #(
    .MEMFILE("verification/directed/directed_isa.hex"),
    .IMEM_DEPTH(1024),
    .DMEM_DEPTH(1024),
    .ICACHE_LINE_COUNT(TB_LINE_COUNT),
    .DCACHE_LINE_COUNT(TB_LINE_COUNT),
    .BRANCH_PREDICT_ENABLE(1),
    .BHT_ENTRIES(256)
) dut (
    .clk(clk), .reset_n(reset_n), .key1_n(key1_n),
    .uart_rx(uart_rx), .uart_tx(uart_tx),
    .HEX0(HEX0), .HEX1(HEX1), .HEX2(HEX2), .HEX3(HEX3),
    .HEX4(HEX4), .HEX5(HEX5), .HEX6(HEX6), .HEX7(HEX7),
    .LEDR(LEDR), .LCD_DATA(LCD_DATA), .LCD_EN(LCD_EN),
    .LCD_RS(LCD_RS), .LCD_RW(LCD_RW), .LCD_ON(LCD_ON),
    .LCD_BLON(LCD_BLON)
);

core_assertions #(.BRANCH_PREDICT_ENABLE(1)) u_core_assertions (
    .clk(clk), .reset_n(reset_n), .stall_pipe(dut.u_core.stall_pipe),
    .valid_d(dut.u_core.u_pipeline.datapath.valid_d),
    .valid_e(dut.u_core.u_pipeline.datapath.valid_e),
    .valid_m(dut.u_core.u_pipeline.datapath.valid_m),
    .valid_w(dut.u_core.u_pipeline.datapath.valid_w),
    .instr_d(dut.u_core.u_pipeline.datapath.instr_d),
    .instr_e(dut.u_core.u_pipeline.datapath.instr_e),
    .instr_m(dut.u_core.u_pipeline.datapath.instr_m),
    .use_rs1_d(dut.u_core.u_pipeline.use_rs1_d),
    .use_rs2_d(dut.u_core.u_pipeline.use_rs2_d),
    .result_src_e(dut.u_core.u_pipeline.result_src_e),
    .load_use_hazard(dut.u_core.u_pipeline.datapath.load_use_hazard),
    .stall_f(dut.u_core.u_pipeline.datapath.stall_f),
    .stall_d(dut.u_core.u_pipeline.datapath.stall_d),
    .flush_e(dut.u_core.u_pipeline.datapath.flush_e),
    .pc_f(dut.u_core.u_pipeline.datapath.pc_f),
    .pc_d(dut.u_core.u_pipeline.datapath.pc_d),
    .pc_e(dut.u_core.u_pipeline.datapath.pc_e),
    .pc_src_e(dut.u_core.u_pipeline.datapath.pc_src_e),
    .is_branch_e(dut.u_core.u_pipeline.datapath.is_branch_e),
    .branch_taken_e(dut.u_core.u_pipeline.datapath.branch_taken_e),
    .mispredict_e(dut.u_core.u_pipeline.datapath.mispredict_e),
    .pc_target_e(dut.u_core.u_pipeline.datapath.pc_target_e),
    .pc_plus4_e(dut.u_core.u_pipeline.datapath.pc_plus4_e),
    .branch_resolve_fire(dut.u_core.u_pipeline.datapath.branch_resolve_fire),
    .bht_update_en(dut.u_core.u_pipeline.datapath.branch_resolve_fire),
    .mem_wr_m(dut.u_core.mem_wr_m),
    .architectural_reg_write(actual_regfile_write),
    .retire_valid(dut.retire_valid), .retire_order(dut.retire_order),
    .retire_pc(dut.retire_pc), .retire_instr(dut.retire_instr),
    .retire_rs1_addr(dut.retire_rs1_addr),
    .retire_rs1_rdata(dut.retire_rs1_rdata),
    .retire_rs2_addr(dut.retire_rs2_addr),
    .retire_rs2_rdata(dut.retire_rs2_rdata),
    .retire_rd_we(dut.retire_rd_we), .retire_rd_addr(dut.retire_rd_addr),
    .retire_mem_write(dut.retire_mem_write),
    .retire_mem_addr(dut.retire_mem_addr),
    .retire_mem_wstrb(dut.retire_mem_wstrb),
    .assertion_checks(core_assertion_checks)
);

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
    .assertion_checks(axi_assertion_checks)
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
    .assertion_checks(cache_assertion_checks)
);

core_coverage u_coverage (
    .clk(clk), .reset_n(reset_n),
    .retire_valid(dut.retire_valid), .retire_instr(dut.retire_instr),
    .forward_a_e(dut.u_core.u_pipeline.datapath.forward_a_e),
    .forward_b_e(dut.u_core.u_pipeline.datapath.forward_b_e),
    .load_use_hazard(dut.u_core.u_pipeline.datapath.load_use_hazard),
    .branch_resolve_fire(dut.u_core.u_pipeline.datapath.branch_resolve_fire),
    .branch_funct3(dut.u_core.u_pipeline.datapath.instr_e[14:12]),
    .branch_taken(dut.u_core.u_pipeline.datapath.branch_taken_e),
    .predicted_taken(dut.u_core.u_pipeline.datapath.predict_taken_e),
    .branch_mispredict(dut.u_core.u_pipeline.datapath.mispredict_e),
    .icache_hit_event(dut.icache_hit_event),
    .icache_miss_event(dut.icache_miss_event),
    .dcache_read_hit_event(dut.dcache_read_hit_event),
    .dcache_read_miss_event(dut.dcache_read_miss_event),
    .dcache_write_hit_event(dut.dcache_write_hit_event),
    .dcache_write_miss_event(dut.dcache_write_miss_event),
    .arvalid(dut.axi_arvalid), .arready(dut.axi_arready),
    .rvalid(dut.axi_rvalid), .rready(dut.axi_rready),
    .awvalid(dut.axi_awvalid), .awready(dut.axi_awready),
    .wvalid(dut.axi_wvalid), .wready(dut.axi_wready),
    .bvalid(dut.axi_bvalid), .bready(dut.axi_bready),
    .irq_accept(dut.u_core.u_pipeline.datapath.irq_accept),
    .cache_wait(dut.if_wait_dbg || dut.d_wait_dbg),
    .axi_busy(dut.axi_memory_busy)
);

always #5 clk = ~clk;

function integer onehot_count;
    input [8:0] value;
    integer k;
begin
    onehot_count = 0;
    for(k = 0; k < 9; k = k + 1)
        onehot_count = onehot_count + value[k];
end
endfunction

always @(posedge clk) begin
    if(reset_n) begin
        cycle_count <= cycle_count + 1;
        if(onehot_count(dut.cycle_reason_onehot_dbg) != 1)
            $fatal(1, "Cycle classifier is not one-hot: %09b",
                   dut.cycle_reason_onehot_dbg);
        if(dut.retire_valid) begin
            if(dut.retire_instr == HALT_INSTR) begin
                done <= 1'b1;
            end
            else begin
                $fdisplay(trace_fd,
                    "%0d,%08x,%08x,%0d,%0d,%08x,%0d,%08x,%08x,%x",
                    dut.retire_order, dut.retire_pc, dut.retire_instr,
                    dut.retire_rd_addr, dut.retire_rd_we, dut.retire_rd_wdata,
                    dut.retire_mem_write, dut.retire_mem_addr,
                    dut.retire_mem_wdata, dut.retire_mem_wstrb);
                retired_before_halt <= retired_before_halt + 1;
                if(dut.retire_rd_we)
                    architectural_regs[dut.retire_rd_addr] <= dut.retire_rd_wdata;
            end
        end
    end
end

initial begin
    clk = 0;
    reset_n = 0;
    key1_n = 1;
    uart_rx = 1;
    done = 0;
    retired_before_halt = 0;
    cycle_count = 0;
    for(i = 0; i < 32; i = i + 1)
        architectural_regs[i] = 0;
    trace_fd = $fopen("verification/results/directed/dut_directed.csv", "w");
    if(trace_fd == 0)
        $fatal(1, "cannot open directed retirement trace");
    $fdisplay(trace_fd,
              "order,pc,instr,rd,we,rd_data,mem_we,mem_addr,mem_wdata,mem_wstrb");

    repeat(5) @(posedge clk);
    @(negedge clk);
    reset_n = 1;

    fork
        begin
            wait(done);
        end
        begin
            repeat(200000) @(posedge clk);
            $fatal(1, "directed full-SoC watchdog timeout");
        end
    join_any
    disable fork;
    #2;

    if(architectural_regs[31] !== 32'd1)
        $fatal(1, "directed ISA self-check failed with code %0d",
               architectural_regs[31]);
`ifdef ASIC_VIEW_SIM
    // Macro-backed RAM: word 1027 is bank 1027[11:9]=2 (R14: 8 banks; 1027[10:9] with 4), offset 1027[8:0]=3.
    if(dut.u_axi_ram.g_bank[2].u_bank.mem[3] !== 32'h0000_0000)
`else
    if({dut.u_axi_ram.RAM3[1027], dut.u_axi_ram.RAM2[1027],
        dut.u_axi_ram.RAM1[1027], dut.u_axi_ram.RAM0[1027]} !== 32'h0000_0000)
`endif
        $fatal(1, "wrong-path cacheable store changed RAM[0x100c]");
    if(dut.apb_transfer_count !== 32'd0)
        $fatal(1, "wrong-path MMIO store reached APB");
    if(dut.u_observability.conditional_branch_count !==
       dut.u_observability.branch_taken_count +
       dut.u_observability.branch_not_taken_count)
        $fatal(1, "conditional branch event invariant failed");
    if(dut.u_observability.branch_prediction_count !==
       dut.u_observability.branch_correct_prediction_count +
       dut.u_observability.mispredict_event_count)
        $fatal(1, "prediction event invariant failed");
    if(dut.perf_mcycle_count_dbg !==
       dut.u_observability.retire_cycle_count +
       dut.u_observability.load_use_cycle_count +
       dut.u_observability.icache_wait_cycle_count +
       dut.u_observability.dcache_wait_cycle_count +
       dut.u_observability.control_redirect_cycle_count +
       dut.u_observability.trap_redirect_cycle_count +
       dut.u_observability.mmio_wait_cycle_count +
       dut.u_observability.pipe_fill_drain_cycle_count +
       dut.u_observability.other_cycle_count)
        $fatal(1, "exclusive cycle counters do not reconstruct mcycle");

    u_coverage.report();
    $fclose(trace_fd);
    $display("[PASS] RV32I claimed-subset directed regression (%0d retirements)",
             retired_before_halt);
    $display("[PASS] Zmmul pipeline execution regression");
    $display("[PASS] Architectural retirement order and payload assertions");
    $display("[PASS] Wrong-path architectural suppression (register/RAM/MMIO)");
    $display("[PASS] Counter and cache accounting invariants");
    $display("[PASS] AXI protocol assertions (%0d sampled cycles)",
             axi_assertion_checks);
    $finish;
end

endmodule
