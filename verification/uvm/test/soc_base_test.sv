// Base test for the SoC environment. The program comes from the MEMFILE
// parameter of soc_top, so there is no backdoor load here: the test only owns
// the run window and the verdict.
class soc_base_test extends uvm_test;

    soc_env env;
    soc_cfg cfg;

    `uvm_component_utils(soc_base_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void configure();
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        cfg       = soc_cfg::type_id::create("cfg");
        cfg.stats = soc_stats::type_id::create("stats");

        configure();

        void'($value$plusargs("EXPECT_RETIRE=%d",   cfg.expected_retire));
        void'($value$plusargs("TIMEOUT_CYCLES=%d",  cfg.timeout_cycles));
        void'($value$plusargs("UART_BIT_CYCLES=%d", cfg.uart_bit_cycles));

        if (!uvm_config_db #(virtual soc_obs_if)::get(this, "", "obs_vif", cfg.obs_vif))
            `uvm_fatal("NOVIF", "virtual interface 'obs_vif' not set")
        if (!uvm_config_db #(virtual apb_if)::get(this, "", "apb_vif", cfg.apb_vif))
            `uvm_fatal("NOVIF", "virtual interface 'apb_vif' not set")
        if (!uvm_config_db #(virtual uart_if)::get(this, "", "uart_vif", cfg.uart_vif))
            `uvm_fatal("NOVIF", "virtual interface 'uart_vif' not set")

        // uvm_reg_block registers a resource named after the block, and a
        // hierarchical block name contains dots, which UVM 1.2 flags as regex
        // meta characters. The warning says nothing about the design, so it is
        // demoted rather than left to clutter every SoC run.
        uvm_root::get().set_report_id_action_hier("UVM/RSRC/NOREGEX", UVM_NO_ACTION);

        cfg.regs = soc_reg_model::type_id::create("regs");
        cfg.regs.build();

        uvm_config_db #(soc_cfg)::set(this, "*", "cfg", cfg);
        env = soc_env::type_id::create("env", this);
    endfunction

    task run_phase(uvm_phase phase);
        phase.raise_objection(this, "soc program");

        wait (cfg.obs_vif.reset_n === 1'b1);

        fork
            begin : wait_halt
                if (!cfg.stats.halt_e.is_on())
                    cfg.stats.halt_e.wait_trigger();
            end
            begin : watchdog
                repeat (cfg.timeout_cycles) @(posedge cfg.obs_vif.clk);
                `uvm_error("TIMEOUT",
                    $sformatf("no HALT after %0d cycles (%0d retirements so far)",
                              cfg.timeout_cycles, cfg.stats.n_retire))
            end
        join_any
        disable fork;

        // Let the last bus and counter activity settle before the checks.
        repeat (16) @(posedge cfg.obs_vif.clk);

        phase.drop_objection(this, "soc program");
    endtask

    function void report_phase(uvm_phase phase);
        uvm_report_server svr;
        uvm_event         assert_e;
        int unsigned      n_err;
        string            status_path;
        int               fd;

        super.report_phase(phase);

        assert_e = uvm_event_pool::get_global("soc_assert_report");
        assert_e.trigger();

        svr   = uvm_report_server::get_server();
        n_err = svr.get_severity_count(UVM_ERROR) + svr.get_severity_count(UVM_FATAL);

        if (n_err == 0)
            $display("[PASS] %s: 0 UVM_ERROR, 0 UVM_FATAL, %0d retirements before HALT",
                     get_type_name(), cfg.stats.n_retire_before_halt);
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
