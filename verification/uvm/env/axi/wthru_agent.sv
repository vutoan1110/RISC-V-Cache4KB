// Initiator agent for the D-cache write-through channel.

class wthru_sequencer extends uvm_sequencer #(wthru_item);
    `uvm_component_utils(wthru_sequencer)
    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
endclass

// The driver finishes an item as soon as the request is accepted, without
// waiting for the response. That is what lets back-to-back stores fill both
// entries of the posted-write buffer, which is the interesting case.
class wthru_driver extends uvm_driver #(wthru_item);

    virtual wthru_if vif;
    axi_cfg          cfg;

    `uvm_component_utils(wthru_driver)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for wthru_driver")
    endfunction

    task run_phase(uvm_phase phase);
        wthru_item item;

        vif.drv_cb.req_valid <= 1'b0;
        vif.drv_cb.req_addr  <= 32'h0;
        vif.drv_cb.req_data  <= 32'h0;
        vif.drv_cb.req_strb  <= 4'h0;
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
            vif.drv_cb.req_data  <= item.data;
            vif.drv_cb.req_strb  <= item.strb;

            do @(vif.drv_cb); while (!vif.drv_cb.req_ready);
            vif.drv_cb.req_valid <= 1'b0;

            seq_item_port.item_done();
        end
    endtask

endclass

class wthru_monitor extends uvm_monitor;

    virtual wthru_if vif;
    axi_cfg          cfg;

    uvm_analysis_port #(wthru_item) ap;

    `uvm_component_utils(wthru_monitor)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for wthru_monitor")
    endfunction

    task run_phase(uvm_phase phase);
        wthru_item       pending[$];
        wthru_item       item;
        longint unsigned cyc;

        cyc = 0;
        forever begin
            @(vif.mon_cb);
            if (!vif.reset_n) begin
                pending.delete();
                cyc = 0;
                continue;
            end
            cyc++;

            if (vif.mon_cb.req_valid && vif.mon_cb.req_ready) begin
                item              = wthru_item::type_id::create("wthru");
                item.addr         = vif.mon_cb.req_addr;
                item.data         = vif.mon_cb.req_data;
                item.strb         = vif.mon_cb.req_strb;
                item.accept_cycle = cyc;
                pending.push_back(item);
                cfg.stats.wthru_req++;
            end

            if (vif.mon_cb.rsp_valid) begin
                if (pending.size() == 0)
                    `uvm_error("WTHRURSP", "write-through response with no accepted request")
                else begin
                    item           = pending.pop_front();
                    item.rsp_cycle = cyc;
                    item.error     = vif.mon_cb.rsp_error;
                    cfg.stats.wthru_rsp++;

                    // Posted-write contract, reference doc 02 section 5.1.
                    if (item.error)
                        `uvm_error("WTHRUERR",
                            $sformatf("d_write_rsp_error is set for 0x%08h; it is always 0",
                                      item.addr))
                    if ((item.rsp_cycle - item.accept_cycle) != 1)
                        `uvm_error("WTHRULAT",
                            $sformatf("write to 0x%08h answered %0d cycles after accept, the posted buffer answers in 1",
                                      item.addr, item.rsp_cycle - item.accept_cycle))
                    ap.write(item);
                end
            end
        end
    endtask

endclass

class wthru_agent extends uvm_agent;

    wthru_driver    driver;
    wthru_monitor   monitor;
    wthru_sequencer sequencer;

    axi_cfg cfg;

    `uvm_component_utils(wthru_agent)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for wthru_agent")

        monitor     = wthru_monitor::type_id::create("monitor", this);
        monitor.vif = cfg.wthru_vif;

        sequencer   = wthru_sequencer::type_id::create("sequencer", this);
        driver      = wthru_driver::type_id::create("driver", this);
        driver.vif  = cfg.wthru_vif;
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
