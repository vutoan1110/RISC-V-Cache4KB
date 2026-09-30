module datapath #(
    parameter integer BRANCH_PREDICT_ENABLE = 1,
    parameter integer BHT_ENTRIES = 256
)(
    input             clk             , 
    input             reset_n         ,
    input             irq_timer       ,
    input      [1:0]  result_src_m    ,  // R9b
    input      [1:0]  result_src_w    ,
    input             alu_src_e       ,
    input             reg_wr_e        ,  // R9a
    input             reg_wr_m        ,
    input             reg_wr_w        ,
    input      [2:0]  imm_src_d       ,
    input      [3:0]  alu_ctrl_e      ,
    input             jump_e          ,
    output reg [31:0] pc_f            ,
    input      [31:0] instr           ,
    output reg [31:0] alu_result_m    ,
    output reg [31:0] wr_data_m       ,
    output reg [31:0] instr_d         ,
    output reg        valid_d         ,
    output            flush_e         ,
    input      [31:0] rd_data         ,
    input      [1:0]  result_src_e    ,
    output            trap_taken      ,
    output     [31:0] mcause_dbg      ,
    output     [31:0] mepc_dbg        ,
    output     [2:0]  mem_funct3_m    ,
    output     [31:0] mtvec_dbg       ,
    input             stall_pipe      ,
    output     [31:0] mcycle_dbg      ,
    output     [31:0] minstret_dbg    ,
    output     [31:0] load_stall_dbg  ,
    output     [31:0] branch_flush_dbg,
    output     [31:0] control_redirect_dbg,
    output            retire_event_dbg,
    output            load_use_stall_event_dbg,
    output            control_redirect_event_dbg,
    output            mispredict_event_dbg,
    output            conditional_branch_event_dbg,
    output            branch_taken_event_dbg,
    output            branch_not_taken_event_dbg,
    output            branch_prediction_event_dbg,
    output            branch_correct_prediction_event_dbg,
    output            pipeline_nonempty_dbg,
    // Architectural retirement trace (RVFI-like, not RVFI-compliant).
    output            retire_valid,
    output     [63:0] retire_order,
    output     [31:0] retire_pc,
    output     [31:0] retire_pc_next,
    output     [31:0] retire_instr,
    output     [4:0]  retire_rs1_addr,
    output     [31:0] retire_rs1_rdata,
    output     [4:0]  retire_rs2_addr,
    output     [31:0] retire_rs2_rdata,
    output     [4:0]  retire_rd_addr,
    output     [31:0] retire_rd_wdata,
    output            retire_rd_we,
    output            retire_mem_valid,
    output            retire_mem_write,
    output     [31:0] retire_mem_addr,
    output     [31:0] retire_mem_wdata,
    output     [3:0]  retire_mem_wstrb,
    output            retire_trap,
    output            retire_interrupt,
    input             use_rs1_d,
    input             use_rs2_d
);

reg  [31:0] instr_e;
reg  [31:0] instr_m;
reg  [31:0] instr_w;
reg         valid_e;
reg         valid_m;
reg         valid_w;
reg  [31:0] pc_d;
reg  [31:0] pc_e;
reg  [31:0] pc_m;
reg  [31:0] pc_w;
wire [31:0] pc_next;
wire [31:0] pc_plus4_f;
reg  [31:0] pc_plus4_d;
reg  [31:0] pc_plus4_e;
reg  [31:0] pc_plus4_m;
reg  [31:0] pc_plus4_w;
reg  [31:0] architectural_next_pc_m;
reg  [31:0] architectural_next_pc_w;
reg  [31:0] pc_target_e;
wire [31:0] immext_d;
reg  [31:0] immext_e;
wire [31:0] src_a;
wire [31:0] src_b;
reg  [31:0] src_a_e;
reg  [31:0] src_b_e;
wire [31:0] result_w;
wire [31:0] alu_result_raw;
wire [31:0] exec_result_e;
reg  [31:0] alu_result_w;
wire        branch_taken_e;
reg  [31:0] wr_data_e;
reg  [31:0] rd_data_w;
reg  [31:0] rd_data_final;
reg  [31:0] store_data_w;
reg  [1:0]  forward_a_e;   // R9a: registered, see below
reg  [1:0]  forward_b_e;
wire        stall_f;
wire        stall_d;
wire        flush_d;
wire        pc_src_e;
wire        is_mret_e;
wire        irq_request;
wire        irq_enabled;
wire        irq_accept;
wire [31:0] irq_resume_pc;
wire        load_use_hazard;
reg         irq_pending;
reg  [1:0]  mem_byte_offset_m;

// Operand metadata, captured after EX forwarding.
reg         use_rs1_e_meta;
reg         use_rs2_e_meta;
reg  [4:0]  rs1_addr_m;
reg  [4:0]  rs1_addr_w;
reg  [4:0]  rs2_addr_m;
reg  [4:0]  rs2_addr_w;
reg  [31:0] rs1_rdata_m;
reg  [31:0] rs1_rdata_w;
reg  [31:0] rs2_rdata_m;
reg  [31:0] rs2_rdata_w;
reg  [63:0] retire_order_q;

// Branch prediction: Fetch
localparam integer BHT_INDEX_BITS = $clog2(BHT_ENTRIES);
wire        bht_pred_f;
wire [BHT_INDEX_BITS-1:0] bht_index_f;
wire [1:0]  bht_state_f;
wire        is_branch_f;
wire        is_jal_f;
wire        pred_taken_f;
wire [31:0] predicted_target_f;
wire [31:0] pred_target_f;
wire [31:0] b_imm_f;
wire [31:0] j_imm_f;
wire        predict_redirect_f;

// Branch prediction: Decode (latched)
reg         predict_taken_d;
reg  [31:0] predicted_target_d;

// Branch prediction: Execute (checked)
reg         predict_taken_e;
reg  [31:0] predicted_target_e;
reg         is_jal_e;
wire        is_branch_e;
wire        is_jalr_e;
wire        mispredict_e;
wire        branch_redirect_e;
wire        branch_resolve_fire;
wire [31:0] recovery_target_e;
wire        branch_mispredict_e;
wire [31:0] branch_recovery_pc;
wire [31:0] architectural_next_pc_e;

reg  [31:0] upper_m;
reg  [31:0] upper_w;
reg         is_upper_m;    // R9c: registered at E->M, see below
reg         is_link_m;
wire [31:0] upper_e;
wire [31:0] forward_result_m;
wire [31:0] forward_src_a_e;
wire [31:0] forward_src_b_e;
wire [31:0] fix_wr_data;
wire        is_csr_e;
wire [11:0] csr_addr_e;
reg  [31:0] csr_rdata_e;
reg  [31:0] csr_wdata_e;
reg  [31:0] csr_mstatus;
reg  [31:0] csr_mie;
reg  [31:0] csr_mtvec;
reg  [31:0] csr_mepc;
reg  [31:0] csr_mcause;
reg  [31:0] csr_mcycle;
reg  [31:0] csr_minstret;
reg  [31:0] load_stall_count;
reg  [31:0] control_redirect_count;
reg  [1:0] load_byte_offset_w;
reg [7:0]  load_byte;
reg [15:0] load_half;

wire [31:0] retire_store_lane_data;
wire [3:0]  retire_store_lane_strb;

assign mcause_dbg       = csr_mcause;
assign mepc_dbg         = csr_mepc;
assign mtvec_dbg        = csr_mtvec;
assign mcycle_dbg       = csr_mcycle;
assign minstret_dbg     = csr_minstret;
assign load_stall_dbg   = load_stall_count;
// alias kept for compatibility (covers mispredict, JALR, mret redirects)
assign branch_flush_dbg           = control_redirect_count;
assign control_redirect_dbg       = control_redirect_count;
assign retire_event_dbg           = !stall_pipe && valid_w;
assign load_use_stall_event_dbg   = load_use_hazard;
assign control_redirect_event_dbg = !stall_pipe && pc_src_e;
assign conditional_branch_event_dbg        = branch_resolve_fire;
assign branch_taken_event_dbg              = branch_resolve_fire && branch_taken_e;
assign branch_not_taken_event_dbg          = branch_resolve_fire && !branch_taken_e;
// BRANCH_PREDICT_ENABLE is an integer parameter, so using it directly as a
// condition mixes a 32-bit value into one-bit logic. BP_ON states the
// intent once, in one bit.
localparam BP_ON = (BRANCH_PREDICT_ENABLE != 0);
assign branch_prediction_event_dbg         = BP_ON && branch_resolve_fire;
assign branch_correct_prediction_event_dbg = BP_ON && branch_resolve_fire && !mispredict_e;
assign mispredict_event_dbg                = BP_ON && branch_resolve_fire && mispredict_e;
assign pipeline_nonempty_dbg      = valid_d || valid_e || valid_m || valid_w;
assign mem_funct3_m = valid_m ? instr_m[14:12] : 3'b000;

// retire pulse == minstret event; payload valid only while retire_valid
assign retire_valid     = !stall_pipe && valid_w;
assign retire_order     = retire_order_q;
assign retire_pc        = retire_valid ? pc_w : 32'h0000_0000;
assign retire_pc_next   = retire_valid ? architectural_next_pc_w : 32'h0000_0000;
assign retire_instr     = retire_valid ? instr_w : 32'h0000_0000;
assign retire_rs1_addr  = retire_valid ? rs1_addr_w : 5'd0;
assign retire_rs1_rdata = retire_valid ? rs1_rdata_w : 32'h0000_0000;
assign retire_rs2_addr  = retire_valid ? rs2_addr_w : 5'd0;
assign retire_rs2_rdata = retire_valid ? rs2_rdata_w : 32'h0000_0000;
assign retire_rd_addr   = retire_valid ? instr_w[11:7] : 5'd0;
assign retire_rd_we     = retire_valid && reg_wr_w && (instr_w[11:7] != 5'd0);
assign retire_rd_wdata  = retire_rd_we ? result_w : 32'h0000_0000;
assign retire_mem_valid = retire_valid && ((instr_w[6:0] == 7'b0000011) ||
                                           (instr_w[6:0] == 7'b0100011));
assign retire_mem_write = retire_mem_valid && (instr_w[6:0] == 7'b0100011);
assign retire_mem_addr  = retire_mem_valid ? alu_result_w : 32'h0000_0000;
assign retire_store_lane_data =
    (instr_w[14:12] == 3'b000) ?
        ({24'h0, store_data_w[7:0]} << (8 * alu_result_w[1:0])) :
    (instr_w[14:12] == 3'b001) ?
        ({16'h0, store_data_w[15:0]} << (8 * alu_result_w[1:0])) :
        store_data_w;
assign retire_store_lane_strb =
    (instr_w[14:12] == 3'b000) ? (4'b0001 << alu_result_w[1:0]) :
    (instr_w[14:12] == 3'b001) ? (4'b0011 << alu_result_w[1:0]) :
                                 4'b1111;
assign retire_mem_wdata = retire_mem_write ? retire_store_lane_data : 32'h0000_0000;
assign retire_mem_wstrb = retire_mem_write ? retire_store_lane_strb : 4'b0000;
assign retire_trap      = 1'b0;   // no synchronous exceptions
assign retire_interrupt = irq_accept;

// Pipeline valid + instruction registers.
// valid_* = occupancy; a bubble is invalid even though its instr reg is 0.
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        instr_d         <= 32'h0000_0000;
        instr_e         <= 32'h0000_0000;
        instr_m         <= 32'h0000_0000;
        instr_w         <= 32'h0000_0000;
        valid_d         <= 1'b0;
        valid_e         <= 1'b0;
        valid_m         <= 1'b0;
        valid_w         <= 1'b0;
        predict_taken_e <= 1'b0;
        predicted_target_e <= 32'h0000_0000;
        is_jal_e        <= 1'b0;
        use_rs1_e_meta  <= 1'b0;
        use_rs2_e_meta  <= 1'b0;
    end
    else if(!stall_pipe) begin
        // flush beats a decode hold (needed when IRQ hits during load-use)
        if(flush_d) begin
            instr_d <= 32'h0000_0000;
            valid_d <= 1'b0;
        end
        else if(stall_d) begin
            instr_d <= instr_d;
            valid_d <= valid_d;
        end
        else begin
            instr_d <= instr;
            valid_d <= 1'b1;
        end

        if(flush_e) begin
            instr_e         <= 32'h0000_0000;
            valid_e         <= 1'b0;
            predict_taken_e <= 1'b0;
            predicted_target_e <= 32'h0000_0000;
            is_jal_e        <= 1'b0;
            use_rs1_e_meta  <= 1'b0;
            use_rs2_e_meta  <= 1'b0;
        end
        else begin
            instr_e         <= instr_d;
            valid_e         <= valid_d;
            predict_taken_e <= predict_taken_d;
            predicted_target_e <= predicted_target_d;
            is_jal_e        <= valid_d && (instr_d[6:0] == 7'b1101111);
            use_rs1_e_meta  <= valid_d && use_rs1_d;
            use_rs2_e_meta  <= valid_d && use_rs2_d;
        end

        instr_m <= instr_e;
        valid_m <= valid_e;
        instr_w <= instr_m;
        valid_w <= valid_m;
    end
end

assign pc_plus4_f = pc_f + 4 ;
assign is_mret_e  = valid_e && (instr_e == 32'h30200073);
assign is_csr_e   = valid_e && (instr_e[6:0] == 7'b1110011) &&
                    (instr_e[14:12] != 3'b000);
assign csr_addr_e = instr_e[31:20];

always @(posedge clk or negedge reset_n) begin
    if(!reset_n)
        load_byte_offset_w <= 2'b00;
    else begin
        if(!stall_pipe)
            load_byte_offset_w <= mem_byte_offset_m;
    end
end

always @(*) begin
    case(csr_addr_e)
        12'h300: csr_rdata_e = csr_mstatus;
        12'h304: csr_rdata_e = csr_mie;
        12'h305: csr_rdata_e = csr_mtvec;
        12'h341: csr_rdata_e = csr_mepc;
        12'h342: csr_rdata_e = csr_mcause;
        12'hB00: csr_rdata_e = csr_mcycle;
        12'hB02: csr_rdata_e = csr_minstret;
        default: csr_rdata_e = 32'h0000_0000;
    endcase
end

always @(*) begin
    case(instr_e[14:12])
        3'b001: csr_wdata_e = forward_src_a_e;
        3'b010: csr_wdata_e = csr_rdata_e | forward_src_a_e;
        3'b011: csr_wdata_e = csr_rdata_e & ~forward_src_a_e;
        default: csr_wdata_e = csr_rdata_e;
    endcase
end

always @(*) begin
    case(instr_e[6:0])
        7'b1100011: pc_target_e = pc_e + immext_e;
        7'b1101111: pc_target_e = pc_e + immext_e;
        7'b1100111: pc_target_e = (forward_src_a_e + immext_e) & ~32'b1;
        default: begin
            if(is_mret_e) pc_target_e = csr_mepc;
            else          pc_target_e = pc_e + immext_e;
        end
    endcase
end

// --- Fetch-stage branch prediction ('instr' is the combinational icache output)
assign is_branch_f = (instr[6:0] == 7'b1100011);
assign is_jal_f    = (instr[6:0] == 7'b1101111);

// B/J immediates rebuilt here (extend.v runs a stage later)
assign b_imm_f = {{20{instr[31]}}, instr[7], instr[30:25], instr[11:8], 1'b0};
assign j_imm_f = {{12{instr[31]}}, instr[19:12], instr[20], instr[30:21], 1'b0};
// R7 (NHAT_KY_RTL 2026-09-25): the same value as
//     pc_f + (is_jal_f ? j_imm_f : b_imm_f)
// restructured for timing. 'instr' comes from the icache SRAM, whose read data
// launches on the FALLING clock edge (OpenRAM), so this path has half a cycle;
// written as above, the imm mux sat in front of a 32-bit carry chain.
// Above the immediate's own bits, every bit of b_imm_f/j_imm_f is the sign
// instr[31], so the high part of the sum is pc_hi, pc_hi+1 or pc_hi-1, all
// taken from pc_f alone (early). Only the low add waits for 'instr': 12 bits
// for B, and for J a 12-bit add plus an 8-bit carry-select. Both targets are
// built side by side and chosen by is_jal_f last. The selects are written as
// AND-OR, not '?:', so that Yosys opt_share cannot fold the parallel adders
// back into one adder behind an input mux (it only merges cells that drive a
// common $mux/$pmux).
wire [12:0] b_lo_f       = {1'b0, pc_f[11:0]} + {1'b0, b_imm_f[11:0]};
wire [19:0] pc_hi20_inc  = pc_f[31:12] + 20'd1;
wire [19:0] pc_hi20_dec  = pc_f[31:12] - 20'd1;
wire        b_hi_keep    = (b_lo_f[12] == instr[31]);
wire        b_hi_up      = b_lo_f[12] & ~instr[31];
wire        b_hi_down    = ~b_lo_f[12] & instr[31];
wire [31:0] b_target_f   = {({20{b_hi_keep}} & pc_f[31:12]) |
                            ({20{b_hi_up}}   & pc_hi20_inc) |
                            ({20{b_hi_down}} & pc_hi20_dec),
                            b_lo_f[11:0]};

wire [12:0] j_lo_f       = {1'b0, pc_f[11:0]} + {1'b0, j_imm_f[11:0]};
wire [8:0]  j_mid0_f     = {1'b0, pc_f[19:12]} + {1'b0, j_imm_f[19:12]};
wire [8:0]  j_mid1_f     = {1'b0, pc_f[19:12]} + {1'b0, j_imm_f[19:12]} + 9'd1;
wire [8:0]  j_mid_f      = ({9{~j_lo_f[12]}} & j_mid0_f) | ({9{j_lo_f[12]}} & j_mid1_f);
wire [11:0] pc_hi12_inc  = pc_f[31:20] + 12'd1;
wire [11:0] pc_hi12_dec  = pc_f[31:20] - 12'd1;
wire        j_hi_keep    = (j_mid_f[8] == instr[31]);
wire        j_hi_up      = j_mid_f[8] & ~instr[31];
wire        j_hi_down    = ~j_mid_f[8] & instr[31];
wire [31:0] j_target_f   = {({12{j_hi_keep}} & pc_f[31:20]) |
                            ({12{j_hi_up}}   & pc_hi12_inc) |
                            ({12{j_hi_down}} & pc_hi12_dec),
                            j_mid_f[7:0], j_lo_f[11:0]};

assign predicted_target_f = ({32{is_jal_f}} & j_target_f) | ({32{~is_jal_f}} & b_target_f);
assign pred_target_f = predicted_target_f;

// conditional prediction is parameterised; JAL always redirects at Fetch
assign pred_taken_f    = BP_ON && is_branch_f && bht_pred_f;

// --- Execute-stage: check the prediction
assign is_branch_e        = valid_e && (instr_e[6:0] == 7'b1100011);
assign is_jalr_e          = valid_e && jump_e && !is_jal_e;
assign mispredict_e       = BP_ON && is_branch_e &&
                            ((predict_taken_e != branch_taken_e) ||
                             (predict_taken_e && branch_taken_e &&
                              (predicted_target_e != pc_target_e)));
assign branch_mispredict_e = mispredict_e;
assign recovery_target_e   = branch_taken_e ? pc_target_e : pc_plus4_e;
assign branch_recovery_pc  = recovery_target_e;
assign branch_resolve_fire = is_branch_e && !stall_pipe;
assign architectural_next_pc_e = is_branch_e ?
                                    (branch_taken_e ? pc_target_e : pc_plus4_e) :
                                  ((is_jal_e || is_jalr_e || is_mret_e) ?
                                    pc_target_e : pc_plus4_e);

// BP_OFF: redirect every taken branch at EX. BP_ON: only on a mismatch.
assign branch_redirect_e = BP_ON ? mispredict_e :
                                                    (is_branch_e && branch_taken_e);

// JALR / MRET are not predicted at Fetch
assign pc_src_e = branch_redirect_e | is_jalr_e | is_mret_e;

// latch the timer pulse so it survives a global stall; an EX redirect wins
assign irq_request   = irq_pending || irq_timer;
assign irq_enabled   = csr_mstatus[3] && csr_mie[7];
assign irq_accept    = irq_request && irq_enabled && !stall_pipe && !pc_src_e;
assign irq_resume_pc = valid_d ? pc_d : pc_f;
assign trap_taken    = irq_accept;

always @(posedge clk or negedge reset_n) begin
    if(!reset_n)
        irq_pending <= 1'b0;
    else if(irq_accept)
        irq_pending <= 1'b0;
    else if(irq_timer)
        irq_pending <= 1'b1;
end

// --- PC mux. Priority: IRQ > EX redirect > Fetch prediction > PC+4.
// During a load-use stall, hold the Fetch redirect (it re-fires when it lifts).
assign predict_redirect_f = (is_jal_f || pred_taken_f) && !stall_d;

assign pc_next = irq_accept         ? csr_mtvec :
                 pc_src_e            ? (branch_redirect_e ? recovery_target_e : pc_target_e) :
                 predict_redirect_f  ? predicted_target_f :
                                       pc_plus4_f;

// --- BHT Instance ---
generate
    if(BP_ON) begin : g_bp_on
        bht_2bit #(
            .BHT_ENTRIES(BHT_ENTRIES),
            .BHT_RESET_STATE(2'b01)
        ) u_bht (
            .clk           (clk),
            .reset_n       (reset_n),
            .fetch_pc      (pc_f),
            .fetch_index   (bht_index_f),
            .fetch_state   (bht_state_f),
            .predict_taken (bht_pred_f),
            .update_en     (branch_resolve_fire),
            .update_pc     (pc_e),
            .actual_taken  (branch_taken_e)
        );
    end
    else begin : g_bp_off
        assign bht_index_f = pc_f[BHT_INDEX_BITS+1:2];
        assign bht_state_f = 2'b01;
        assign bht_pred_f  = 1'b0;
    end
endgenerate

// --- PC + pipeline registers ---
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        pc_f       <= 0 ;
        pc_d       <= 0 ;
        pc_e       <= 0 ;
        pc_m       <= 0 ;
        pc_w       <= 0 ;
        pc_plus4_d <= 0 ;
        pc_plus4_e <= 0 ;
        pc_plus4_m <= 0 ;
        pc_plus4_w <= 0 ;
        predict_taken_d <= 0 ;
        predicted_target_d <= 0 ;
        architectural_next_pc_m <= 0 ;
        architectural_next_pc_w <= 0 ;
    end
    else begin
        if(!stall_pipe) begin
            if(irq_accept)      pc_f <= csr_mtvec;
            else if(!stall_f)   pc_f <= pc_next;
            else                pc_f <= pc_f;

            if(flush_d) begin
                pc_d            <= 32'h0000_0000;
                pc_plus4_d      <= 32'h0000_0000;
                predict_taken_d <= 1'b0;
                predicted_target_d <= 32'h0000_0000;
            end
            else if(stall_d) begin
                pc_d            <= pc_d;
                pc_plus4_d      <= pc_plus4_d;
                predict_taken_d <= predict_taken_d;
                predicted_target_d <= predicted_target_d;
            end
            else begin
                pc_d            <= pc_f;
                pc_plus4_d      <= pc_plus4_f;
                predict_taken_d <= pred_taken_f;
                predicted_target_d <= pred_target_f;
            end

            if(!flush_e) begin
                pc_e       <= pc_d       ;
                pc_plus4_e <= pc_plus4_d ;
            end
            else begin
                pc_e       <= 0 ;
                pc_plus4_e <= 0 ;
            end

            pc_plus4_m <= pc_plus4_e ;
            pc_plus4_w <= pc_plus4_m ;
            pc_m       <= pc_e;
            pc_w       <= pc_m;
            architectural_next_pc_m <= architectural_next_pc_e;
            architectural_next_pc_w <= architectural_next_pc_m;
        end
    end
end

// pipeline the forwarded source operands
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        rs1_addr_m  <= 5'd0;
        rs1_addr_w  <= 5'd0;
        rs2_addr_m  <= 5'd0;
        rs2_addr_w  <= 5'd0;
        rs1_rdata_m <= 32'h0000_0000;
        rs1_rdata_w <= 32'h0000_0000;
        rs2_rdata_m <= 32'h0000_0000;
        rs2_rdata_w <= 32'h0000_0000;
    end
    else if(!stall_pipe) begin
        rs1_addr_m  <= use_rs1_e_meta ? instr_e[19:15] : 5'd0;
        rs2_addr_m  <= use_rs2_e_meta ? instr_e[24:20] : 5'd0;
        rs1_rdata_m <= use_rs1_e_meta ? forward_src_a_e : 32'h0000_0000;
        rs2_rdata_m <= use_rs2_e_meta ? forward_src_b_e : 32'h0000_0000;
        rs1_addr_w  <= rs1_addr_m;
        rs2_addr_w  <= rs2_addr_m;
        rs1_rdata_w <= rs1_rdata_m;
        rs2_rdata_w <= rs2_rdata_m;
    end
end

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        immext_e <= 0 ;
    end
    else begin
        if(!stall_pipe) begin
            if(!flush_e) immext_e <= immext_d ;
            else         immext_e <= 0        ;
        end
    end
end

extend extend(
    .instr_d  (instr_d[31:7]) ,
    .immsrc_d (imm_src_d)     ,
    .immext_d (immext_d)
);

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        src_a_e <= 0 ;
        src_b_e <= 0 ;
    end
    else begin
        if(!stall_pipe) begin
            if(!flush_e) begin
                src_a_e <= src_a ;
                src_b_e <= src_b ;
            end
            else begin
                src_a_e <= 0 ;
                src_b_e <= 0 ;
            end
        end
    end
end

regfile regfile(
    .clk   (clk)            , 
    .we    (reg_wr_w && valid_w && !stall_pipe),
    .rs1   (instr_d[19:15]) ,
    .rs2   (instr_d[24:20]) ,
    .rd    (instr_w[11:7])  ,
    .wd    (result_w)       ,
    .rd1_d (src_a)          ,
    .rd2_d (src_b)
);

// ---------------------------------------------------------------------------
// R9 (NHAT_KY_RTL 2026-09-26): decodes moved off the ss-critical paths.
// Each register below is loaded under exactly the enable (!stall_pipe), flush
// and reset of the registers it replaces the decode of, so it holds the same
// value as the old combinational decode in every cycle; the simulation-only
// checker at the end of this block compares them every cycle.

// R9a -- EX forwarding selects. At an edge with !stall_pipe the pipeline does
// instr_e <= flush_e ? 0 : instr_d, instr_m <= instr_e, reg_wr_m <= reg_wr_e,
// instr_w <= instr_m, reg_wr_w <= reg_wr_m, so the old select of the next
// cycle is flush_e ? 00 : f(instr_d rs, instr_e rd, reg_wr_e, instr_m rd,
// reg_wr_m). A flushed E slot has rs = 0, which never forwards.
wire [4:0] r9_rs1_d = instr_d[19:15];
wire [4:0] r9_rs2_d = instr_d[24:20];
wire [1:0] fwd_a_next = ((r9_rs1_d == instr_e[11:7]) && reg_wr_e && (r9_rs1_d != 5'd0)) ? 2'b10 :
                        ((r9_rs1_d == instr_m[11:7]) && reg_wr_m && (r9_rs1_d != 5'd0)) ? 2'b01 :
                                                                                         2'b00;
wire [1:0] fwd_b_next = ((r9_rs2_d == instr_e[11:7]) && reg_wr_e && (r9_rs2_d != 5'd0)) ? 2'b10 :
                        ((r9_rs2_d == instr_m[11:7]) && reg_wr_m && (r9_rs2_d != 5'd0)) ? 2'b01 :
                                                                                         2'b00;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        forward_a_e <= 2'b00;
        forward_b_e <= 2'b00;
    end
    else if(!stall_pipe) begin
        forward_a_e <= flush_e ? 2'b00 : fwd_a_next;
        forward_b_e <= flush_e ? 2'b00 : fwd_b_next;
    end
end

// R9c -- M-stage result kind (instr_m <= instr_e, valid_m <= valid_e).
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        is_upper_m <= 1'b0;
        is_link_m  <= 1'b0;
    end
    else if(!stall_pipe) begin
        is_upper_m <= valid_e && ((instr_e[6:0] == 7'b0110111) ||
                                  (instr_e[6:0] == 7'b0010111));
        is_link_m  <= valid_e && ((instr_e[6:0] == 7'b1101111) ||
                                  (instr_e[6:0] == 7'b1100111));
    end
end

// R9b -- W-stage selects (instr_w <= instr_m, valid_w <= valid_m,
// load_byte_offset_w <= mem_byte_offset_m, result_src_w <= result_src_m).
// ld_kind_w one-hot {LHU, LBU, LH, LB}; all zero for LW, any other funct3 and
// any non-load, which all pass rd_data_w through unchanged.
reg  [3:0]  ld_kind_w;
reg  [3:0]  ld_lane_w;        // one-hot byte offset, reset = lane 0
reg  [3:0]  rsel_w;           // one-hot {upper, pc+4, load, alu}, reset = alu
wire        r9_is_load_m = valid_m && (instr_m[6:0] == 7'b0000011);
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        ld_kind_w <= 4'b0000;
        ld_lane_w <= 4'b0001;
        rsel_w    <= 4'b0001;
    end
    else if(!stall_pipe) begin
        ld_kind_w <= {r9_is_load_m && (instr_m[14:12] == 3'b101),
                      r9_is_load_m && (instr_m[14:12] == 3'b100),
                      r9_is_load_m && (instr_m[14:12] == 3'b001),
                      r9_is_load_m && (instr_m[14:12] == 3'b000)};
        ld_lane_w <= 4'b0001 << mem_byte_offset_m;
        rsel_w    <= {result_src_m == 2'b11, result_src_m == 2'b10,
                      result_src_m == 2'b01, result_src_m == 2'b00};
    end
end
assign upper_e    = (instr_e[5] ? 32'b0 : pc_e) + immext_e;

always @(posedge clk, negedge reset_n) begin
    if(!reset_n) begin
        upper_m <= 0 ;
        upper_w <= 0 ;
    end
    else begin
        if(!stall_pipe) begin
            upper_m <= upper_e ;
            upper_w <= upper_m ;
        end
    end
end

// forward the value each producer will actually write in WB:
// PC+4 for JAL/JALR (link), upper for LUI/AUIPC, else the ALU result
assign forward_result_m = is_upper_m ? upper_m :
                          is_link_m  ? pc_plus4_m :
                                       alu_result_m;

assign forward_src_a_e = forward_a_e[1] ? forward_result_m :
                         (forward_a_e[0] ? result_w : src_a_e);

assign forward_src_b_e = forward_b_e[1] ? forward_result_m :
                         (forward_b_e[0] ? result_w : src_b_e);

alu alu(
    .src_a      (forward_src_a_e)                         ,
    .src_b      (alu_src_e ? immext_e : forward_src_b_e) ,
    .alu_ctrl   (alu_ctrl_e)                              ,
    .alu_result (alu_result_raw) 
);

assign exec_result_e = is_csr_e ? csr_rdata_e : alu_result_raw;

branch branch(
    .reg1           (forward_src_a_e) ,
    .reg2           (forward_src_b_e) ,
    .branch_en      (is_branch_e) ,
    .funct3         (instr_e[14:12]) ,
    .branch_taken_e (branch_taken_e)
);

// R9b: one-hot result select registered at M->W (was decoded from result_src_w)
assign result_w = ({32{rsel_w[3]}} & upper_w)       |
                  ({32{rsel_w[2]}} & pc_plus4_w)    |
                  ({32{rsel_w[1]}} & rd_data_final) |
                  ({32{rsel_w[0]}} & alu_result_w)  ;

assign fix_wr_data = forward_src_b_e;

always @(posedge clk, negedge reset_n) begin
    if(!reset_n) begin
        alu_result_m      <= 0;
        alu_result_w      <= 0;
        mem_byte_offset_m <= 0;
    end
    else begin
        if(!stall_pipe) begin
            alu_result_m      <= exec_result_e;
            alu_result_w      <= alu_result_m;
            mem_byte_offset_m <= exec_result_e[1:0];
        end
    end
end

always @(*) begin
    case(instr_e[14:12])
        3'b000:  wr_data_e = {24'b0, fix_wr_data[7:0]};    // SB
        3'b001:  wr_data_e = {16'b0, fix_wr_data[15:0]};   // SH
        3'b010:  wr_data_e = fix_wr_data;                  // SW
        default: wr_data_e = fix_wr_data;
    endcase
end                

always @(posedge clk, negedge reset_n) begin
    if(!reset_n) begin
        wr_data_m <= 0 ;
    end
    else begin
        if(!stall_pipe)
            wr_data_m <= wr_data_e ;
    end
end

always @(posedge clk or negedge reset_n) begin
    if(!reset_n)
        store_data_w <= 32'h0000_0000;
    else if(!stall_pipe)
        store_data_w <= wr_data_m;
end

always @(posedge clk, negedge reset_n) begin
    if(!reset_n) begin
        rd_data_w <= 0 ;
    end
    else begin
        if(!stall_pipe)
            rd_data_w <= rd_data ;
    end
end

always @(*) begin
    // R9b: byte lane and load kind come from registered one-hot selects
    load_byte = ({8{ld_lane_w[0]}} & rd_data_w[7:0])   |
                ({8{ld_lane_w[1]}} & rd_data_w[15:8])  |
                ({8{ld_lane_w[2]}} & rd_data_w[23:16]) |
                ({8{ld_lane_w[3]}} & rd_data_w[31:24]);

    if(load_byte_offset_w[1] == 1'b0)
        load_half = rd_data_w[15:0];
    else
        load_half = rd_data_w[31:16];

    rd_data_final = ld_kind_w[0] ? {{24{load_byte[7]}},  load_byte} : // LB
                    ld_kind_w[1] ? {{16{load_half[15]}}, load_half} : // LH
                    ld_kind_w[2] ? {24'b0, load_byte}               : // LBU
                    ld_kind_w[3] ? {16'b0, load_half}               : // LHU
                                   rd_data_w;                         // LW / other / not a load
end
// R10b -- the retire-gated increment is a kept net, so the late retire enable
// meets it only in the final select instead of at the base of a ripple carry
// chain (20 cells after retire_event in r9_ecf4). Same logic, different shape.
(* keep *) wire [31:0] csr_minstret_inc = csr_minstret + 32'd1;
// --- CSR registers ---
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        csr_mstatus        <= 32'h0000_0000;
        csr_mie            <= 32'h0000_0000;
        csr_mtvec          <= 32'h0000_0080;
        csr_mepc           <= 32'h0000_0000;
        csr_mcause         <= 32'h0000_0000;
        csr_mcycle         <= 32'h0000_0000;
        csr_minstret       <= 32'h0000_0000;
        load_stall_count   <= 32'h0000_0000;
        control_redirect_count <= 32'h0000_0000;
    end
    else begin
        csr_mcycle <= csr_mcycle + 1'b1;

        if(load_use_hazard && !stall_pipe)
            load_stall_count <= load_stall_count + 1'b1;

        if(pc_src_e && !stall_pipe)
            control_redirect_count <= control_redirect_count + 1'b1;

        if(!stall_pipe && valid_w)
            csr_minstret <= csr_minstret_inc;

        if(irq_accept) begin
            csr_mepc       <= irq_resume_pc;
            csr_mcause     <= 32'h8000_0007;
            csr_mstatus[3] <= 1'b0;
        end
        else begin
            if(!stall_pipe && is_csr_e) begin
                case(csr_addr_e)
                    12'h300: csr_mstatus  <= csr_wdata_e;
                    12'h304: csr_mie      <= csr_wdata_e;
                    12'h305: csr_mtvec    <= csr_wdata_e;
                    12'h341: csr_mepc     <= csr_wdata_e;
                    12'h342: csr_mcause   <= csr_wdata_e;
                    12'hB00: csr_mcycle   <= csr_wdata_e;
                    12'hB02: csr_minstret <= csr_wdata_e;
                    default: ;
                endcase
            end
            if(!stall_pipe && is_mret_e) begin
                csr_mstatus[3] <= 1'b1;
            end
        end
    end
end

// retire order: bubbles and flushed slots do not consume a value
always @(posedge clk or negedge reset_n) begin
    if(!reset_n)
        retire_order_q <= 64'd0;
    else if(retire_valid)
        retire_order_q <= retire_order_q + 64'd1;
end

// --- Hazard Unit ---
hazard_unit hazard_unit (
    .rs1_d           (instr_d[19:15])  ,
    .rs2_d           (instr_d[24:20])  ,
    .use_rs1_d       (use_rs1_d)       ,
    .use_rs2_d       (use_rs2_d)       ,
    .rd_e            (instr_e[11:7])   ,
    .result_src_e    (result_src_e)    ,
    .pc_src_e        (pc_src_e)        ,
    .irq_flush       (irq_accept)      ,
    .cache_stall     (stall_pipe)      ,
    .stall_f         (stall_f)         ,
    .stall_d         (stall_d)         ,
    .flush_d         (flush_d)         ,
    .flush_e         (flush_e),
    .load_use_hazard (load_use_hazard)
);

// R9 equivalence checker -- simulation only (hidden from Quartus by
// translate_off and from every OpenLane tool, lint included, by __openlane__).
// Recomputes each decode exactly as the RTL did before R9 and stops the
// simulation on the first cycle where a registered select differs.
`ifndef __openlane__
// synthesis translate_off
reg  [1:0]  r9_ref_fwd_a, r9_ref_fwd_b;
reg  [7:0]  r9_ref_byte;
reg  [15:0] r9_ref_half;
reg  [31:0] r9_ref_rd_data_final;
reg  [31:0] r9_ref_result_w;
reg         r9_ref_is_upper_m, r9_ref_is_link_m;
always @(*) begin
    if((instr_e[19:15] == instr_m[11:7]) && reg_wr_m && (instr_e[19:15] != 0))      r9_ref_fwd_a = 2'b10;
    else if((instr_e[19:15] == instr_w[11:7]) && reg_wr_w && (instr_e[19:15] != 0)) r9_ref_fwd_a = 2'b01;
    else                                                                             r9_ref_fwd_a = 2'b00;
    if((instr_e[24:20] == instr_m[11:7]) && reg_wr_m && (instr_e[24:20] != 0))      r9_ref_fwd_b = 2'b10;
    else if((instr_e[24:20] == instr_w[11:7]) && reg_wr_w && (instr_e[24:20] != 0)) r9_ref_fwd_b = 2'b01;
    else                                                                             r9_ref_fwd_b = 2'b00;

    r9_ref_is_upper_m = valid_m && ((instr_m[6:0] == 7'b0110111) || (instr_m[6:0] == 7'b0010111));
    r9_ref_is_link_m  = valid_m && ((instr_m[6:0] == 7'b1101111) || (instr_m[6:0] == 7'b1100111));

    case(load_byte_offset_w)
        2'b00: r9_ref_byte = rd_data_w[7:0];
        2'b01: r9_ref_byte = rd_data_w[15:8];
        2'b10: r9_ref_byte = rd_data_w[23:16];
        default: r9_ref_byte = rd_data_w[31:24];
    endcase
    r9_ref_half = load_byte_offset_w[1] ? rd_data_w[31:16] : rd_data_w[15:0];
    if(valid_w && (instr_w[6:0] == 7'b0000011)) begin
        case(instr_w[14:12])
            3'b000:  r9_ref_rd_data_final = {{24{r9_ref_byte[7]}}, r9_ref_byte};
            3'b001:  r9_ref_rd_data_final = {{16{r9_ref_half[15]}}, r9_ref_half};
            3'b100:  r9_ref_rd_data_final = {24'b0, r9_ref_byte};
            3'b101:  r9_ref_rd_data_final = {16'b0, r9_ref_half};
            default: r9_ref_rd_data_final = rd_data_w;
        endcase
    end
    else
        r9_ref_rd_data_final = rd_data_w;
    r9_ref_result_w = (result_src_w == 2'b11) ? upper_w              :
                      (result_src_w == 2'b10) ? pc_plus4_w           :
                      (result_src_w == 2'b01) ? r9_ref_rd_data_final :
                                                alu_result_w;
end
// reset_n is used here only as an asynchronous reset, like every flop of the
// design: a synchronous "if(reset_n && ...)" made lint_asic report
// SYNCASYNCNET on the wrapper's reset synchroniser.
reg  [63:0] r9_checks;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n)
        r9_checks <= 64'd0;
    else if((forward_a_e !== r9_ref_fwd_a) || (forward_b_e !== r9_ref_fwd_b) ||
            (is_upper_m !== r9_ref_is_upper_m) || (is_link_m !== r9_ref_is_link_m) ||
            (rd_data_final !== r9_ref_rd_data_final) || (result_w !== r9_ref_result_w))
        $fatal(1, "R9 equivalence broken at %0t: fwd_a %b/%b fwd_b %b/%b upper %b/%b link %b/%b rd_final %h/%h result_w %h/%h",
               $time, forward_a_e, r9_ref_fwd_a, forward_b_e, r9_ref_fwd_b, is_upper_m, r9_ref_is_upper_m,
               is_link_m, r9_ref_is_link_m, rd_data_final, r9_ref_rd_data_final, result_w, r9_ref_result_w);
    else
        r9_checks <= r9_checks + 64'd1;
end
final
    $display("R9_EQUIV %m: %0d cycles matched", r9_checks);
// synthesis translate_on
`endif

endmodule
