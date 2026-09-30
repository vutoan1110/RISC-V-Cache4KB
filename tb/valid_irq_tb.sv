`timescale 1ns/1ps

module tb_valid_irq;

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
wire [2:0]  mem_funct3_m;
wire        trap_taken;
wire [31:0] mcause_dbg;
wire [31:0] mepc_dbg;
wire [31:0] mtvec_dbg;
wire [31:0] mcycle_dbg;
wire [31:0] minstret_dbg;
wire [31:0] load_stall_dbg;
wire [31:0] branch_flush_dbg;

reg [31:0] imem [0:63];
integer i;
integer errors;
integer trap_count;
integer x11_write_count;
integer timeout_count;
reg [31:0] expected_mepc;
reg [31:0] frozen_pc;
reg [31:0] prev_minstret;
reg        expected_retire;
reg        retire_check_enabled;

assign instr = imem[pc_f[7:2]];

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
    .rd_data          (32'h0000_0000),
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

// Architectural-event monitors. They also verify that invalid pipeline slots
// cannot create register-file or memory side effects.
always @(posedge clk) begin
    if (reset_n) begin
        if (trap_taken)
            trap_count = trap_count + 1;

        if (dut.reg_wr_w && dut.datapath.valid_w && !stall_pipe &&
            (dut.datapath.instr_w[11:7] == 5'd11))
            x11_write_count = x11_write_count + 1;

        if (!dut.datapath.valid_w && dut.reg_wr_w) begin
            $display("[ERROR] reg_wr_w asserted for an invalid WB slot at t=%0t", $time);
            errors = errors + 1;
        end

        if (!dut.datapath.valid_m && (mem_wr_m || mem_rd_m)) begin
            $display("[ERROR] memory request asserted for an invalid MEM slot at t=%0t", $time);
            errors = errors + 1;
        end
    end
end

// Check that minstret advances exactly once for each valid, advancing WB slot.
// Sampling at negedge avoids races with the posedge nonblocking assignments.
always @(negedge clk) begin
    #1;
    if (!reset_n) begin
        prev_minstret       = minstret_dbg;
        expected_retire     = 1'b0;
        retire_check_enabled = 1'b0;
    end
    else begin
        if (retire_check_enabled &&
            (minstret_dbg !== (prev_minstret + expected_retire))) begin
            $display("[ERROR] minstret mismatch at t=%0t: prev=%0d expected_inc=%0d got=%0d",
                     $time, prev_minstret, expected_retire, minstret_dbg);
            errors = errors + 1;
        end

        prev_minstret        = minstret_dbg;
        expected_retire      = dut.datapath.valid_w && !stall_pipe;
        retire_check_enabled = 1'b1;
    end
end

initial begin
    clk                  = 1'b0;
    reset_n              = 1'b0;
    irq_timer            = 1'b0;
    stall_pipe           = 1'b0;
    errors               = 0;
    trap_count           = 0;
    x11_write_count      = 0;
    timeout_count        = 0;
    expected_mepc        = 32'h0000_0000;
    frozen_pc            = 32'h0000_0000;
    prev_minstret        = 32'h0000_0000;
    expected_retire      = 1'b0;
    retire_check_enabled = 1'b0;

    for (i = 0; i < 64; i = i + 1)
        imem[i] = 32'h0000_0013; // canonical NOP

    // Main program
    // 0x00: addi  x4,  x0, 8
    // 0x04: csrrw x0,  mstatus, x4    ; MIE=1
    // 0x08: addi  x5,  x0, 128
    // 0x0c: csrrw x0,  mie, x5        ; MTIE=1
    // 0x10: addi  x10, x0, 0x55      ; older than interrupted slot
    // 0x14: addi  x11, x0, 0x66      ; must be resumed after mret
    // 0x18: jal   x0,  0              ; stop loop
    imem[ 0] = 32'h0080_0213;
    imem[ 1] = 32'h3002_1073;
    imem[ 2] = 32'h0800_0293;
    imem[ 3] = 32'h3042_9073;
    imem[ 4] = 32'h0550_0513;
    imem[ 5] = 32'h0660_0593;
    imem[ 6] = 32'h0000_006f;

    // Handler at mtvec=0x80
    // 0x80: addi x20, x0, 1
    // 0x84: mret
    imem[32] = 32'h0010_0a13;
    imem[33] = 32'h3020_0073;

    $dumpfile("valid_irq_tb.vcd");
    $dumpvars(0, tb_valid_irq);

    repeat (3) @(posedge clk);
    @(negedge clk);
    #1 reset_n = 1'b1;

    // Sample at negedge, after the preceding posedge NBAs have settled. This
    // avoids observing the old pc_d and accidentally advancing to PC=0x18.
    while (!((dut.datapath.csr_mstatus[3] === 1'b1) &&
             (dut.datapath.csr_mie[7]     === 1'b1) &&
             (dut.datapath.valid_d        === 1'b1) &&
             (dut.datapath.pc_d           == 32'h0000_0014))) begin
        @(negedge clk);
        timeout_count = timeout_count + 1;
        if (timeout_count > 80)
            $fatal(1, "Timeout waiting for enabled interrupt point");
    end

    // Freeze the whole pipeline as a cache miss would do, then pulse the IRQ.
    // The request must become pending but must not update CSR/PC while stalled.
    stall_pipe    = 1'b1;
    expected_mepc = dut.datapath.pc_d;
    frozen_pc     = pc_f;

    @(negedge clk);
    irq_timer = 1'b1;
    @(negedge clk);
    irq_timer = 1'b0;

    repeat (2) begin
        @(posedge clk);
        #1;
        if (trap_taken !== 1'b0) begin
            $display("[ERROR] interrupt accepted while stall_pipe=1");
            errors = errors + 1;
        end
        if (pc_f !== frozen_pc) begin
            $display("[ERROR] PC changed during global stall: expected=%08h got=%08h",
                     frozen_pc, pc_f);
            errors = errors + 1;
        end
        if (dut.datapath.irq_pending !== 1'b1) begin
            $display("[ERROR] one-cycle IRQ pulse was not retained as pending");
            errors = errors + 1;
        end
    end

    // Releasing the cache stall must accept the pending IRQ exactly once.
    @(negedge clk);
    stall_pipe = 1'b0;
    #1;
    if (trap_taken !== 1'b1) begin
        $display("[ERROR] pending interrupt was not accepted after stall release");
        errors = errors + 1;
    end

    @(posedge clk);
    #1;
    if (pc_f !== mtvec_dbg) begin
        $display("[ERROR] PC did not redirect to mtvec: pc=%08h mtvec=%08h", pc_f, mtvec_dbg);
        errors = errors + 1;
    end
    if (mepc_dbg !== expected_mepc) begin
        $display("[ERROR] mepc mismatch: expected Decode PC=%08h got=%08h",
                 expected_mepc, mepc_dbg);
        errors = errors + 1;
    end
    if (mcause_dbg !== 32'h8000_0007) begin
        $display("[ERROR] mcause mismatch: got=%08h", mcause_dbg);
        errors = errors + 1;
    end
    if ((dut.datapath.valid_d !== 1'b0) || (dut.datapath.valid_e !== 1'b0)) begin
        $display("[ERROR] younger D/E slots were not invalidated on interrupt acceptance");
        errors = errors + 1;
    end
    // The core register file has no reset input, so an unwritten x11 may be
    // X in simulation. Check the architectural write event instead of assuming
    // an initial register-array value.
    if (x11_write_count != 0) begin
        $display("[ERROR] interrupted instruction executed before handler return");
        errors = errors + 1;
    end

    // Wait for handler execution, mret, and resumed instruction at 0x14.
    timeout_count = 0;
    while (dut.datapath.regfile.regs[11] !== 32'h0000_0066) begin
        @(posedge clk);
        #1;
        timeout_count = timeout_count + 1;
        if (timeout_count > 80)
            $fatal(1, "Timeout waiting for resumed instruction");
    end

    if (dut.datapath.regfile.regs[20] !== 32'h0000_0001) begin
        $display("[ERROR] interrupt handler did not execute");
        errors = errors + 1;
    end
    if (x11_write_count != 1) begin
        $display("[ERROR] resumed instruction write count expected=1 got=%0d", x11_write_count);
        errors = errors + 1;
    end
    if (trap_count != 1) begin
        $display("[ERROR] trap pulse count expected=1 got=%0d", trap_count);
        errors = errors + 1;
    end
    if (mepc_dbg !== 32'h0000_0014) begin
        $display("[ERROR] final mepc expected=0x14 got=%08h", mepc_dbg);
        errors = errors + 1;
    end

    $display("----- VALID IRQ SUMMARY -----");
    $display("mepc              = 0x%08h", mepc_dbg);
    $display("mcause            = 0x%08h", mcause_dbg);
    $display("trap_count        = %0d", trap_count);
    $display("x11_write_count   = %0d", x11_write_count);
    $display("minstret          = %0d", minstret_dbg);
    $display("x20(handler flag) = 0x%08h", dut.datapath.regfile.regs[20]);
    $display("x11(resumed)      = 0x%08h", dut.datapath.regfile.regs[11]);

    if (errors != 0)
        $fatal(1, "valid IRQ test failed with %0d error(s)", errors);

    $display("[PASS] Valid-bit and pending-interrupt test");
    $finish;
end

endmodule
