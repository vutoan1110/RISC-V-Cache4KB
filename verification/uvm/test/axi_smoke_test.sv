// Default AXI test: three initiators running at once against a cooperative
// slave.
class axi_smoke_test extends axi_base_test;
    `uvm_component_utils(axi_smoke_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void configure();
        cfg.mem_size_bytes = 8192;
        cfg.timeout_cycles = 50000;
    endfunction
endclass

// Same traffic against a slave that stalls every channel and delays B. This is
// the case the ordering invariant is about: a read must not overtake a store
// is still draining to memory.
class axi_stress_test extends axi_base_test;
    `uvm_component_utils(axi_stress_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void configure();
        cfg.mem_size_bytes = 8192;
        cfg.timeout_cycles = 200000;
        cfg.ar_stall_pct   = 30;
        cfg.r_stall_pct    = 30;
        cfg.aw_stall_pct   = 30;
        cfg.w_stall_pct    = 30;
        cfg.b_delay_max    = 4;
        n_write            = 60;
    endfunction
endclass
