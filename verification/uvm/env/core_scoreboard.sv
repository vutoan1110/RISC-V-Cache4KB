// Core scoreboard. Three layers of checking, each independent of the others:
//
//   1. self-consistency of the retirement trace (order, PC chain, x0, traps);
//   2. cross-check of every retired memory operation against the transaction
//      the data agent actually saw on the bus;
//   3. instruction-by-instruction comparison against rv32_iss, the reference
//      model (phase 2), plus a full register and memory image compare at end
//      of test.
//
// Layer 3 can be turned off with core_cfg::use_iss; layers 1 and 2 stay as the
// safety net that catches a wrong reference model.
class core_scoreboard extends uvm_scoreboard;

    uvm_analysis_imp_imem #(native_mem_item, core_scoreboard) imem_export;
    uvm_analysis_imp_dmem #(native_mem_item, core_scoreboard) dmem_export;
    uvm_analysis_imp_rvfi #(rvfi_item,       core_scoreboard) rvfi_export;

    core_cfg cfg;

    // Data-port accepts still waiting for their retirement record. The core is
    // in order and has a single data port, so bus order is program order and
    // one FIFO is enough.
    protected native_mem_item d_pending_q[$];

    protected bit [63:0] expected_order;
    protected bit        have_prev_pc;
    protected bit [31:0] prev_pc_next;

    // Reference model state. iss_active drops once the model reaches HALT; the
    // DUT keeps retiring the halt loop after that and there is nothing left to
    // predict.
    protected bit              iss_active;
    protected longint unsigned iss_compared;

    `uvm_component_utils(core_scoreboard)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        imem_export = new("imem_export", this);
        dmem_export = new("dmem_export", this);
        rvfi_export = new("rvfi_export", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(core_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "core_cfg not found for core_scoreboard")
        expected_order = 64'd0;
        have_prev_pc   = 1'b0;
        iss_active     = cfg.use_iss;
        iss_compared   = 0;
    endfunction

    function void write_imem(native_mem_item item);
        case (item.evt)
            NATIVE_ACCEPT: cfg.stats.i_access++;
            NATIVE_RESPONSE: begin
                cfg.stats.i_response++;
                if (item.error) begin
                    cfg.stats.i_error++;
                    `uvm_error("IFERR",
                        $sformatf("instruction fetch answered with rsp_error at cycle %0d",
                                  item.cycle))
                end
            end
        endcase
    endfunction

    function void write_dmem(native_mem_item item);
        case (item.evt)
            NATIVE_ACCEPT: begin
                cfg.stats.d_access++;
                if (item.is_write) cfg.stats.d_write++;
                else               cfg.stats.d_read++;
                case (native_mem_model::decode(item.addr))
                    REGION_MMIO:     cfg.stats.d_mmio++;
                    REGION_UNMAPPED: cfg.stats.d_unmapped++;
                    default: ;
                endcase
                d_pending_q.push_back(item);
            end
            NATIVE_RESPONSE: begin
                cfg.stats.d_response++;
                if (item.error) begin
                    cfg.stats.d_error++;
                    `uvm_error("DERR",
                        $sformatf("data access answered with rsp_error at cycle %0d",
                                  item.cycle))
                end
            end
        endcase
    endfunction

    function void write_rvfi(rvfi_item item);
        native_mem_item bus;

        // No trap or interrupt is expected while irq_timer is tied low.
        if (item.trap)
            `uvm_error("TRAP",
                $sformatf("retire_trap asserted at order=%0d pc=0x%08h",
                          item.order, item.pc))
        if (item.interrupt)
            `uvm_error("IRQ",
                $sformatf("retire_interrupt asserted at order=%0d pc=0x%08h",
                          item.order, item.pc))

        // retire_order is dense and monotonic.
        if (item.order !== expected_order)
            `uvm_error("ORDER",
                $sformatf("retire_order expected %0d, got %0d at pc=0x%08h",
                          expected_order, item.order, item.pc))
        expected_order = item.order + 64'd1;

        if (item.pc[1:0] != 2'b00)
            `uvm_error("PCALIGN",
                $sformatf("unaligned retired pc=0x%08h", item.pc))

        // Architectural PC chain: every retirement starts where the previous
        // one said it would go, redirects included.
        if (cfg.check_pc_chain && have_prev_pc && (item.pc !== prev_pc_next))
            `uvm_error("PCCHAIN",
                $sformatf("pc discontinuity at order=%0d: previous pc_next=0x%08h, this pc=0x%08h",
                          item.order, prev_pc_next, item.pc))
        prev_pc_next = item.pc_next;
        have_prev_pc = 1'b1;

        if (item.rd_we && (item.rd_addr == 5'd0))
            `uvm_error("X0WRITE",
                $sformatf("architectural write to x0 at order=%0d pc=0x%08h",
                          item.order, item.pc))

        if (item.rd_we)
            cfg.stats.arch_regs[item.rd_addr] = item.rd_wdata;

        if (iss_active)
            compare_with_iss(item);

        if (!item.mem_valid)
            return;

        if (item.mem_write) cfg.stats.r_mem_write++;
        else                cfg.stats.r_mem_read++;

        // Every retired memory operation must match exactly one data-port
        // transaction, in order.
        if (d_pending_q.size() == 0) begin
            `uvm_error("NOBUSOP",
                $sformatf("retired %s at order=%0d pc=0x%08h has no observed data-port transaction",
                          item.mem_write ? "store" : "load", item.order, item.pc))
            return;
        end

        bus = d_pending_q.pop_front();

        if (bus.is_write !== item.mem_write)
            `uvm_error("MEMDIR",
                $sformatf("order=%0d pc=0x%08h retired a %s but the bus saw a %s",
                          item.order, item.pc,
                          item.mem_write ? "store" : "load",
                          bus.is_write ? "store" : "load"))
        else if (bus.addr !== item.mem_addr)
            `uvm_error("MEMADDR",
                $sformatf("order=%0d pc=0x%08h retired addr=0x%08h but the bus saw 0x%08h",
                          item.order, item.pc, item.mem_addr, bus.addr))
        else if (item.mem_write &&
                 ((bus.wdata !== item.mem_wdata) || (bus.wstrb !== item.mem_wstrb)))
            `uvm_error("MEMDATA",
                $sformatf("order=%0d pc=0x%08h retired wdata=0x%08h wstrb=%4b but the bus saw 0x%08h/%4b",
                          item.order, item.pc, item.mem_wdata, item.mem_wstrb,
                          bus.wdata, bus.wstrb))
    endfunction

    // ---------------------------------------------------------------------
    // Layer 3: compare one retirement against the reference model.
    // ---------------------------------------------------------------------
    protected function void compare_with_iss(rvfi_item item);
        rv32_step_s s;
        string      ctx;

        s   = cfg.iss.step();
        ctx = $sformatf("order=%0d dut_pc=0x%08h dut_instr=0x%08h",
                        item.order, item.pc, item.instr);

        if (s.unsupported) begin
            `uvm_error("ISSUNSUP",
                $sformatf("%s: reference model cannot execute this instruction: %s",
                          ctx, s.reason))
            iss_active = 1'b0;
            return;
        end

        if (s.halted) begin
            // The model stops at HALT; make sure the DUT retired the same
            // instruction there and stop predicting.
            if (item.instr !== cfg.halt_instr)
                `uvm_error("ISSHALT",
                    $sformatf("%s: reference model reached HALT at pc=0x%08h but the DUT retired 0x%08h",
                              ctx, s.pc, item.instr))
            else if (item.pc !== s.pc)
                `uvm_error("ISSHALT",
                    $sformatf("%s: HALT pc mismatch, reference 0x%08h", ctx, s.pc))
            iss_active = 1'b0;
            return;
        end

        iss_compared++;

        if (s.pc !== item.pc) begin
            `uvm_error("ISSPC",
                $sformatf("%s: reference pc=0x%08h", ctx, s.pc))
            iss_active = 1'b0;   // the models have diverged, stop the noise
            return;
        end
        if (s.instr !== item.instr) begin
            `uvm_error("ISSINSTR",
                $sformatf("%s: reference instr=0x%08h", ctx, s.instr))
            iss_active = 1'b0;
            return;
        end
        if (s.next_pc !== item.pc_next)
            `uvm_error("ISSNEXTPC",
                $sformatf("%s: pc_next reference=0x%08h dut=0x%08h",
                          ctx, s.next_pc, item.pc_next))

        if (s.rd_we !== item.rd_we)
            `uvm_error("ISSRDWE",
                $sformatf("%s: rd_we reference=%0b dut=%0b", ctx, s.rd_we, item.rd_we))
        else if (s.rd_addr !== item.rd_addr)
            `uvm_error("ISSRDADDR",
                $sformatf("%s: rd reference=x%0d dut=x%0d", ctx, s.rd_addr, item.rd_addr))
        else if (s.rd_we && s.rd_wdata_known && (s.rd_wdata !== item.rd_wdata))
            `uvm_error("ISSRDDATA",
                $sformatf("%s: x%0d reference=0x%08h dut=0x%08h",
                          ctx, s.rd_addr, s.rd_wdata, item.rd_wdata))
        else if (s.rd_we && !s.rd_wdata_known)
            // Free running counter read: take the DUT value so the rest of the
            // program stays comparable.
            cfg.iss.adopt_rd(s.rd_addr, item.rd_wdata);

        if (s.mem_valid !== item.mem_valid)
            `uvm_error("ISSMEMVALID",
                $sformatf("%s: mem_valid reference=%0b dut=%0b",
                          ctx, s.mem_valid, item.mem_valid))
        else if (s.mem_valid) begin
            if (s.mem_write !== item.mem_write)
                `uvm_error("ISSMEMDIR",
                    $sformatf("%s: mem_write reference=%0b dut=%0b",
                              ctx, s.mem_write, item.mem_write))
            else if (s.mem_addr !== item.mem_addr)
                `uvm_error("ISSMEMADDR",
                    $sformatf("%s: mem_addr reference=0x%08h dut=0x%08h",
                              ctx, s.mem_addr, item.mem_addr))
            else if (s.mem_write &&
                     ((s.mem_wdata !== item.mem_wdata) ||
                      (s.mem_wstrb !== item.mem_wstrb)))
                `uvm_error("ISSMEMDATA",
                    $sformatf("%s: store reference=0x%08h/%4b dut=0x%08h/%4b",
                              ctx, s.mem_wdata, s.mem_wstrb,
                              item.mem_wdata, item.mem_wstrb))
        end
    endfunction

    // ---------------------------------------------------------------------
    // End-of-test invariants.
    // ---------------------------------------------------------------------
    function void check_phase(uvm_phase phase);
        core_stats     s;
        longint signed mcycle_delta;
        longint signed minstret_delta;

        super.check_phase(phase);
        s = cfg.stats;

        if (!s.halt_seen)
            `uvm_error("NOHALT",
                $sformatf("HALT instruction 0x%08h never retired (%0d retirements observed)",
                          cfg.halt_instr, s.n_retire))

        if ((cfg.expected_retire != 0) &&
            (s.n_retire_before_halt != cfg.expected_retire))
            `uvm_error("RETIRECOUNT",
                $sformatf("expected %0d retirements before HALT, observed %0d",
                          cfg.expected_retire, s.n_retire_before_halt))

        if (d_pending_q.size() != 0)
            `uvm_error("BUSLEFTOVER",
                $sformatf("%0d data-port transactions never matched a retirement (first addr=0x%08h)",
                          d_pending_q.size(), d_pending_q[0].addr))

        if (s.if_error_sticky)
            `uvm_error("IFSTICKY",
                "if_error_dbg is set: the core latched an instruction-side error")
        if (s.d_error_sticky)
            `uvm_error("DSTICKY",
                "d_error_dbg is set: the core latched a data-side error")

        // Handshake conservation on both native ports. The protocol allows one
        // request to be in flight, so the fetch accepted on the last sampled
        // edge may legitimately have no response yet.
        check_handshake("instruction", s.i_access, s.i_response);
        check_handshake("data",        s.d_access, s.d_response);

        // docs/reference/02 section 3, restricted to what the core boundary
        // exposes. The cache-side identities need the SoC DUT of phase 4/5.
        if (s.d_access != (s.d_read + s.d_write))
            `uvm_error("DACCESS",
                $sformatf("D_access %0d != D_read %0d + D_write %0d",
                          s.d_access, s.d_read, s.d_write))
        if (s.d_access != (s.r_mem_read + s.r_mem_write))
            `uvm_error("DVSRETIRE",
                $sformatf("data port saw %0d transactions but %0d memory operations retired",
                          s.d_access, s.r_mem_read + s.r_mem_write))
        if (s.i_access < s.n_retire)
            `uvm_error("IACCESS",
                $sformatf("instruction port accepted %0d fetches for %0d retirements",
                          s.i_access, s.n_retire))

        if (s.ev_branch != (s.ev_branch_taken + s.ev_branch_not_taken))
            `uvm_error("BRANCHEQ",
                $sformatf("branch %0d != taken %0d + not_taken %0d",
                          s.ev_branch, s.ev_branch_taken, s.ev_branch_not_taken))
        if (s.ev_prediction != (s.ev_prediction_correct + s.ev_mispredict))
            `uvm_error("PREDEQ",
                $sformatf("prediction %0d != correct %0d + mispredict %0d",
                          s.ev_prediction, s.ev_prediction_correct, s.ev_mispredict))

        // mcycle and minstret lose one increment per retired CSR write that
        // targets them, see rvfi_monitor::count_counter_csr. The remaining
        // slack of one is the sampling offset between the monitor counter and
        // the DUT register.
        mcycle_delta   = longint'(s.n_cycle)  - longint'(s.mcycle_last)
                       - longint'(s.n_csr_wr_mcycle);
        minstret_delta = longint'(s.n_retire) - longint'(s.minstret_last)
                       - longint'(s.n_csr_wr_minstret);

        if ((mcycle_delta < 0) || (mcycle_delta > 1))
            `uvm_error("MCYCLE",
                $sformatf("mcycle=%0d but %0d cycles elapsed with %0d counter CSR writes (delta %0d)",
                          s.mcycle_last, s.n_cycle, s.n_csr_wr_mcycle, mcycle_delta))
        if ((minstret_delta < 0) || (minstret_delta > 1))
            `uvm_error("MINSTRET",
                $sformatf("minstret=%0d but %0d instructions retired with %0d counter CSR writes (delta %0d)",
                          s.minstret_last, s.n_retire, s.n_csr_wr_minstret, minstret_delta))

        if (cfg.use_iss)
            check_iss_final();
    endfunction

    // Whole-state comparison against the reference model: every architectural
    // register and every word of RAM.
    protected function void check_iss_final();
        string       diff_text;
        int unsigned mem_diffs;
        int unsigned reg_diffs = 0;

        if (iss_compared == 0) begin
            `uvm_error("ISSIDLE", "the reference model compared no instruction at all")
            return;
        end
        if (iss_compared != cfg.stats.n_retire_before_halt)
            `uvm_error("ISSCOUNT",
                $sformatf("reference model executed %0d instructions but %0d retired before HALT",
                          iss_compared, cfg.stats.n_retire_before_halt))

        // x0 is hardwired, start at x1.
        for (int r = 1; r < 32; r++) begin
            if (cfg.iss.regs[r] !== cfg.stats.arch_regs[r]) begin
                reg_diffs++;
                `uvm_error("ISSREG",
                    $sformatf("x%0d: reference=0x%08h dut trace=0x%08h",
                              r, cfg.iss.regs[r], cfg.stats.arch_regs[r]))
            end
        end

        mem_diffs = cfg.iss_mem.compare(cfg.mem, diff_text);
        if (mem_diffs != 0)
            `uvm_error("ISSMEM",
                $sformatf("%0d memory words differ between the reference model and the DUT memory:%s",
                          mem_diffs, diff_text))

        if ((reg_diffs == 0) && (mem_diffs == 0))
            `uvm_info("ISS",
                $sformatf("reference model matched %0d instructions, 32 registers and %0d bytes of RAM",
                          iss_compared, cfg.mem.size_bytes), UVM_LOW)
    endfunction

    protected function void check_handshake(string port, longint unsigned accepts,
                                           longint unsigned responses);
        if (responses > accepts)
            `uvm_error("HANDSHAKE",
                $sformatf("%s port: %0d responses for only %0d accepts",
                          port, responses, accepts))
        else if ((accepts - responses) > 1)
            `uvm_error("HANDSHAKE",
                $sformatf("%s port: %0d accepts but only %0d responses",
                          port, accepts, responses))
    endfunction

    function void report_phase(uvm_phase phase);
        core_stats s;
        super.report_phase(phase);
        s = cfg.stats;
        `uvm_info("SUMMARY", $sformatf(
            {"\n  retirements before HALT : %0d",
             "\n  retirements total       : %0d",
             "\n  cycles (reset_n high)   : %0d",
             "\n  mcycle / minstret       : %0d / %0d",
             "\n  counter CSR writes      : mcycle %0d, minstret %0d",
             "\n  I port accept/response  : %0d / %0d",
             "\n  D port accept/response  : %0d / %0d (read %0d, write %0d)",
             "\n  retired memory ops      : read %0d, write %0d",
             "\n  branch taken/not-taken  : %0d / %0d of %0d",
             "\n  prediction ok/mispred   : %0d / %0d of %0d",
             "\n  load-use / redirects    : %0d / %0d",
             "\n  ISS instructions matched: %0d"},
            s.n_retire_before_halt, s.n_retire, s.n_cycle,
            s.mcycle_last, s.minstret_last,
            s.n_csr_wr_mcycle, s.n_csr_wr_minstret,
            s.i_access, s.i_response,
            s.d_access, s.d_response, s.d_read, s.d_write,
            s.r_mem_read, s.r_mem_write,
            s.ev_branch_taken, s.ev_branch_not_taken, s.ev_branch,
            s.ev_prediction_correct, s.ev_mispredict, s.ev_prediction,
            s.ev_load_use, s.ev_control_redirect, iss_compared), UVM_LOW)
    endfunction

endclass
