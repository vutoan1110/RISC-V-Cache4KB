// Passive retirement monitor. It publishes one item per retirement and keeps
// the cycle/event counters that the scoreboard checks at end of test.
class rvfi_monitor extends uvm_monitor;

    virtual rvfi_if vif;
    core_cfg        cfg;

    uvm_analysis_port #(rvfi_item) ap;

    // Optional retirement trace in the canonical schema of
    // docs/reference/02 section 6, so verification/diff/compare_trace.py can
    // diff a UVM run against the Python reference model.
    protected int trace_fd = 0;

    `uvm_component_utils(rvfi_monitor)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(core_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "core_cfg not found for rvfi_monitor")
    endfunction

    function void start_of_simulation_phase(uvm_phase phase);
        string path;
        super.start_of_simulation_phase(phase);
        if (!$value$plusargs("TRACE=%s", path))
            return;
        trace_fd = $fopen(path, "w");
        if (trace_fd == 0) begin
            `uvm_warning("TRACE", $sformatf("cannot open retirement trace %s", path))
            return;
        end
        $fdisplay(trace_fd,
                  "order,pc,instr,rd,we,rd_data,mem_we,mem_addr,mem_wdata,mem_wstrb");
        `uvm_info("TRACE", $sformatf("writing retirement trace to %s", path), UVM_LOW)
    endfunction

    function void final_phase(uvm_phase phase);
        super.final_phase(phase);
        if (trace_fd != 0) begin
            $fclose(trace_fd);
            trace_fd = 0;
        end
    endfunction

    protected function void trace_write(rvfi_item item);
        if (trace_fd == 0)
            return;
        $fdisplay(trace_fd, "%0d,%08x,%08x,%0d,%0d,%08x,%0d,%08x,%08x,%x",
                  item.order, item.pc, item.instr, item.rd_addr, item.rd_we,
                  item.rd_wdata, item.mem_write, item.mem_addr, item.mem_wdata,
                  item.mem_wstrb);
    endfunction

    // CSRRW/CSRRS/CSRRC targeting mcycle (0xB00) or minstret (0xB02). This RTL
    // commits the write even when rs1 == x0, so each one costs the targeted
    // counter a single increment.
    protected function void count_counter_csr(bit [31:0] instr);
        bit [11:0] csr    = instr[31:20];
        bit [2:0]  funct3 = instr[14:12];
        if (instr[6:0] != 7'b1110011)
            return;
        if (!(funct3 inside {3'b001, 3'b010, 3'b011}))
            return;
        if (csr == 12'hB00) cfg.stats.n_csr_wr_mcycle++;
        if (csr == 12'hB02) cfg.stats.n_csr_wr_minstret++;
    endfunction

    task run_phase(uvm_phase phase);
        rvfi_item item;

        forever begin
            @(vif.mon_cb);

            if (!vif.reset_n) begin
                cfg.stats.n_cycle = 0;
                continue;
            end
            cfg.stats.n_cycle++;

            cfg.stats.mcycle_last     = vif.mon_cb.mcycle_dbg;
            cfg.stats.minstret_last   = vif.mon_cb.minstret_dbg;
            cfg.stats.if_error_sticky |= vif.mon_cb.if_error_dbg;
            cfg.stats.d_error_sticky  |= vif.mon_cb.d_error_dbg;

            if (vif.mon_cb.conditional_branch_event_dbg)        cfg.stats.ev_branch++;
            if (vif.mon_cb.branch_taken_event_dbg)              cfg.stats.ev_branch_taken++;
            if (vif.mon_cb.branch_not_taken_event_dbg)          cfg.stats.ev_branch_not_taken++;
            if (vif.mon_cb.branch_prediction_event_dbg)         cfg.stats.ev_prediction++;
            if (vif.mon_cb.branch_correct_prediction_event_dbg) cfg.stats.ev_prediction_correct++;
            if (vif.mon_cb.mispredict_event_dbg)                cfg.stats.ev_mispredict++;
            if (vif.mon_cb.load_use_stall_event_dbg)            cfg.stats.ev_load_use++;
            if (vif.mon_cb.control_redirect_event_dbg)          cfg.stats.ev_control_redirect++;

            if (!vif.mon_cb.retire_valid)
                continue;

            item           = rvfi_item::type_id::create("rvfi");
            item.order     = vif.mon_cb.retire_order;
            item.pc        = vif.mon_cb.retire_pc;
            item.pc_next   = vif.mon_cb.retire_pc_next;
            item.instr     = vif.mon_cb.retire_instr;
            item.rs1_addr  = vif.mon_cb.retire_rs1_addr;
            item.rs1_rdata = vif.mon_cb.retire_rs1_rdata;
            item.rs2_addr  = vif.mon_cb.retire_rs2_addr;
            item.rs2_rdata = vif.mon_cb.retire_rs2_rdata;
            item.rd_addr   = vif.mon_cb.retire_rd_addr;
            item.rd_wdata  = vif.mon_cb.retire_rd_wdata;
            item.rd_we     = vif.mon_cb.retire_rd_we;
            item.mem_valid = vif.mon_cb.retire_mem_valid;
            item.mem_write = vif.mon_cb.retire_mem_write;
            item.mem_addr  = vif.mon_cb.retire_mem_addr;
            item.mem_wdata = vif.mon_cb.retire_mem_wdata;
            item.mem_wstrb = vif.mon_cb.retire_mem_wstrb;
            item.trap      = vif.mon_cb.retire_trap;
            item.interrupt = vif.mon_cb.retire_interrupt;

            cfg.stats.n_retire++;
            count_counter_csr(item.instr);
            if (!cfg.stats.halt_seen && (item.instr != cfg.halt_instr))
                trace_write(item);

            if (!cfg.stats.halt_seen) begin
                if (item.instr == cfg.halt_instr) begin
                    cfg.stats.halt_seen = 1'b1;
                    cfg.stats.halt_pc   = item.pc;
                    cfg.stats.halt_e.trigger();
                    `uvm_info("HALT",
                        $sformatf("HALT instruction retired at pc=0x%08h after %0d retirements",
                                  item.pc, cfg.stats.n_retire_before_halt), UVM_LOW)
                end
                else begin
                    cfg.stats.n_retire_before_halt++;
                end
            end

            ap.write(item);
        end
    endtask

endclass
