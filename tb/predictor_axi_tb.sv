`timescale 1ns/1ps

// Full active-architecture test: core -> native IF -> I-cache -> AXI master ->
// AXI RAM.  A trained taken prediction targets a cold cache line while the AXI
// slave inserts ARREADY delay and RVALID gaps.
module tb_predictor_axi;

reg clk;
reg reset_n;
reg key1_n;
reg uart_rx;
wire uart_tx;
wire [6:0] HEX0, HEX1, HEX2, HEX3, HEX4, HEX5, HEX6, HEX7;
wire [7:0] LEDR, LCD_DATA;
wire LCD_EN, LCD_RS, LCD_RW, LCD_ON, LCD_BLON;

integer i;
integer failures;
integer timeout_cycles;
integer branch_events;
integer prediction_events;
integer correct_events;
integer mispredict_events;
integer predicted_pc_redirects;
integer target_refills;
integer ar_backpressure_cycles;
integer r_gap_cycles_observed;

localparam [31:0] NOP = 32'h0000_0013;

function [31:0] RV32_I;
    input [11:0] imm;
    input [4:0] rs1;
    input [2:0] funct3;
    input [4:0] rd;
    begin RV32_I = {imm, rs1, funct3, rd, 7'b0010011}; end
endfunction

function [31:0] RV32_B;
    input [12:0] imm;
    input [4:0] rs2;
    input [4:0] rs1;
    input [2:0] funct3;
    begin
        RV32_B = {imm[12], imm[10:5], rs2, rs1,
                  funct3, imm[4:1], imm[11], 7'b1100011};
    end
endfunction

function [31:0] RV32_J;
    input [20:0] imm;
    input [4:0] rd;
    begin
        RV32_J = {imm[20], imm[10:1], imm[11], imm[19:12],
                  rd, 7'b1101111};
    end
endfunction

soc_top #(
    .ICACHE_LINE_COUNT(8),
    .DCACHE_LINE_COUNT(8),
    .ICACHE_MISS_PENALTY(1),
    .DCACHE_MISS_PENALTY(1),
    .IMEM_DEPTH(1024),
    .DMEM_DEPTH(64),
    .MEMFILE(""),
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

always #5 clk = ~clk;

task automatic ram_set_word;
    input integer word_index;
    input [31:0] value;
    begin
        dut.u_axi_ram.RAM0[word_index] = value[7:0];
        dut.u_axi_ram.RAM1[word_index] = value[15:8];
        dut.u_axi_ram.RAM2[word_index] = value[23:16];
        dut.u_axi_ram.RAM3[word_index] = value[31:24];
    end
endtask

task automatic check;
    input condition;
    input string message;
    begin
        if (condition !== 1'b1) begin
            failures = failures + 1;
            $error("[FAIL] %s", message);
        end
        else
            $display("[PASS] %s", message);
    end
endtask

always @(posedge clk) begin
    if (reset_n) begin
        if (dut.conditional_branch_event_dbg) branch_events = branch_events + 1;
        if (dut.branch_prediction_event_dbg) prediction_events = prediction_events + 1;
        if (dut.branch_correct_prediction_event_dbg) correct_events = correct_events + 1;
        if (dut.mispredict_event_dbg) mispredict_events = mispredict_events + 1;

        if (dut.icache_refill_req_valid && dut.icache_refill_req_ready &&
            dut.icache_refill_req_addr == 32'h0000_0040)
            target_refills = target_refills + 1;

        if (dut.axi_arvalid && !dut.axi_arready)
            ar_backpressure_cycles = ar_backpressure_cycles + 1;
        if (dut.u_axi_ram.rd_state != 2'd0 && !dut.axi_rvalid)
            r_gap_cycles_observed = r_gap_cycles_observed + 1;

        if (dut.u_core.u_pipeline.datapath.pred_taken_f &&
            dut.u_core.u_pipeline.datapath.predict_redirect_f &&
            !dut.u_core.u_pipeline.datapath.pc_src_e) begin
            automatic reg [31:0] expected_target;
            expected_target = dut.u_core.u_pipeline.datapath.pred_target_f;
            #1;
            if (dut.pc_f_dbg == expected_target)
                predicted_pc_redirects = predicted_pc_redirects + 1;
        end

        assert(dut.u_observability.conditional_branch_count ==
               dut.u_observability.branch_taken_count +
               dut.u_observability.branch_not_taken_count)
            else $fatal(1, "Branch direction counter invariant failed");
        assert(dut.u_observability.branch_prediction_count ==
               dut.u_observability.branch_correct_prediction_count +
               dut.u_observability.mispredict_event_count)
            else $fatal(1, "Prediction counter invariant failed");
    end
end

initial begin
    clk = 1'b0;
    reset_n = 1'b0;
    key1_n = 1'b1;
    uart_rx = 1'b1;
    failures = 0;
    timeout_cycles = 0;
    branch_events = 0;
    prediction_events = 0;
    correct_events = 0;
    mispredict_events = 0;
    predicted_pc_redirects = 0;
    target_refills = 0;
    ar_backpressure_cycles = 0;
    r_gap_cycles_observed = 0;

    // Exercise the existing AXI RAM verification controls without changing
    // any synthesizable bus architecture.
    force dut.axi_test_ar_stall_cycles = 8'd3;
    force dut.axi_test_r_first_delay_cycles = 8'd2;
    force dut.axi_test_r_gap_cycles = 8'd2;

    #1;
    for (i = 0; i < 1088; i = i + 1)
        ram_set_word(i, 32'h0000_0000);
    for (i = 0; i < 64; i = i + 1)
        ram_set_word(i, NOP);

    // PC 0x04 predicts directly to cold line 0x40.  The instruction at 0x08
    // must never retire when the prediction is correct.
    ram_set_word(0,  RV32_I(12'd1, 5'd0, 3'b000, 5'd1));
    ram_set_word(1,  RV32_B(13'd60, 5'd1, 5'd1, 3'b000));
    ram_set_word(2,  RV32_I(12'd123, 5'd0, 3'b000, 5'd20));
    ram_set_word(16, RV32_I(12'd7, 5'd0, 3'b000, 5'd3));
    ram_set_word(17, RV32_J(21'd0, 5'd0));

    repeat (4) @(posedge clk);
    @(negedge clk);
    for (i = 0; i < 32; i = i + 1)
        dut.u_core.u_pipeline.datapath.regfile.regs[i] = 32'h0000_0000;
    dut.u_core.u_pipeline.datapath.g_bp_on.u_bht.bht_mem[1] = 2'b11;
    reset_n = 1'b1;

    while (dut.u_core.u_pipeline.datapath.regfile.regs[3] !== 32'd7) begin
        @(posedge clk); #1;
        timeout_cycles = timeout_cycles + 1;
        if (timeout_cycles > 1000)
            $fatal(1, "[FAIL] timeout waiting for predicted target program");
    end
    repeat (10) @(posedge clk); #2;

    check(predicted_pc_redirects == 1,
          "Taken BHT result drives PC to predicted target before EX");
    check(target_refills == 1 && dut.icache_miss_count >= 2,
          "Predicted cold target causes exactly one I-cache refill");
    check(ar_backpressure_cycles > 0 && r_gap_cycles_observed > 0,
          "ARREADY delay and RVALID gaps are both observed");
    check(branch_events == 1 && prediction_events == 1 &&
          correct_events == 1 && mispredict_events == 0,
          "Cache/AXI stalls do not duplicate the branch resolve/update event");
    check(dut.u_core.u_pipeline.datapath.g_bp_on.u_bht.bht_mem[1] == 2'b11,
          "Correct taken resolve updates saturated BHT exactly once");
    check(dut.u_core.u_pipeline.datapath.regfile.regs[20] == 32'h0,
          "Sequential wrong-path instruction does not retire");
    check(dut.u_core.u_pipeline.datapath.regfile.regs[3] == 32'd7,
          "Architectural result survives I-cache miss and AXI backpressure");

    release dut.axi_test_ar_stall_cycles;
    release dut.axi_test_r_first_delay_cycles;
    release dut.axi_test_r_gap_cycles;

    if (failures == 0) begin
        $display("[PASS] Predicted-target I-cache miss test");
        $display("[PASS] Predictor AXI backpressure test");
        $finish;
    end
    else
        $fatal(1, "[FAIL] predictor_axi_tb: %0d checks failed", failures);
end

initial begin
    #30000;
    $fatal(1, "[FAIL] predictor_axi_tb global timeout");
end

endmodule
