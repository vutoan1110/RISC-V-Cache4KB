// Passive observer of one native port. Besides publishing accepts and
// responses it enforces the three protocol rules of
// docs/reference/01_RTL_ARCHITECTURE.md section 2.
class native_mem_monitor extends uvm_monitor;

    virtual native_if vif;
    core_cfg          cfg;
    bit               is_data   = 1;
    string            port_name = "d";

    uvm_analysis_port #(native_mem_item) ap;

    `uvm_component_utils(native_mem_monitor)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(core_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "core_cfg not found for native_mem_monitor")
    endfunction

    task run_phase(uvm_phase phase);
        int              outstanding;
        bit              hold_active;
        bit              h_write;
        bit [31:0]       h_addr;
        bit [31:0]       h_wdata;
        bit [3:0]        h_wstrb;
        longint unsigned cyc;
        native_mem_item  item;

        outstanding = 0;
        hold_active = 1'b0;
        cyc         = 0;

        forever begin
            @(vif.mon_cb);

            if (!vif.reset_n) begin
                outstanding = 0;
                hold_active = 1'b0;
                cyc         = 0;
                continue;
            end
            cyc++;

            // The requester must hold the payload stable under backpressure.
            if (hold_active) begin
                if (!vif.mon_cb.req_valid)
                    `uvm_error("REQDROP",
                        $sformatf("%s port dropped req_valid before req_ready", port_name))
                else if ((vif.mon_cb.req_addr !== h_addr) ||
                         (is_data && ((vif.mon_cb.req_write !== h_write) ||
                                      (vif.mon_cb.req_wdata !== h_wdata) ||
                                      (vif.mon_cb.req_wstrb !== h_wstrb))))
                    `uvm_error("REQUNSTABLE",
                        $sformatf("%s port request payload changed before req_ready", port_name))
            end

            if (vif.mon_cb.req_valid && vif.mon_cb.req_ready) begin
                hold_active = 1'b0;
                outstanding++;
                if (outstanding > 1)
                    `uvm_error("MULTIOUTSTANDING",
                        $sformatf("%s port has %0d outstanding requests, the protocol allows one",
                                  port_name, outstanding))

                item          = native_mem_item::type_id::create("acc");
                item.evt      = NATIVE_ACCEPT;
                item.is_write = is_data ? vif.mon_cb.req_write : 1'b0;
                item.addr     = vif.mon_cb.req_addr;
                item.wdata    = is_data ? vif.mon_cb.req_wdata : 32'h0;
                item.wstrb    = is_data ? vif.mon_cb.req_wstrb : 4'h0;
                item.cycle    = cyc;
                ap.write(item);
            end
            else if (vif.mon_cb.req_valid && !vif.mon_cb.req_ready) begin
                hold_active = 1'b1;
                h_write     = vif.mon_cb.req_write;
                h_addr      = vif.mon_cb.req_addr;
                h_wdata     = vif.mon_cb.req_wdata;
                h_wstrb     = vif.mon_cb.req_wstrb;
            end

            if (vif.mon_cb.rsp_valid) begin
                if (outstanding == 0)
                    `uvm_error("RSPNOREQ",
                        $sformatf("%s port response with no accepted request", port_name))
                else
                    outstanding--;

                item       = native_mem_item::type_id::create("rsp");
                item.evt   = NATIVE_RESPONSE;
                item.rdata = vif.mon_cb.rsp_rdata;
                item.error = vif.mon_cb.rsp_error;
                item.cycle = cyc;
                ap.write(item);
            end
        end
    endtask

endclass
