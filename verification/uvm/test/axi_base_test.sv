// Base test for the cache_axi_master environment.
class axi_base_test extends uvm_test;

    axi_env env;
    axi_cfg cfg;

    int unsigned n_i_refill = 20;
    int unsigned n_d_refill = 20;
    int unsigned n_write    = 40;

    bit [31:0] read_base  = 32'h0000_0000;
    bit [31:0] read_span  = 32'h0000_0400;
    bit [31:0] write_base = 32'h0000_1000;
    bit [31:0] write_span = 32'h0000_0400;

    `uvm_component_utils(axi_base_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void configure();
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        cfg       = axi_cfg::type_id::create("cfg");
        cfg.stats = axi_stats::type_id::create("stats");
        cfg.mem   = native_mem_model::type_id::create("mem");

        configure();
        cfg.mem.set_size(cfg.mem_size_bytes);

        void'($value$plusargs("N_I_REFILL=%d", n_i_refill));
        void'($value$plusargs("N_D_REFILL=%d", n_d_refill));
        void'($value$plusargs("N_WRITE=%d",    n_write));
        void'($value$plusargs("AR_STALL=%d",   cfg.ar_stall_pct));
        void'($value$plusargs("R_STALL=%d",    cfg.r_stall_pct));
        void'($value$plusargs("AW_STALL=%d",   cfg.aw_stall_pct));
        void'($value$plusargs("W_STALL=%d",    cfg.w_stall_pct));
        void'($value$plusargs("B_DELAY=%d",    cfg.b_delay_max));

        // Published by the testbench from its own LINE_WORDS parameter, so
        // the checkers always expect the burst the DUT was built to issue.
        if (!uvm_config_db #(int unsigned)::get(this, "", "refill_beats",
                                                cfg.refill_beats))
            `uvm_fatal("CFG", "refill_beats not provided by the testbench")

        if (!uvm_config_db #(virtual refill_if)::get(this, "", "i_refill_vif", cfg.i_refill_vif))
            `uvm_fatal("NOVIF", "virtual interface 'i_refill_vif' not set")
        if (!uvm_config_db #(virtual refill_if)::get(this, "", "d_refill_vif", cfg.d_refill_vif))
            `uvm_fatal("NOVIF", "virtual interface 'd_refill_vif' not set")
        if (!uvm_config_db #(virtual wthru_if)::get(this, "", "wthru_vif", cfg.wthru_vif))
            `uvm_fatal("NOVIF", "virtual interface 'wthru_vif' not set")
        if (!uvm_config_db #(virtual axi4_if)::get(this, "", "axi_vif", cfg.axi_vif))
            `uvm_fatal("NOVIF", "virtual interface 'axi_vif' not set")

        uvm_config_db #(axi_cfg)::set(this, "*", "cfg", cfg);
        env = axi_env::type_id::create("env", this);
    endfunction

    // Give the read window content, otherwise every refill check compares
    // zeroes against zeroes and proves nothing.
    function void start_of_simulation_phase(uvm_phase phase);
        bit [31:0] a;
        super.start_of_simulation_phase(phase);
        for (a = read_base; a < (read_base + read_span); a += 4)
            cfg.mem.write_word(a, a ^ 32'hA5A5_5A5A, 4'b1111);
        `uvm_info("MEMINIT",
            $sformatf("seeded read window 0x%08h..0x%08h with a per-address pattern",
                      read_base, read_base + read_span - 1), UVM_LOW)
    endfunction

    task run_phase(uvm_phase phase);
        axi_traffic_seq seq;

        phase.raise_objection(this, "axi traffic");

        seq            = axi_traffic_seq::type_id::create("seq");
        seq.i_sqr      = env.i_refill_agent.sequencer;
        seq.d_sqr      = env.d_refill_agent.sequencer;
        seq.w_sqr      = env.write_agent.sequencer;
        seq.n_i_refill = n_i_refill;
        seq.n_d_refill = n_d_refill;
        seq.n_write    = n_write;
        seq.read_base  = read_base;
        seq.read_span  = read_span;
        seq.write_base = write_base;
        seq.write_span = write_span;

        fork
            seq.start(null);
            begin
                repeat (cfg.timeout_cycles) @(posedge cfg.axi_vif.clk);
                `uvm_error("TIMEOUT",
                    $sformatf("AXI traffic did not finish in %0d cycles", cfg.timeout_cycles))
            end
        join_any
        disable fork;

        // Let the posted-write buffer drain before the checks run.
        repeat (64) @(posedge cfg.axi_vif.clk);

        phase.drop_objection(this, "axi traffic");
    endtask

    // The stimulus has to have reached the DUT, otherwise every check above
    // passes on an empty run.
    function void check_phase(uvm_phase phase);
        super.check_phase(phase);
        if (cfg.stats.i_refill_done != n_i_refill)
            `uvm_error("STIMULUS",
                $sformatf("asked for %0d I refills, %0d completed", n_i_refill,
                          cfg.stats.i_refill_done))
        if (cfg.stats.d_refill_done != n_d_refill)
            `uvm_error("STIMULUS",
                $sformatf("asked for %0d D refills, %0d completed", n_d_refill,
                          cfg.stats.d_refill_done))
        if (cfg.stats.wthru_req != n_write)
            `uvm_error("STIMULUS",
                $sformatf("asked for %0d writes, %0d were accepted", n_write,
                          cfg.stats.wthru_req))
    endfunction

    function void report_phase(uvm_phase phase);
        uvm_report_server svr;
        uvm_event         assert_e;
        int unsigned      n_err;
        string            status_path;
        int               fd;

        super.report_phase(phase);

        // Let tb_axi_top print how many cycles the bound assertions sampled.
        assert_e = uvm_event_pool::get_global("axi_assert_report");
        assert_e.trigger();

        svr   = uvm_report_server::get_server();
        n_err = svr.get_severity_count(UVM_ERROR) + svr.get_severity_count(UVM_FATAL);

        if (n_err == 0)
            $display("[PASS] %s: 0 UVM_ERROR, 0 UVM_FATAL, %0d read bursts, %0d writes",
                     get_type_name(), cfg.stats.axi_read_burst, cfg.stats.axi_write);
        else
            $display("[FAIL] %s: %0d UVM_ERROR/UVM_FATAL", get_type_name(), n_err);

        status_path = {"verification/uvm/out/", get_type_name(), ".status"};
        void'($value$plusargs("STATUS=%s", status_path));
        fd = $fopen(status_path, "w");
        if (fd != 0) begin
            $fdisplay(fd, "%s %s %0d", (n_err == 0) ? "PASS" : "FAIL",
                      get_type_name(), n_err);
            $fclose(fd);
        end
    endfunction

endclass
