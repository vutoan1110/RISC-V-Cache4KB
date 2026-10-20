// Retirement port is observation only, so this agent is always passive.
class rvfi_agent extends uvm_agent;

    rvfi_monitor monitor;
    core_cfg     cfg;

    `uvm_component_utils(rvfi_agent)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(core_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "core_cfg not found for rvfi_agent")
        is_active = UVM_PASSIVE;
        monitor     = rvfi_monitor::type_id::create("monitor", this);
        monitor.vif = cfg.rvfi_vif;
    endfunction

endclass
