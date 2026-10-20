// Passive APB agent plus the explicit predictor that keeps the register model
// in step with what the CPU writes.
class apb_monitor extends uvm_monitor;

    virtual apb_if vif;
    soc_cfg        cfg;

    uvm_analysis_port #(apb_item) ap;

    `uvm_component_utils(apb_monitor)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(soc_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "soc_cfg not found for apb_monitor")
    endfunction

    task run_phase(uvm_phase phase);
        apb_item         item;
        longint unsigned cyc;

        cyc = 0;
        forever begin
            @(vif.mon_cb);
            if (!vif.reset_n) begin
                cyc = 0;
                continue;
            end
            cyc++;

            // A transfer completes in the ACCESS phase, when PREADY is high.
            if (vif.mon_cb.psel && vif.mon_cb.penable && vif.mon_cb.pready) begin
                item        = apb_item::type_id::create("apb");
                item.addr   = vif.mon_cb.paddr;
                item.write  = vif.mon_cb.pwrite;
                item.strb   = vif.mon_cb.pstrb;
                item.wdata  = vif.mon_cb.pwdata;
                item.rdata  = vif.mon_cb.prdata;
                item.slverr = vif.mon_cb.pslverr;
                item.cycle  = cyc;

                if (item.write) cfg.stats.apb_write++;
                else            cfg.stats.apb_read++;

                if (item.slverr)
                    `uvm_error("APBSLVERR",
                        $sformatf("APB %s to 0x%08h answered PSLVERR",
                                  item.write ? "write" : "read", item.addr))

                ap.write(item);
            end
        end
    endtask

endclass

// Turns observed APB traffic into register-model updates. A write predicts the
// value the CPU stored; a read predicts what the RTL returned, so the mirror
// tracks read-only status registers too.
class apb_reg_predictor extends uvm_subscriber #(apb_item);

    soc_cfg cfg;

    `uvm_component_utils(apb_reg_predictor)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(soc_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "soc_cfg not found for apb_reg_predictor")
    endfunction

    function void write(apb_item t);
        uvm_reg        r;
        uvm_reg_data_t value;

        if (cfg.regs == null)
            return;

        r = cfg.regs.default_map.get_reg_by_offset(t.addr);
        if (r == null) begin
            `uvm_info("REGPRED",
                $sformatf("APB access to 0x%08h is not in the register model", t.addr),
                UVM_HIGH)
            return;
        end

        value = t.write ? t.wdata : t.rdata;
        void'(r.predict(value, t.write ? t.strb : 4'hF,
                        t.write ? UVM_PREDICT_WRITE : UVM_PREDICT_READ));
        `uvm_info("REGPRED",
            $sformatf("%s %s <= 0x%08h", r.get_full_name(),
                      t.write ? "write" : "read", value), UVM_HIGH)
    endfunction

endclass

class apb_agent extends uvm_agent;

    apb_monitor       monitor;
    apb_reg_predictor predictor;

    soc_cfg cfg;

    `uvm_component_utils(apb_agent)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(soc_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "soc_cfg not found for apb_agent")
        is_active   = UVM_PASSIVE;
        monitor     = apb_monitor::type_id::create("monitor", this);
        monitor.vif = cfg.apb_vif;
        predictor   = apb_reg_predictor::type_id::create("predictor", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        monitor.ap.connect(predictor.analysis_export);
    endfunction

endclass
