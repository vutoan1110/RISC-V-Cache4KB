// Environment for hdl/soc_top.v: passive observation of the retirement port
// and the counter bank, a passive APB agent feeding the register model, and a
// UART serial agent.
class soc_env extends uvm_env;

    soc_obs_agent  obs_agent;
    apb_agent      bus_agent;
    uart_agent     serial_agent;
    soc_scoreboard scoreboard;

    soc_apb_coverage    apb_cov;
    soc_retire_coverage retire_cov;

    soc_cfg cfg;

    `uvm_component_utils(soc_env)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(soc_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "soc_cfg not found for soc_env")

        obs_agent    = soc_obs_agent::type_id::create("obs_agent", this);
        bus_agent    = apb_agent::type_id::create("bus_agent", this);
        serial_agent = uart_agent::type_id::create("serial_agent", this);
        scoreboard   = soc_scoreboard::type_id::create("scoreboard", this);
        apb_cov      = soc_apb_coverage::type_id::create("apb_cov", this);
        retire_cov   = soc_retire_coverage::type_id::create("retire_cov", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        obs_agent.monitor.ap.connect(scoreboard.retire_export);
        bus_agent.monitor.ap.connect(scoreboard.apb_export);
        bus_agent.monitor.ap.connect(apb_cov.analysis_export);
        obs_agent.monitor.ap.connect(retire_cov.analysis_export);
    endfunction

endclass
