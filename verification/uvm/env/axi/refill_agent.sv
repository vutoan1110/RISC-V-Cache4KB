// Initiator agent for one native refill channel of cache_axi_master.

class refill_sequencer extends uvm_sequencer #(refill_item);
    `uvm_component_utils(refill_sequencer)
    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
endclass

// Drives one refill request at a time and holds it until the last response
// beat, which is what the cache controllers do.
class refill_driver extends uvm_driver #(refill_item);

    virtual refill_if vif;
    axi_cfg           cfg;
    string            port_name = "I";

    `uvm_component_utils(refill_driver)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for refill_driver")
    endfunction

    task run_phase(uvm_phase phase);
        refill_item item;

        vif.drv_cb.req_valid <= 1'b0;
        vif.drv_cb.req_addr  <= 32'h0;
        wait (vif.reset_n === 1'b1);
        // Align to the clocking block before the first drive. A drive issued
        // between edges is applied at the next edge plus the output skew, so
        // the DUT would not see req_valid on the cycle the accept loop below
        // examines, and the first request would be silently lost.
        @(vif.drv_cb);

        forever begin
            seq_item_port.get_next_item(item);

            vif.drv_cb.req_valid <= 1'b1;
            vif.drv_cb.req_addr  <= item.addr;

            // Hold the request stable until it is accepted.
            do @(vif.drv_cb); while (!vif.drv_cb.req_ready);
            vif.drv_cb.req_valid <= 1'b0;

            // Collect the burst. The channel carries one refill at a time.
            item.beat.delete();
            item.error = 1'b0;
            forever begin
                @(vif.drv_cb);
                if (vif.drv_cb.rsp_valid) begin
                    item.beat.push_back(vif.drv_cb.rsp_data);
                    item.error = item.error | vif.drv_cb.rsp_error;
                    if (vif.drv_cb.rsp_last)
                        break;
                end
            end

            seq_item_port.item_done();
        end
    endtask

endclass

class refill_monitor extends uvm_monitor;

    virtual refill_if vif;
    axi_cfg           cfg;
    bit               is_icache = 1;
    string            port_name = "I";

    uvm_analysis_port #(refill_item) ap;

    `uvm_component_utils(refill_monitor)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for refill_monitor")
    endfunction

    task run_phase(uvm_phase phase);
        refill_item      item;
        bit              active;
        longint unsigned cyc;

        active = 1'b0;
        cyc    = 0;
        item   = null;

        forever begin
            @(vif.mon_cb);
            if (!vif.reset_n) begin
                active = 1'b0;
                cyc    = 0;
                continue;
            end
            cyc++;

            if (vif.mon_cb.req_valid && vif.mon_cb.req_ready) begin
                if (active)
                    `uvm_error("REFILLOVERLAP",
                        $sformatf("%s refill accepted a second request before the first finished",
                                  port_name))
                item              = refill_item::type_id::create("refill");
                item.addr         = vif.mon_cb.req_addr;
                item.is_icache    = is_icache;
                item.accept_cycle = cyc;
                item.error        = 1'b0;
                active            = 1'b1;
                if (is_icache) cfg.stats.i_refill_req++;
                else           cfg.stats.d_refill_req++;

                if (vif.mon_cb.req_addr[3:0] != 4'h0)
                    `uvm_error("REFILLALIGN",
                        $sformatf("%s refill address 0x%08h is not 16-byte aligned",
                                  port_name, vif.mon_cb.req_addr))
            end

            if (vif.mon_cb.rsp_valid) begin
                if (!active) begin
                    `uvm_error("REFILLRSP",
                        $sformatf("%s refill response with no outstanding request", port_name))
                    continue;
                end
                item.beat.push_back(vif.mon_cb.rsp_data);
                item.error = item.error | vif.mon_cb.rsp_error;
                if (vif.mon_cb.rsp_last) begin
                    item.done_cycle = cyc;
                    active          = 1'b0;
                    ap.write(item);
                end
                else if (item.beat.size() > cfg.refill_beats)
                    `uvm_error("REFILLLEN",
                        $sformatf("%s refill produced more than %0d beats without rsp_last",
                                  port_name, cfg.refill_beats))
            end
        end
    endtask

endclass

class refill_agent extends uvm_agent;

    refill_driver    driver;
    refill_monitor   monitor;
    refill_sequencer sequencer;

    axi_cfg cfg;
    bit     is_icache = 1;
    string  port_name = "I";

    `uvm_component_utils(refill_agent)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for refill_agent")

        monitor           = refill_monitor::type_id::create("monitor", this);
        monitor.vif       = is_icache ? cfg.i_refill_vif : cfg.d_refill_vif;
        monitor.is_icache = is_icache;
        monitor.port_name = port_name;

        sequencer      = refill_sequencer::type_id::create("sequencer", this);
        driver         = refill_driver::type_id::create("driver", this);
        driver.vif     = is_icache ? cfg.i_refill_vif : cfg.d_refill_vif;
        driver.port_name = port_name;
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
