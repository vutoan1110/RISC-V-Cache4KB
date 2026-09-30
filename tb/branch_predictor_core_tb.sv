`timescale 1ns/1ps

module tb_branch_predictor_core;

reg         clk;
reg         reset_n;
reg         irq_timer;
reg         stall_pipe;

wire [31:0] pc_f;
wire [31:0] instr;
wire        mem_wr_m;
wire        mem_rd_m;
wire [31:0] alu_result_m;
wire [31:0] wr_data_m;
wire [31:0] rd_data;
wire        trap_taken;
wire [31:0] mcause_dbg;
wire [31:0] mepc_dbg;
wire [31:0] mtvec_dbg;
wire [31:0] mcycle_dbg;
wire [31:0] minstret_dbg;
wire [2:0]  mem_funct3_m;
wire [31:0] load_stall_dbg;
wire [31:0] branch_flush_dbg;

reg [31:0] imem [0:255];

integer i;
integer cycle_count;
integer total_checks;
integer failed_checks;

integer branch_resolve_count;
integer taken_resolve_count;
integer not_taken_resolve_count;
integer correct_prediction_count;
integer mispredict_count;
integer nt_to_t_mispredict_count;
integer t_to_nt_mispredict_count;
integer fetch_redirect_count;
integer jal_execute_redirect_count;

integer watch_pc_enable;
reg [31:0] watch_pc;
integer watch_pc_fetch_count;
integer watch_rd_enable;
reg [4:0] watch_rd;
integer watch_rd_write_count;

reg [1:0] observed_bht_state [0:31];
reg       observed_prediction [0:31];
reg       observed_actual [0:31];
reg       observed_mispredict [0:31];

integer stall_injected;
integer stall_hold_ok;
reg [31:0] held_pc;

localparam [31:0] NOP    = 32'h0000_0013;
localparam [31:0] EBREAK = 32'h0010_0073;

function [31:0] RV32_I;
    input [11:0] imm;
    input [4:0]  rs1;
    input [2:0]  funct3;
    input [4:0]  rd;
    begin
        RV32_I = {imm, rs1, funct3, rd, 7'b0010011};
    end
endfunction

function [31:0] RV32_B;
    input [12:0] imm;
    input [4:0]  rs2;
    input [4:0]  rs1;
    input [2:0]  funct3;
    begin
        RV32_B = {imm[12], imm[10:5], rs2, rs1,
                  funct3, imm[4:1], imm[11], 7'b1100011};
    end
endfunction

function [31:0] RV32_J;
    input [20:0] imm;
    input [4:0]  rd;
    begin
        RV32_J = {imm[20], imm[10:1], imm[11], imm[19:12],
                  rd, 7'b1101111};
    end
endfunction

assign instr   = (pc_f[31:2] < 256) ? imem[pc_f[31:2]] : NOP;
assign rd_data = 32'h0000_0000;

riscv_core dut (
    .clk              (clk),
    .reset_n          (reset_n),
    .irq_timer        (irq_timer),
    .pc_f             (pc_f),
    .instr            (instr),
    .mem_wr_m         (mem_wr_m),
    .mem_rd_m         (mem_rd_m),
    .alu_result_m     (alu_result_m),
    .wr_data_m        (wr_data_m),
    .rd_data          (rd_data),
    .trap_taken       (trap_taken),
    .mcause_dbg       (mcause_dbg),
    .mepc_dbg         (mepc_dbg),
    .mtvec_dbg        (mtvec_dbg),
    .stall_pipe       (stall_pipe),
    .mcycle_dbg       (mcycle_dbg),
    .minstret_dbg     (minstret_dbg),
    .mem_funct3_m     (mem_funct3_m),
    .load_stall_dbg   (load_stall_dbg),
    .branch_flush_dbg (branch_flush_dbg),
    .control_redirect_dbg(),
    .retire_event_dbg(),
    .load_use_stall_event_dbg(),
    .control_redirect_event_dbg(),
    .mispredict_event_dbg(),
    .conditional_branch_event_dbg(),
    .branch_taken_event_dbg(),
    .branch_not_taken_event_dbg(),
    .branch_prediction_event_dbg(),
    .branch_correct_prediction_event_dbg(),
    .pipeline_nonempty_dbg(),
    .retire_valid(), .retire_order(), .retire_pc(), .retire_pc_next(),
    .retire_instr(), .retire_rs1_addr(), .retire_rs1_rdata(),
    .retire_rs2_addr(), .retire_rs2_rdata(), .retire_rd_addr(),
    .retire_rd_wdata(), .retire_rd_we(), .retire_mem_valid(),
    .retire_mem_write(), .retire_mem_addr(), .retire_mem_wdata(),
    .retire_mem_wstrb(), .retire_trap(), .retire_interrupt()
);

always #5 clk = ~clk;

task automatic check_ok;
    input condition;
    input string description;
    begin
        total_checks = total_checks + 1;
        if (condition === 1'b1)
            $display("  [OK]   %s", description);
        else begin
            failed_checks = failed_checks + 1;
            $display("  [FAIL] %s", description);
        end
    end
endtask

task automatic prepare_scenario;
    input string scenario_name;
    integer r;
    begin
        $display("");
        $display("============================================================");
        $display("SCENARIO: %s", scenario_name);
        $display("============================================================");

        reset_n        = 1'b0;
        irq_timer      = 1'b0;
        stall_pipe     = 1'b0;
        watch_pc_enable = 0;
        watch_rd_enable = 0;
        stall_injected  = 0;
        stall_hold_ok   = 1;

        for (r = 0; r < 256; r = r + 1)
            imem[r] = NOP;

        repeat (3) @(posedge clk);

        // The core register file has no reset input. Clear it from the
        // testbench so every scenario starts from the same architectural state.
        for (r = 0; r < 32; r = r + 1)
            dut.datapath.regfile.regs[r] = 32'h0000_0000;
    end
endtask

task automatic release_reset;
    begin
        @(negedge clk);
        reset_n = 1'b1;
    end
endtask

// Observe prediction and recovery at the same Execute edge at which the BHT
// sees its update. Therefore observed_bht_state[] is the state before update.
always @(posedge clk) begin
    if (!reset_n) begin
        cycle_count                  = 0;
        branch_resolve_count         = 0;
        taken_resolve_count          = 0;
        not_taken_resolve_count      = 0;
        correct_prediction_count     = 0;
        mispredict_count             = 0;
        nt_to_t_mispredict_count     = 0;
        t_to_nt_mispredict_count     = 0;
        fetch_redirect_count         = 0;
        jal_execute_redirect_count   = 0;
        watch_pc_fetch_count         = 0;
        watch_rd_write_count         = 0;
    end
    else begin
        cycle_count = cycle_count + 1;

        if (watch_pc_enable && pc_f == watch_pc)
            watch_pc_fetch_count = watch_pc_fetch_count + 1;

        // Count only a prediction that actually wins the PC mux. A younger
        // wrong-path branch may assert predict_redirect_f in the same cycle
        // that an older branch asserts pc_src_e; Execute recovery has priority.
        if (dut.datapath.predict_redirect_f &&
            !dut.datapath.pc_src_e &&
            !trap_taken)
            fetch_redirect_count = fetch_redirect_count + 1;

        if (dut.datapath.is_jal_e && dut.datapath.pc_src_e)
            jal_execute_redirect_count = jal_execute_redirect_count + 1;

        if (watch_rd_enable && dut.controller.reg_wr_w &&
            dut.datapath.instr_w[11:7] == watch_rd)
            watch_rd_write_count = watch_rd_write_count + 1;

        if (dut.datapath.is_branch_e && !stall_pipe) begin
            if (branch_resolve_count < 32) begin
                observed_bht_state[branch_resolve_count] =
                    dut.datapath.g_bp_on.u_bht.bht_mem[dut.datapath.pc_e[9:2]];
                observed_prediction[branch_resolve_count] =
                    dut.datapath.predict_taken_e;
                observed_actual[branch_resolve_count] =
                    dut.datapath.branch_taken_e;
                observed_mispredict[branch_resolve_count] =
                    dut.datapath.mispredict_e;
            end

            $display("[C%0d] BRANCH pc=%08h state=%b pred=%0d actual=%0d miss=%0d",
                     cycle_count,
                     dut.datapath.pc_e,
                     dut.datapath.g_bp_on.u_bht.bht_mem[dut.datapath.pc_e[9:2]],
                     dut.datapath.predict_taken_e,
                     dut.datapath.branch_taken_e,
                     dut.datapath.mispredict_e);

            branch_resolve_count = branch_resolve_count + 1;

            if (dut.datapath.branch_taken_e)
                taken_resolve_count = taken_resolve_count + 1;
            else
                not_taken_resolve_count = not_taken_resolve_count + 1;

            if (dut.datapath.mispredict_e) begin
                mispredict_count = mispredict_count + 1;

                if (!dut.datapath.predict_taken_e &&
                    dut.datapath.branch_taken_e)
                    nt_to_t_mispredict_count = nt_to_t_mispredict_count + 1;

                if (dut.datapath.predict_taken_e &&
                    !dut.datapath.branch_taken_e)
                    t_to_nt_mispredict_count = t_to_nt_mispredict_count + 1;
            end
            else begin
                correct_prediction_count = correct_prediction_count + 1;
            end
        end
    end
end

task automatic test_reset_and_not_taken;
    integer fail_before;
    begin
        fail_before = failed_checks;
        prepare_scenario("BHT reset + correct not-taken prediction");

        // PC=0x04: BEQ is not taken. Initial BHT=01 predicts not-taken,
        // then the counter must move to strongly not-taken (00).
        imem[0] = RV32_I(12'd1, 5'd0, 3'b000, 5'd1);    // addi x1, x0, 1
        imem[1] = RV32_B(13'd8, 5'd0, 5'd1, 3'b000);    // beq  x1, x0, +8 (NT)
        imem[2] = RV32_I(12'h011, 5'd0, 3'b000, 5'd10); // executed
        imem[3] = EBREAK;

        watch_rd_enable = 1;
        watch_rd = 5'd10;

        check_ok(dut.datapath.g_bp_on.u_bht.bht_mem[1] === 2'b01,
                 "BHT entry resets to weakly not-taken (01)");
        check_ok(dut.datapath.predict_taken_e === 1'b0,
                 "Execute prediction register resets to 0");
        check_ok(dut.datapath.is_jal_e === 1'b0,
                 "Execute JAL marker resets to 0");

        release_reset();
        repeat (18) @(posedge clk);
        #1;

        check_ok(branch_resolve_count == 1,
                 "Exactly one conditional branch resolves");
        check_ok(correct_prediction_count == 1 && mispredict_count == 0,
                 "Initial not-taken prediction is correct");
        check_ok(observed_bht_state[0] === 2'b01 &&
                 observed_prediction[0] === 1'b0 &&
                 observed_actual[0] === 1'b0,
                 "Resolution observes state=01, prediction=NT, actual=NT");
        check_ok(dut.datapath.g_bp_on.u_bht.bht_mem[1] === 2'b00,
                 "Not-taken update changes BHT 01 -> 00");
        check_ok(branch_flush_dbg == 32'd0,
                 "Correct not-taken prediction causes no recovery flush");
        check_ok(dut.datapath.regfile.regs[10] == 32'h0000_0011 &&
                 watch_rd_write_count == 1,
                 "Fall-through instruction commits exactly once");

        if (failed_checks == fail_before)
            $display("[SCENARIO PASS] BHT reset + correct not-taken");
        else
            $display("[SCENARIO FAIL] BHT reset + correct not-taken");
    end
endtask

task automatic test_loop_learning_and_recovery;
    integer fail_before;
    begin
        fail_before = failed_checks;
        prepare_scenario("2-bit BHT learning + both misprediction directions");

        // PC=0x0c outcomes: T, T, T, NT.
        // State before each update: 01, 10, 11, 11. Final state: 10.
        imem[0] = RV32_I(12'd0, 5'd0, 3'b000, 5'd1);    // addi x1, x0, 0
        imem[1] = RV32_I(12'd4, 5'd0, 3'b000, 5'd2);    // addi x2, x0, 4
        imem[2] = RV32_I(12'd1, 5'd1, 3'b000, 5'd1);    // addi x1, x1, 1
        imem[3] = RV32_B(-13'sd4, 5'd2, 5'd1, 3'b100);  // blt x1, x2, -4
        imem[4] = RV32_I(12'h055, 5'd0, 3'b000, 5'd10); // exit marker
        imem[5] = EBREAK;

        watch_rd_enable = 1;
        watch_rd = 5'd10;

        release_reset();
        repeat (30) @(posedge clk);
        #1;

        check_ok(branch_resolve_count == 4 &&
                 taken_resolve_count == 3 &&
                 not_taken_resolve_count == 1,
                 "Dynamic branch outcomes are T,T,T,NT");
        check_ok(correct_prediction_count == 2 && mispredict_count == 2,
                 "Two predictions correct and two predictions wrong");
        check_ok(nt_to_t_mispredict_count == 1 &&
                 t_to_nt_mispredict_count == 1,
                 "Both NT->T and T->NT recovery paths occur once");

        check_ok(observed_bht_state[0] === 2'b01 &&
                 observed_bht_state[1] === 2'b10 &&
                 observed_bht_state[2] === 2'b11 &&
                 observed_bht_state[3] === 2'b11,
                 "BHT state sequence before updates is 01,10,11,11");
        check_ok(observed_prediction[0] === 1'b0 &&
                 observed_prediction[1] === 1'b1 &&
                 observed_prediction[2] === 1'b1 &&
                 observed_prediction[3] === 1'b1,
                 "Prediction sequence is NT,T,T,T");
        check_ok(dut.datapath.g_bp_on.u_bht.bht_mem[3] === 2'b10,
                 "Final BHT state is weakly taken (10)");
        check_ok(fetch_redirect_count == 3,
                 "Taken prediction redirects Fetch on the last three visits");
        check_ok(branch_flush_dbg == 32'd2,
                 "Only the two mispredictions cause Execute recovery flushes");
        check_ok(dut.datapath.regfile.regs[1] == 32'd4 &&
                 dut.datapath.regfile.regs[10] == 32'h0000_0055 &&
                 watch_rd_write_count == 1,
                 "Loop result is correct and exit path commits once");

        if (failed_checks == fail_before)
            $display("[SCENARIO PASS] 2-bit learning + recovery");
        else
            $display("[SCENARIO FAIL] 2-bit learning + recovery");
    end
endtask

task automatic test_all_branch_types;
    integer fail_before;
    begin
        fail_before = failed_checks;
        prepare_scenario("All six RV32I conditional branch types");

        // Every branch is taken from initial BHT state 01. Each must recover
        // from NT->T, skip its wrong-path ADDI, and update its own BHT entry.
        imem[0]  = RV32_I(12'd1,   5'd0, 3'b000, 5'd1);  // x1 = 1
        imem[1]  = RV32_I(12'd2,   5'd0, 3'b000, 5'd2);  // x2 = 2
        imem[2]  = RV32_I(12'hfff, 5'd0, 3'b000, 5'd3);  // x3 = -1
        imem[3]  = RV32_I(12'd1,   5'd0, 3'b000, 5'd4);  // x4 = 1
        imem[4]  = RV32_B(13'd8, 5'd1, 5'd1, 3'b000);    // beq  x1,x1,+8
        imem[5]  = RV32_I(12'h061, 5'd0, 3'b000, 5'd10); // wrong path
        imem[6]  = RV32_B(13'd8, 5'd2, 5'd1, 3'b001);    // bne  x1,x2,+8
        imem[7]  = RV32_I(12'h062, 5'd0, 3'b000, 5'd11); // wrong path
        imem[8]  = RV32_B(13'd8, 5'd4, 5'd3, 3'b100);    // blt  x3,x4,+8
        imem[9]  = RV32_I(12'h063, 5'd0, 3'b000, 5'd12); // wrong path
        imem[10] = RV32_B(13'd8, 5'd3, 5'd4, 3'b101);    // bge  x4,x3,+8
        imem[11] = RV32_I(12'h064, 5'd0, 3'b000, 5'd13); // wrong path
        imem[12] = RV32_B(13'd8, 5'd3, 5'd4, 3'b110);    // bltu x4,x3,+8
        imem[13] = RV32_I(12'h065, 5'd0, 3'b000, 5'd14); // wrong path
        imem[14] = RV32_B(13'd8, 5'd4, 5'd3, 3'b111);    // bgeu x3,x4,+8
        imem[15] = RV32_I(12'h066, 5'd0, 3'b000, 5'd15); // wrong path
        imem[16] = RV32_I(12'h05a, 5'd0, 3'b000, 5'd20); // final marker
        imem[17] = EBREAK;

        watch_rd_enable = 1;
        watch_rd = 5'd20;

        release_reset();
        repeat (60) @(posedge clk);
        #1;

        check_ok(branch_resolve_count == 6 && taken_resolve_count == 6,
                 "BEQ/BNE/BLT/BGE/BLTU/BGEU all resolve taken");
        check_ok(mispredict_count == 6 && nt_to_t_mispredict_count == 6,
                 "All six cold branches exercise NT->T recovery");
        check_ok(correct_prediction_count == 0 && fetch_redirect_count == 0,
                 "No cold branch falsely reports a BHT-taken prediction");
        check_ok(branch_flush_dbg == 32'd6,
                 "Exactly six recovery flushes occur");

        check_ok(dut.datapath.g_bp_on.u_bht.bht_mem[4]  === 2'b10 &&
                 dut.datapath.g_bp_on.u_bht.bht_mem[6]  === 2'b10 &&
                 dut.datapath.g_bp_on.u_bht.bht_mem[8]  === 2'b10 &&
                 dut.datapath.g_bp_on.u_bht.bht_mem[10] === 2'b10 &&
                 dut.datapath.g_bp_on.u_bht.bht_mem[12] === 2'b10 &&
                 dut.datapath.g_bp_on.u_bht.bht_mem[14] === 2'b10,
                 "Each branch updates its own BHT entry 01 -> 10");

        check_ok(dut.datapath.regfile.regs[10] == 32'd0 &&
                 dut.datapath.regfile.regs[11] == 32'd0 &&
                 dut.datapath.regfile.regs[12] == 32'd0 &&
                 dut.datapath.regfile.regs[13] == 32'd0 &&
                 dut.datapath.regfile.regs[14] == 32'd0 &&
                 dut.datapath.regfile.regs[15] == 32'd0,
                 "All six wrong-path instructions are squashed");
        check_ok(dut.datapath.regfile.regs[20] == 32'h0000_005a &&
                 watch_rd_write_count == 1,
                 "Final correct-path marker commits exactly once");

        if (failed_checks == fail_before)
            $display("[SCENARIO PASS] All six B-type instructions");
        else
            $display("[SCENARIO FAIL] All six B-type instructions");
    end
endtask

task automatic test_jal_early_redirect;
    integer fail_before;
    begin
        fail_before = failed_checks;
        prepare_scenario("JAL early Fetch redirect without Execute re-flush");

        // JAL at PC=0x04 targets PC=0x0c and writes return PC=0x08 to x5.
        imem[0] = RV32_I(12'd1, 5'd0, 3'b000, 5'd1);    // setup
        imem[1] = RV32_J(21'd8, 5'd5);                  // jal x5, +8
        imem[2] = RV32_I(12'h066, 5'd0, 3'b000, 5'd22); // wrong path
        imem[3] = RV32_I(12'h023, 5'd0, 3'b000, 5'd23); // target
        imem[4] = EBREAK;

        watch_pc_enable = 1;
        watch_pc = 32'h0000_000c;
        watch_rd_enable = 1;
        watch_rd = 5'd23;

        release_reset();
        repeat (22) @(posedge clk);
        #1;

        check_ok(branch_resolve_count == 0,
                 "JAL does not update the conditional-branch BHT");
        check_ok(dut.datapath.g_bp_on.u_bht.bht_mem[1] === 2'b01,
                 "BHT entry at the JAL PC remains unchanged");
        check_ok(fetch_redirect_count == 1,
                 "JAL redirects Fetch exactly once");
        check_ok(watch_pc_fetch_count == 1,
                 "JAL target PC is fetched exactly once");
        check_ok(jal_execute_redirect_count == 0,
                 "JAL is not redirected/flushed again in Execute");
        check_ok(branch_flush_dbg == 32'd0,
                 "Correct early JAL redirect adds no Execute flush");
        check_ok(dut.datapath.regfile.regs[5] == 32'h0000_0008,
                 "JAL writes the correct return address to x5");
        check_ok(dut.datapath.regfile.regs[22] == 32'd0 &&
                 dut.datapath.regfile.regs[23] == 32'h0000_0023 &&
                 watch_rd_write_count == 1,
                 "JAL wrong path is squashed and target commits once");

        if (failed_checks == fail_before)
            $display("[SCENARIO PASS] JAL early redirect");
        else
            $display("[SCENARIO FAIL] JAL early redirect");
    end
endtask

task automatic test_prediction_during_stall;
    integer fail_before;
    begin
        fail_before = failed_checks;
        prepare_scenario("BHT-taken prediction held safely during stall_pipe");

        // PC=0x0c outcomes: T,T,NT. Stall Fetch for two cycles when the
        // second visit has become predicted-taken.
        imem[0] = RV32_I(12'd0, 5'd0, 3'b000, 5'd1);    // addi x1, x0, 0
        imem[1] = RV32_I(12'd3, 5'd0, 3'b000, 5'd2);    // addi x2, x0, 3
        imem[2] = RV32_I(12'd1, 5'd1, 3'b000, 5'd1);    // addi x1, x1, 1
        imem[3] = RV32_B(-13'sd4, 5'd2, 5'd1, 3'b100);  // blt x1, x2, -4
        imem[4] = RV32_I(12'h033, 5'd0, 3'b000, 5'd10); // exit marker
        imem[5] = EBREAK;

        watch_rd_enable = 1;
        watch_rd = 5'd10;

        release_reset();

        fork
            begin : inject_cache_style_stall
                wait (reset_n && pc_f == 32'h0000_000c &&
                      dut.datapath.bht_pred_f === 1'b1);
                @(negedge clk);
                held_pc = pc_f;
                stall_pipe = 1'b1;
                stall_injected = 1;

                repeat (2) begin
                    @(posedge clk);
                    #1;
                    if (pc_f !== held_pc ||
                        dut.datapath.predict_redirect_f !== 1'b0)
                        stall_hold_ok = 0;
                end

                @(negedge clk);
                stall_pipe = 1'b0;
            end

            begin : scenario_runtime
                repeat (50) @(posedge clk);
            end
        join
        #1;

        check_ok(stall_injected == 1 && stall_hold_ok == 1,
                 "PC holds and Fetch redirect is suppressed while stalled");
        check_ok(branch_resolve_count == 3 &&
                 taken_resolve_count == 2 &&
                 not_taken_resolve_count == 1,
                 "Stall does not duplicate or lose a branch update");
        check_ok(correct_prediction_count == 1 && mispredict_count == 2,
                 "Prediction classification remains correct across the stall");
        check_ok(observed_bht_state[0] === 2'b01 &&
                 observed_bht_state[1] === 2'b10 &&
                 observed_bht_state[2] === 2'b11,
                 "BHT updates once per branch: 01,10,11 before updates");
        check_ok(fetch_redirect_count == 2,
                 "Each predicted-taken visit redirects once, not once per stall cycle");
        check_ok(dut.datapath.g_bp_on.u_bht.bht_mem[3] === 2'b10,
                 "Final state after T,T,NT is 10");
        check_ok(branch_flush_dbg == 32'd2,
                 "Only the first-taken and final-not-taken misses flush");
        check_ok(dut.datapath.regfile.regs[1] == 32'd3 &&
                 dut.datapath.regfile.regs[10] == 32'h0000_0033 &&
                 watch_rd_write_count == 1,
                 "Architectural result stays correct across stall_pipe");

        if (failed_checks == fail_before)
            $display("[SCENARIO PASS] Prediction during stall_pipe");
        else
            $display("[SCENARIO FAIL] Prediction during stall_pipe");
    end
endtask

initial begin
    clk           = 1'b0;
    reset_n       = 1'b0;
    irq_timer     = 1'b0;
    stall_pipe    = 1'b0;
    total_checks  = 0;
    failed_checks = 0;

    $dumpfile("branch_predictor_core.vcd");
    $dumpvars(0, tb_branch_predictor_core);

    test_reset_and_not_taken();
    test_loop_learning_and_recovery();
    test_all_branch_types();
    test_jal_early_redirect();
    test_prediction_during_stall();

    $display("");
    $display("============================================================");
    $display("COMPLETE BRANCH-PREDICTION TEST SUMMARY");
    $display("Checks: %0d, failures: %0d", total_checks, failed_checks);
    $display("============================================================");

    if (failed_checks == 0) begin
        $display("[PASS] All branch-prediction scenarios passed");
        $finish;
    end
    else begin
        $fatal(1, "[FAIL] %0d branch-prediction checks failed", failed_checks);
    end
end

initial begin
    #10000;
    $fatal(1, "[FAIL] Global timeout in complete branch-prediction test");
end

endmodule
