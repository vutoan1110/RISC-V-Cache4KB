// Integration wrapper for the cycle classifier, counter bank and APB monitor.
module performance_observability #(
    // 1 keeps the counter bank and the APB snapshot registers. 0 removes
    // them and ties every count to zero, which isolates the CPU core's
    // own area from the instrumentation's.
    parameter integer PERF_COUNTERS_ENABLE = 1
)(
    input  wire        clk,
    input  wire        reset_n,

    input  wire        retire_event,
    input  wire        load_use_stall,
    input  wire        icache_wait,
    input  wire        dcache_wait,
    input  wire        control_redirect_event,
    input  wire        trap_redirect_event,
    input  wire        mmio_wait,
    input  wire        pipeline_nonempty,

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

    input  wire        PSEL,
    input  wire        PENABLE,
    input  wire        PWRITE,
    input  wire [3:0]  PSTRB,
    input  wire [11:0] PADDR,
    input  wire [31:0] PWDATA,
    output wire [31:0] PRDATA,
    output wire        PREADY,
    output wire        PSLVERR,
    input  wire        freeze_early,

    output wire [8:0]  cycle_reason_onehot_dbg,
    output wire [31:0] mcycle_count_dbg,
    output wire [31:0] minstret_count_dbg,
    output wire        counter_freeze_dbg,
    output wire        snapshot_valid_dbg,

    // Posted-write error state, passed through to the sysmon registers.
    input  wire        bus_wr_err,
    input  wire [31:0] bus_wr_err_addr,
    output wire        bus_wr_err_clear
);

wire counter_clear;
wire counter_freeze;
wire [31:0] snapshot_sequence;

wire [31:0] retire_cycle_count;
wire [31:0] load_use_cycle_count;
wire [31:0] icache_wait_cycle_count;
wire [31:0] dcache_wait_cycle_count;
wire [31:0] control_redirect_cycle_count;
wire [31:0] trap_redirect_cycle_count;
wire [31:0] mmio_wait_cycle_count;
wire [31:0] pipe_fill_drain_cycle_count;
wire [31:0] other_cycle_count;
wire [31:0] icache_access_count;
wire [31:0] icache_hit_count;
wire [31:0] icache_miss_count;
wire [31:0] dcache_read_access_count;
wire [31:0] dcache_read_hit_count;
wire [31:0] dcache_read_miss_count;
wire [31:0] dcache_write_access_count;
wire [31:0] dcache_write_hit_count;
wire [31:0] dcache_write_miss_count;
wire [31:0] icache_main_hit_count;
wire [31:0] icache_victim_hit_count;
wire [31:0] icache_true_miss_count;
wire [31:0] dcache_main_hit_count;
wire [31:0] dcache_victim_hit_count;
wire [31:0] dcache_true_miss_count;
wire [31:0] control_redirect_event_count;
wire [31:0] mispredict_event_count;
wire [31:0] conditional_branch_count;
wire [31:0] branch_taken_count;
wire [31:0] branch_not_taken_count;
wire [31:0] branch_prediction_count;
wire [31:0] branch_correct_prediction_count;
wire [31:0] trap_event_count;
wire [31:0] axi_read_txn_count;
wire [31:0] axi_write_txn_count;
wire [31:0] last_mcause;

assign counter_freeze_dbg = counter_freeze;

perf_counters #(.PERF_COUNTERS_ENABLE(PERF_COUNTERS_ENABLE))
u_perf_counters (
    .clk                           (clk),
    .reset_n                       (reset_n),
    .counter_clear                 (counter_clear),
    .counter_freeze                (counter_freeze),
    .retire_event                  (retire_event),
    .load_use_stall                (load_use_stall),
    .icache_wait                   (icache_wait),
    .dcache_wait                   (dcache_wait),
    .control_redirect_event        (control_redirect_event),
    .trap_redirect_event           (trap_redirect_event),
    .mmio_wait                     (mmio_wait),
    .pipeline_nonempty             (pipeline_nonempty),
    .icache_access_event           (icache_access_event),
    .icache_hit_event              (icache_hit_event),
    .icache_miss_event             (icache_miss_event),
    .dcache_read_access_event      (dcache_read_access_event),
    .dcache_read_hit_event         (dcache_read_hit_event),
    .dcache_read_miss_event        (dcache_read_miss_event),
    .dcache_write_access_event     (dcache_write_access_event),
    .dcache_write_hit_event        (dcache_write_hit_event),
    .dcache_write_miss_event       (dcache_write_miss_event),
    .icache_main_hit_event         (icache_main_hit_event),
    .icache_victim_hit_event       (icache_victim_hit_event),
    .icache_true_miss_event        (icache_true_miss_event),
    .dcache_main_hit_event         (dcache_main_hit_event),
    .dcache_victim_hit_event       (dcache_victim_hit_event),
    .dcache_true_miss_event        (dcache_true_miss_event),
    .mispredict_event              (mispredict_event),
    .conditional_branch_event      (conditional_branch_event),
    .branch_taken_event            (branch_taken_event),
    .branch_not_taken_event        (branch_not_taken_event),
    .branch_prediction_event       (branch_prediction_event),
    .branch_correct_prediction_event(branch_correct_prediction_event),
    .axi_read_txn_event            (axi_read_txn_event),
    .axi_write_txn_event           (axi_write_txn_event),
    .trap_mcause                   (trap_mcause),
    .cycle_reason_onehot           (cycle_reason_onehot_dbg),
    .mcycle_count                  (mcycle_count_dbg),
    .retire_cycle_count            (retire_cycle_count),
    .load_use_cycle_count          (load_use_cycle_count),
    .icache_wait_cycle_count       (icache_wait_cycle_count),
    .dcache_wait_cycle_count       (dcache_wait_cycle_count),
    .control_redirect_cycle_count  (control_redirect_cycle_count),
    .trap_redirect_cycle_count     (trap_redirect_cycle_count),
    .mmio_wait_cycle_count         (mmio_wait_cycle_count),
    .pipe_fill_drain_cycle_count   (pipe_fill_drain_cycle_count),
    .other_cycle_count             (other_cycle_count),
    .minstret_count                (minstret_count_dbg),
    .icache_access_count           (icache_access_count),
    .icache_hit_count              (icache_hit_count),
    .icache_miss_count             (icache_miss_count),
    .dcache_read_access_count      (dcache_read_access_count),
    .dcache_read_hit_count         (dcache_read_hit_count),
    .dcache_read_miss_count        (dcache_read_miss_count),
    .dcache_write_access_count     (dcache_write_access_count),
    .dcache_write_hit_count        (dcache_write_hit_count),
    .dcache_write_miss_count       (dcache_write_miss_count),
    .icache_main_hit_count         (icache_main_hit_count),
    .icache_victim_hit_count       (icache_victim_hit_count),
    .icache_true_miss_count        (icache_true_miss_count),
    .dcache_main_hit_count         (dcache_main_hit_count),
    .dcache_victim_hit_count       (dcache_victim_hit_count),
    .dcache_true_miss_count        (dcache_true_miss_count),
    .control_redirect_event_count  (control_redirect_event_count),
    .mispredict_event_count        (mispredict_event_count),
    .conditional_branch_count      (conditional_branch_count),
    .branch_taken_count            (branch_taken_count),
    .branch_not_taken_count        (branch_not_taken_count),
    .branch_prediction_count       (branch_prediction_count),
    .branch_correct_prediction_count(branch_correct_prediction_count),
    .trap_event_count              (trap_event_count),
    .axi_read_txn_count            (axi_read_txn_count),
    .axi_write_txn_count           (axi_write_txn_count),
    .last_mcause                   (last_mcause)
);

apb_performance_monitor #(.PERF_COUNTERS_ENABLE(PERF_COUNTERS_ENABLE))
u_sysmon (
    .PCLK                          (clk),
    .PRESETn                       (reset_n),
    .PSEL                          (PSEL),
    .PENABLE                       (PENABLE),
    .PWRITE                        (PWRITE),
    .PSTRB                         (PSTRB),
    .PADDR                         (PADDR),
    .PWDATA                        (PWDATA),
    .PRDATA                        (PRDATA),
    .PREADY                        (PREADY),
    .PSLVERR                       (PSLVERR),
    .freeze_early                  (freeze_early),
    .counter_clear                 (counter_clear),
    .counter_freeze                (counter_freeze),
    .snapshot_valid_dbg            (snapshot_valid_dbg),
    .snapshot_sequence_dbg         (snapshot_sequence),
    .cycle_reason_onehot           (cycle_reason_onehot_dbg),
    .mcycle_count                  (mcycle_count_dbg),
    .retire_cycle_count            (retire_cycle_count),
    .load_use_cycle_count          (load_use_cycle_count),
    .icache_wait_cycle_count       (icache_wait_cycle_count),
    .dcache_wait_cycle_count       (dcache_wait_cycle_count),
    .control_redirect_cycle_count  (control_redirect_cycle_count),
    .trap_redirect_cycle_count     (trap_redirect_cycle_count),
    .mmio_wait_cycle_count         (mmio_wait_cycle_count),
    .pipe_fill_drain_cycle_count   (pipe_fill_drain_cycle_count),
    .other_cycle_count             (other_cycle_count),
    .minstret_count                (minstret_count_dbg),
    .icache_access_count           (icache_access_count),
    .icache_hit_count              (icache_hit_count),
    .icache_miss_count             (icache_miss_count),
    .dcache_read_access_count      (dcache_read_access_count),
    .dcache_read_hit_count         (dcache_read_hit_count),
    .dcache_read_miss_count        (dcache_read_miss_count),
    .dcache_write_access_count     (dcache_write_access_count),
    .dcache_write_hit_count        (dcache_write_hit_count),
    .dcache_write_miss_count       (dcache_write_miss_count),
    .icache_main_hit_count         (icache_main_hit_count),
    .icache_victim_hit_count       (icache_victim_hit_count),
    .icache_true_miss_count        (icache_true_miss_count),
    .dcache_main_hit_count         (dcache_main_hit_count),
    .dcache_victim_hit_count       (dcache_victim_hit_count),
    .dcache_true_miss_count        (dcache_true_miss_count),
    .control_redirect_event_count  (control_redirect_event_count),
    .mispredict_event_count        (mispredict_event_count),
    .conditional_branch_count      (conditional_branch_count),
    .branch_taken_count            (branch_taken_count),
    .branch_not_taken_count        (branch_not_taken_count),
    .branch_prediction_count       (branch_prediction_count),
    .branch_correct_prediction_count(branch_correct_prediction_count),
    .trap_event_count              (trap_event_count),
    .axi_read_txn_count            (axi_read_txn_count),
    .axi_write_txn_count           (axi_write_txn_count),
    .last_mcause                   (last_mcause),
    .bus_wr_err                    (bus_wr_err),
    .bus_wr_err_addr               (bus_wr_err_addr),
    .bus_wr_err_clear              (bus_wr_err_clear)
);

endmodule
