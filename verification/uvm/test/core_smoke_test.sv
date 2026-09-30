// Smoke test: run the existing directed ISA image on riscv_core_native and
// check the architectural results the program itself encodes.
//
// The image is verification/directed/directed_isa.hex, the same one
// tb/directed_isa_tb.sv runs on the full SoC. It writes 1 into x31 unless a
// self-check fails, in which case x31 holds the failing check code.
class core_smoke_test extends core_base_test;

    `uvm_component_utils(core_smoke_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void configure();
        cfg.program_hex     = "verification/directed/directed_isa.hex";
        cfg.expected_retire = 217;         // matches the locked golden trace
        cfg.mem_size_bytes  = 8192;        // physical RAM of the SoC
        cfg.timeout_cycles  = 20000;
    endfunction

    function void check_phase(uvm_phase phase);
        bit [31:0] x31;
        super.check_phase(phase);

        // The program's own pass marker.
        x31 = cfg.stats.arch_regs[31];
        if (x31 !== 32'd1)
            `uvm_error("SELFCHECK",
                $sformatf("directed ISA self-check failed with code %0d in x31", x31))

        // Data region written by the load/store section, at x30 = 0x1000.
        check_word(32'h0000_1000, 32'h80ff_7f01, "SW word");
        check_word(32'h0000_1004, 32'h8123_aa00, "SB byte 5 merged with SH halfword 6");
        check_word(32'h0000_1008, 32'h1234_5678, "SW word at offset 8");

        // The store at offset 12 sits on a wrong path and must never commit.
        check_word(32'h0000_100c, 32'h0000_0000, "wrong-path store suppression");

        // The wrong-path MMIO store at 0x40000100 must never reach the bus.
        if (cfg.stats.d_mmio != 0)
            `uvm_error("WRONGPATHMMIO",
                $sformatf("%0d MMIO transactions reached the data port, expected none",
                          cfg.stats.d_mmio))
        if (cfg.stats.d_unmapped != 0)
            `uvm_error("UNMAPPED",
                $sformatf("%0d unmapped transactions reached the data port, expected none",
                          cfg.stats.d_unmapped))
    endfunction

    protected function void check_word(bit [31:0] addr, bit [31:0] expected,
                                       string what);
        bit [31:0] got = cfg.mem.read_word(addr);
        if (got !== expected)
            `uvm_error("MEMCHECK",
                $sformatf("%s: RAM[0x%08h] expected 0x%08h, got 0x%08h",
                          what, addr, expected, got))
    endfunction

endclass
