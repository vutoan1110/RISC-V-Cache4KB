// Runs verification/directed/directed_isa.hex on the full SoC, the same image
// tb/directed_isa_tb.sv uses, and checks the architectural result the program
// encodes plus the complete counter contract of docs/reference/02 section 3.
class soc_directed_test extends soc_base_test;

    `uvm_component_utils(soc_directed_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void configure();
        cfg.expected_retire = 217;      // the locked golden trace
        cfg.timeout_cycles  = 200000;
    endfunction

    function void check_phase(uvm_phase phase);
        bit [31:0] x31;
        super.check_phase(phase);

        x31 = cfg.stats.arch_regs[31];
        if (x31 !== 32'd1)
            `uvm_error("SELFCHECK",
                $sformatf("directed ISA self-check failed with code %0d in x31", x31))

        // The program's wrong-path MMIO store must never reach the APB bus,
        // and it makes no other peripheral access.
        if (cfg.obs_vif.apb_transfer_count !== 32'd0)
            `uvm_error("WRONGPATHMMIO",
                $sformatf("%0d APB transfers occurred, the directed program makes none",
                          cfg.obs_vif.apb_transfer_count))

        // irq_timer stays low, so no retirement may be flagged as an interrupt.
        if (cfg.stats.n_retire == 0)
            `uvm_error("NORETIRE", "no instruction retired at all")
    endfunction

endclass
