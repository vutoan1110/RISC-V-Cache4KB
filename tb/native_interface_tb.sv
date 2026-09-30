`timescale 1ns/1ps

module tb_native_interface;

reg clk;
reg reset_n;
reg irq_timer;

wire        if_req_valid;
wire [31:0] if_req_addr;
wire        if_req_ready;
reg         if_rsp_valid;
reg  [31:0] if_rsp_data;
wire        if_rsp_error = 1'b0;

wire        d_req_valid;
wire        d_req_write;
wire [31:0] d_req_addr;
wire [31:0] d_req_wdata;
wire [3:0]  d_req_wstrb;
wire        d_req_ready;
reg         d_rsp_valid;
reg  [31:0] d_rsp_rdata;
wire        d_rsp_error = 1'b0;

wire trap_taken;
wire [31:0] mcause_dbg;
wire [31:0] mepc_dbg;
wire [31:0] mtvec_dbg;
wire [31:0] mcycle_dbg;
wire [31:0] minstret_dbg;
wire [31:0] load_stall_dbg;
wire [31:0] branch_flush_dbg;
wire [31:0] pc_f_dbg;
wire if_wait_dbg;
wire d_wait_dbg;
wire if_error_dbg;
wire d_error_dbg;

reg [31:0] imem [0:63];
reg [31:0] dmem [0:63];

integer cycle_count;
integer errors;
integer timeout_count;
integer if_accept_count;
integer if_response_count;
integer d_accept_count;
integer d_response_count;
integer store_accept_count;
integer load_accept_count;
integer i;

reg        if_mem_pending;
reg [31:0] if_addr_q;
reg [2:0]  if_delay_q;
reg        d_mem_pending;
reg        d_write_q;
reg [31:0] d_addr_q;
reg [31:0] d_wdata_q;
reg [3:0]  d_wstrb_q;
reg [2:0]  d_delay_q;

reg        if_hold_active;
reg [31:0] if_hold_addr;
reg        d_hold_active;
reg        d_hold_write;
reg [31:0] d_hold_addr;
reg [31:0] d_hold_wdata;
reg [3:0]  d_hold_wstrb;

assign if_req_ready = !if_mem_pending && (cycle_count[1:0] != 2'b01);
assign d_req_ready  = !d_mem_pending  && (cycle_count[1:0] != 2'b10);

riscv_core_native dut (
    .clk              (clk),
    .reset_n          (reset_n),
    .irq_timer        (irq_timer),
    .if_req_valid     (if_req_valid),
    .if_req_addr      (if_req_addr),
    .if_req_ready     (if_req_ready),
    .if_rsp_valid     (if_rsp_valid),
    .if_rsp_data      (if_rsp_data),
    .if_rsp_error     (if_rsp_error),
    .d_req_valid      (d_req_valid),
    .d_req_write      (d_req_write),
    .d_req_addr       (d_req_addr),
    .d_req_wdata      (d_req_wdata),
    .d_req_wstrb      (d_req_wstrb),
    .d_req_ready      (d_req_ready),
    .d_rsp_valid      (d_rsp_valid),
    .d_rsp_rdata      (d_rsp_rdata),
    .d_rsp_error      (d_rsp_error),
    .trap_taken       (trap_taken),
    .mcause_dbg       (mcause_dbg),
    .mepc_dbg         (mepc_dbg),
    .mtvec_dbg        (mtvec_dbg),
    .mcycle_dbg       (mcycle_dbg),
    .minstret_dbg     (minstret_dbg),
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
    .retire_mem_wstrb(), .retire_trap(), .retire_interrupt(),
    .pc_f_dbg         (pc_f_dbg),
    .if_wait_dbg      (if_wait_dbg),
    .d_wait_dbg       (d_wait_dbg),
    .if_error_dbg     (if_error_dbg),
    .d_error_dbg      (d_error_dbg)
);

always #5 clk = ~clk;

function automatic [31:0] apply_wstrb;
    input [31:0] old_word;
    input [31:0] new_word;
    input [3:0]  strobe;
    begin
        apply_wstrb = old_word;
        if(strobe[0]) apply_wstrb[7:0]   = new_word[7:0];
        if(strobe[1]) apply_wstrb[15:8]  = new_word[15:8];
        if(strobe[2]) apply_wstrb[23:16] = new_word[23:16];
        if(strobe[3]) apply_wstrb[31:24] = new_word[31:24];
    end
endfunction

// Delayed instruction responder. The accepted address is latched, then the
// live request bus is deliberately free to change before the response.
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        if_mem_pending  <= 1'b0;
        if_addr_q       <= 32'h0000_0000;
        if_delay_q      <= 3'd0;
        if_rsp_valid    <= 1'b0;
        if_rsp_data     <= 32'h0000_0013;
        if_accept_count <= 0;
        if_response_count <= 0;
    end
    else begin
        if_rsp_valid <= 1'b0;

        if(if_req_valid && if_req_ready) begin
            if_mem_pending  <= 1'b1;
            if_addr_q       <= if_req_addr;
            if_delay_q      <= if_req_addr[3] ? 3'd2 : 3'd1;
            if_accept_count <= if_accept_count + 1;
        end

        if(if_mem_pending) begin
            if(if_delay_q == 0) begin
                if_rsp_valid      <= 1'b1;
                if_rsp_data       <= imem[if_addr_q[7:2]];
                if_mem_pending    <= 1'b0;
                if_response_count <= if_response_count + 1;
            end
            else begin
                if_delay_q <= if_delay_q - 1'b1;
            end
        end
    end
end

// Delayed data responder. Every accepted store is committed exactly once at
// response time, making duplicate requests visible in the counters below.
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        d_mem_pending    <= 1'b0;
        d_write_q        <= 1'b0;
        d_addr_q         <= 32'h0000_0000;
        d_wdata_q        <= 32'h0000_0000;
        d_wstrb_q        <= 4'b0000;
        d_delay_q        <= 3'd0;
        d_rsp_valid      <= 1'b0;
        d_rsp_rdata      <= 32'h0000_0000;
        d_accept_count   <= 0;
        d_response_count <= 0;
        store_accept_count <= 0;
        load_accept_count  <= 0;
    end
    else begin
        d_rsp_valid <= 1'b0;

        if(d_req_valid && d_req_ready) begin
            d_mem_pending  <= 1'b1;
            d_write_q      <= d_req_write;
            d_addr_q       <= d_req_addr;
            d_wdata_q      <= d_req_wdata;
            d_wstrb_q      <= d_req_wstrb;
            d_delay_q      <= 3'd2;
            d_accept_count <= d_accept_count + 1;

            if(d_req_write)
                store_accept_count <= store_accept_count + 1;
            else
                load_accept_count <= load_accept_count + 1;

            if(d_req_write && (d_req_addr == 32'h0000_1000) &&
               (store_accept_count == 0) &&
               ((d_req_wdata !== 32'h0000_0005) || (d_req_wstrb !== 4'b1111))) begin
                $display("[ERROR] SW byte lanes: data=%08h strb=%b", d_req_wdata, d_req_wstrb);
                errors = errors + 1;
            end

            if(d_req_write && (d_req_addr == 32'h0000_1001) &&
               ((d_req_wdata !== 32'h0000_0600) || (d_req_wstrb !== 4'b0010))) begin
                $display("[ERROR] SB byte lanes: data=%08h strb=%b", d_req_wdata, d_req_wstrb);
                errors = errors + 1;
            end
        end

        if(d_mem_pending) begin
            if(d_delay_q == 0) begin
                if(d_write_q) begin
                    dmem[(d_addr_q - 32'h0000_1000) >> 2] <=
                        apply_wstrb(dmem[(d_addr_q - 32'h0000_1000) >> 2],
                                    d_wdata_q, d_wstrb_q);
                    d_rsp_rdata <= 32'h0000_0000;
                end
                else begin
                    d_rsp_rdata <= dmem[(d_addr_q - 32'h0000_1000) >> 2];
                end
                d_rsp_valid      <= 1'b1;
                d_mem_pending    <= 1'b0;
                d_response_count <= d_response_count + 1;
            end
            else begin
                d_delay_q <= d_delay_q - 1'b1;
            end
        end
    end
end

// valid and all request payload fields must remain stable during backpressure.
always @(posedge clk) begin
    if(!reset_n) begin
        if_hold_active <= 1'b0;
        d_hold_active  <= 1'b0;
    end
    else begin
        if(if_hold_active) begin
            if(!if_req_valid || (if_req_addr !== if_hold_addr)) begin
                $display("[ERROR] IF request changed before ready at t=%0t", $time);
                errors = errors + 1;
            end
            if(if_req_valid && if_req_ready)
                if_hold_active <= 1'b0;
        end
        else if(if_req_valid && !if_req_ready) begin
            if_hold_active <= 1'b1;
            if_hold_addr   <= if_req_addr;
        end

        if(d_hold_active) begin
            if(!d_req_valid || (d_req_write !== d_hold_write) ||
               (d_req_addr !== d_hold_addr) || (d_req_wdata !== d_hold_wdata) ||
               (d_req_wstrb !== d_hold_wstrb)) begin
                $display("[ERROR] D request changed before ready at t=%0t", $time);
                errors = errors + 1;
            end
            if(d_req_valid && d_req_ready)
                d_hold_active <= 1'b0;
        end
        else if(d_req_valid && !d_req_ready) begin
            d_hold_active <= 1'b1;
            d_hold_write  <= d_req_write;
            d_hold_addr   <= d_req_addr;
            d_hold_wdata  <= d_req_wdata;
            d_hold_wstrb  <= d_req_wstrb;
        end

        if(if_response_count > if_accept_count) begin
            $display("[ERROR] IF response without accepted request");
            errors = errors + 1;
        end
        if(d_response_count > d_accept_count) begin
            $display("[ERROR] D response without accepted request");
            errors = errors + 1;
        end
    end
end

always @(posedge clk or negedge reset_n) begin
    if(!reset_n)
        cycle_count <= 0;
    else
        cycle_count <= cycle_count + 1;
end

initial begin
    clk           = 1'b0;
    reset_n       = 1'b0;
    irq_timer     = 1'b0;
    cycle_count   = 0;
    errors        = 0;
    timeout_count = 0;
    if_hold_active = 1'b0;
    d_hold_active  = 1'b0;

    for(i = 0; i < 64; i = i + 1) begin
        imem[i] = 32'h0000_0013;
        dmem[i] = 32'h0000_0000;
    end

    imem[0] = 32'h0050_0093; // addi x1, x0, 5
    imem[1] = 32'h0000_1137; // lui  x2, 0x1
    imem[2] = 32'h0011_2023; // sw   x1, 0(x2)
    imem[3] = 32'h0001_2183; // lw   x3, 0(x2)
    imem[4] = 32'h0011_8213; // addi x4, x3, 1
    imem[5] = 32'h0041_00a3; // sb   x4, 1(x2)
    imem[6] = 32'h0011_4283; // lbu  x5, 1(x2)
    imem[7] = 32'h0012_8313; // addi x6, x5, 1
    imem[8] = 32'h0000_006f; // jal  x0, 0

    $dumpfile("native_interface_tb.vcd");
    $dumpvars(0, tb_native_interface);

    repeat(3) @(posedge clk);
    @(negedge clk);
    reset_n = 1'b1;

    while(dut.u_pipeline.datapath.regfile.regs[6] !== 32'h0000_0007) begin
        @(posedge clk);
        #1;
        timeout_count = timeout_count + 1;
        if(timeout_count > 500)
            $fatal(1, "Timeout waiting for native-interface program completion");
    end

    repeat(3) @(posedge clk);
    #1;

    if(dmem[0] !== 32'h0000_0605) begin
        $display("[ERROR] final memory expected=00000605 got=%08h", dmem[0]);
        errors = errors + 1;
    end
    if(dut.u_pipeline.datapath.regfile.regs[3] !== 32'h0000_0005) begin
        $display("[ERROR] x3 load result=%08h", dut.u_pipeline.datapath.regfile.regs[3]);
        errors = errors + 1;
    end
    if(dut.u_pipeline.datapath.regfile.regs[4] !== 32'h0000_0006) begin
        $display("[ERROR] x4 dependent result=%08h", dut.u_pipeline.datapath.regfile.regs[4]);
        errors = errors + 1;
    end
    if(dut.u_pipeline.datapath.regfile.regs[5] !== 32'h0000_0006) begin
        $display("[ERROR] x5 byte-load result=%08h", dut.u_pipeline.datapath.regfile.regs[5]);
        errors = errors + 1;
    end
    if((d_accept_count != 4) || (d_response_count != 4) ||
       (store_accept_count != 2) || (load_accept_count != 2)) begin
        $display("[ERROR] D handshake counts req=%0d rsp=%0d stores=%0d loads=%0d",
                 d_accept_count, d_response_count, store_accept_count, load_accept_count);
        errors = errors + 1;
    end
    if(if_error_dbg || d_error_dbg) begin
        $display("[ERROR] unexpected sticky interface error IF=%b D=%b", if_error_dbg, d_error_dbg);
        errors = errors + 1;
    end

    $display("----- NATIVE INTERFACE SUMMARY -----");
    $display("IF accepted/responses = %0d/%0d", if_accept_count, if_response_count);
    $display("D accepted/responses  = %0d/%0d", d_accept_count, d_response_count);
    $display("Final RAM[0]          = 0x%08h", dmem[0]);
    $display("x3/x4/x5/x6           = %0d/%0d/%0d/%0d",
             dut.u_pipeline.datapath.regfile.regs[3],
             dut.u_pipeline.datapath.regfile.regs[4],
             dut.u_pipeline.datapath.regfile.regs[5],
             dut.u_pipeline.datapath.regfile.regs[6]);

    if(errors != 0)
        $fatal(1, "native-interface test failed with %0d error(s)", errors);

    $display("[PASS] Native CPU request/response interface test");
    $finish;
end

endmodule
