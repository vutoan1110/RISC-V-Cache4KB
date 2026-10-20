// Environment for riscv_core_native: one responder agent per native port, a
// passive retirement monitor and the self-consistency scoreboard.
class core_env extends uvm_env;

    native_mem_agent imem_agent;
    native_mem_agent dmem_agent;
    rvfi_agent       retire_agent;
    core_scoreboard  scoreboard;

    core_retire_coverage retire_cov;
    core_dmem_coverage   dmem_cov;

    core_cfg cfg;

    `uvm_component_utils(core_env)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(core_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "core_cfg not found for core_env")

        imem_agent           = native_mem_agent::type_id::create("imem_agent", this);
        imem_agent.is_data   = 1'b0;
        imem_agent.port_name = "I";

        dmem_agent           = native_mem_agent::type_id::create("dmem_agent", this);
        dmem_agent.is_data   = 1'b1;
        dmem_agent.port_name = "D";

        retire_agent = rvfi_agent::type_id::create("retire_agent", this);
        scoreboard   = core_scoreboard::type_id::create("scoreboard", this);
        retire_cov   = core_retire_coverage::type_id::create("retire_cov", this);
        dmem_cov     = core_dmem_coverage::type_id::create("dmem_cov", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        imem_agent.monitor.ap.connect(scoreboard.imem_export);
        dmem_agent.monitor.ap.connect(scoreboard.dmem_export);
        retire_agent.monitor.ap.connect(scoreboard.rvfi_export);
        retire_agent.monitor.ap.connect(retire_cov.analysis_export);
        dmem_agent.monitor.ap.connect(dmem_cov.analysis_export);
    endfunction

endclass
