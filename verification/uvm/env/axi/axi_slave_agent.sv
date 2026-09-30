// AXI4 slave agent. It answers cache_axi_master out of the shared memory
// model and can apply backpressure on every channel.
//
// Only the subset the design uses is modelled: 32-bit data, ID 0, reads are a
// single INCR burst, writes are a single beat. Anything else the DUT emits is
// reported by the monitor rather than silently absorbed.
class axi_slave_driver extends uvm_driver;

    virtual axi4_if vif;
    axi_cfg         cfg;

    `uvm_component_utils(axi_slave_driver)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for axi_slave_driver")
    endfunction

    protected function bit stall(int unsigned pct);
        if (pct == 0)
            return 1'b0;
        return ($urandom_range(99, 0) < pct);
    endfunction

    protected task drive_idle();
        vif.slv_cb.arready <= 1'b0;
        vif.slv_cb.rvalid  <= 1'b0;
        vif.slv_cb.rdata   <= 32'h0;
        vif.slv_cb.rlast   <= 1'b0;
        vif.slv_cb.rresp   <= 2'b00;
        vif.slv_cb.awready <= 1'b0;
        vif.slv_cb.wready  <= 1'b0;
        vif.slv_cb.bvalid  <= 1'b0;
        vif.slv_cb.bresp   <= 2'b00;
    endtask

    task run_phase(uvm_phase phase);
        // Read side.
        bit          rd_active;
        bit [31:0]   rd_addr;
        int unsigned rd_len;
        int unsigned rd_idx;
        // Write side.
        bit          aw_seen;
        bit          w_seen;
        bit [31:0]   wr_addr;
        bit [31:0]   wr_data;
        bit [3:0]    wr_strb;
        bit          b_armed;
        int unsigned b_delay;
        // What is currently driven, so the handshakes can be evaluated.
        bit          ar_ready_now;
        bit          r_valid_now;
        bit          aw_ready_now;
        bit          w_ready_now;
        bit          b_valid_now;
        // Next values.
        bit          nxt_arready;
        bit          nxt_rvalid;
        bit          nxt_rlast;
        bit [31:0]   nxt_rdata;
        bit          nxt_awready;
        bit          nxt_wready;
        bit          nxt_bvalid;

        drive_idle();
        rd_active = 0; aw_seen = 0; w_seen = 0; b_armed = 0;
        ar_ready_now = 0; r_valid_now = 0;
        aw_ready_now = 0; w_ready_now = 0; b_valid_now = 0;
        nxt_rdata = 32'h0; nxt_rlast = 1'b0;

        forever begin
            @(vif.slv_cb);

            if (!vif.reset_n) begin
                rd_active = 0; rd_idx = 0; aw_seen = 0; w_seen = 0; b_armed = 0;
                ar_ready_now = 0; r_valid_now = 0;
                aw_ready_now = 0; w_ready_now = 0; b_valid_now = 0;
                drive_idle();
                continue;
            end

            // ---------------- read address ----------------
            if (!rd_active && ar_ready_now && vif.slv_cb.arvalid) begin
                rd_active = 1'b1;
                rd_addr   = vif.slv_cb.araddr;
                rd_len    = int'(vif.slv_cb.arlen) + 1;
                rd_idx    = 0;
            end

            // ---------------- read data ----------------
            if (r_valid_now && vif.slv_cb.rready) begin
                rd_idx++;
                if (rd_idx >= rd_len)
                    rd_active = 1'b0;
            end

            // AXI forbids dropping RVALID before RREADY, so an in-flight beat
            // is held; a stall may only delay a beat that has not started.
            if (r_valid_now && !vif.slv_cb.rready) begin
                nxt_rvalid = 1'b1;      // nxt_rdata / nxt_rlast keep their value
            end
            else if (rd_active && !stall(cfg.r_stall_pct)) begin
                nxt_rvalid = 1'b1;
                nxt_rdata  = cfg.mem.read_word(rd_addr + 32'(4 * rd_idx));
                nxt_rlast  = (rd_idx == (rd_len - 1));
            end
            else begin
                nxt_rvalid = 1'b0;
                nxt_rlast  = 1'b0;
            end

            nxt_arready = !rd_active && !stall(cfg.ar_stall_pct);

            // ---------------- write address and data ----------------
            if (!aw_seen && aw_ready_now && vif.slv_cb.awvalid) begin
                aw_seen = 1'b1;
                wr_addr = vif.slv_cb.awaddr;
            end
            if (!w_seen && w_ready_now && vif.slv_cb.wvalid) begin
                w_seen  = 1'b1;
                wr_data = vif.slv_cb.wdata;
                wr_strb = vif.slv_cb.wstrb;
            end

            if (aw_seen && w_seen && !b_armed && !b_valid_now) begin
                cfg.mem.write_word(wr_addr, wr_data, wr_strb);
                b_armed = 1'b1;
                b_delay = (cfg.b_delay_max == 0) ? 0 :
                          $urandom_range(cfg.b_delay_max, 0);
            end

            if (b_valid_now && vif.slv_cb.bready) begin
                aw_seen = 1'b0;
                w_seen  = 1'b0;
                b_armed = 1'b0;
                nxt_bvalid = 1'b0;
            end
            else if (b_valid_now) begin
                nxt_bvalid = 1'b1;      // hold until BREADY
            end
            else if (b_armed) begin
                if (b_delay == 0)
                    nxt_bvalid = 1'b1;
                else begin
                    b_delay--;
                    nxt_bvalid = 1'b0;
                end
            end
            else begin
                nxt_bvalid = 1'b0;
            end

            nxt_awready = !aw_seen && !stall(cfg.aw_stall_pct);
            nxt_wready  = !w_seen  && !stall(cfg.w_stall_pct);

            ar_ready_now = nxt_arready;
            r_valid_now  = nxt_rvalid;
            aw_ready_now = nxt_awready;
            w_ready_now  = nxt_wready;
            b_valid_now  = nxt_bvalid;

            vif.slv_cb.arready <= nxt_arready;
            vif.slv_cb.rvalid  <= nxt_rvalid;
            vif.slv_cb.rdata   <= nxt_rdata;
            vif.slv_cb.rlast   <= nxt_rlast;
            vif.slv_cb.rresp   <= 2'b00;
            vif.slv_cb.awready <= nxt_awready;
            vif.slv_cb.wready  <= nxt_wready;
            vif.slv_cb.bvalid  <= nxt_bvalid;
            vif.slv_cb.bresp   <= 2'b00;
        end
    endtask

endclass

class axi_monitor extends uvm_monitor;

    virtual axi4_if vif;
    axi_cfg         cfg;

    uvm_analysis_port #(axi_item) ap;

    `uvm_component_utils(axi_monitor)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for axi_monitor")
    endfunction

    task run_phase(uvm_phase phase);
        axi_item         rd;
        axi_item         wr;
        int              outstanding_rd;
        bit              wr_open;
        longint unsigned cyc;

        rd = null;
        wr = null;
        outstanding_rd = 0;
        wr_open = 1'b0;
        cyc = 0;

        forever begin
            @(vif.mon_cb);
            if (!vif.reset_n) begin
                rd = null; wr = null;
                outstanding_rd = 0; wr_open = 1'b0; cyc = 0;
                continue;
            end
            cyc++;

            // ---------------- AR ----------------
            if (vif.mon_cb.arvalid && vif.mon_cb.arready) begin
                outstanding_rd++;
                if (outstanding_rd > 1)
                    `uvm_error("AXIOUTSTANDING",
                        $sformatf("%0d read bursts outstanding; the design issues one at a time",
                                  outstanding_rd))
                if (longint'(outstanding_rd) > cfg.stats.max_outstanding_reads)
                    cfg.stats.max_outstanding_reads = outstanding_rd;

                rd             = axi_item::type_id::create("rd");
                rd.kind        = AXI_READ_BURST;
                rd.addr        = vif.mon_cb.araddr;
                rd.len         = vif.mon_cb.arlen;
                rd.size        = vif.mon_cb.arsize;
                rd.burst       = vif.mon_cb.arburst;
                rd.start_cycle = cyc;
            end

            // ---------------- R ----------------
            if (vif.mon_cb.rvalid && vif.mon_cb.rready) begin
                if (rd == null)
                    `uvm_error("AXIRNOAR", "R beat with no outstanding read burst")
                else begin
                    rd.data.push_back(vif.mon_cb.rdata);
                    rd.resp = vif.mon_cb.rresp;
                    cfg.stats.axi_read_beats++;
                    if (vif.mon_cb.rlast) begin
                        rd.end_cycle = cyc;
                        outstanding_rd--;
                        cfg.stats.axi_read_burst++;
                        ap.write(rd);
                        rd = null;
                    end
                end
            end

            // ---------------- AW / W ----------------
            if (vif.mon_cb.awvalid && vif.mon_cb.awready) begin
                if (wr == null) begin
                    wr = axi_item::type_id::create("wr");
                    wr.kind = AXI_WRITE;
                    wr.start_cycle = cyc;
                end
                wr.addr  = vif.mon_cb.awaddr;
                wr.len   = vif.mon_cb.awlen;
                wr.size  = vif.mon_cb.awsize;
                wr.burst = vif.mon_cb.awburst;
                wr_open  = 1'b1;
            end

            if (vif.mon_cb.wvalid && vif.mon_cb.wready) begin
                if (wr == null) begin
                    wr = axi_item::type_id::create("wr");
                    wr.kind = AXI_WRITE;
                    wr.start_cycle = cyc;
                end
                wr.data.push_back(vif.mon_cb.wdata);
                wr.strb = vif.mon_cb.wstrb;
                if (!vif.mon_cb.wlast)
                    `uvm_error("AXIWLAST",
                        "W beat without wlast; the design only issues single-beat writes")
                wr_open = 1'b1;
            end

            // ---------------- B ----------------
            if (vif.mon_cb.bvalid && vif.mon_cb.bready) begin
                if (!wr_open || (wr == null))
                    `uvm_error("AXIBNOAW", "B response with no outstanding write")
                else begin
                    wr.resp      = vif.mon_cb.bresp;
                    wr.end_cycle = cyc;
                    cfg.stats.axi_write++;
                    ap.write(wr);
                    wr      = null;
                    wr_open = 1'b0;
                end
            end
        end
    endtask

endclass

class axi_slave_agent extends uvm_agent;

    axi_slave_driver driver;
    axi_monitor      monitor;

    axi_cfg cfg;

    `uvm_component_utils(axi_slave_agent)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(axi_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("NOCFG", "axi_cfg not found for axi_slave_agent")

        monitor     = axi_monitor::type_id::create("monitor", this);
        monitor.vif = cfg.axi_vif;
        driver      = axi_slave_driver::type_id::create("driver", this);
        driver.vif  = cfg.axi_vif;
    endfunction

endclass
