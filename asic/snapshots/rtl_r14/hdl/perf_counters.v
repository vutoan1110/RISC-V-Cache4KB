// Performance / event counter bank.
// Cycle counters are mutually exclusive; event counters are independent.
// All counters are mod-2^32 and share one clear/freeze boundary.
module perf_counters #(
    // 0 holds the whole bank at zero so synthesis can remove it, which is how
    // the core's own area is measured apart from the instrumentation's.
    parameter integer PERF_COUNTERS_ENABLE = 1
)(
    input  wire        clk,
    input  wire        reset_n,
    input  wire        counter_clear,
    input  wire        counter_freeze,

    // Raw cycle causes from the core and memory system.
    input  wire        retire_event,
    input  wire        load_use_stall,
    input  wire        icache_wait,
    input  wire        dcache_wait,
    input  wire        control_redirect_event,
    input  wire        trap_redirect_event,
    input  wire        mmio_wait,
    input  wire        pipeline_nonempty,

    // Cache/bus events (CPU-request events, not refill beats).
    input  wire        icache_access_event,
    input  wire        icache_hit_event,
    input  wire        icache_miss_event,
    input  wire        dcache_read_access_event,
    input  wire        dcache_read_hit_event,
    input  wire        dcache_read_miss_event,
    input  wire        dcache_write_access_event,
    input  wire        dcache_write_hit_event,
    input  wire        dcache_write_miss_event,
    input  wire        icache_main_hit_event,
    input  wire        icache_victim_hit_event,
    input  wire        icache_true_miss_event,
    input  wire        dcache_main_hit_event,
    input  wire        dcache_victim_hit_event,
    input  wire        dcache_true_miss_event,
    input  wire        mispredict_event,
    input  wire        conditional_branch_event,
    input  wire        branch_taken_event,
    input  wire        branch_not_taken_event,
    input  wire        branch_prediction_event,
    input  wire        branch_correct_prediction_event,
    input  wire        axi_read_txn_event,
    input  wire        axi_write_txn_event,
    input  wire [31:0] trap_mcause,

    // one-hot: [0]RETIRE [1]LOAD_USE [2]I_WAIT [3]D_WAIT [4]CONTROL_REDIRECT
    //          [5]TRAP_REDIRECT [6]MMIO_WAIT [7]PIPE_FILL_DRAIN [8]OTHER
    output reg  [8:0]  cycle_reason_onehot,

    output reg  [31:0] mcycle_count,
    output reg  [31:0] retire_cycle_count,
    output reg  [31:0] load_use_cycle_count,
    output reg  [31:0] icache_wait_cycle_count,
    output reg  [31:0] dcache_wait_cycle_count,
    output reg  [31:0] control_redirect_cycle_count,
    output reg  [31:0] trap_redirect_cycle_count,
    output reg  [31:0] mmio_wait_cycle_count,
    output reg  [31:0] pipe_fill_drain_cycle_count,
    output reg  [31:0] other_cycle_count,

    output reg  [31:0] minstret_count,
    output reg  [31:0] icache_access_count,
    output reg  [31:0] icache_hit_count,
    output reg  [31:0] icache_miss_count,
    output reg  [31:0] dcache_read_access_count,
    output reg  [31:0] dcache_read_hit_count,
    output reg  [31:0] dcache_read_miss_count,
    output reg  [31:0] dcache_write_access_count,
    output reg  [31:0] dcache_write_hit_count,
    output reg  [31:0] dcache_write_miss_count,
    output reg  [31:0] icache_main_hit_count,
    output reg  [31:0] icache_victim_hit_count,
    output reg  [31:0] icache_true_miss_count,
    output reg  [31:0] dcache_main_hit_count,
    output reg  [31:0] dcache_victim_hit_count,
    output reg  [31:0] dcache_true_miss_count,
    output reg  [31:0] control_redirect_event_count,
    output reg  [31:0] mispredict_event_count,
    output reg  [31:0] conditional_branch_count,
    output reg  [31:0] branch_taken_count,
    output reg  [31:0] branch_not_taken_count,
    output reg  [31:0] branch_prediction_count,
    output reg  [31:0] branch_correct_prediction_count,
    output reg  [31:0] trap_event_count,
    output reg  [31:0] axi_read_txn_count,
    output reg  [31:0] axi_write_txn_count,
    output reg  [31:0] last_mcause
);

// ---------------------------------------------------------------------------
// Register stage on the event signals (critical-path relief).
//
// REASON: post-routing STA showed the path
//     datapath.valid_w -> u_observability.retire_cycle_count[30]
// missing setup by -11.579 ns at corner nom_ss_100C_1v60, across 56 logic levels.
//     7.47 -> 22.0 ns  event and stall computation inside the core   (14.5 ns)
//     22.0 -> 29.0 ns  the 9-level priority chain below             ( 7.0 ns)
//     29.0 -> 37.5 ns  the counter's 32-bit carry chain             ( 8.5 ns)
// The budget is 19.6 ns. Cutting at the module boundary splits it into 14.5 and 15.5 ns.
//
// WHY THIS DOES NOT CHANGE FUNCTION:
//  - These are OBSERVABILITY counters, read over APB. A one-cycle delay leaves every
//    TOTAL unchanged; the observation simply arrives one cycle later.
//  - The invariant "mcycle_count == sum of the 9 cycle counters" still holds: mcycle and
//    all 9 counters increment exactly once per cycle, so any delay leaves the sums equal.
//  - Out of reset, all 8 _q cause signals are 0, so the priority block falls through to
//    the else branch -> OTHER. Still one-hot, so no assertion is violated.
//  - counter_clear / counter_freeze are DELIBERATELY not registered: they gate the whole
//    block uniformly, and registering them would only add a pointless cycle of skew.
//  - trap_mcause MUST be registered in the same cycle as trap_redirect_event, otherwise
//    the wrong mcause value gets latched.
reg retire_event_q;
reg load_use_stall_q;
reg icache_wait_q;
reg dcache_wait_q;
reg control_redirect_event_q;
reg trap_redirect_event_q;
reg mmio_wait_q;
reg pipeline_nonempty_q;
reg icache_access_event_q;
reg icache_hit_event_q;
reg icache_miss_event_q;
reg dcache_read_access_event_q;
reg dcache_read_hit_event_q;
reg dcache_read_miss_event_q;
reg dcache_write_access_event_q;
reg dcache_write_hit_event_q;
reg dcache_write_miss_event_q;
reg icache_main_hit_event_q;
reg icache_victim_hit_event_q;
reg icache_true_miss_event_q;
reg dcache_main_hit_event_q;
reg dcache_victim_hit_event_q;
reg dcache_true_miss_event_q;
reg mispredict_event_q;
reg conditional_branch_event_q;
reg branch_taken_event_q;
reg branch_not_taken_event_q;
reg branch_prediction_event_q;
reg branch_correct_prediction_event_q;
reg axi_read_txn_event_q;
reg axi_write_txn_event_q;
reg [31:0] trap_mcause_q;

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        retire_event_q                     <= 1'b0;
        load_use_stall_q                   <= 1'b0;
        icache_wait_q                      <= 1'b0;
        dcache_wait_q                      <= 1'b0;
        control_redirect_event_q           <= 1'b0;
        trap_redirect_event_q              <= 1'b0;
        mmio_wait_q                        <= 1'b0;
        pipeline_nonempty_q                <= 1'b0;
        icache_access_event_q              <= 1'b0;
        icache_hit_event_q                 <= 1'b0;
        icache_miss_event_q                <= 1'b0;
        dcache_read_access_event_q         <= 1'b0;
        dcache_read_hit_event_q            <= 1'b0;
        dcache_read_miss_event_q           <= 1'b0;
        dcache_write_access_event_q        <= 1'b0;
        dcache_write_hit_event_q           <= 1'b0;
        dcache_write_miss_event_q          <= 1'b0;
        icache_main_hit_event_q            <= 1'b0;
        icache_victim_hit_event_q          <= 1'b0;
        icache_true_miss_event_q           <= 1'b0;
        dcache_main_hit_event_q            <= 1'b0;
        dcache_victim_hit_event_q          <= 1'b0;
        dcache_true_miss_event_q           <= 1'b0;
        mispredict_event_q                 <= 1'b0;
        conditional_branch_event_q         <= 1'b0;
        branch_taken_event_q               <= 1'b0;
        branch_not_taken_event_q           <= 1'b0;
        branch_prediction_event_q          <= 1'b0;
        branch_correct_prediction_event_q  <= 1'b0;
        axi_read_txn_event_q               <= 1'b0;
        axi_write_txn_event_q              <= 1'b0;
        trap_mcause_q                      <= 32'h0000_0000;
    end
    else begin
        retire_event_q                     <= retire_event;
        load_use_stall_q                   <= load_use_stall;
        icache_wait_q                      <= icache_wait;
        dcache_wait_q                      <= dcache_wait;
        control_redirect_event_q           <= control_redirect_event;
        trap_redirect_event_q              <= trap_redirect_event;
        mmio_wait_q                        <= mmio_wait;
        pipeline_nonempty_q                <= pipeline_nonempty;
        icache_access_event_q              <= icache_access_event;
        icache_hit_event_q                 <= icache_hit_event;
        icache_miss_event_q                <= icache_miss_event;
        dcache_read_access_event_q         <= dcache_read_access_event;
        dcache_read_hit_event_q            <= dcache_read_hit_event;
        dcache_read_miss_event_q           <= dcache_read_miss_event;
        dcache_write_access_event_q        <= dcache_write_access_event;
        dcache_write_hit_event_q           <= dcache_write_hit_event;
        dcache_write_miss_event_q          <= dcache_write_miss_event;
        icache_main_hit_event_q            <= icache_main_hit_event;
        icache_victim_hit_event_q          <= icache_victim_hit_event;
        icache_true_miss_event_q           <= icache_true_miss_event;
        dcache_main_hit_event_q            <= dcache_main_hit_event;
        dcache_victim_hit_event_q          <= dcache_victim_hit_event;
        dcache_true_miss_event_q           <= dcache_true_miss_event;
        mispredict_event_q                 <= mispredict_event;
        conditional_branch_event_q         <= conditional_branch_event;
        branch_taken_event_q               <= branch_taken_event;
        branch_not_taken_event_q           <= branch_not_taken_event;
        branch_prediction_event_q          <= branch_prediction_event;
        branch_correct_prediction_event_q  <= branch_correct_prediction_event;
        axi_read_txn_event_q               <= axi_read_txn_event;
        axi_write_txn_event_q              <= axi_write_txn_event;
        trap_mcause_q                      <= trap_mcause;
    end
end

// Fixed priority (part of the counter ABI):
// TRAP > CONTROL > MMIO > D$ > I$ > LOAD_USE > RETIRE > FILL/DRAIN > OTHER.
always @(*) begin
    cycle_reason_onehot = 9'b0;
    if(trap_redirect_event_q)
        cycle_reason_onehot[5] = 1'b1;
    else if(control_redirect_event_q)
        cycle_reason_onehot[4] = 1'b1;
    else if(mmio_wait_q)
        cycle_reason_onehot[6] = 1'b1;
    else if(dcache_wait_q)
        cycle_reason_onehot[3] = 1'b1;
    else if(icache_wait_q)
        cycle_reason_onehot[2] = 1'b1;
    else if(load_use_stall_q)
        cycle_reason_onehot[1] = 1'b1;
    else if(retire_event_q)
        cycle_reason_onehot[0] = 1'b1;
    else if(pipeline_nonempty_q)
        cycle_reason_onehot[7] = 1'b1;
    else
        cycle_reason_onehot[8] = 1'b1;
end

// R10b -- every increment below is a kept net: synthesis builds the +1 from
// the counter's own flops, and the late enables (counter_clear/freeze come
// straight from an APB write, the events from the pipeline) meet it only in
// the final select. Without the cut ABC folded the enable into the base of a
// ripple carry chain (26 cells, ~13 ns at ss). Same logic, different shape.
// R10 fix 2: the cut is for Yosys/ABC only. Quartus honours keep too and paid
// +17 % LE for it (15,425 -> 18,063 on dm_4kb), so it is ASIC-only.
`ifdef __openlane__
`define R10B_KEEP (* keep *)
`else
`define R10B_KEEP
`endif
`R10B_KEEP wire [31:0] mcycle_count_inc = mcycle_count + 32'd1;
`R10B_KEEP wire [31:0] retire_cycle_count_inc = retire_cycle_count + 32'd1;
`R10B_KEEP wire [31:0] load_use_cycle_count_inc = load_use_cycle_count + 32'd1;
`R10B_KEEP wire [31:0] icache_wait_cycle_count_inc = icache_wait_cycle_count + 32'd1;
`R10B_KEEP wire [31:0] dcache_wait_cycle_count_inc = dcache_wait_cycle_count + 32'd1;
`R10B_KEEP wire [31:0] control_redirect_cycle_count_inc = control_redirect_cycle_count + 32'd1;
`R10B_KEEP wire [31:0] trap_redirect_cycle_count_inc = trap_redirect_cycle_count + 32'd1;
`R10B_KEEP wire [31:0] mmio_wait_cycle_count_inc = mmio_wait_cycle_count + 32'd1;
`R10B_KEEP wire [31:0] pipe_fill_drain_cycle_count_inc = pipe_fill_drain_cycle_count + 32'd1;
`R10B_KEEP wire [31:0] other_cycle_count_inc = other_cycle_count + 32'd1;
`R10B_KEEP wire [31:0] minstret_count_inc = minstret_count + 32'd1;
`R10B_KEEP wire [31:0] icache_access_count_inc = icache_access_count + 32'd1;
`R10B_KEEP wire [31:0] icache_hit_count_inc = icache_hit_count + 32'd1;
`R10B_KEEP wire [31:0] icache_miss_count_inc = icache_miss_count + 32'd1;
`R10B_KEEP wire [31:0] dcache_read_access_count_inc = dcache_read_access_count + 32'd1;
`R10B_KEEP wire [31:0] dcache_read_hit_count_inc = dcache_read_hit_count + 32'd1;
`R10B_KEEP wire [31:0] dcache_read_miss_count_inc = dcache_read_miss_count + 32'd1;
`R10B_KEEP wire [31:0] dcache_write_access_count_inc = dcache_write_access_count + 32'd1;
`R10B_KEEP wire [31:0] dcache_write_hit_count_inc = dcache_write_hit_count + 32'd1;
`R10B_KEEP wire [31:0] dcache_write_miss_count_inc = dcache_write_miss_count + 32'd1;
`R10B_KEEP wire [31:0] icache_main_hit_count_inc = icache_main_hit_count + 32'd1;
`R10B_KEEP wire [31:0] icache_victim_hit_count_inc = icache_victim_hit_count + 32'd1;
`R10B_KEEP wire [31:0] icache_true_miss_count_inc = icache_true_miss_count + 32'd1;
`R10B_KEEP wire [31:0] dcache_main_hit_count_inc = dcache_main_hit_count + 32'd1;
`R10B_KEEP wire [31:0] dcache_victim_hit_count_inc = dcache_victim_hit_count + 32'd1;
`R10B_KEEP wire [31:0] dcache_true_miss_count_inc = dcache_true_miss_count + 32'd1;
`R10B_KEEP wire [31:0] control_redirect_event_count_inc = control_redirect_event_count + 32'd1;
`R10B_KEEP wire [31:0] mispredict_event_count_inc = mispredict_event_count + 32'd1;
`R10B_KEEP wire [31:0] conditional_branch_count_inc = conditional_branch_count + 32'd1;
`R10B_KEEP wire [31:0] branch_taken_count_inc = branch_taken_count + 32'd1;
`R10B_KEEP wire [31:0] branch_not_taken_count_inc = branch_not_taken_count + 32'd1;
`R10B_KEEP wire [31:0] branch_prediction_count_inc = branch_prediction_count + 32'd1;
`R10B_KEEP wire [31:0] branch_correct_prediction_count_inc = branch_correct_prediction_count + 32'd1;
`R10B_KEEP wire [31:0] trap_event_count_inc = trap_event_count + 32'd1;
`R10B_KEEP wire [31:0] axi_read_txn_count_inc = axi_read_txn_count + 32'd1;
`R10B_KEEP wire [31:0] axi_write_txn_count_inc = axi_write_txn_count + 32'd1;
`undef R10B_KEEP

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        mcycle_count                  <= 32'h0000_0000;
        retire_cycle_count            <= 32'h0000_0000;
        load_use_cycle_count          <= 32'h0000_0000;
        icache_wait_cycle_count       <= 32'h0000_0000;
        dcache_wait_cycle_count       <= 32'h0000_0000;
        control_redirect_cycle_count  <= 32'h0000_0000;
        trap_redirect_cycle_count     <= 32'h0000_0000;
        mmio_wait_cycle_count         <= 32'h0000_0000;
        pipe_fill_drain_cycle_count   <= 32'h0000_0000;
        other_cycle_count             <= 32'h0000_0000;
        minstret_count                <= 32'h0000_0000;
        icache_access_count           <= 32'h0000_0000;
        icache_hit_count              <= 32'h0000_0000;
        icache_miss_count             <= 32'h0000_0000;
        dcache_read_access_count      <= 32'h0000_0000;
        dcache_read_hit_count         <= 32'h0000_0000;
        dcache_read_miss_count        <= 32'h0000_0000;
        dcache_write_access_count     <= 32'h0000_0000;
        dcache_write_hit_count        <= 32'h0000_0000;
        dcache_write_miss_count       <= 32'h0000_0000;
        icache_main_hit_count         <= 32'h0000_0000;
        icache_victim_hit_count       <= 32'h0000_0000;
        icache_true_miss_count        <= 32'h0000_0000;
        dcache_main_hit_count         <= 32'h0000_0000;
        dcache_victim_hit_count       <= 32'h0000_0000;
        dcache_true_miss_count        <= 32'h0000_0000;
        control_redirect_event_count  <= 32'h0000_0000;
        mispredict_event_count        <= 32'h0000_0000;
        conditional_branch_count      <= 32'h0000_0000;
        branch_taken_count            <= 32'h0000_0000;
        branch_not_taken_count        <= 32'h0000_0000;
        branch_prediction_count       <= 32'h0000_0000;
        branch_correct_prediction_count <= 32'h0000_0000;
        trap_event_count              <= 32'h0000_0000;
        axi_read_txn_count            <= 32'h0000_0000;
        axi_write_txn_count           <= 32'h0000_0000;
        last_mcause                   <= 32'h0000_0000;
    end
    else if(counter_clear) begin
        mcycle_count                  <= 32'h0000_0000;
        retire_cycle_count            <= 32'h0000_0000;
        load_use_cycle_count          <= 32'h0000_0000;
        icache_wait_cycle_count       <= 32'h0000_0000;
        dcache_wait_cycle_count       <= 32'h0000_0000;
        control_redirect_cycle_count  <= 32'h0000_0000;
        trap_redirect_cycle_count     <= 32'h0000_0000;
        mmio_wait_cycle_count         <= 32'h0000_0000;
        pipe_fill_drain_cycle_count   <= 32'h0000_0000;
        other_cycle_count             <= 32'h0000_0000;
        minstret_count                <= 32'h0000_0000;
        icache_access_count           <= 32'h0000_0000;
        icache_hit_count              <= 32'h0000_0000;
        icache_miss_count             <= 32'h0000_0000;
        dcache_read_access_count      <= 32'h0000_0000;
        dcache_read_hit_count         <= 32'h0000_0000;
        dcache_read_miss_count        <= 32'h0000_0000;
        dcache_write_access_count     <= 32'h0000_0000;
        dcache_write_hit_count        <= 32'h0000_0000;
        dcache_write_miss_count       <= 32'h0000_0000;
        icache_main_hit_count         <= 32'h0000_0000;
        icache_victim_hit_count       <= 32'h0000_0000;
        icache_true_miss_count        <= 32'h0000_0000;
        dcache_main_hit_count         <= 32'h0000_0000;
        dcache_victim_hit_count       <= 32'h0000_0000;
        dcache_true_miss_count        <= 32'h0000_0000;
        control_redirect_event_count  <= 32'h0000_0000;
        mispredict_event_count        <= 32'h0000_0000;
        conditional_branch_count      <= 32'h0000_0000;
        branch_taken_count            <= 32'h0000_0000;
        branch_not_taken_count        <= 32'h0000_0000;
        branch_prediction_count       <= 32'h0000_0000;
        branch_correct_prediction_count <= 32'h0000_0000;
        trap_event_count              <= 32'h0000_0000;
        axi_read_txn_count            <= 32'h0000_0000;
        axi_write_txn_count           <= 32'h0000_0000;
        last_mcause                   <= 32'h0000_0000;
    end
    else if(!counter_freeze && (PERF_COUNTERS_ENABLE != 0)) begin
        mcycle_count <= mcycle_count_inc;

        case(cycle_reason_onehot)
            9'b000000001: retire_cycle_count           <= retire_cycle_count_inc;
            9'b000000010: load_use_cycle_count         <= load_use_cycle_count_inc;
            9'b000000100: icache_wait_cycle_count      <= icache_wait_cycle_count_inc;
            9'b000001000: dcache_wait_cycle_count      <= dcache_wait_cycle_count_inc;
            9'b000010000: control_redirect_cycle_count <= control_redirect_cycle_count_inc;
            9'b000100000: trap_redirect_cycle_count    <= trap_redirect_cycle_count_inc;
            9'b001000000: mmio_wait_cycle_count        <= mmio_wait_cycle_count_inc;
            9'b010000000: pipe_fill_drain_cycle_count  <= pipe_fill_drain_cycle_count_inc;
            default:      other_cycle_count            <= other_cycle_count_inc;
        endcase

        if(retire_event_q)
            minstret_count <= minstret_count_inc;

        if(icache_access_event_q)
            icache_access_count <= icache_access_count_inc;
        if(icache_hit_event_q)
            icache_hit_count <= icache_hit_count_inc;
        if(icache_miss_event_q)
            icache_miss_count <= icache_miss_count_inc;

        if(dcache_read_access_event_q)
            dcache_read_access_count <= dcache_read_access_count_inc;
        if(dcache_read_hit_event_q)
            dcache_read_hit_count <= dcache_read_hit_count_inc;
        if(dcache_read_miss_event_q)
            dcache_read_miss_count <= dcache_read_miss_count_inc;

        if(dcache_write_access_event_q)
            dcache_write_access_count <= dcache_write_access_count_inc;
        if(dcache_write_hit_event_q)
            dcache_write_hit_count <= dcache_write_hit_count_inc;
        if(dcache_write_miss_event_q)
            dcache_write_miss_count <= dcache_write_miss_count_inc;
        if(icache_main_hit_event_q)
            icache_main_hit_count <= icache_main_hit_count_inc;
        if(icache_victim_hit_event_q)
            icache_victim_hit_count <= icache_victim_hit_count_inc;
        if(icache_true_miss_event_q)
            icache_true_miss_count <= icache_true_miss_count_inc;
        if(dcache_main_hit_event_q)
            dcache_main_hit_count <= dcache_main_hit_count_inc;
        if(dcache_victim_hit_event_q)
            dcache_victim_hit_count <= dcache_victim_hit_count_inc;
        if(dcache_true_miss_event_q)
            dcache_true_miss_count <= dcache_true_miss_count_inc;

        if(control_redirect_event_q)
            control_redirect_event_count <= control_redirect_event_count_inc;
        if(mispredict_event_q)
            mispredict_event_count <= mispredict_event_count_inc;
        if(conditional_branch_event_q)
            conditional_branch_count <= conditional_branch_count_inc;
        if(branch_taken_event_q)
            branch_taken_count <= branch_taken_count_inc;
        if(branch_not_taken_event_q)
            branch_not_taken_count <= branch_not_taken_count_inc;
        if(branch_prediction_event_q)
            branch_prediction_count <= branch_prediction_count_inc;
        if(branch_correct_prediction_event_q)
            branch_correct_prediction_count <= branch_correct_prediction_count_inc;
        if(trap_redirect_event_q) begin
            trap_event_count <= trap_event_count_inc;
            last_mcause      <= trap_mcause_q;
        end
        if(axi_read_txn_event_q)
            axi_read_txn_count <= axi_read_txn_count_inc;
        if(axi_write_txn_event_q)
            axi_write_txn_count <= axi_write_txn_count_inc;
    end
end

// synthesis translate_off
wire [35:0] exclusive_cycle_sum =
    {4'b0, retire_cycle_count} +
    {4'b0, load_use_cycle_count} +
    {4'b0, icache_wait_cycle_count} +
    {4'b0, dcache_wait_cycle_count} +
    {4'b0, control_redirect_cycle_count} +
    {4'b0, trap_redirect_cycle_count} +
    {4'b0, mmio_wait_cycle_count} +
    {4'b0, pipe_fill_drain_cycle_count} +
    {4'b0, other_cycle_count};

// reset_n is the asynchronous reset of every other block in this module. A
// checker that sampled it synchronously would be the only place where the same
// net acts as ordinary data, which is exactly the mixed discipline a reset net
// must not have. The sensitivity list matches the counters: on negedge reset_n
// the guard is false, so no check runs while the module is held in reset.
always @(posedge clk or negedge reset_n) begin
    if(reset_n) begin
        if((cycle_reason_onehot == 9'b0) ||
           ((cycle_reason_onehot & (cycle_reason_onehot - 1'b1)) != 9'b0))
            $fatal(1, "Cycle reason is not one-hot: %b", cycle_reason_onehot);

        if(mcycle_count !== exclusive_cycle_sum[31:0])
            $fatal(1, "mcycle reconstruction failed: mcycle=%0d sum=%0d",
                   mcycle_count, exclusive_cycle_sum[31:0]);

        if(icache_access_count !== (icache_hit_count + icache_miss_count))
            $fatal(1, "I-cache access=hit+miss invariant failed");
        if(dcache_read_access_count !==
           (dcache_read_hit_count + dcache_read_miss_count))
            $fatal(1, "D-cache read access=hit+miss invariant failed");
        if(dcache_write_access_count !==
           (dcache_write_hit_count + dcache_write_miss_count))
            $fatal(1, "D-cache write access=hit+miss invariant failed");
        if(icache_access_count !==
           (icache_main_hit_count + icache_victim_hit_count + icache_true_miss_count))
            $fatal(1, "I-cache access=main+victim+true-miss invariant failed");
        if((dcache_read_access_count + dcache_write_access_count) !==
           (dcache_main_hit_count + dcache_victim_hit_count + dcache_true_miss_count))
            $fatal(1, "D-cache access=main+victim+true-miss invariant failed");

        if(conditional_branch_count !==
           (branch_taken_count + branch_not_taken_count))
            $fatal(1, "Conditional branch=taken+not-taken invariant failed");
        if(branch_prediction_count !==
           (branch_correct_prediction_count + mispredict_event_count))
            $fatal(1, "Prediction=correct+mispredict invariant failed");

        if(icache_access_event_q && !(icache_hit_event_q ^ icache_miss_event_q))
            $fatal(1, "I-cache access event must be exactly one of hit/miss");
        if(!icache_access_event_q && (icache_hit_event_q || icache_miss_event_q))
            $fatal(1, "I-cache hit/miss without a CPU access event");
        if(dcache_read_access_event_q &&
           !(dcache_read_hit_event_q ^ dcache_read_miss_event_q))
            $fatal(1, "D-cache read access must be exactly one of hit/miss");
        if(!dcache_read_access_event_q &&
           (dcache_read_hit_event_q || dcache_read_miss_event_q))
            $fatal(1, "D-cache read hit/miss without CPU read access");
        if(dcache_write_access_event_q &&
           !(dcache_write_hit_event_q ^ dcache_write_miss_event_q))
            $fatal(1, "D-cache write access must be exactly one of hit/miss");
        if(!dcache_write_access_event_q &&
           (dcache_write_hit_event_q || dcache_write_miss_event_q))
            $fatal(1, "D-cache write hit/miss without CPU write access");
        if(conditional_branch_event_q &&
           !(branch_taken_event_q ^ branch_not_taken_event_q))
            $fatal(1, "Resolved branch must be exactly taken/not-taken");
        if(!conditional_branch_event_q &&
           (branch_taken_event_q || branch_not_taken_event_q))
            $fatal(1, "Branch outcome event without resolved branch");
        if(branch_prediction_event_q &&
           !(branch_correct_prediction_event_q ^ mispredict_event_q))
            $fatal(1, "Prediction must be exactly correct/mispredict");
        if(!branch_prediction_event_q &&
           (branch_correct_prediction_event_q || mispredict_event_q))
            $fatal(1, "Prediction result without prediction event");
    end
end
// synthesis translate_on

endmodule
