// Base test: build the environment, load a program image into the shared
// memory model before reset is released, and run until HALT.
class core_base_test extends uvm_test;

    core_env env;
    core_cfg cfg;

    `uvm_component_utils(core_base_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    // Subclasses override this to point at a different program or to tighten
    // the expected retirement count.
    virtual function void configure();
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        cfg       = core_cfg::type_id::create("cfg");
        cfg.stats = core_stats::type_id::create("stats");
        cfg.mem   = native_mem_model::type_id::create("mem");
        cfg.iss     = rv32_iss::type_id::create("iss");
        cfg.iss_mem = native_mem_model::type_id::create("iss_mem");

        configure();

        cfg.mem.set_size(cfg.mem_size_bytes);
        cfg.iss_mem.set_size(cfg.mem_size_bytes);
        cfg.iss.mem        = cfg.iss_mem;
        cfg.iss.halt_instr = cfg.halt_instr;
        cfg.iss.reset();

        // Plusargs win over the compiled-in defaults so one test class can run
        // several images or retirement budgets.
        void'($value$plusargs("HEX=%s", cfg.program_hex));
        void'($value$plusargs("EXPECT_RETIRE=%d", cfg.expected_retire));
        void'($value$plusargs("TIMEOUT_CYCLES=%d", cfg.timeout_cycles));
        void'($value$plusargs("RSP_LAT_MIN=%d", cfg.rsp_latency_min));
        void'($value$plusargs("RSP_LAT_MAX=%d", cfg.rsp_latency_max));

        if (!uvm_config_db #(virtual native_if)::get(this, "", "imem_vif", cfg.imem_vif))
            `uvm_fatal("NOVIF", "virtual interface 'imem_vif' not set")
        if (!uvm_config_db #(virtual native_if)::get(this, "", "dmem_vif", cfg.dmem_vif))
            `uvm_fatal("NOVIF", "virtual interface 'dmem_vif' not set")
        if (!uvm_config_db #(virtual rvfi_if)::get(this, "", "rvfi_vif", cfg.rvfi_vif))
            `uvm_fatal("NOVIF", "virtual interface 'rvfi_vif' not set")

        uvm_config_db #(core_cfg)::set(this, "*", "cfg", cfg);

        env = core_env::type_id::create("env", this);
    endfunction

    // Reset is released a few cycles into the run, so time zero is early
    // enough for a backdoor load.
    function void start_of_simulation_phase(uvm_phase phase);
        super.start_of_simulation_phase(phase);
        load_program();
    endfunction

    // Overridden by tests that build their program instead of reading a file.
    virtual function void load_program();
        void'(mem_backdoor::load(cfg.mem, cfg.program_hex, get_type_name()));
        if (cfg.use_iss)
            void'(mem_backdoor::load(cfg.iss_mem, cfg.program_hex, get_type_name()));
    endfunction

    task run_phase(uvm_phase phase);
        program_seq seq;
        phase.raise_objection(this, "core program");
        seq     = program_seq::type_id::create("seq");
        seq.cfg = cfg;
        seq.start(env.dmem_agent.sequencer);
        phase.drop_objection(this, "core program");
    endtask

    // The verdict is printed with the [PASS]/[FAIL] tokens the rest of the
    // project already uses, and mirrored into a status file so the runner can
    // set an exit code without parsing the transcript.
    function void report_phase(uvm_phase phase);
        uvm_report_server svr;
        uvm_event         coverage_e;
        int unsigned      n_err;
        string            status_path;
        int               fd;

        super.report_phase(phase);

        // Let tb_core_top print the procedural coverage bins.
        coverage_e = uvm_event_pool::get_global("core_coverage_report");
        coverage_e.trigger();

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
