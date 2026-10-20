`timescale 1ns/1ps

// Generic flat-memory harness for ACT4/RISCOF-style signature programs.
// This is a DUT adapter, not an assertion of official-suite compliance.
module tb_architecture_signature;

localparam [31:0] NOP  = 32'h0000_0013;
localparam [31:0] HALT = 32'h0000_006f;
// External core-verification RAM only. The SoC/FPGA RAM size is unchanged.
// Current ACT4 load/halfword tests are larger than 64 KiB.
localparam integer MEM_WORDS = 262144; // 1 MiB address window at reset address 0
localparam [31:0] MEM_BYTES = MEM_WORDS * 4;

reg clk;
reg reset_n;
reg [31:0] mem [0:MEM_WORDS-1];
reg [31:0] sig_begin;
reg [31:0] sig_end;
reg [31:0] halt_pc;
reg [31:0] tohost_addr;
reg use_halt_pc;
integer max_cycles;
integer cycles;
integer expected_order;
integer i;
integer signature_fd;
string hex_path;
string signature_path;

wire [31:0] pc;
wire [31:0] instr =
    (pc < MEM_BYTES) ? mem[pc[18:2]] : NOP;
wire mem_wr;
wire mem_rd;
wire [31:0] mem_addr;
wire [31:0] mem_wdata_raw;
wire [2:0] mem_funct3;
wire [31:0] mem_rdata =
    (mem_addr < MEM_BYTES) ? mem[mem_addr[18:2]] : 32'h0000_0000;
wire [31:0] store_lane_data =
    (mem_funct3 == 3'b000) ?
        ({24'h0, mem_wdata_raw[7:0]} << (8 * mem_addr[1:0])) :
    (mem_funct3 == 3'b001) ?
        ({16'h0, mem_wdata_raw[15:0]} << (8 * mem_addr[1:0])) :
        mem_wdata_raw;
wire [3:0] store_strb =
    (mem_funct3 == 3'b000) ? (4'b0001 << mem_addr[1:0]) :
    (mem_funct3 == 3'b001) ? (4'b0011 << mem_addr[1:0]) :
                             4'b1111;
wire retire_valid;
wire [63:0] retire_order;
wire [31:0] retire_pc;
wire [31:0] retire_instr;

riscv_core #(
    .BRANCH_PREDICT_ENABLE(1),
    .BHT_ENTRIES(256)
) dut (
    .clk(clk), .reset_n(reset_n), .irq_timer(1'b0),
    .pc_f(pc), .instr(instr),
    .mem_wr_m(mem_wr), .mem_rd_m(mem_rd),
    .alu_result_m(mem_addr), .wr_data_m(mem_wdata_raw),
    .rd_data(mem_rdata), .mem_funct3_m(mem_funct3),
    .stall_pipe(1'b0),
    .trap_taken(), .mcause_dbg(), .mepc_dbg(), .mtvec_dbg(),
    .mcycle_dbg(), .minstret_dbg(), .load_stall_dbg(),
    .branch_flush_dbg(), .control_redirect_dbg(), .retire_event_dbg(),
    .load_use_stall_event_dbg(), .control_redirect_event_dbg(),
    .mispredict_event_dbg(), .conditional_branch_event_dbg(),
    .branch_taken_event_dbg(), .branch_not_taken_event_dbg(),
    .branch_prediction_event_dbg(), .branch_correct_prediction_event_dbg(),
    .pipeline_nonempty_dbg(),
    .retire_valid(retire_valid), .retire_order(retire_order),
    .retire_pc(retire_pc), .retire_pc_next(), .retire_instr(retire_instr),
    .retire_rs1_addr(), .retire_rs1_rdata(),
    .retire_rs2_addr(), .retire_rs2_rdata(),
    .retire_rd_addr(), .retire_rd_wdata(), .retire_rd_we(),
    .retire_mem_valid(), .retire_mem_write(), .retire_mem_addr(),
    .retire_mem_wdata(), .retire_mem_wstrb(),
    .retire_trap(), .retire_interrupt()
);

always #5 clk = ~clk;

task automatic dump_signature;
    integer word_index;
begin
    if(sig_begin[1:0] != 0 || sig_end[1:0] != 0 ||
       sig_end < sig_begin || sig_end > MEM_WORDS * 4)
        $fatal(1, "invalid signature range [%08x,%08x)", sig_begin, sig_end);
    signature_fd = $fopen(signature_path, "w");
    if(signature_fd == 0)
        $fatal(1, "cannot open signature output %s", signature_path);
    for(word_index = sig_begin >> 2;
        word_index < (sig_end >> 2);
        word_index = word_index + 1)
        $fdisplay(signature_fd, "%08x", mem[word_index]);
    $fclose(signature_fd);
end
endtask

task automatic finish_pass;
    input [255:0] reason;
begin
    dump_signature();
    $display("[PASS] Signature harness %s retirements=%0d cycles=%0d",
             reason, expected_order, cycles);
    $finish;
end
endtask

always @(posedge clk) begin
    if(reset_n) begin
        cycles <= cycles + 1;
        if(cycles >= max_cycles)
            $fatal(1, "signature test timeout after %0d cycles", max_cycles);

        if(mem_wr) begin
            if(mem_addr >= MEM_BYTES)
                $fatal(1, "store outside 1 MiB architecture-test window: %08x", mem_addr);
            if(store_strb[0]) mem[mem_addr[18:2]][7:0]   <= store_lane_data[7:0];
            if(store_strb[1]) mem[mem_addr[18:2]][15:8]  <= store_lane_data[15:8];
            if(store_strb[2]) mem[mem_addr[18:2]][23:16] <= store_lane_data[23:16];
            if(store_strb[3]) mem[mem_addr[18:2]][31:24] <= store_lane_data[31:24];
            if(mem_addr == tohost_addr) begin
                if(store_lane_data == 32'd1)
                    finish_pass("TOHOST");
                else
                    $fatal(1, "DUT test reported failure code %08x", store_lane_data);
            end
        end

        if(retire_valid) begin
            if(retire_order !== expected_order)
                $fatal(1, "retire_order expected %0d got %0d",
                       expected_order, retire_order);
            expected_order <= expected_order + 1;
            if((use_halt_pc && retire_pc == halt_pc) ||
               (!use_halt_pc && retire_instr == HALT))
                finish_pass("HALT");
        end
    end
end

initial begin
    clk = 0;
    reset_n = 0;
    cycles = 0;
    expected_order = 0;
    max_cycles = 2000000;
    halt_pc = 32'hffff_ffff;
    tohost_addr = 32'h0008_1ff0;
    use_halt_pc = 0;
    for(i = 0; i < MEM_WORDS; i = i + 1)
        mem[i] = NOP;

    if(!$value$plusargs("HEX=%s", hex_path))
        $fatal(1, "+HEX=<word-hex> is required");
    if(!$value$plusargs("SIGNATURE=%s", signature_path))
        $fatal(1, "+SIGNATURE=<output-file> is required");
    if(!$value$plusargs("SIG_BEGIN=%h", sig_begin))
        $fatal(1, "+SIG_BEGIN=<hex-address> is required");
    if(!$value$plusargs("SIG_END=%h", sig_end))
        $fatal(1, "+SIG_END=<hex-address> is required");
    if($value$plusargs("HALT_PC=%h", halt_pc))
        use_halt_pc = 1;
    void'($value$plusargs("TOHOST_ADDR=%h", tohost_addr));
    void'($value$plusargs("MAX_CYCLES=%d", max_cycles));

    $readmemh(hex_path, mem);
    repeat(5) @(posedge clk);
    reset_n <= 1;
end

endmodule
