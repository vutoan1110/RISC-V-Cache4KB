// APB performance-monitor register bank.
// Reads take the snapshot bank when snapshot_valid=1, else the live bank.
// Commands are encoded values, so clear/snapshot/freeze ordering is unambiguous.
module apb_performance_monitor #(
    // 0 holds the snapshot registers at zero so synthesis removes them. See
    // perf_counters.v; the two are enabled together or not at all.
    parameter integer PERF_COUNTERS_ENABLE = 1
)(
    input  wire        PCLK,
    input  wire        PRESETn,
    input  wire        PSEL,
    input  wire        PENABLE,
    input  wire        PWRITE,
    input  wire [3:0]  PSTRB,
    input  wire [11:0] PADDR,
    input  wire [31:0] PWDATA,
    output reg  [31:0] PRDATA,
    output wire        PREADY,
    output wire        PSLVERR,

    // stop counting at request acceptance, before APB transport latency
    input  wire        freeze_early,
    output wire        counter_clear,
    output wire        counter_freeze,
    output wire        snapshot_valid_dbg,
    output wire [31:0] snapshot_sequence_dbg,

    input  wire [8:0]  cycle_reason_onehot,
    input  wire [31:0] mcycle_count,
    input  wire [31:0] retire_cycle_count,
    input  wire [31:0] load_use_cycle_count,
    input  wire [31:0] icache_wait_cycle_count,
    input  wire [31:0] dcache_wait_cycle_count,
    input  wire [31:0] control_redirect_cycle_count,
    input  wire [31:0] trap_redirect_cycle_count,
    input  wire [31:0] mmio_wait_cycle_count,
    input  wire [31:0] pipe_fill_drain_cycle_count,
    input  wire [31:0] other_cycle_count,
    input  wire [31:0] minstret_count,
    input  wire [31:0] icache_access_count,
    input  wire [31:0] icache_hit_count,
    input  wire [31:0] icache_miss_count,
    input  wire [31:0] dcache_read_access_count,
    input  wire [31:0] dcache_read_hit_count,
    input  wire [31:0] dcache_read_miss_count,
    input  wire [31:0] dcache_write_access_count,
    input  wire [31:0] dcache_write_hit_count,
    input  wire [31:0] dcache_write_miss_count,
    input  wire [31:0] icache_main_hit_count,
    input  wire [31:0] icache_victim_hit_count,
    input  wire [31:0] icache_true_miss_count,
    input  wire [31:0] dcache_main_hit_count,
    input  wire [31:0] dcache_victim_hit_count,
    input  wire [31:0] dcache_true_miss_count,
    input  wire [31:0] control_redirect_event_count,
    input  wire [31:0] mispredict_event_count,
    input  wire [31:0] conditional_branch_count,
    input  wire [31:0] branch_taken_count,
    input  wire [31:0] branch_not_taken_count,
    input  wire [31:0] branch_prediction_count,
    input  wire [31:0] branch_correct_prediction_count,
    input  wire [31:0] trap_event_count,
    input  wire [31:0] axi_read_txn_count,
    input  wire [31:0] axi_write_txn_count,
    input  wire [31:0] last_mcause,

    // Posted-write error state from cache_axi_master. Not a counter: it is
    // readable whether or not PERF_COUNTERS_ENABLE builds the counter bank.
    input  wire        bus_wr_err,
    input  wire [31:0] bus_wr_err_addr,
    output wire        bus_wr_err_clear
);

localparam [7:0] CMD_CLEAR_START       = 8'h01;
localparam [7:0] CMD_SNAPSHOT          = 8'h02;
localparam [7:0] CMD_FREEZE_SNAPSHOT   = 8'h03;
localparam [7:0] CMD_UNFREEZE          = 8'h04;
localparam [7:0] CMD_CLEAR_FROZEN      = 8'h05;
localparam [7:0] CMD_INVALIDATE_SNAPSHOT = 8'h06;

wire apb_rd = PSEL && PENABLE && !PWRITE;
wire apb_wr = PSEL && PENABLE && PWRITE;
wire ctrl_wr = apb_wr && (PADDR[7:0] == 8'h04) && PSTRB[0];
wire [7:0] command = PWDATA[7:0];
wire command_valid = (command == CMD_CLEAR_START) ||
                     (command == CMD_SNAPSHOT) ||
                     (command == CMD_FREEZE_SNAPSHOT) ||
                     (command == CMD_UNFREEZE) ||
                     (command == CMD_CLEAR_FROZEN) ||
                     (command == CMD_INVALIDATE_SNAPSHOT);
wire do_snapshot = ctrl_wr && ((command == CMD_SNAPSHOT) ||
                               (command == CMD_FREEZE_SNAPSHOT));
wire do_freeze_snapshot = ctrl_wr && (command == CMD_FREEZE_SNAPSHOT);
wire do_clear = ctrl_wr && ((command == CMD_CLEAR_START) ||
                            (command == CMD_CLEAR_FROZEN));
wire freeze_early_active = (freeze_early === 1'b1);

reg freeze_q;
reg snapshot_valid_q;
reg [31:0] snapshot_sequence_q;

reg [31:0] snap_mcycle;
reg [31:0] snap_retire_cycle;
reg [31:0] snap_load_use_cycle;
reg [31:0] snap_icache_wait_cycle;
reg [31:0] snap_dcache_wait_cycle;
reg [31:0] snap_control_redirect_cycle;
reg [31:0] snap_trap_redirect_cycle;
reg [31:0] snap_mmio_wait_cycle;
reg [31:0] snap_pipe_fill_drain_cycle;
reg [31:0] snap_other_cycle;
reg [31:0] snap_minstret;
reg [31:0] snap_icache_access;
reg [31:0] snap_icache_hit;
reg [31:0] snap_icache_miss;
reg [31:0] snap_dcache_read_access;
reg [31:0] snap_dcache_read_hit;
reg [31:0] snap_dcache_read_miss;
reg [31:0] snap_dcache_write_access;
reg [31:0] snap_dcache_write_hit;
reg [31:0] snap_dcache_write_miss;
reg [31:0] snap_icache_main_hit;
reg [31:0] snap_icache_victim_hit;
reg [31:0] snap_icache_true_miss;
reg [31:0] snap_dcache_main_hit;
reg [31:0] snap_dcache_victim_hit;
reg [31:0] snap_dcache_true_miss;
reg [31:0] snap_control_redirect_event;
reg [31:0] snap_mispredict_event;
reg [31:0] snap_conditional_branch;
reg [31:0] snap_branch_taken;
reg [31:0] snap_branch_not_taken;
reg [31:0] snap_branch_prediction;
reg [31:0] snap_branch_correct_prediction;
reg [31:0] snap_trap_event;
reg [31:0] snap_axi_read_txn;
reg [31:0] snap_axi_write_txn;
reg [31:0] snap_last_mcause;

assign PREADY = 1'b1;
// 0xAC bit 0 is write-1-to-clear for the bus write error; it is the only
// writable register besides the command register.
wire bus_err_wr = apb_wr && (PADDR[7:0] == 8'hAC) && PSTRB[0];
assign bus_wr_err_clear = bus_err_wr && PWDATA[0];
assign PSLVERR = apb_wr && !(ctrl_wr && command_valid) && !bus_err_wr;
assign counter_clear = do_clear;
assign counter_freeze = freeze_q || freeze_early_active || do_freeze_snapshot;
assign snapshot_valid_dbg = snapshot_valid_q;
assign snapshot_sequence_dbg = snapshot_sequence_q;

always @(posedge PCLK or negedge PRESETn) begin
    if(!PRESETn) begin
        freeze_q                    <= 1'b0;
        snapshot_valid_q            <= 1'b0;
        snapshot_sequence_q         <= 32'h0000_0000;
        snap_mcycle                 <= 32'h0000_0000;
        snap_retire_cycle           <= 32'h0000_0000;
        snap_load_use_cycle         <= 32'h0000_0000;
        snap_icache_wait_cycle      <= 32'h0000_0000;
        snap_dcache_wait_cycle      <= 32'h0000_0000;
        snap_control_redirect_cycle <= 32'h0000_0000;
        snap_trap_redirect_cycle    <= 32'h0000_0000;
        snap_mmio_wait_cycle        <= 32'h0000_0000;
        snap_pipe_fill_drain_cycle  <= 32'h0000_0000;
        snap_other_cycle            <= 32'h0000_0000;
        snap_minstret               <= 32'h0000_0000;
        snap_icache_access          <= 32'h0000_0000;
        snap_icache_hit             <= 32'h0000_0000;
        snap_icache_miss            <= 32'h0000_0000;
        snap_dcache_read_access     <= 32'h0000_0000;
        snap_dcache_read_hit        <= 32'h0000_0000;
        snap_dcache_read_miss       <= 32'h0000_0000;
        snap_dcache_write_access    <= 32'h0000_0000;
        snap_dcache_write_hit       <= 32'h0000_0000;
        snap_dcache_write_miss      <= 32'h0000_0000;
        snap_icache_main_hit        <= 32'h0000_0000;
        snap_icache_victim_hit      <= 32'h0000_0000;
        snap_icache_true_miss       <= 32'h0000_0000;
        snap_dcache_main_hit        <= 32'h0000_0000;
        snap_dcache_victim_hit      <= 32'h0000_0000;
        snap_dcache_true_miss       <= 32'h0000_0000;
        snap_control_redirect_event <= 32'h0000_0000;
        snap_mispredict_event       <= 32'h0000_0000;
        snap_conditional_branch     <= 32'h0000_0000;
        snap_branch_taken           <= 32'h0000_0000;
        snap_branch_not_taken       <= 32'h0000_0000;
        snap_branch_prediction      <= 32'h0000_0000;
        snap_branch_correct_prediction <= 32'h0000_0000;
        snap_trap_event             <= 32'h0000_0000;
        snap_axi_read_txn           <= 32'h0000_0000;
        snap_axi_write_txn          <= 32'h0000_0000;
        snap_last_mcause            <= 32'h0000_0000;
    end
    else begin
        if(freeze_early_active)
            freeze_q <= 1'b1;

        if(ctrl_wr && command_valid) begin
            case(command)
                CMD_CLEAR_START: begin
                    freeze_q         <= 1'b0;
                    snapshot_valid_q <= 1'b0;
                end
                CMD_FREEZE_SNAPSHOT: freeze_q <= 1'b1;
                CMD_UNFREEZE:        freeze_q <= 1'b0;
                CMD_CLEAR_FROZEN: begin
                    freeze_q         <= 1'b1;
                    snapshot_valid_q <= 1'b0;
                end
                CMD_INVALIDATE_SNAPSHOT: snapshot_valid_q <= 1'b0;
                default: ;
            endcase
        end

        if(do_snapshot && (PERF_COUNTERS_ENABLE != 0)) begin
            snapshot_valid_q            <= 1'b1;
            snapshot_sequence_q         <= snapshot_sequence_q + 1'b1;
            snap_mcycle                 <= mcycle_count;
            snap_retire_cycle           <= retire_cycle_count;
            snap_load_use_cycle         <= load_use_cycle_count;
            snap_icache_wait_cycle      <= icache_wait_cycle_count;
            snap_dcache_wait_cycle      <= dcache_wait_cycle_count;
            snap_control_redirect_cycle <= control_redirect_cycle_count;
            snap_trap_redirect_cycle    <= trap_redirect_cycle_count;
            snap_mmio_wait_cycle        <= mmio_wait_cycle_count;
            snap_pipe_fill_drain_cycle  <= pipe_fill_drain_cycle_count;
            snap_other_cycle            <= other_cycle_count;
            snap_minstret               <= minstret_count;
            snap_icache_access          <= icache_access_count;
            snap_icache_hit             <= icache_hit_count;
            snap_icache_miss            <= icache_miss_count;
            snap_dcache_read_access     <= dcache_read_access_count;
            snap_dcache_read_hit        <= dcache_read_hit_count;
            snap_dcache_read_miss       <= dcache_read_miss_count;
            snap_dcache_write_access    <= dcache_write_access_count;
            snap_dcache_write_hit       <= dcache_write_hit_count;
            snap_dcache_write_miss      <= dcache_write_miss_count;
            snap_icache_main_hit        <= icache_main_hit_count;
            snap_icache_victim_hit      <= icache_victim_hit_count;
            snap_icache_true_miss       <= icache_true_miss_count;
            snap_dcache_main_hit        <= dcache_main_hit_count;
            snap_dcache_victim_hit      <= dcache_victim_hit_count;
            snap_dcache_true_miss       <= dcache_true_miss_count;
            snap_control_redirect_event <= control_redirect_event_count;
            snap_mispredict_event       <= mispredict_event_count;
            snap_conditional_branch     <= conditional_branch_count;
            snap_branch_taken           <= branch_taken_count;
            snap_branch_not_taken       <= branch_not_taken_count;
            snap_branch_prediction      <= branch_prediction_count;
            snap_branch_correct_prediction <= branch_correct_prediction_count;
            snap_trap_event             <= trap_event_count;
            snap_axi_read_txn           <= axi_read_txn_count;
            snap_axi_write_txn          <= axi_write_txn_count;
            snap_last_mcause            <= last_mcause;
        end
    end
end

always @(*) begin
    PRDATA = 32'h0000_0000;
    if(apb_rd) begin
        case(PADDR[7:0])
            // ABI version 2 adds 0xAC/0xB0, the bus write error registers.
            8'h00: PRDATA = 32'h5338_0002; // "S8", ABI version 2
            8'h04: begin
                PRDATA[0]    = freeze_q;
                PRDATA[1]    = snapshot_valid_q;
                PRDATA[2]    = snapshot_valid_q; // counter reads use snapshot
                PRDATA[15:8] = snapshot_sequence_q[7:0];
                PRDATA[31:16]= 16'h0008;
            end
            8'h08: PRDATA = snapshot_sequence_q;
            8'h0C: PRDATA = snapshot_valid_q ? snap_last_mcause : last_mcause;
            8'h10: PRDATA = snapshot_valid_q ? snap_mcycle : mcycle_count;
            8'h14: PRDATA = snapshot_valid_q ? snap_retire_cycle : retire_cycle_count;
            8'h18: PRDATA = snapshot_valid_q ? snap_load_use_cycle : load_use_cycle_count;
            8'h1C: PRDATA = snapshot_valid_q ? snap_icache_wait_cycle : icache_wait_cycle_count;
            8'h20: PRDATA = snapshot_valid_q ? snap_dcache_wait_cycle : dcache_wait_cycle_count;
            8'h24: PRDATA = snapshot_valid_q ? snap_control_redirect_cycle : control_redirect_cycle_count;
            8'h28: PRDATA = snapshot_valid_q ? snap_trap_redirect_cycle : trap_redirect_cycle_count;
            8'h2C: PRDATA = snapshot_valid_q ? snap_mmio_wait_cycle : mmio_wait_cycle_count;
            8'h30: PRDATA = snapshot_valid_q ? snap_pipe_fill_drain_cycle : pipe_fill_drain_cycle_count;
            8'h34: PRDATA = snapshot_valid_q ? snap_other_cycle : other_cycle_count;
            8'h40: PRDATA = snapshot_valid_q ? snap_minstret : minstret_count;
            8'h44: PRDATA = snapshot_valid_q ? snap_icache_access : icache_access_count;
            8'h48: PRDATA = snapshot_valid_q ? snap_icache_hit : icache_hit_count;
            8'h4C: PRDATA = snapshot_valid_q ? snap_icache_miss : icache_miss_count;
            8'h50: PRDATA = snapshot_valid_q ? snap_dcache_read_access : dcache_read_access_count;
            8'h54: PRDATA = snapshot_valid_q ? snap_dcache_read_hit : dcache_read_hit_count;
            8'h58: PRDATA = snapshot_valid_q ? snap_dcache_read_miss : dcache_read_miss_count;
            8'h5C: PRDATA = snapshot_valid_q ? snap_dcache_write_access : dcache_write_access_count;
            8'h60: PRDATA = snapshot_valid_q ? snap_dcache_write_hit : dcache_write_hit_count;
            8'h64: PRDATA = snapshot_valid_q ? snap_dcache_write_miss : dcache_write_miss_count;
            8'h68: PRDATA = snapshot_valid_q ? snap_control_redirect_event : control_redirect_event_count;
            8'h6C: PRDATA = snapshot_valid_q ? snap_mispredict_event : mispredict_event_count;
            8'h70: PRDATA = snapshot_valid_q ? snap_trap_event : trap_event_count;
            8'h74: PRDATA = snapshot_valid_q ? snap_axi_read_txn : axi_read_txn_count;
            8'h78: PRDATA = snapshot_valid_q ? snap_axi_write_txn : axi_write_txn_count;
            8'h7C: PRDATA = {23'h0, cycle_reason_onehot};
            8'h80: PRDATA = snapshot_valid_q ? snap_conditional_branch : conditional_branch_count;
            8'h84: PRDATA = snapshot_valid_q ? snap_branch_taken : branch_taken_count;
            8'h88: PRDATA = snapshot_valid_q ? snap_branch_not_taken : branch_not_taken_count;
            8'h8C: PRDATA = snapshot_valid_q ? snap_branch_prediction : branch_prediction_count;
            8'h90: PRDATA = snapshot_valid_q ? snap_branch_correct_prediction : branch_correct_prediction_count;
            8'h94: PRDATA = snapshot_valid_q ? snap_icache_main_hit : icache_main_hit_count;
            8'h98: PRDATA = snapshot_valid_q ? snap_icache_victim_hit : icache_victim_hit_count;
            8'h9C: PRDATA = snapshot_valid_q ? snap_icache_true_miss : icache_true_miss_count;
            8'hA0: PRDATA = snapshot_valid_q ? snap_dcache_main_hit : dcache_main_hit_count;
            8'hA4: PRDATA = snapshot_valid_q ? snap_dcache_victim_hit : dcache_victim_hit_count;
            8'hA8: PRDATA = snapshot_valid_q ? snap_dcache_true_miss : dcache_true_miss_count;
            8'hAC: PRDATA = {31'h0, bus_wr_err};
            8'hB0: PRDATA = bus_wr_err_addr;
            default: PRDATA = 32'h0000_0000;
        endcase
    end
end

endmodule
