// Environment for hdl/axi/cache_axi_master.v: the three native initiators, the
// AXI slave responder and the checks.
class axi_env extends uvm_env;

    refill_agent    i_refill_agent;
    refill_agent    d_refill_agent;
    wthru_agent     write_agent;
    axi_slave_agent slave_agent;
    axi_scoreboard  scoreboard;

    axi_bus_coverage    bus_cov;
    axi_refill_coverage refill_cov;

    axi_cfg cfg;

    `uvm_component_utils(axi_env)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for axi_env")

        i_refill_agent           = refill_agent::type_id::create("i_refill_agent", this);
        i_refill_agent.is_icache = 1'b1;
        i_refill_agent.port_name = "I";

        d_refill_agent           = refill_agent::type_id::create("d_refill_agent", this);
        d_refill_agent.is_icache = 1'b0;
        d_refill_agent.port_name = "D";

        write_agent = wthru_agent::type_id::create("write_agent", this);
        slave_agent = axi_slave_agent::type_id::create("slave_agent", this);
        scoreboard  = axi_scoreboard::type_id::create("scoreboard", this);
        bus_cov     = axi_bus_coverage::type_id::create("bus_cov", this);
        refill_cov  = axi_refill_coverage::type_id::create("refill_cov", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        i_refill_agent.monitor.ap.connect(scoreboard.refill_export);
        d_refill_agent.monitor.ap.connect(scoreboard.refill_export);
        write_agent.monitor.ap.connect(scoreboard.wthru_export);
        slave_agent.monitor.ap.connect(scoreboard.axi_export);
        slave_agent.monitor.ap.connect(bus_cov.analysis_export);
        i_refill_agent.monitor.ap.connect(refill_cov.analysis_export);
        d_refill_agent.monitor.ap.connect(refill_cov.analysis_export);
    endfunction

endclass
