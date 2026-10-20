`timescale 1ns/1ps

module tb_performance_counters;

localparam [8:0] R_RETIRE  = 9'b000000001;
localparam [8:0] R_LOAD    = 9'b000000010;
localparam [8:0] R_IWAIT   = 9'b000000100;
localparam [8:0] R_DWAIT   = 9'b000001000;
localparam [8:0] R_CONTROL = 9'b000010000;
localparam [8:0] R_TRAP    = 9'b000100000;
localparam [8:0] R_MMIO    = 9'b001000000;
localparam [8:0] R_FILL    = 9'b010000000;
localparam [8:0] R_OTHER   = 9'b100000000;

localparam [7:0] CMD_CLEAR_START     = 8'h01;
localparam [7:0] CMD_SNAPSHOT        = 8'h02;
localparam [7:0] CMD_FREEZE_SNAPSHOT = 8'h03;
localparam [7:0] CMD_UNFREEZE        = 8'h04;
localparam [7:0] CMD_CLEAR_FROZEN    = 8'h05;

reg clk;
reg reset_n;
reg retire_event;
reg load_use_stall;
reg icache_wait;
reg dcache_wait;
reg control_redirect_event;
reg trap_redirect_event;
reg mmio_wait;
reg pipeline_nonempty;
reg icache_access_event;
reg icache_hit_event;
reg icache_miss_event;
reg dcache_read_access_event;
reg dcache_read_hit_event;
reg dcache_read_miss_event;
reg dcache_write_access_event;
reg dcache_write_hit_event;
reg dcache_write_miss_event;
reg mispredict_event;
reg conditional_branch_event;
reg branch_taken_event;
reg branch_not_taken_event;
reg branch_prediction_event;
reg branch_correct_prediction_event;
reg axi_read_txn_event;
reg axi_write_txn_event;
reg [31:0] trap_mcause;

reg PSEL;
reg PENABLE;
reg PWRITE;
reg [3:0] PSTRB;
reg [11:0] PADDR;
reg [31:0] PWDATA;
wire [31:0] PRDATA;
wire PREADY;
wire PSLVERR;
reg freeze_early;

wire [8:0] cycle_reason_onehot_dbg;
wire [31:0] mcycle_count_dbg;
wire [31:0] minstret_count_dbg;
wire counter_freeze_dbg;
// Bus write error inputs, driven here so the sysmon registers 0xAC / 0xB0
// and the write-1-to-clear pulse can be checked directly.
reg         tb_bus_wr_err;
reg  [31:0] tb_bus_wr_err_addr;
wire        tb_bus_wr_err_clear;
reg         tb_clear_seen;
reg  [31:0] bus_err_rd;
wire snapshot_valid_dbg;

performance_observability dut (
    .clk(clk), .reset_n(reset_n),
    .retire_event(retire_event),
    .load_use_stall(load_use_stall),
    .icache_wait(icache_wait),
    .dcache_wait(dcache_wait),
    .control_redirect_event(control_redirect_event),
    .trap_redirect_event(trap_redirect_event),
    .mmio_wait(mmio_wait),
    .pipeline_nonempty(pipeline_nonempty),
    .icache_access_event(icache_access_event),
    .icache_hit_event(icache_hit_event),
    .icache_miss_event(icache_miss_event),
    .dcache_read_access_event(dcache_read_access_event),
    .dcache_read_hit_event(dcache_read_hit_event),
    .dcache_read_miss_event(dcache_read_miss_event),
    .dcache_write_access_event(dcache_write_access_event),
    .dcache_write_hit_event(dcache_write_hit_event),
    .dcache_write_miss_event(dcache_write_miss_event),
    .icache_main_hit_event(icache_hit_event),
    .icache_victim_hit_event(1'b0),
    .icache_true_miss_event(icache_miss_event),
    .dcache_main_hit_event(dcache_read_hit_event || dcache_write_hit_event),
    .dcache_victim_hit_event(1'b0),
    .dcache_true_miss_event(dcache_read_miss_event || dcache_write_miss_event),
    .mispredict_event(mispredict_event),
    .conditional_branch_event(conditional_branch_event),
    .branch_taken_event(branch_taken_event),
    .branch_not_taken_event(branch_not_taken_event),
    .branch_prediction_event(branch_prediction_event),
    .branch_correct_prediction_event(branch_correct_prediction_event),
    .axi_read_txn_event(axi_read_txn_event),
    .axi_write_txn_event(axi_write_txn_event),
    .trap_mcause(trap_mcause),
    .PSEL(PSEL), .PENABLE(PENABLE), .PWRITE(PWRITE), .PSTRB(PSTRB),
    .PADDR(PADDR), .PWDATA(PWDATA), .PRDATA(PRDATA),
    .PREADY(PREADY), .PSLVERR(PSLVERR), .freeze_early(freeze_early),
    .cycle_reason_onehot_dbg(cycle_reason_onehot_dbg),
    .mcycle_count_dbg(mcycle_count_dbg),
    .minstret_count_dbg(minstret_count_dbg),
    .counter_freeze_dbg(counter_freeze_dbg),
    .snapshot_valid_dbg(snapshot_valid_dbg),
    .bus_wr_err(tb_bus_wr_err),
    .bus_wr_err_addr(tb_bus_wr_err_addr),
    .bus_wr_err_clear(tb_bus_wr_err_clear)
);

always @(posedge clk)
    if(tb_bus_wr_err_clear) tb_clear_seen <= 1'b1;

always #5 clk = ~clk;

task automatic clear_raw;
begin
    retire_event = 0;
    load_use_stall = 0;
    icache_wait = 0;
    dcache_wait = 0;
    control_redirect_event = 0;
    trap_redirect_event = 0;
    mmio_wait = 0;
    pipeline_nonempty = 0;
    icache_access_event = 0;
    icache_hit_event = 0;
    icache_miss_event = 0;
    dcache_read_access_event = 0;
    dcache_read_hit_event = 0;
    dcache_read_miss_event = 0;
    dcache_write_access_event = 0;
    dcache_write_hit_event = 0;
    dcache_write_miss_event = 0;
    mispredict_event = 0;
    conditional_branch_event = 0;
    branch_taken_event = 0;
    branch_not_taken_event = 0;
    branch_prediction_event = 0;
    branch_correct_prediction_event = 0;
    axi_read_txn_event = 0;
    axi_write_txn_event = 0;
end
endtask

task automatic expect32(input [31:0] got, input [31:0] expected,
                        input string label_text);
begin
    if(got !== expected)
        $fatal(1, "%s: expected %0d (0x%08x), got %0d (0x%08x)",
               label_text, expected, expected, got, got);
end
endtask

task automatic apb_write(input [7:0] addr, input [31:0] data);
begin
    @(negedge clk);
    PSEL = 1; PENABLE = 0; PWRITE = 1; PSTRB = 4'hF;
    PADDR = {4'h3, addr}; PWDATA = data;
    @(negedge clk);
    PENABLE = 1;
    @(posedge clk); #1;
    if(!PREADY || PSLVERR)
        $fatal(1, "APB write failed addr=0x%02x data=0x%08x", addr, data);
    @(negedge clk);
    PSEL = 0; PENABLE = 0; PWRITE = 0; PSTRB = 0; PADDR = 0; PWDATA = 0;
end
endtask

task automatic apb_read(input [7:0] addr, output [31:0] data);
begin
    @(negedge clk);
    PSEL = 1; PENABLE = 0; PWRITE = 0; PSTRB = 0;
    PADDR = {4'h3, addr}; PWDATA = 0;
    @(negedge clk);
    PENABLE = 1;
    @(posedge clk); #1;
    if(!PREADY || PSLVERR)
        $fatal(1, "APB read failed addr=0x%02x", addr);
    data = PRDATA;
    @(negedge clk);
    PSEL = 0; PENABLE = 0; PADDR = 0;
end
endtask

task automatic reason_cycle(input [8:0] expected_reason);
begin
    @(posedge clk); #1;
    if(cycle_reason_onehot_dbg !== expected_reason)
        $fatal(1, "cycle reason expected %b got %b",
               expected_reason, cycle_reason_onehot_dbg);
end
endtask

function automatic [31:0] exclusive_sum;
begin
    exclusive_sum = dut.u_perf_counters.retire_cycle_count +
                    dut.u_perf_counters.load_use_cycle_count +
                    dut.u_perf_counters.icache_wait_cycle_count +
                    dut.u_perf_counters.dcache_wait_cycle_count +
                    dut.u_perf_counters.control_redirect_cycle_count +
                    dut.u_perf_counters.trap_redirect_cycle_count +
                    dut.u_perf_counters.mmio_wait_cycle_count +
                    dut.u_perf_counters.pipe_fill_drain_cycle_count +
                    dut.u_perf_counters.other_cycle_count;
end
endfunction

reg [31:0] snap_cycle;
reg [31:0] snap_cycle_again;
reg [31:0] snap_i_access;
reg [31:0] snap_i_hit;
reg [31:0] snap_i_miss;
reg [31:0] live_before_freeze;
reg [31:0] cache_before_internal;
reg [31:0] snap_conditional;
reg [31:0] snap_taken;
reg [31:0] snap_not_taken;
reg [31:0] snap_prediction;
reg [31:0] snap_correct;
reg [31:0] snap_mispredict;
reg [31:0] snap_i_main, snap_i_victim, snap_i_true;
reg [31:0] snap_d_main, snap_d_victim, snap_d_true;
integer k;

initial begin
    tb_bus_wr_err = 1'b0; tb_bus_wr_err_addr = 32'h0; tb_clear_seen = 1'b0;
    clk = 0;
    reset_n = 0;
    clear_raw();
    trap_mcause = 32'h8000_0007;
    PSEL = 0; PENABLE = 0; PWRITE = 0; PSTRB = 0; PADDR = 0; PWDATA = 0;
    freeze_early = 0;

    repeat(3) @(posedge clk);
    @(negedge clk); reset_n = 1;

    $display("[TEST 1] one-hot classifier and priority overlaps");
    apb_write(8'h04, CMD_CLEAR_START);

    clear_raw(); retire_event = 1;
    reason_cycle(R_RETIRE);
    clear_raw(); retire_event = 1; load_use_stall = 1;
    reason_cycle(R_LOAD);
    clear_raw(); retire_event = 1; load_use_stall = 1; icache_wait = 1;
    reason_cycle(R_IWAIT);
    clear_raw(); retire_event = 1; load_use_stall = 1; icache_wait = 1; dcache_wait = 1;
    reason_cycle(R_DWAIT);
    clear_raw(); retire_event = 1; load_use_stall = 1; icache_wait = 1;
    dcache_wait = 1; mmio_wait = 1;
    reason_cycle(R_MMIO);
    clear_raw(); retire_event = 1; mmio_wait = 1; control_redirect_event = 1;
    conditional_branch_event = 1; branch_taken_event = 1;
    branch_prediction_event = 1; mispredict_event = 1;
    reason_cycle(R_CONTROL);
    clear_raw(); trap_redirect_event = 1; mmio_wait = 1;
    reason_cycle(R_TRAP);
    clear_raw(); pipeline_nonempty = 1;
    reason_cycle(R_FILL);
    clear_raw();
    reason_cycle(R_OTHER);

    expect32(mcycle_count_dbg, 9, "mcycle after nine reason classes");
    expect32(exclusive_sum(), 9, "exclusive cycle sum");
    expect32(dut.u_perf_counters.load_use_cycle_count, 1,
             "load-use loses to cache wait on overlaps");
    expect32(dut.u_perf_counters.icache_wait_cycle_count, 1,
             "I-wait count");
    expect32(dut.u_perf_counters.dcache_wait_cycle_count, 1,
             "D-wait priority over I-wait");
    expect32(dut.u_perf_counters.mmio_wait_cycle_count, 1,
             "MMIO priority over D/I waits");
    expect32(dut.u_perf_counters.control_redirect_cycle_count, 1,
             "control redirect attribution");
    expect32(dut.u_perf_counters.trap_redirect_cycle_count, 1,
             "trap redirect attribution");
    expect32(dut.u_perf_counters.control_redirect_event_count, 1,
             "control redirect event count");
    expect32(dut.u_perf_counters.mispredict_event_count, 1,
             "mispredict event count");
    expect32(dut.u_perf_counters.conditional_branch_count, 1,
             "conditional branch event count");
    expect32(dut.u_perf_counters.branch_taken_count, 1,
             "branch taken event count");
    expect32(dut.u_perf_counters.branch_not_taken_count, 0,
             "branch not-taken event count");
    expect32(dut.u_perf_counters.branch_prediction_count, 1,
             "branch prediction event count");
    expect32(dut.u_perf_counters.branch_correct_prediction_count, 0,
             "correct prediction event count");
    expect32(dut.u_perf_counters.conditional_branch_count,
             dut.u_perf_counters.branch_taken_count + dut.u_perf_counters.branch_not_taken_count,
             "conditional=taken+not-taken");
    expect32(dut.u_perf_counters.branch_prediction_count,
             dut.u_perf_counters.branch_correct_prediction_count + dut.u_perf_counters.mispredict_event_count,
             "prediction=correct+mispredict");
    expect32(dut.u_perf_counters.trap_event_count, 1, "trap event count");
    expect32(dut.u_perf_counters.last_mcause, 32'h8000_0007, "last mcause");

    $display("[TEST 2] cache event equations and internal/refill exclusion");
    clear_raw(); icache_access_event = 1; icache_hit_event = 1;
    reason_cycle(R_OTHER);
    clear_raw(); icache_access_event = 1; icache_miss_event = 1;
    reason_cycle(R_OTHER);
    clear_raw(); dcache_read_access_event = 1; dcache_read_hit_event = 1;
    reason_cycle(R_OTHER);
    clear_raw(); dcache_read_access_event = 1; dcache_read_miss_event = 1;
    reason_cycle(R_OTHER);
    clear_raw(); dcache_write_access_event = 1; dcache_write_hit_event = 1;
    reason_cycle(R_OTHER);
    clear_raw(); dcache_write_access_event = 1; dcache_write_miss_event = 1;
    reason_cycle(R_OTHER);
    clear_raw(); axi_read_txn_event = 1; axi_write_txn_event = 1;
    reason_cycle(R_OTHER);

    cache_before_internal = dut.u_perf_counters.icache_access_count;
    // Four internal/refill-like cycles deliberately carry no CPU access event.
    for(k = 0; k < 4; k = k + 1) begin
        clear_raw();
        reason_cycle(R_OTHER);
    end
    expect32(dut.u_perf_counters.icache_access_count, cache_before_internal,
             "internal/refill traffic must not increment I access");
    expect32(dut.u_perf_counters.icache_access_count,
             dut.u_perf_counters.icache_hit_count + dut.u_perf_counters.icache_miss_count,
             "I access=hit+miss");
    expect32(dut.u_perf_counters.dcache_read_access_count,
             dut.u_perf_counters.dcache_read_hit_count + dut.u_perf_counters.dcache_read_miss_count,
             "D read access=hit+miss");
    expect32(dut.u_perf_counters.dcache_write_access_count,
             dut.u_perf_counters.dcache_write_hit_count + dut.u_perf_counters.dcache_write_miss_count,
             "D write access=hit+miss");
    expect32(dut.u_perf_counters.icache_access_count,
             dut.u_perf_counters.icache_main_hit_count + dut.u_perf_counters.icache_victim_hit_count + dut.u_perf_counters.icache_true_miss_count,
             "I access=main+victim+true miss");
    expect32(dut.u_perf_counters.dcache_read_access_count + dut.u_perf_counters.dcache_write_access_count,
             dut.u_perf_counters.dcache_main_hit_count + dut.u_perf_counters.dcache_victim_hit_count + dut.u_perf_counters.dcache_true_miss_count,
             "D access=main+victim+true miss");
    expect32(dut.u_perf_counters.axi_read_txn_count, 1, "AXI read transaction event");
    expect32(dut.u_perf_counters.axi_write_txn_count, 1, "AXI write transaction event");
    expect32(mcycle_count_dbg, exclusive_sum(), "mcycle exact reconstruction");

    $display("[TEST 3] atomic snapshot while live counters continue");
    clear_raw();
    apb_write(8'h04, CMD_SNAPSHOT);
    if(!snapshot_valid_dbg)
        $fatal(1, "snapshot_valid not set");
    apb_read(8'h10, snap_cycle);
    apb_read(8'h44, snap_i_access);
    apb_read(8'h48, snap_i_hit);
    apb_read(8'h4C, snap_i_miss);
    apb_read(8'h6C, snap_mispredict);
    apb_read(8'h80, snap_conditional);
    apb_read(8'h84, snap_taken);
    apb_read(8'h88, snap_not_taken);
    apb_read(8'h8C, snap_prediction);
    apb_read(8'h90, snap_correct);
    apb_read(8'h94, snap_i_main);
    apb_read(8'h98, snap_i_victim);
    apb_read(8'h9C, snap_i_true);
    apb_read(8'hA0, snap_d_main);
    apb_read(8'hA4, snap_d_victim);
    apb_read(8'hA8, snap_d_true);
    expect32(snap_i_access, snap_i_hit + snap_i_miss,
             "snapshot I access=hit+miss");
    expect32(snap_conditional, snap_taken + snap_not_taken,
             "snapshot conditional=taken+not-taken");
    expect32(snap_prediction, snap_correct + snap_mispredict,
             "snapshot prediction=correct+mispredict");
    clear_raw(); conditional_branch_event = 1; branch_not_taken_event = 1;
    branch_prediction_event = 1; branch_correct_prediction_event = 1;
    reason_cycle(R_OTHER);
    repeat(5) begin clear_raw(); reason_cycle(R_OTHER); end
    apb_read(8'h10, snap_cycle_again);
    expect32(snap_cycle_again, snap_cycle, "snapshot remains atomic/stable");
    apb_read(8'h80, snap_cycle_again);
    expect32(snap_cycle_again, snap_conditional,
             "branch snapshot remains atomic while live branch counters advance");
    if(mcycle_count_dbg <= snap_cycle)
        $fatal(1, "live counters did not continue after non-freezing snapshot");

    $display("[TEST 4] freeze-snapshot, clear-frozen, and unfreeze");
    apb_write(8'h04, CMD_FREEZE_SNAPSHOT);
    if(!counter_freeze_dbg || !snapshot_valid_dbg)
        $fatal(1, "FREEZE_SNAPSHOT did not freeze and validate snapshot");
    live_before_freeze = mcycle_count_dbg;
    for(k = 0; k < 5; k = k + 1) begin
        clear_raw();
        icache_access_event = 1; icache_hit_event = 1;
        reason_cycle(R_OTHER);
    end
    expect32(mcycle_count_dbg, live_before_freeze, "frozen mcycle");

    clear_raw();
    apb_write(8'h04, CMD_CLEAR_FROZEN);
    expect32(mcycle_count_dbg, 0, "clear while frozen");
    if(!counter_freeze_dbg || snapshot_valid_dbg)
        $fatal(1, "CLEAR_FROZEN status is incorrect");
    repeat(3) reason_cycle(R_OTHER);
    expect32(mcycle_count_dbg, 0, "no increments while frozen after clear");

    apb_write(8'h04, CMD_UNFREEZE);
    if(counter_freeze_dbg)
        $fatal(1, "UNFREEZE did not release counter bank");
    clear_raw(); retire_event = 1;
    reason_cycle(R_RETIRE);
    expect32(mcycle_count_dbg, 1, "first cycle after unfreeze");
    clear_raw();
    @(posedge clk); #1;
    expect32(minstret_count_dbg, 1, "independent retire event after unfreeze");
    expect32(mcycle_count_dbg, exclusive_sum(), "final mcycle reconstruction");

    $display("[TEST 5] early freeze excludes control-transport latency");
    clear_raw();
    live_before_freeze = mcycle_count_dbg;
    @(negedge clk); freeze_early = 1;
    @(posedge clk); #1;
    expect32(mcycle_count_dbg, live_before_freeze, "early-freeze boundary");
    if(!counter_freeze_dbg)
        $fatal(1, "early freeze did not latch frozen state");
    @(negedge clk); freeze_early = 0;
    repeat(2) reason_cycle(R_OTHER);
    expect32(mcycle_count_dbg, live_before_freeze,
             "transport-like cycles excluded after early freeze");

    // ABI v2: identity word, bus write error registers, write-1-to-clear.
    apb_read(8'h00, bus_err_rd);
    if(bus_err_rd !== 32'h5338_0002)
        $fatal(1, "sysmon ident is 0x%08x, ABI v2 expects 0x53380002", bus_err_rd);
    tb_bus_wr_err = 1'b0; tb_bus_wr_err_addr = 32'h0;
    apb_read(8'hAC, bus_err_rd);
    if(bus_err_rd !== 32'h0)
        $fatal(1, "0xAC reads 0x%08x with no bus error", bus_err_rd);
    tb_bus_wr_err = 1'b1; tb_bus_wr_err_addr = 32'hDEAD_BEEC;
    apb_read(8'hAC, bus_err_rd);
    if(bus_err_rd !== 32'h1)
        $fatal(1, "0xAC reads 0x%08x with a bus error pending", bus_err_rd);
    apb_read(8'hB0, bus_err_rd);
    if(bus_err_rd !== 32'hDEAD_BEEC)
        $fatal(1, "0xB0 reads 0x%08x, expected the error address", bus_err_rd);
    // A write of 0 must not clear; apb_write itself fails on PSLVERR, so both
    // writes also prove 0xAC is accepted as a writable register.
    tb_clear_seen = 1'b0;
    apb_write(8'hAC, 32'h0);
    if(tb_clear_seen !== 1'b0)
        $fatal(1, "writing 0 to 0xAC pulsed bus_wr_err_clear");
    apb_write(8'hAC, 32'h1);
    if(tb_clear_seen !== 1'b1)
        $fatal(1, "writing 1 to 0xAC did not pulse bus_wr_err_clear");
    tb_bus_wr_err = 1'b0;
    $display("[PASS] Sysmon ABI v2 bus write error registers");
    $display("[PASS] Classifier, counter equations, snapshot/freeze/clear tests");
    $finish;
end

endmodule
