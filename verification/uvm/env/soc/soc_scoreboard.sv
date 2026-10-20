// SoC-level scoreboard.
//
// This is where the whole of docs/reference/02 section 3 becomes checkable:
// the nine-way mcycle decomposition and the cache accounting identities need
// the counter bank of performance_observability, which only exists at SoC
// level. The core environment can only check the branch and prediction parts.
class soc_scoreboard extends uvm_scoreboard;

    uvm_analysis_imp_retire #(soc_retire_item, soc_scoreboard) retire_export;
    uvm_analysis_imp_apb    #(apb_item,        soc_scoreboard) apb_export;

    soc_cfg cfg;

    protected bit [63:0] expected_order;
    protected bit        have_prev_pc;
    protected bit [31:0] prev_pc_next;
    protected bit        prev_was_interrupt;
    protected int        irq_credits;

    `uvm_component_utils(soc_scoreboard)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        retire_export = new("retire_export", this);
        apb_export    = new("apb_export", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(soc_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "soc_cfg not found for soc_scoreboard")
        expected_order     = 64'd0;
        have_prev_pc       = 1'b0;
        prev_was_interrupt = 1'b0;
        irq_credits        = 0;
    endfunction

    function void write_retire(soc_retire_item item);
        if (item.trap)
            `uvm_error("TRAP",
                $sformatf("retire_trap at order=%0d pc=0x%08h", item.order, item.pc))

        if (item.order !== expected_order)
            `uvm_error("ORDER",
                $sformatf("retire_order expected %0d, got %0d at pc=0x%08h",
                          expected_order, item.order, item.pc))
        expected_order = item.order + 64'd1;

        if (item.pc[1:0] != 2'b00)
            `uvm_error("PCALIGN", $sformatf("unaligned retired pc=0x%08h", item.pc))

        // Each accepted interrupt buys exactly one permitted discontinuity: the
        // redirect to mtvec. Instructions already in M and W retire after the
        // acceptance, so which retirement carries it is not fixed, and a credit
        // is the honest way to allow one and only one.
        irq_credits += item.irq_pulses;
        if (have_prev_pc && (item.pc !== prev_pc_next)) begin
            if (irq_credits > 0) begin
                irq_credits--;
                `uvm_info("IRQREDIRECT",
                    $sformatf("interrupt redirect at order=%0d: 0x%08h -> 0x%08h",
                              item.order, prev_pc_next, item.pc), UVM_LOW)
            end
            else begin
                `uvm_error("PCCHAIN",
                    $sformatf("pc discontinuity at order=%0d: previous pc_next=0x%08h, this pc=0x%08h",
                              item.order, prev_pc_next, item.pc))
            end
        end
        prev_pc_next       = item.pc_next;
        prev_was_interrupt = item.interrupt;
        have_prev_pc       = 1'b1;

        if (item.rd_we && (item.rd_addr == 5'd0))
            `uvm_error("X0WRITE",
                $sformatf("architectural write to x0 at order=%0d pc=0x%08h",
                          item.order, item.pc))

        if (item.rd_we)
            cfg.stats.arch_regs[item.rd_addr] = item.rd_wdata;

        // Store strobes must match the width the instruction encodes.
        if (item.mem_write) begin
            case (item.instr[14:12])
                3'b000: if (item.mem_wstrb !== (4'b0001 << item.mem_addr[1:0]))
                            `uvm_error("SBSTRB",
                                $sformatf("SB at 0x%08h has strobe %4b", item.mem_addr, item.mem_wstrb))
                3'b001: if (item.mem_wstrb !== (4'b0011 << item.mem_addr[1:0]))
                            `uvm_error("SHSTRB",
                                $sformatf("SH at 0x%08h has strobe %4b", item.mem_addr, item.mem_wstrb))
                3'b010: if (item.mem_wstrb !== 4'b1111)
                            `uvm_error("SWSTRB",
                                $sformatf("SW at 0x%08h has strobe %4b", item.mem_addr, item.mem_wstrb))
                default: `uvm_error("STOREF3",
                            $sformatf("unsupported store funct3 %0b retired", item.instr[14:12]))
            endcase
        end
    endfunction

    function void write_apb(apb_item item);
        // The APB traffic itself is checked by the monitor and mirrored into
        // the register model by the predictor; nothing more to do here.
    endfunction

    // ---------------------------------------------------------------------
    // docs/reference/02 section 3, in full.
    // ---------------------------------------------------------------------
    protected function void check_counter_equations();
        virtual soc_obs_if v = cfg.obs_vif;
        bit [31:0]     sum;
        longint signed minstret_delta;

        sum = v.retire_cycle_count + v.load_use_cycle_count +
              v.icache_wait_cycle_count + v.dcache_wait_cycle_count +
              v.control_redirect_cycle_count + v.trap_redirect_cycle_count +
              v.mmio_wait_cycle_count + v.pipe_fill_drain_cycle_count +
              v.other_cycle_count;
        if (v.mcycle_count !== sum)
            `uvm_error("MCYCLEEQ",
                $sformatf("mcycle=%0d but the nine exclusive cycle counters sum to %0d",
                          v.mcycle_count, sum))

        if (v.icache_access_count !== (v.icache_main_hit_count +
                                       v.icache_victim_hit_count +
                                       v.icache_true_miss_count))
            `uvm_error("IACCESSEQ",
                $sformatf("I_access=%0d != main_hit %0d + victim_hit %0d + true_miss %0d",
                          v.icache_access_count, v.icache_main_hit_count,
                          v.icache_victim_hit_count, v.icache_true_miss_count))

        if (v.icache_access_count !== (v.icache_hit_count + v.icache_miss_count))
            `uvm_error("IHITMISSEQ",
                $sformatf("I_access=%0d != hit %0d + miss %0d",
                          v.icache_access_count, v.icache_hit_count, v.icache_miss_count))

        if (v.dcache_access_count !== (v.dcache_read_count + v.dcache_write_count))
            `uvm_error("DACCESSEQ",
                $sformatf("D_access=%0d != read %0d + write %0d",
                          v.dcache_access_count, v.dcache_read_count, v.dcache_write_count))

        if (v.dcache_read_count !== (v.dcache_read_hit_count + v.dcache_read_miss_count))
            `uvm_error("DREADEQ",
                $sformatf("D_read=%0d != read_hit %0d + read_miss %0d",
                          v.dcache_read_count, v.dcache_read_hit_count,
                          v.dcache_read_miss_count))

        if (v.dcache_write_count !== (v.dcache_write_hit_count + v.dcache_write_miss_count))
            `uvm_error("DWRITEEQ",
                $sformatf("D_write=%0d != write_hit %0d + write_miss %0d",
                          v.dcache_write_count, v.dcache_write_hit_count,
                          v.dcache_write_miss_count))

        if (v.dcache_access_count !== (v.dcache_main_hit_count +
                                       v.dcache_victim_hit_count +
                                       v.dcache_true_miss_count))
            `uvm_error("DSPLITEQ",
                $sformatf("D_access=%0d != main_hit %0d + victim_hit %0d + true_miss %0d",
                          v.dcache_access_count, v.dcache_main_hit_count,
                          v.dcache_victim_hit_count, v.dcache_true_miss_count))

        if (v.conditional_branch_count !== (v.branch_taken_count + v.branch_not_taken_count))
            `uvm_error("BRANCHEQ",
                $sformatf("branch=%0d != taken %0d + not_taken %0d",
                          v.conditional_branch_count, v.branch_taken_count,
                          v.branch_not_taken_count))

        if (v.branch_prediction_count !== (v.branch_correct_prediction_count +
                                           v.mispredict_event_count))
            `uvm_error("PREDEQ",
                $sformatf("pred=%0d != correct %0d + mispredict %0d",
                          v.branch_prediction_count, v.branch_correct_prediction_count,
                          v.mispredict_event_count))

        // The counter bank counts retirements directly, unlike the core CSR,
        // which loses an increment to every CSR write that targets it. The
        // slack of one is the sampling boundary: the monitor process stops with
        // the run phase, while the DUT counter can take one more increment
        // before check_phase reads it.
        minstret_delta = longint'(v.minstret_count) - longint'(cfg.stats.n_retire);
        if ((minstret_delta < 0) || (minstret_delta > 1))
            `uvm_error("MINSTRETEQ",
                $sformatf("perf minstret=%0d but %0d instructions retired (delta %0d)",
                          v.minstret_count, cfg.stats.n_retire, minstret_delta))
    endfunction

    // Every register the CPU touched must still agree with the RTL.
    protected function void check_register_model();
        uvm_reg          regs[$];
        uvm_reg_data_t   mirrored;

        if (cfg.regs == null)
            return;

        cfg.regs.get_registers(regs);
        `uvm_info("REGMODEL",
            $sformatf("register model holds %0d registers across uart, timer and sysmon",
                      regs.size()), UVM_LOW)
        foreach (regs[i]) begin
            mirrored = regs[i].get_mirrored_value();
            `uvm_info("REGMODEL",
                $sformatf("  %-28s mirrored=0x%08h", regs[i].get_full_name(), mirrored),
                UVM_HIGH)
        end
    endfunction

    function void check_phase(uvm_phase phase);
        super.check_phase(phase);

        if (!cfg.stats.halt_seen)
            `uvm_error("NOHALT",
                $sformatf("HALT 0x%08h never retired (%0d retirements observed)",
                          cfg.halt_instr, cfg.stats.n_retire))

        if ((cfg.expected_retire != 0) &&
            (cfg.stats.n_retire_before_halt != cfg.expected_retire))
            `uvm_error("RETIRECOUNT",
                $sformatf("expected %0d retirements before HALT, observed %0d",
                          cfg.expected_retire, cfg.stats.n_retire_before_halt))

        check_counter_equations();
        check_register_model();
    endfunction

    function void report_phase(uvm_phase phase);
        virtual soc_obs_if v = cfg.obs_vif;
        super.report_phase(phase);
        `uvm_info("SUMMARY", $sformatf(
            {"\n  retirements before HALT : %0d",
             "\n  cycles / mcycle         : %0d / %0d",
             "\n  perf minstret           : %0d",
             "\n  cycle split retire/load-use/i-wait/d-wait : %0d/%0d/%0d/%0d",
             "\n  cycle split ctrl/trap/mmio/fill/other     : %0d/%0d/%0d/%0d/%0d",
             "\n  I cache access/hit/miss : %0d/%0d/%0d",
             "\n  D cache read/write      : %0d/%0d",
             "\n  branch taken/not-taken  : %0d/%0d of %0d",
             "\n  prediction ok/mispred   : %0d/%0d of %0d",
             "\n  APB reads/writes        : %0d/%0d",
             "\n  UART bytes tx/rx        : %0d/%0d"},
            cfg.stats.n_retire_before_halt,
            cfg.stats.n_cycle, v.mcycle_count, v.minstret_count,
            v.retire_cycle_count, v.load_use_cycle_count,
            v.icache_wait_cycle_count, v.dcache_wait_cycle_count,
            v.control_redirect_cycle_count, v.trap_redirect_cycle_count,
            v.mmio_wait_cycle_count, v.pipe_fill_drain_cycle_count,
            v.other_cycle_count,
            v.icache_access_count, v.icache_hit_count, v.icache_miss_count,
            v.dcache_read_count, v.dcache_write_count,
            v.branch_taken_count, v.branch_not_taken_count, v.conditional_branch_count,
            v.branch_correct_prediction_count, v.mispredict_event_count,
            v.branch_prediction_count,
            cfg.stats.apb_read, cfg.stats.apb_write,
            cfg.stats.uart_tx_bytes, cfg.stats.uart_rx_bytes), UVM_LOW)
    endfunction

endclass
