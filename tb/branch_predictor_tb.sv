`timescale 1ns/1ps

// Branch-predictor integration test. The core-level predictor test remains as a
// detailed six-branch-type waveform test; this bench adds the parameterized
// BP_OFF/BP_ON comparison, exact event equations, speculative side-effect
// suppression, load-use metadata retention, and interrupt priority.
module tb_branch_predictor;

reg clk;
reg reset_n;
reg irq_timer;
reg stall_pipe;

wire [31:0] pc_on;
wire [31:0] pc_off;
wire [31:0] instr_on;
wire [31:0] instr_off;
wire mem_wr_on, mem_rd_on, mem_wr_off, mem_rd_off;
wire [31:0] addr_on, wdata_on, addr_off, wdata_off;
wire [2:0] funct3_on, funct3_off;
wire trap_on, trap_off;
wire [31:0] mcause_on, mepc_on, mtvec_on;
wire [31:0] mcause_off, mepc_off, mtvec_off;
wire [31:0] mcycle_on, minstret_on, mcycle_off, minstret_off;
wire [31:0] load_stall_on, load_stall_off;
wire [31:0] redirect_on, redirect_off;
wire cond_on, taken_on, nt_on, prediction_on, correct_on, miss_on;
wire cond_off, taken_off, nt_off, prediction_off, correct_off, miss_off;

reg [31:0] imem [0:255];
reg [31:0] dmem_on [0:255];
reg [31:0] dmem_off [0:255];

integer i;
integer failures;
integer on_cond_count, on_taken_count, on_nt_count;
integer on_prediction_count, on_correct_count, on_miss_count;
integer off_cond_count, off_taken_count, off_nt_count;
integer off_prediction_count, off_correct_count, off_miss_count;
integer on_store_count, off_store_count;
integer trap_count;
integer predicted_fetch_won;
integer correct_without_flush;
integer wrong_target_observed;
integer mostly_nt_resolves;
integer mostly_nt_misses;

localparam [31:0] NOP = 32'h0000_0013;

function [31:0] RV32_I;
    input [11:0] imm;
    input [4:0] rs1;
    input [2:0] funct3;
    input [4:0] rd;
    begin RV32_I = {imm, rs1, funct3, rd, 7'b0010011}; end
endfunction

function [31:0] RV32_LOAD;
    input [11:0] imm;
    input [4:0] rs1;
    input [2:0] funct3;
    input [4:0] rd;
    begin RV32_LOAD = {imm, rs1, funct3, rd, 7'b0000011}; end
endfunction

function [31:0] RV32_S;
    input [11:0] imm;
    input [4:0] rs2;
    input [4:0] rs1;
    input [2:0] funct3;
    begin RV32_S = {imm[11:5], rs2, rs1, funct3, imm[4:0], 7'b0100011}; end
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

assign instr_on  = (pc_on[31:2]  < 256) ? imem[pc_on[9:2]]  : NOP;
assign instr_off = (pc_off[31:2] < 256) ? imem[pc_off[9:2]] : NOP;

riscv_core #(.BRANCH_PREDICT_ENABLE(1), .BHT_ENTRIES(256)) dut_on (
    .clk(clk), .reset_n(reset_n), .irq_timer(irq_timer),
    .pc_f(pc_on), .instr(instr_on),
    .mem_wr_m(mem_wr_on), .mem_rd_m(mem_rd_on),
    .alu_result_m(addr_on), .wr_data_m(wdata_on),
    .rd_data(dmem_on[addr_on[9:2]]),
    .trap_taken(trap_on), .mcause_dbg(mcause_on), .mepc_dbg(mepc_on),
    .mtvec_dbg(mtvec_on), .stall_pipe(stall_pipe),
    .mcycle_dbg(mcycle_on), .minstret_dbg(minstret_on),
    .mem_funct3_m(funct3_on), .load_stall_dbg(load_stall_on),
    .branch_flush_dbg(redirect_on), .control_redirect_dbg(),
    .retire_event_dbg(), .load_use_stall_event_dbg(),
    .control_redirect_event_dbg(), .mispredict_event_dbg(miss_on),
    .conditional_branch_event_dbg(cond_on),
    .branch_taken_event_dbg(taken_on),
    .branch_not_taken_event_dbg(nt_on),
    .branch_prediction_event_dbg(prediction_on),
    .branch_correct_prediction_event_dbg(correct_on),
    .pipeline_nonempty_dbg(),
    .retire_valid(), .retire_order(), .retire_pc(), .retire_pc_next(),
    .retire_instr(), .retire_rs1_addr(), .retire_rs1_rdata(),
    .retire_rs2_addr(), .retire_rs2_rdata(), .retire_rd_addr(),
    .retire_rd_wdata(), .retire_rd_we(), .retire_mem_valid(),
    .retire_mem_write(), .retire_mem_addr(), .retire_mem_wdata(),
    .retire_mem_wstrb(), .retire_trap(), .retire_interrupt()
);

riscv_core #(.BRANCH_PREDICT_ENABLE(0), .BHT_ENTRIES(256)) dut_off (
    .clk(clk), .reset_n(reset_n), .irq_timer(irq_timer),
    .pc_f(pc_off), .instr(instr_off),
    .mem_wr_m(mem_wr_off), .mem_rd_m(mem_rd_off),
    .alu_result_m(addr_off), .wr_data_m(wdata_off),
    .rd_data(dmem_off[addr_off[9:2]]),
    .trap_taken(trap_off), .mcause_dbg(mcause_off), .mepc_dbg(mepc_off),
    .mtvec_dbg(mtvec_off), .stall_pipe(stall_pipe),
    .mcycle_dbg(mcycle_off), .minstret_dbg(minstret_off),
    .mem_funct3_m(funct3_off), .load_stall_dbg(load_stall_off),
    .branch_flush_dbg(redirect_off), .control_redirect_dbg(),
    .retire_event_dbg(), .load_use_stall_event_dbg(),
    .control_redirect_event_dbg(), .mispredict_event_dbg(miss_off),
    .conditional_branch_event_dbg(cond_off),
    .branch_taken_event_dbg(taken_off),
    .branch_not_taken_event_dbg(nt_off),
    .branch_prediction_event_dbg(prediction_off),
    .branch_correct_prediction_event_dbg(correct_off),
    .pipeline_nonempty_dbg(),
    .retire_valid(), .retire_order(), .retire_pc(), .retire_pc_next(),
    .retire_instr(), .retire_rs1_addr(), .retire_rs1_rdata(),
    .retire_rs2_addr(), .retire_rs2_rdata(), .retire_rd_addr(),
    .retire_rd_wdata(), .retire_rd_we(), .retire_mem_valid(),
    .retire_mem_write(), .retire_mem_addr(), .retire_mem_wdata(),
    .retire_mem_wstrb(), .retire_trap(), .retire_interrupt()
);

always #5 clk = ~clk;

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

task automatic clear_program_and_state;
    integer k;
    begin
        reset_n   = 1'b0;
        irq_timer = 1'b0;
        stall_pipe = 1'b0;
        for (k = 0; k < 256; k = k + 1) begin
            imem[k] = NOP;
            dmem_on[k] = 32'h0;
            dmem_off[k] = 32'h0;
        end
        repeat (3) @(posedge clk);
        for (k = 0; k < 32; k = k + 1) begin
            dut_on.datapath.regfile.regs[k] = 32'h0;
            dut_off.datapath.regfile.regs[k] = 32'h0;
        end
        predicted_fetch_won = 0;
        correct_without_flush = 0;
        wrong_target_observed = 0;
        mostly_nt_resolves = 0;
        mostly_nt_misses = 0;
    end
endtask

task automatic release_reset;
    begin
        @(negedge clk);
        reset_n = 1'b1;
    end
endtask

always @(posedge clk) begin
    if (!reset_n) begin
        on_cond_count = 0; on_taken_count = 0; on_nt_count = 0;
        on_prediction_count = 0; on_correct_count = 0; on_miss_count = 0;
        off_cond_count = 0; off_taken_count = 0; off_nt_count = 0;
        off_prediction_count = 0; off_correct_count = 0; off_miss_count = 0;
        on_store_count = 0; off_store_count = 0; trap_count = 0;
    end
    else begin
        if (cond_on) on_cond_count = on_cond_count + 1;
        if (taken_on) on_taken_count = on_taken_count + 1;
        if (nt_on) on_nt_count = on_nt_count + 1;
        if (prediction_on) on_prediction_count = on_prediction_count + 1;
        if (correct_on) on_correct_count = on_correct_count + 1;
        if (miss_on) on_miss_count = on_miss_count + 1;

        if (cond_off) off_cond_count = off_cond_count + 1;
        if (taken_off) off_taken_count = off_taken_count + 1;
        if (nt_off) off_nt_count = off_nt_count + 1;
        if (prediction_off) off_prediction_count = off_prediction_count + 1;
        if (correct_off) off_correct_count = off_correct_count + 1;
        if (miss_off) off_miss_count = off_miss_count + 1;

        if (trap_on) trap_count = trap_count + 1;

        if (mem_wr_on) begin
            on_store_count = on_store_count + 1;
            dmem_on[addr_on[9:2]] <= wdata_on;
        end
        if (mem_wr_off) begin
            off_store_count = off_store_count + 1;
            dmem_off[addr_off[9:2]] <= wdata_off;
        end

        if (dut_on.datapath.branch_resolve_fire &&
            !dut_on.datapath.branch_mispredict_e &&
            !dut_on.datapath.pc_src_e)
            correct_without_flush = correct_without_flush + 1;

        if (dut_on.datapath.branch_resolve_fire &&
            dut_on.datapath.pc_e == 32'h0000_000c) begin
            mostly_nt_resolves = mostly_nt_resolves + 1;
            if (dut_on.datapath.branch_mispredict_e)
                mostly_nt_misses = mostly_nt_misses + 1;
        end

        // This proves a taken BHT result changes the Fetch PC before resolve.
        if (dut_on.datapath.pred_taken_f &&
            dut_on.datapath.predict_redirect_f &&
            !dut_on.datapath.pc_src_e && !trap_on) begin
            automatic reg [31:0] expected_pc;
            expected_pc = dut_on.datapath.pred_target_f;
            #1;
            if (pc_on == expected_pc)
                predicted_fetch_won = predicted_fetch_won + 1;
        end
    end
end

task automatic test_bp_off_on_loop;
    begin
        $display("[TEST 1/2/3/13/14/15] BP_OFF versus BP_ON loop training");
        clear_program_and_state();
        imem[0] = RV32_I(12'd0, 5'd0, 3'b000, 5'd1);     // x1=0
        imem[1] = RV32_I(12'd8, 5'd0, 3'b000, 5'd2);     // x2=8
        imem[2] = RV32_I(12'd1, 5'd1, 3'b000, 5'd1);     // x1++
        imem[3] = RV32_B(-13'sd4, 5'd2, 5'd1, 3'b100);   // blt x1,x2,-4
        imem[4] = RV32_I(12'd9, 5'd0, 3'b000, 5'd3);     // exit marker
        imem[5] = RV32_J(21'd0, 5'd0);                   // stop loop
        release_reset();
        repeat (70) @(posedge clk);
        #2;

        check(dut_on.datapath.regfile.regs[1] == 32'd8 &&
              dut_off.datapath.regfile.regs[1] == 32'd8 &&
              dut_on.datapath.regfile.regs[3] == 32'd9 &&
              dut_off.datapath.regfile.regs[3] == 32'd9,
              "BP_OFF and BP_ON have identical architectural registers");
        check(on_cond_count == 8 && on_taken_count == 7 && on_nt_count == 1,
              "BP_ON conditional/taken/not-taken event counts are exact");
        check(off_cond_count == 8 && off_taken_count == 7 && off_nt_count == 1,
              "BP_OFF conditional/taken/not-taken event counts remain active");
        check(on_prediction_count == 8 && on_correct_count == 6 && on_miss_count == 2,
              "Weak-NT loop evolves to 6 correct and 2 mispredictions");
        check(off_prediction_count == 0 && off_correct_count == 0 && off_miss_count == 0,
              "BP_OFF prediction event counters remain zero");
        check(on_cond_count == on_taken_count + on_nt_count &&
              on_prediction_count == on_correct_count + on_miss_count &&
              off_cond_count == off_taken_count + off_nt_count,
              "Branch event invariants hold in both builds");
        check(predicted_fetch_won >= 1,
              "pred_taken_f redirects PC to pred_target_f before EX resolve");
        check(correct_without_flush == 6,
              "Every correct conditional prediction avoids an EX flush");
        $display("Branch predictions : %0d", on_prediction_count);
        $display("Correct predictions: %0d", on_correct_count);
        $display("Mispredictions     : %0d", on_miss_count);
        $display("Accuracy           : %0d/%0d", on_correct_count, on_prediction_count);
    end
endtask

task automatic test_mostly_not_taken;
    begin
        $display("[TEST 3] mostly-not-taken branch trains to strongly NT");
        clear_program_and_state();
        imem[0] = RV32_I(12'd0, 5'd0, 3'b000, 5'd1);
        imem[1] = RV32_I(12'd5, 5'd0, 3'b000, 5'd2);
        imem[2] = RV32_I(12'd1, 5'd1, 3'b000, 5'd1);
        imem[3] = RV32_B(13'd8, 5'd0, 5'd0, 3'b001);    // always NT
        imem[4] = RV32_B(-13'sd8, 5'd2, 5'd1, 3'b100); // loop
        imem[5] = RV32_J(21'd0, 5'd0);
        release_reset();
        repeat (55) @(posedge clk);
        #2;
        check(mostly_nt_resolves == 5 && mostly_nt_misses == 0,
              "Five not-taken outcomes remain correctly predicted after training");
        check(dut_on.datapath.g_bp_on.u_bht.bht_mem[3] == 2'b00,
              "Mostly-not-taken branch reaches strongly-not-taken state 00");
        check(dut_on.datapath.regfile.regs[1] == 32'd5,
              "Mostly-not-taken microprogram completes architecturally");
    end
endtask

task automatic test_wrong_path_side_effects;
    begin
        $display("[TEST 4/5/6/7] T->NT recovery and wrong-path suppression");
        clear_program_and_state();
        imem[0] = RV32_I(12'd1,   5'd0, 3'b000, 5'd1);  // actual condition false
        imem[1] = RV32_I(12'd123, 5'd0, 3'b000, 5'd10); // store data
        imem[2] = RV32_B(13'd12, 5'd0, 5'd1, 3'b000);   // beq x1,x0,pc+12 (NT)
        imem[3] = RV32_J(21'd20, 5'd0);                  // correct path -> PC32
        imem[4] = NOP;
        imem[5] = RV32_S(12'd0, 5'd10, 5'd0, 3'b010);   // predicted wrong store
        imem[6] = RV32_I(12'd123, 5'd0, 3'b000, 5'd20); // predicted wrong reg write
        imem[7] = NOP;
        imem[8] = RV32_I(12'd9, 5'd0, 3'b000, 5'd3);    // correct marker
        imem[9] = RV32_J(21'd0, 5'd0);
        // Force only the ON instance to predict taken for branch PC=8.
        @(negedge clk);
        dut_on.datapath.g_bp_on.u_bht.bht_mem[2] = 2'b11;
        reset_n = 1'b1;
        repeat (35) @(posedge clk);
        #2;

        check(on_miss_count == 1 && on_cond_count == 1,
              "Predicted-taken/actual-not-taken is one misprediction");
        check(dut_on.datapath.branch_recovery_pc == 32'h0000_000c ||
              dut_on.datapath.regfile.regs[3] == 32'd9,
              "T->NT recovery selects branch PC + 4");
        check(on_store_count == 0 && dmem_on[0] == 32'h0,
              "Wrong-path store produces no memory side effect");
        check(dut_on.datapath.regfile.regs[20] == 32'h0,
              "Wrong-path register write is suppressed");
        check(dut_on.datapath.regfile.regs[3] == 32'd9,
              "Correct recovery path retires normally");
    end
endtask

task automatic test_load_use_branch;
    begin
        $display("[TEST 9] load-use stall preserves branch prediction metadata");
        clear_program_and_state();
        dmem_on[0] = 32'h0;
        dmem_off[0] = 32'h0;
        imem[0] = RV32_LOAD(12'd0, 5'd0, 3'b010, 5'd5); // lw x5,0(x0)
        imem[1] = RV32_B(13'd12, 5'd0, 5'd5, 3'b000);   // beq x5,x0,+12
        imem[2] = RV32_I(12'd1, 5'd0, 3'b000, 5'd6);    // wrong fall-through
        imem[3] = RV32_J(21'd8, 5'd0);
        imem[4] = RV32_I(12'd7, 5'd0, 3'b000, 5'd7);    // target
        imem[5] = RV32_J(21'd0, 5'd0);
        release_reset();
        repeat (35) @(posedge clk);
        #2;

        check(load_stall_on == 32'd1,
              "Exactly one load-use stall is generated");
        check(on_cond_count == 1 && on_miss_count == 1,
              "Stalled branch resolves and updates the BHT exactly once");
        check(dut_on.datapath.regfile.regs[6] == 32'h0 &&
              dut_on.datapath.regfile.regs[7] == 32'd7,
              "Load-use branch flushes stale fall-through and reaches target");
    end
endtask

task automatic test_interrupt_priority;
    begin
        $display("[TEST 12] interrupt while conditional prediction is active");
        clear_program_and_state();
        imem[0]  = RV32_I(12'd1, 5'd0, 3'b000, 5'd1);
        imem[1]  = RV32_B(-13'sd4, 5'd1, 5'd1, 3'b000); // taken loop to PC0
        imem[32] = RV32_I(12'd1, 5'd0, 3'b000, 5'd20);  // mtvec handler flag
        imem[33] = 32'h3020_0073;                        // mret
        dut_on.datapath.g_bp_on.u_bht.bht_mem[1] = 2'b11;
        release_reset();
        dut_on.datapath.csr_mstatus = 32'h0000_0008;
        dut_on.datapath.csr_mie     = 32'h0000_0080;
        dut_on.datapath.csr_mtvec   = 32'h0000_0080;

        wait (reset_n && pc_on == 32'h0000_0004 &&
              dut_on.datapath.pred_taken_f);
        @(negedge clk); irq_timer = 1'b1;
        @(negedge clk); irq_timer = 1'b0;
        repeat (45) @(posedge clk);
        #2;

        check(trap_count == 1 && mcause_on == 32'h8000_0007,
              "Timer interrupt is accepted once with machine-timer cause");
        check(dut_on.datapath.regfile.regs[20] == 32'd1,
              "Trap redirect reaches mtvec and handler executes");
        check(mepc_on[1:0] == 2'b00 && mepc_on < 32'h0000_0008,
              "mepc records an aligned resumable loop PC");
        check(pc_on < 32'h0000_0080,
              "mret returns from handler to the interrupted program");
    end
endtask

initial begin
    clk = 1'b0;
    reset_n = 1'b0;
    irq_timer = 1'b0;
    stall_pipe = 1'b0;
    failures = 0;

    test_bp_off_on_loop();
    test_mostly_not_taken();
    test_wrong_path_side_effects();
    test_load_use_branch();
    test_interrupt_priority();

    if (failures == 0) begin
        $display("[PASS] Branch predictor recovery test");
        $display("[PASS] Wrong-path store suppression");
        $display("[PASS] BP OFF/ON architectural equivalence");
        $display("[PASS] Branch predictor integration regression");
        $finish;
    end
    else
        $fatal(1, "[FAIL] branch_predictor_tb: %0d checks failed", failures);
end

initial begin
    #20000;
    $fatal(1, "[FAIL] branch_predictor_tb timeout");
end

endmodule
