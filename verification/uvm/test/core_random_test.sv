// Constrained-random program test. The whole verdict rests on the reference
// model: the program is different for every seed, so there is no golden
// retirement count to compare against.
//
// The memory responders also run with randomised latency here, so a seed
// exercises both a new instruction stream and a new timing profile.
class core_random_test extends core_base_test;

    rv32_program_gen gen;

    int unsigned prog_length = 160;

    `uvm_component_utils(core_random_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void configure();
        cfg.expected_retire = 0;          // program length is not fixed
        cfg.mem_size_bytes  = 16384;  // R14: SoC RAM, was 8192
        cfg.timeout_cycles  = 100000;
        cfg.rsp_latency_min = 1;
        cfg.rsp_latency_max = 3;
        void'($value$plusargs("PROG_LEN=%d", prog_length));
    endfunction

    virtual function void load_program();
        string dump_path;

        gen             = rv32_program_gen::type_id::create("gen");
        gen.length      = prog_length;
        gen.data_bytes  = 256;
        // Keep the data window past the last instruction word so a store can
        // never rewrite code, rounded up to a 256-byte boundary.
        gen.data_base   = (((prog_length + 1) * 4 + 255) / 256) * 256;
        if (gen.data_base < 32'h400)
            gen.data_base = 32'h400;

        if ((gen.data_base + gen.data_bytes) > cfg.mem_size_bytes)
            `uvm_fatal("PROGSIZE",
                $sformatf("program of %0d words needs a data window at 0x%08h, past the %0d-byte memory",
                          prog_length, gen.data_base, cfg.mem_size_bytes))

        gen.generate_program();
        if (!gen.code_and_data_disjoint())
            `uvm_fatal("PROGSIZE", "generated code overlaps its own data window")

        gen.write_to(cfg.mem);
        if (cfg.use_iss)
            gen.write_to(cfg.iss_mem);

        dump_path = $sformatf("verification/uvm/out/%s.hex", get_type_name());
        void'($value$plusargs("PROG_DUMP=%s", dump_path));
        gen.dump_hex(dump_path);

        `uvm_info("PROGGEN",
            $sformatf("generated %0d words, data window 0x%08h..0x%08h",
                      gen.words.size(), gen.data_base,
                      gen.data_base + gen.data_bytes - 1), UVM_LOW)
    endfunction

    function void check_phase(uvm_phase phase);
        super.check_phase(phase);
        // Without a reference model this test would check nothing at all.
        if (!cfg.use_iss)
            `uvm_error("NOISS", "core_random_test needs the reference model enabled")
    endfunction

endclass
