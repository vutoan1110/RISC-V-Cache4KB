// Passive agent over the SoC observation interface: publishes one item per
// retirement and enforces the per-cycle invariant that the cycle classifier is
// one-hot, which is what makes the mcycle decomposition meaningful.

class soc_retire_item extends uvm_sequence_item;

    bit [63:0] order;
    bit [31:0] pc;
    bit [31:0] pc_next;
    bit [31:0] instr;
    bit [4:0]  rd_addr;
    bit [31:0] rd_wdata;
    bit        rd_we;
    bit        mem_valid;
    bit        mem_write;
    bit [31:0] mem_addr;
    bit [31:0] mem_wdata;
    bit [3:0]  mem_wstrb;
    bit        trap;
    bit        interrupt;      // as reported by the DUT on this retirement
    int unsigned irq_pulses;   // interrupts accepted since the previous retirement

    `uvm_object_utils(soc_retire_item)

    function new(string name = "soc_retire_item");
        super.new(name);
    endfunction

    function string convert2string();
        return $sformatf("order=%0d pc=%08h instr=%08h rd=x%0d we=%0b",
                         order, pc, instr, rd_addr, rd_we);
    endfunction

endclass

class soc_obs_monitor extends uvm_monitor;

    virtual soc_obs_if vif;
    soc_cfg            cfg;

    uvm_analysis_port #(soc_retire_item) ap;

    `uvm_component_utils(soc_obs_monitor)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(soc_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "soc_cfg not found for soc_obs_monitor")
    endfunction

    protected function int unsigned onehot_count(bit [8:0] value);
        int unsigned n = 0;
        foreach (value[i])
            n += value[i];
        return n;
    endfunction

    task run_phase(uvm_phase phase);
        soc_retire_item item;
        int unsigned    irq_pulses;
        bit             saw_trap;

        irq_pulses = 0;
        forever begin
            @(vif.mon_cb);
            if (!vif.reset_n) begin
                cfg.stats.n_cycle = 0;
                irq_pulses        = 0;
                continue;
            end

            // irq_accept can fire on a cycle with no retirement, and the
            // instructions already in M and W still retire after it, so the
            // count is handed to the scoreboard, which spends one credit on the
            // redirect whenever it actually shows up in the PC chain.
            saw_trap = vif.mon_cb.trap_taken;
            if (saw_trap)
                cfg.stats.irq_taken++;
            cfg.stats.n_cycle++;

            // docs/reference/01 section 5: exactly one cycle_reason per cycle.
            if (onehot_count(vif.mon_cb.cycle_reason_onehot) != 1) begin
                cfg.stats.onehot_violations++;
                `uvm_error("ONEHOT",
                    $sformatf("cycle classifier is not one-hot: %09b at cycle %0d",
                              vif.mon_cb.cycle_reason_onehot, cfg.stats.n_cycle))
            end

            if (!vif.mon_cb.retire_valid) begin
                irq_pulses += saw_trap;
                continue;
            end

            item           = soc_retire_item::type_id::create("retire");
            item.order     = vif.mon_cb.retire_order;
            item.pc        = vif.mon_cb.retire_pc;
            item.pc_next   = vif.mon_cb.retire_pc_next;
            item.instr     = vif.mon_cb.retire_instr;
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
            item.irq_pulses = irq_pulses + int'(saw_trap);
            irq_pulses      = 0;

            cfg.stats.n_retire++;
            if (!cfg.stats.halt_seen) begin
                if (item.instr == cfg.halt_instr) begin
                    cfg.stats.halt_seen = 1'b1;
                    cfg.stats.halt_e.trigger();
                    `uvm_info("HALT",
                        $sformatf("HALT retired at pc=0x%08h after %0d retirements",
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

class soc_obs_agent extends uvm_agent;

    soc_obs_monitor monitor;
    soc_cfg         cfg;

    `uvm_component_utils(soc_obs_agent)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(soc_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "soc_cfg not found for soc_obs_agent")
        is_active   = UVM_PASSIVE;
        monitor     = soc_obs_monitor::type_id::create("monitor", this);
        monitor.vif = cfg.obs_vif;
    endfunction

endclass
