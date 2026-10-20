// Responder agent for one native port. Active in the UVM sense: the driver
// answers the DUT rather than initiating traffic.
class native_mem_agent extends uvm_agent;

    native_mem_driver    driver;
    native_mem_monitor   monitor;
    native_mem_sequencer sequencer;

    core_cfg cfg;
    bit      is_data   = 1;
    string   port_name = "d";

    `uvm_component_utils(native_mem_agent)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(core_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "core_cfg not found for native_mem_agent")

        monitor           = native_mem_monitor::type_id::create("monitor", this);
        monitor.vif       = is_data ? cfg.dmem_vif : cfg.imem_vif;
        monitor.is_data   = is_data;
        monitor.port_name = port_name;

        if (get_is_active() == UVM_ACTIVE) begin
            sequencer         = native_mem_sequencer::type_id::create("sequencer", this);
            driver            = native_mem_driver::type_id::create("driver", this);
            driver.vif        = is_data ? cfg.dmem_vif : cfg.imem_vif;
            driver.allow_write = is_data;
            driver.port_name   = port_name;
        end
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        if (get_is_active() == UVM_ACTIVE)
            driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
