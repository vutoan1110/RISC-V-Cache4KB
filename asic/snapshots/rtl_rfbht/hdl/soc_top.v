module soc_top #(
    parameter ICACHE_LINE_COUNT   = 64,
    parameter DCACHE_LINE_COUNT   = 64,
    parameter ICACHE_MISS_PENALTY = 2,
    parameter DCACHE_MISS_PENALTY = 2,
    parameter IMEM_DEPTH          = 2048,   // R14 2026-09-29: 16 KiB unified RAM, was 1024+1024 words (RAM16K_CHANGES.md)
    parameter DMEM_DEPTH          = 2048,
    parameter MEMFILE             = "riscv_full.hex",
    parameter integer BRANCH_PREDICT_ENABLE = 1,
    parameter integer BHT_ENTRIES = 256,
    parameter integer CACHE_CONFIG = 0,
    parameter integer VICTIM_ENTRIES = 4,
    parameter integer CACHE_LINE_WORDS = 4,
    // R16 (review M1): 1 = DSE / N-way caches answer main-array hits in ST_LOOKUP (no effect on CACHE_CONFIG 0).
    parameter integer CACHE_FAST_HIT = 0,
    // 1 builds the performance counter bank and the APB snapshot registers;
    // 0 removes them so the core's own area can be measured on its own.
    parameter integer PERF_COUNTERS_ENABLE = 1,
    // Depth of the instruction cache's L0 hot buffer. Each entry is a whole
    // line in flip-flops; see icache_controller.v.
    parameter integer L0_ENTRIES = 8
) (
    input  wire        clk,
    input  wire        reset_n,
    input  wire        key1_n,
    input  wire        uart_rx,
    output wire        uart_tx,
    output wire [6:0]  HEX0,
    output wire [6:0]  HEX1,
    output wire [6:0]  HEX2,
    output wire [6:0]  HEX3,
    output wire [6:0]  HEX4,
    output wire [6:0]  HEX5,
    output wire [6:0]  HEX6,
    output wire [6:0]  HEX7,
    output wire [7:0]  LEDR,
    output wire [7:0]  LCD_DATA,
    output wire        LCD_EN,
    output wire        LCD_RS,
    output wire        LCD_RW,
    output wire        LCD_ON,
    output wire        LCD_BLON
);

wire cts_n = 1'b0;

wire        if_req_valid;
wire [31:0] if_req_addr;
wire        if_req_ready;
wire        if_rsp_valid;
wire [31:0] if_rsp_data;
wire        if_rsp_error;

wire        d_req_valid;
wire        d_req_write;
wire [31:0] d_req_addr;
wire [31:0] d_req_wdata;
wire [3:0]  d_req_wstrb;
wire        d_req_ready;
wire        d_rsp_valid;
wire [31:0] d_rsp_rdata;
wire        d_rsp_error;

wire        irq_timer;
wire        trap_taken_dbg;
wire [31:0] mcause_dbg;
wire [31:0] mepc_dbg;
wire [31:0] mtvec_dbg;
wire [31:0] mcycle_dbg;
wire [31:0] minstret_dbg;
wire [31:0] load_stall_dbg;
wire [31:0] branch_flush_dbg;
wire [31:0] pc_f_dbg;
wire        if_wait_dbg;
wire        d_wait_dbg;
wire        if_error_dbg;
wire        d_error_dbg;
wire [31:0] control_redirect_dbg;
wire        retire_event_dbg;
wire        load_use_stall_event_dbg;
wire        control_redirect_event_dbg;
wire        mispredict_event_dbg;
wire        conditional_branch_event_dbg;
wire        branch_taken_event_dbg;
wire        branch_not_taken_event_dbg;
wire        branch_prediction_event_dbg;
wire        branch_correct_prediction_event_dbg;
wire        pipeline_nonempty_dbg;
// Architectural retirement trace (internal; tests observe these wires).
wire        retire_valid;
wire [63:0] retire_order;
wire [31:0] retire_pc;
wire [31:0] retire_pc_next;
wire [31:0] retire_instr;
wire [4:0]  retire_rs1_addr;
wire [31:0] retire_rs1_rdata;
wire [4:0]  retire_rs2_addr;
wire [31:0] retire_rs2_rdata;
wire [4:0]  retire_rd_addr;
wire [31:0] retire_rd_wdata;
wire        retire_rd_we;
wire        retire_mem_valid;
wire        retire_mem_write;
wire [31:0] retire_mem_addr;
wire [31:0] retire_mem_wdata;
wire [3:0]  retire_mem_wstrb;
wire        retire_trap;
wire        retire_interrupt;
wire [8:0]  cycle_reason_onehot_dbg;
wire [31:0] perf_mcycle_count_dbg;
wire [31:0] perf_minstret_count_dbg;
wire        perf_snapshot_valid_dbg;

// aliases for the waveform tests
wire [31:0] pc_f       = pc_f_dbg;
wire [31:0] instr      = if_rsp_data;
wire        mem_wr_m   = d_req_valid && d_req_write;
wire        mem_rd_m   = d_req_valid && !d_req_write;
wire [31:0] wr_data_m  = d_req_wdata;

wire [31:0] icache_hit_count;
wire [31:0] icache_miss_count;
wire [31:0] icache_access_count;
wire        icache_access_event;
wire        icache_hit_event;
wire        icache_miss_event;
wire [31:0] icache_main_hit_count, icache_victim_hit_count, icache_true_miss_count;
wire        icache_main_hit_event, icache_victim_hit_event, icache_true_miss_event;
wire [31:0] dcache_hit_count;
wire [31:0] dcache_miss_count;
wire [31:0] dcache_access_count;
wire [31:0] dcache_read_count;
wire [31:0] dcache_write_count;
wire [31:0] dcache_read_hit_count;
wire [31:0] dcache_read_miss_count;
wire [31:0] dcache_write_hit_count;
wire [31:0] dcache_write_miss_count;
wire        dcache_read_access_event, dcache_read_hit_event, dcache_read_miss_event;
wire        dcache_write_access_event, dcache_write_hit_event, dcache_write_miss_event;
wire [31:0] dcache_main_hit_count, dcache_victim_hit_count, dcache_true_miss_count;
wire        dcache_main_hit_event, dcache_victim_hit_event, dcache_true_miss_event;

riscv_core_native #(
    .BRANCH_PREDICT_ENABLE(BRANCH_PREDICT_ENABLE),
    .BHT_ENTRIES(BHT_ENTRIES)
) u_core (
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
    .trap_taken       (trap_taken_dbg),
    .mcause_dbg       (mcause_dbg),
    .mepc_dbg         (mepc_dbg),
    .mtvec_dbg        (mtvec_dbg),
    .mcycle_dbg       (mcycle_dbg),
    .minstret_dbg     (minstret_dbg),
    .load_stall_dbg   (load_stall_dbg),
    .branch_flush_dbg (branch_flush_dbg),
    .control_redirect_dbg (control_redirect_dbg),
    .retire_event_dbg (retire_event_dbg),
    .load_use_stall_event_dbg (load_use_stall_event_dbg),
    .control_redirect_event_dbg (control_redirect_event_dbg),
    .mispredict_event_dbg (mispredict_event_dbg),
    .conditional_branch_event_dbg (conditional_branch_event_dbg),
    .branch_taken_event_dbg (branch_taken_event_dbg),
    .branch_not_taken_event_dbg (branch_not_taken_event_dbg),
    .branch_prediction_event_dbg (branch_prediction_event_dbg),
    .branch_correct_prediction_event_dbg (branch_correct_prediction_event_dbg),
    .pipeline_nonempty_dbg (pipeline_nonempty_dbg),
    .retire_valid      (retire_valid),
    .retire_order      (retire_order),
    .retire_pc         (retire_pc),
    .retire_pc_next    (retire_pc_next),
    .retire_instr      (retire_instr),
    .retire_rs1_addr   (retire_rs1_addr),
    .retire_rs1_rdata  (retire_rs1_rdata),
    .retire_rs2_addr   (retire_rs2_addr),
    .retire_rs2_rdata  (retire_rs2_rdata),
    .retire_rd_addr    (retire_rd_addr),
    .retire_rd_wdata   (retire_rd_wdata),
    .retire_rd_we      (retire_rd_we),
    .retire_mem_valid  (retire_mem_valid),
    .retire_mem_write  (retire_mem_write),
    .retire_mem_addr   (retire_mem_addr),
    .retire_mem_wdata  (retire_mem_wdata),
    .retire_mem_wstrb  (retire_mem_wstrb),
    .retire_trap       (retire_trap),
    .retire_interrupt  (retire_interrupt),
    .pc_f_dbg         (pc_f_dbg),
    .if_wait_dbg      (if_wait_dbg),
    .d_wait_dbg       (d_wait_dbg),
    .if_error_dbg     (if_error_dbg),
    .d_error_dbg      (d_error_dbg)
);

// -------------------------------------------------------------------------
// Instruction-cache frontend.
// -------------------------------------------------------------------------
wire        icache_refill_req_valid;
wire [31:0] icache_refill_req_addr;
wire        icache_refill_req_ready;
wire        icache_refill_rsp_valid;
wire [31:0] icache_refill_rsp_data;
wire        icache_refill_rsp_last;
wire        icache_refill_rsp_error;

icache #(
    .LINE_COUNT     (ICACHE_LINE_COUNT),
    .CACHE_CONFIG   (CACHE_CONFIG),
    .LINE_WORDS     (CACHE_LINE_WORDS),
    .VICTIM_ENTRIES (VICTIM_ENTRIES),
    .L0_ENTRIES     (L0_ENTRIES),
    .FAST_HIT       (CACHE_FAST_HIT)
) u_icache (
    .clk              (clk),
    .reset_n          (reset_n),
    .req_valid        (if_req_valid),
    .req_addr         (if_req_addr),
    .req_ready        (if_req_ready),
    .rsp_valid        (if_rsp_valid),
    .rsp_data         (if_rsp_data),
    .rsp_error        (if_rsp_error),
    .refill_req_valid (icache_refill_req_valid),
    .refill_req_addr  (icache_refill_req_addr),
    .refill_req_ready (icache_refill_req_ready),
    .refill_rsp_valid (icache_refill_rsp_valid),
    .refill_rsp_data  (icache_refill_rsp_data),
    .refill_rsp_last  (icache_refill_rsp_last),
    .refill_rsp_error (icache_refill_rsp_error),
    .access_count     (icache_access_count),
    .hit_count        (icache_hit_count),
    .miss_count       (icache_miss_count)
    ,.access_event    (icache_access_event)
    ,.hit_event       (icache_hit_event)
    ,.miss_event      (icache_miss_event)
    ,.main_hit_count  (icache_main_hit_count)
    ,.victim_hit_count(icache_victim_hit_count)
    ,.true_miss_count (icache_true_miss_count)
    ,.main_hit_event  (icache_main_hit_event)
    ,.victim_hit_event(icache_victim_hit_event)
    ,.true_miss_event (icache_true_miss_event)
);

// -------------------------------------------------------------------------
// Address decode and data-cache frontend.
// -------------------------------------------------------------------------
wire data_sel_cacheable;
wire data_sel_mmio;
wire data_sel_sysmon;
wire data_sel_unmapped;

soc_address_decoder u_data_addr_dec (
    .addr          (d_req_addr),
    .sel_cacheable (data_sel_cacheable),
    .sel_mmio      (data_sel_mmio),
    // The per-peripheral selects are decoded again inside the APB bridge, which
    // is what drives PSEL; at this level only cacheable/MMIO routing is needed.
    .sel_uart      (),
    .sel_display   (),
    .sel_timer     (),
    .sel_sysmon    (data_sel_sysmon),
    .sel_unmapped  (data_sel_unmapped)
);

wire        dcache_req_ready;
wire        dcache_rsp_valid;
wire [31:0] dcache_rsp_rdata;
wire        dcache_rsp_error;
wire        dcache_refill_req_valid;
wire [31:0] dcache_refill_req_addr;
wire        dcache_refill_req_ready;
wire        dcache_refill_rsp_valid;
wire [31:0] dcache_refill_rsp_data;
wire        dcache_refill_rsp_last;
wire        dcache_refill_rsp_error;
wire        dcache_mem_wr_valid;
wire [31:0] dcache_mem_wr_addr;
wire [31:0] dcache_mem_wr_data;
wire [3:0]  dcache_mem_wr_strb;
wire        dcache_mem_wr_ready;
wire        dcache_mem_wr_rsp_valid;
wire        dcache_mem_wr_rsp_error;

reg         d_route_pending_q;
reg         d_route_mmio_q;

wire dcache_cpu_req_valid = d_req_valid && !d_route_pending_q &&
                            data_sel_cacheable;
wire mmio_cpu_req_valid = d_req_valid && !d_route_pending_q && data_sel_mmio;

dcache #(
    .LINE_COUNT     (DCACHE_LINE_COUNT),
    .CACHE_CONFIG   (CACHE_CONFIG),
    .LINE_WORDS     (CACHE_LINE_WORDS),
    .VICTIM_ENTRIES (VICTIM_ENTRIES),
    .FAST_HIT       (CACHE_FAST_HIT)
) u_dcache (
    .clk                  (clk),
    .reset_n              (reset_n),
    .req_valid            (dcache_cpu_req_valid),
    .req_write            (d_req_write),
    .req_addr             (d_req_addr),
    .req_wdata            (d_req_wdata),
    .req_wstrb            (d_req_wstrb),
    .req_ready            (dcache_req_ready),
    .rsp_valid            (dcache_rsp_valid),
    .rsp_rdata            (dcache_rsp_rdata),
    .rsp_error            (dcache_rsp_error),
    .refill_req_valid     (dcache_refill_req_valid),
    .refill_req_addr      (dcache_refill_req_addr),
    .refill_req_ready     (dcache_refill_req_ready),
    .refill_rsp_valid     (dcache_refill_rsp_valid),
    .refill_rsp_data      (dcache_refill_rsp_data),
    .refill_rsp_last      (dcache_refill_rsp_last),
    .refill_rsp_error     (dcache_refill_rsp_error),
    .mem_wr_valid         (dcache_mem_wr_valid),
    .mem_wr_addr          (dcache_mem_wr_addr),
    .mem_wr_data          (dcache_mem_wr_data),
    .mem_wr_strb          (dcache_mem_wr_strb),
    .mem_wr_ready         (dcache_mem_wr_ready),
    .mem_wr_rsp_valid     (dcache_mem_wr_rsp_valid),
    .mem_wr_rsp_error     (dcache_mem_wr_rsp_error),
    .access_count         (dcache_access_count),
    .read_count           (dcache_read_count),
    .write_count          (dcache_write_count),
    .hit_count            (dcache_hit_count),
    .miss_count           (dcache_miss_count),
    .read_hit_count       (dcache_read_hit_count),
    .read_miss_count      (dcache_read_miss_count),
    .write_hit_count      (dcache_write_hit_count),
    .write_miss_count     (dcache_write_miss_count)
    ,.read_access_event   (dcache_read_access_event)
    ,.read_hit_event      (dcache_read_hit_event)
    ,.read_miss_event     (dcache_read_miss_event)
    ,.write_access_event  (dcache_write_access_event)
    ,.write_hit_event     (dcache_write_hit_event)
    ,.write_miss_event    (dcache_write_miss_event)
    ,.main_hit_count      (dcache_main_hit_count)
    ,.victim_hit_count    (dcache_victim_hit_count)
    ,.true_miss_count     (dcache_true_miss_count)
    ,.main_hit_event      (dcache_main_hit_event)
    ,.victim_hit_event    (dcache_victim_hit_event)
    ,.true_miss_event     (dcache_true_miss_event)
);

// -------------------------------------------------------------------------
// One global AXI4 Full master and one shared program/data AXI RAM.
// -------------------------------------------------------------------------
wire [31:0] axi_araddr;
wire [7:0]  axi_arlen;
wire [2:0]  axi_arsize;
wire [1:0]  axi_arburst;
wire        axi_arvalid;
wire        axi_arready;
wire [31:0] axi_rdata;
wire [1:0]  axi_rresp;
wire        axi_rlast;
wire        axi_rvalid;
wire        axi_rready;
wire [31:0] axi_awaddr;
wire [7:0]  axi_awlen;
wire [2:0]  axi_awsize;
wire [1:0]  axi_awburst;
wire        axi_awvalid;
wire        axi_awready;
wire [31:0] axi_wdata;
wire [3:0]  axi_wstrb;
wire        axi_wlast;
wire        axi_wvalid;
wire        axi_wready;
wire [1:0]  axi_bresp;
wire        axi_bvalid;
wire        axi_bready;

wire        axi_memory_busy;
wire [31:0] axi_read_txn_count;
wire [31:0] axi_write_txn_count;
wire        axi_read_txn_event;
wire        axi_write_txn_event;

// Posted-write error state: set by cache_axi_master on a failing BRESP,
// read and cleared through the sysmon registers 0xAC / 0xB0.
wire        bus_wr_err;
wire [31:0] bus_wr_err_addr;
wire        bus_wr_err_clear;

cache_axi_master #(.LINE_WORDS(CACHE_LINE_WORDS)) u_cache_axi_master (
    .clk                    (clk),
    .reset_n                (reset_n),
    .i_refill_req_valid     (icache_refill_req_valid),
    .i_refill_req_addr      (icache_refill_req_addr),
    .i_refill_req_ready     (icache_refill_req_ready),
    .i_refill_rsp_valid     (icache_refill_rsp_valid),
    .i_refill_rsp_data      (icache_refill_rsp_data),
    .i_refill_rsp_last      (icache_refill_rsp_last),
    .i_refill_rsp_error     (icache_refill_rsp_error),
    .d_refill_req_valid     (dcache_refill_req_valid),
    .d_refill_req_addr      (dcache_refill_req_addr),
    .d_refill_req_ready     (dcache_refill_req_ready),
    .d_refill_rsp_valid     (dcache_refill_rsp_valid),
    .d_refill_rsp_data      (dcache_refill_rsp_data),
    .d_refill_rsp_last      (dcache_refill_rsp_last),
    .d_refill_rsp_error     (dcache_refill_rsp_error),
    .d_write_req_valid      (dcache_mem_wr_valid),
    .d_write_req_addr       (dcache_mem_wr_addr),
    .d_write_req_data       (dcache_mem_wr_data),
    .d_write_req_strb       (dcache_mem_wr_strb),
    .d_write_req_ready      (dcache_mem_wr_ready),
    .d_write_rsp_valid      (dcache_mem_wr_rsp_valid),
    .d_write_rsp_error      (dcache_mem_wr_rsp_error),
    .m_axi_araddr           (axi_araddr),
    .m_axi_arlen            (axi_arlen),
    .m_axi_arsize           (axi_arsize),
    .m_axi_arburst          (axi_arburst),
    .m_axi_arvalid          (axi_arvalid),
    .m_axi_arready          (axi_arready),
    .m_axi_rdata            (axi_rdata),
    .m_axi_rresp            (axi_rresp),
    .m_axi_rlast            (axi_rlast),
    .m_axi_rvalid           (axi_rvalid),
    .m_axi_rready           (axi_rready),
    .m_axi_awaddr           (axi_awaddr),
    .m_axi_awlen            (axi_awlen),
    .m_axi_awsize           (axi_awsize),
    .m_axi_awburst          (axi_awburst),
    .m_axi_awvalid          (axi_awvalid),
    .m_axi_awready          (axi_awready),
    .m_axi_wdata            (axi_wdata),
    .m_axi_wstrb            (axi_wstrb),
    .m_axi_wlast            (axi_wlast),
    .m_axi_wvalid           (axi_wvalid),
    .m_axi_wready           (axi_wready),
    .m_axi_bresp            (axi_bresp),
    .m_axi_bvalid           (axi_bvalid),
    .m_axi_bready           (axi_bready),
    .busy                   (axi_memory_busy),
    .active_source          (),
    .axi_read_txn_count     (axi_read_txn_count),
    .axi_write_txn_count    (axi_write_txn_count)
    ,.axi_read_txn_event    (axi_read_txn_event)
    ,.axi_write_txn_event   (axi_write_txn_event)
    ,.wr_err                (bus_wr_err)
    ,.wr_err_addr           (bus_wr_err_addr)
    ,.wr_err_clear          (bus_wr_err_clear)
);

// axi_ram_32 test hooks are constant here (tests drive it directly)
wire [7:0] axi_test_ar_stall_cycles = 8'd0;
wire [7:0] axi_test_r_first_delay_cycles = ICACHE_MISS_PENALTY[7:0];
wire [7:0] axi_test_r_gap_cycles = 8'd0;
wire [7:0] axi_test_aw_stall_cycles = 8'd0;
wire [7:0] axi_test_w_stall_cycles = 8'd0;
wire [7:0] axi_test_b_delay_cycles = DCACHE_MISS_PENALTY[7:0];
wire       axi_test_rresp_error = 1'b0;
wire       axi_test_bresp_error = 1'b0;
wire [31:0] axi_ram_read_burst_count;
wire [31:0] axi_ram_write_txn_count;

axi_ram_32 #(
    .DEPTH_WORDS (IMEM_DEPTH + DMEM_DEPTH),
    .MEMFILE     (MEMFILE)
) u_axi_ram (
    .clk                       (clk),
    .reset_n                   (reset_n),
    .s_axi_araddr              (axi_araddr),
    .s_axi_arlen               (axi_arlen),
    .s_axi_arsize              (axi_arsize),
    .s_axi_arburst             (axi_arburst),
    .s_axi_arvalid             (axi_arvalid),
    .s_axi_arready             (axi_arready),
    .s_axi_rdata               (axi_rdata),
    .s_axi_rresp               (axi_rresp),
    .s_axi_rlast               (axi_rlast),
    .s_axi_rvalid              (axi_rvalid),
    .s_axi_rready              (axi_rready),
    .s_axi_awaddr              (axi_awaddr),
    .s_axi_awlen               (axi_awlen),
    .s_axi_awsize              (axi_awsize),
    .s_axi_awburst             (axi_awburst),
    .s_axi_awvalid             (axi_awvalid),
    .s_axi_awready             (axi_awready),
    .s_axi_wdata               (axi_wdata),
    .s_axi_wstrb               (axi_wstrb),
    .s_axi_wlast               (axi_wlast),
    .s_axi_wvalid              (axi_wvalid),
    .s_axi_wready              (axi_wready),
    .s_axi_bresp               (axi_bresp),
    .s_axi_bvalid              (axi_bvalid),
    .s_axi_bready              (axi_bready),
    .test_ar_stall_cycles      (axi_test_ar_stall_cycles),
    .test_r_first_delay_cycles (axi_test_r_first_delay_cycles),
    .test_r_gap_cycles         (axi_test_r_gap_cycles),
    .test_aw_stall_cycles      (axi_test_aw_stall_cycles),
    .test_w_stall_cycles       (axi_test_w_stall_cycles),
    .test_b_delay_cycles       (axi_test_b_delay_cycles),
    .test_rresp_error          (axi_test_rresp_error),
    .test_bresp_error          (axi_test_bresp_error),
    .read_burst_count          (axi_ram_read_burst_count),
    .write_txn_count           (axi_ram_write_txn_count)
);

// -------------------------------------------------------------------------
// Native MMIO -> AXI4-Lite master -> AXI4-Lite-to-APB bridge.
// -------------------------------------------------------------------------
wire        mmio_req_ready;
wire        mmio_rsp_valid;
wire [31:0] mmio_rsp_rdata;
wire        mmio_rsp_error;

wire [31:0] axil_awaddr;
wire        axil_awvalid;
wire        axil_awready;
wire [31:0] axil_wdata;
wire [3:0]  axil_wstrb;
wire        axil_wvalid;
wire        axil_wready;
wire [1:0]  axil_bresp;
wire        axil_bvalid;
wire        axil_bready;
wire [31:0] axil_araddr;
wire        axil_arvalid;
wire        axil_arready;
wire [31:0] axil_rdata;
wire [1:0]  axil_rresp;
wire        axil_rvalid;
wire        axil_rready;

native_axi_lite_master u_mmio_axil_master (
    .clk             (clk),
    .reset_n         (reset_n),
    .req_valid       (mmio_cpu_req_valid),
    .req_write       (d_req_write),
    .req_addr        (d_req_addr),
    .req_wdata       (d_req_wdata),
    .req_wstrb       (d_req_wstrb),
    .req_ready       (mmio_req_ready),
    .rsp_valid       (mmio_rsp_valid),
    .rsp_rdata       (mmio_rsp_rdata),
    .rsp_error       (mmio_rsp_error),
    .m_axil_awaddr   (axil_awaddr),
    .m_axil_awvalid  (axil_awvalid),
    .m_axil_awready  (axil_awready),
    .m_axil_wdata    (axil_wdata),
    .m_axil_wstrb    (axil_wstrb),
    .m_axil_wvalid   (axil_wvalid),
    .m_axil_wready   (axil_wready),
    .m_axil_bresp    (axil_bresp),
    .m_axil_bvalid   (axil_bvalid),
    .m_axil_bready   (axil_bready),
    .m_axil_araddr   (axil_araddr),
    .m_axil_arvalid  (axil_arvalid),
    .m_axil_arready  (axil_arready),
    .m_axil_rdata    (axil_rdata),
    .m_axil_rresp    (axil_rresp),
    .m_axil_rvalid   (axil_rvalid),
    .m_axil_rready   (axil_rready)
);

wire        PSEL_bus;
wire        PENABLE_bus;
wire        PWRITE_bus;
wire [3:0]  PSTRB_bus;
wire [31:0] PADDR_bus;
wire [31:0] PWDATA_bus;
wire [31:0] PRDATA_bus;
wire        PREADY_bus;
wire        PSLVERR_bus;
wire [31:0] apb_transfer_count;

axi_lite_to_apb u_axil2apb (
    .clk                (clk),
    .reset_n            (reset_n),
    .s_axil_awaddr      (axil_awaddr),
    .s_axil_awvalid     (axil_awvalid),
    .s_axil_awready     (axil_awready),
    .s_axil_wdata       (axil_wdata),
    .s_axil_wstrb       (axil_wstrb),
    .s_axil_wvalid      (axil_wvalid),
    .s_axil_wready      (axil_wready),
    .s_axil_bresp       (axil_bresp),
    .s_axil_bvalid      (axil_bvalid),
    .s_axil_bready      (axil_bready),
    .s_axil_araddr      (axil_araddr),
    .s_axil_arvalid     (axil_arvalid),
    .s_axil_arready     (axil_arready),
    .s_axil_rdata       (axil_rdata),
    .s_axil_rresp       (axil_rresp),
    .s_axil_rvalid      (axil_rvalid),
    .s_axil_rready      (axil_rready),
    .PSEL               (PSEL_bus),
    .PENABLE            (PENABLE_bus),
    .PWRITE             (PWRITE_bus),
    .PSTRB              (PSTRB_bus),
    .PADDR              (PADDR_bus),
    .PWDATA             (PWDATA_bus),
    .PRDATA             (PRDATA_bus),
    .PREADY             (PREADY_bus),
    .PSLVERR            (PSLVERR_bus),
    .apb_transfer_count (apb_transfer_count)
);

// Latch the accepted route so response routing ignores the live address.
wire d_selected_rsp_valid = d_route_mmio_q ? mmio_rsp_valid : dcache_rsp_valid;
wire d_route_accept = !d_route_pending_q && d_req_valid && d_req_ready &&
                      !data_sel_unmapped;
wire d_accept_rsp_valid = data_sel_mmio ? mmio_rsp_valid : dcache_rsp_valid;
wire d_same_cycle_rsp = d_route_accept && d_accept_rsp_valid;

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        d_route_pending_q <= 1'b0;
        d_route_mmio_q    <= 1'b0;
    end
    else begin
        if(d_route_accept) begin
            // no phantom pending when the response already came same-cycle
            d_route_pending_q <= !d_accept_rsp_valid;
            d_route_mmio_q    <= data_sel_mmio;
        end
        else if(d_route_pending_q && d_selected_rsp_valid) begin
            d_route_pending_q <= 1'b0;
        end
    end
end

assign d_req_ready = d_route_pending_q ? 1'b0 :
                     data_sel_cacheable ? dcache_req_ready :
                     data_sel_mmio      ? mmio_req_ready   :
                     data_sel_unmapped  ? 1'b1             : 1'b0;

assign d_rsp_valid = d_route_pending_q ? d_selected_rsp_valid :
                     (d_same_cycle_rsp ||
                      (d_req_valid && data_sel_unmapped));
assign d_rsp_rdata = d_route_pending_q ?
                     (d_route_mmio_q ? mmio_rsp_rdata : dcache_rsp_rdata) :
                     (d_same_cycle_rsp ?
                      (data_sel_mmio ? mmio_rsp_rdata : dcache_rsp_rdata) :
                      32'h0000_0000);
assign d_rsp_error = d_route_pending_q ?
                     (d_route_mmio_q ? mmio_rsp_error : dcache_rsp_error) :
                     (d_same_cycle_rsp ?
                      (data_sel_mmio ? mmio_rsp_error : dcache_rsp_error) :
                      (d_req_valid && data_sel_unmapped));

// -------------------------------------------------------------------------
// APB address decode and peripherals.
// -------------------------------------------------------------------------
wire apb_sel_cacheable_unused;
wire apb_sel_mmio_unused;
wire apb_sel_uart;
wire apb_sel_disp;
wire apb_sel_timer;
wire apb_sel_sysmon;

soc_address_decoder u_apb_addr_dec (
    .addr          (PADDR_bus),
    .sel_cacheable (apb_sel_cacheable_unused),
    .sel_mmio      (apb_sel_mmio_unused),
    .sel_uart      (apb_sel_uart),
    .sel_display   (apb_sel_disp),
    .sel_timer     (apb_sel_timer),
    .sel_sysmon    (apb_sel_sysmon),
    .sel_unmapped  ()
);

wire [31:0] PRDATA_uart;
wire [31:0] PRDATA_disp;
wire [31:0] PRDATA_timer;
wire [31:0] PRDATA_sysmon;
wire        PREADY_uart;
wire        PREADY_disp;
wire        PREADY_timer;
wire        PREADY_sysmon;
wire        PSLVERR_uart;
wire        PSLVERR_disp;
wire        PSLVERR_timer;
wire        PSLVERR_sysmon;

assign PRDATA_bus  = apb_sel_uart   ? PRDATA_uart   :
                     apb_sel_disp   ? PRDATA_disp   :
                     apb_sel_timer  ? PRDATA_timer  :
                     apb_sel_sysmon ? PRDATA_sysmon : 32'h0000_0000;
assign PREADY_bus  = apb_sel_uart   ? PREADY_uart   :
                     apb_sel_disp   ? PREADY_disp   :
                     apb_sel_timer  ? PREADY_timer  :
                     apb_sel_sysmon ? PREADY_sysmon : 1'b1;
assign PSLVERR_bus = apb_sel_uart   ? PSLVERR_uart   :
                     apb_sel_disp   ? PSLVERR_disp   :
                     apb_sel_timer  ? PSLVERR_timer  :
                     apb_sel_sysmon ? PSLVERR_sysmon : 1'b1;

uart_apb u_uart (
    .clk      (clk),
    .reset_n  (reset_n),
    .pclk     (clk),
    .preset_n (reset_n),
    .psel     (PSEL_bus && apb_sel_uart),
    .penable  (PENABLE_bus && apb_sel_uart),
    .pwrite   (PWRITE_bus),
    .pstrb    (PSTRB_bus),
    .paddr    (PADDR_bus[11:0]),
    .pwdata   (PWDATA_bus),
    .rx       (uart_rx),
    .cts_n    (cts_n),
    .pready   (PREADY_uart),
    .pslverr  (PSLVERR_uart),
    .prdata   (PRDATA_uart),
    .tx       (uart_tx),
    .rts_n    ()   // flow control is not wired to a pin on this board
);

wire [31:0] disp_value;
wire [31:0] disp_ctrl;
wire [7:0]  disp_led;

apb_display_regs u_disp (
    .PCLK       (clk),
    .PRESETn    (reset_n),
    .PSEL       (PSEL_bus && apb_sel_disp),
    .PENABLE    (PENABLE_bus && apb_sel_disp),
    .PWRITE     (PWRITE_bus),
    .PSTRB      (PSTRB_bus),
    .PADDR      (PADDR_bus[11:0]),
    .PWDATA     (PWDATA_bus),
    .PRDATA     (PRDATA_disp),
    .PREADY     (PREADY_disp),
    .PSLVERR    (PSLVERR_disp),
    .disp_value (disp_value),
    .disp_led   (disp_led),
    .disp_ctrl  (disp_ctrl),
    .key1_n     (key1_n)
);

apb_timer u_timer (
    .PCLK    (clk),
    .PRESETn (reset_n),
    .PSEL    (PSEL_bus && apb_sel_timer),
    .PENABLE (PENABLE_bus && apb_sel_timer),
    .PWRITE  (PWRITE_bus),
    .PSTRB   (PSTRB_bus),
    .PADDR   (PADDR_bus[11:0]),
    .PWDATA  (PWDATA_bus),
    .PRDATA  (PRDATA_timer),
    .PREADY  (PREADY_timer),
    .PSLVERR (PSLVERR_timer),
    .irq     (irq_timer)
);

wire perf_mmio_wait = d_wait_dbg &&
                      ((d_route_pending_q && d_route_mmio_q) ||
                       (!d_route_pending_q && data_sel_mmio));
wire perf_dcache_wait = d_wait_dbg &&
                        ((d_route_pending_q && !d_route_mmio_q) ||
                         (!d_route_pending_q && data_sel_cacheable));
wire perf_freeze_early = d_req_valid && d_req_ready && data_sel_sysmon &&
                         d_req_write && (d_req_addr[7:0] == 8'h04) &&
                         (d_req_wdata[7:0] == 8'h03);

performance_observability #(.PERF_COUNTERS_ENABLE(PERF_COUNTERS_ENABLE))
u_observability (
    .clk                           (clk),
    .reset_n                       (reset_n),
    .retire_event                  (retire_event_dbg),
    .load_use_stall                (load_use_stall_event_dbg),
    .icache_wait                   (if_wait_dbg),
    .dcache_wait                   (perf_dcache_wait),
    .control_redirect_event        (control_redirect_event_dbg),
    .trap_redirect_event           (trap_taken_dbg),
    .mmio_wait                     (perf_mmio_wait),
    .pipeline_nonempty             (pipeline_nonempty_dbg),
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
    .mispredict_event              (mispredict_event_dbg),
    .conditional_branch_event      (conditional_branch_event_dbg),
    .branch_taken_event            (branch_taken_event_dbg),
    .branch_not_taken_event        (branch_not_taken_event_dbg),
    .branch_prediction_event       (branch_prediction_event_dbg),
    .branch_correct_prediction_event(branch_correct_prediction_event_dbg),
    .axi_read_txn_event            (axi_read_txn_event),
    .axi_write_txn_event           (axi_write_txn_event),
    .trap_mcause                   (32'h8000_0007),
    .PSEL                          (PSEL_bus && apb_sel_sysmon),
    .PENABLE                       (PENABLE_bus && apb_sel_sysmon),
    .PWRITE                        (PWRITE_bus),
    .PSTRB                         (PSTRB_bus),
    .PADDR                         (PADDR_bus[11:0]),
    .PWDATA                        (PWDATA_bus),
    .PRDATA                        (PRDATA_sysmon),
    .PREADY                        (PREADY_sysmon),
    .PSLVERR                       (PSLVERR_sysmon),
    .freeze_early                  (perf_freeze_early),
    .cycle_reason_onehot_dbg       (cycle_reason_onehot_dbg),
    .mcycle_count_dbg              (perf_mcycle_count_dbg),
    .minstret_count_dbg            (perf_minstret_count_dbg),
    .counter_freeze_dbg            (),
    .snapshot_valid_dbg            (perf_snapshot_valid_dbg),
    .bus_wr_err                    (bus_wr_err),
    .bus_wr_err_addr               (bus_wr_err_addr),
    .bus_wr_err_clear              (bus_wr_err_clear)
);

assign LEDR = disp_led;

hex7seg_decoder u_hex0 (.hex(disp_value[ 3: 0]), .seg(HEX0));
hex7seg_decoder u_hex1 (.hex(disp_value[ 7: 4]), .seg(HEX1));
hex7seg_decoder u_hex2 (.hex(disp_value[11: 8]), .seg(HEX2));
hex7seg_decoder u_hex3 (.hex(disp_value[15:12]), .seg(HEX3));
hex7seg_decoder u_hex4 (.hex(disp_value[19:16]), .seg(HEX4));
hex7seg_decoder u_hex5 (.hex(disp_value[23:20]), .seg(HEX5));
hex7seg_decoder u_hex6 (.hex(disp_value[27:24]), .seg(HEX6));
hex7seg_decoder u_hex7 (.hex(disp_value[31:28]), .seg(HEX7));

lcd_1602_hex #(
    .CLK_HZ(50_000_000)
) u_lcd (
    .clk        (clk),
    .reset_n    (reset_n),
    .disp_value (disp_value),
    .LCD_DATA   (LCD_DATA),
    .LCD_EN     (LCD_EN),
    .LCD_RS     (LCD_RS),
    .LCD_RW     (LCD_RW),
    .LCD_ON     (LCD_ON),
    .LCD_BLON   (LCD_BLON)
);

endmodule
