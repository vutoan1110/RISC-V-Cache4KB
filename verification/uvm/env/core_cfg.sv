// Single configuration object for the core environment. Milestone 1 keeps the
// responders deterministic (ready always high, one-cycle response); the knobs
// for random latency and backpressure are already here for phase 3.
class core_cfg extends uvm_object;

    virtual native_if imem_vif;
    virtual native_if dmem_vif;
    virtual rvfi_if   rvfi_vif;

    native_mem_model mem;
    core_stats       stats;

    // Phase 2 reference model. It owns a second copy of the program image so a
    // divergence shows up both per instruction and as a memory mismatch.
    rv32_iss         iss;
    native_mem_model iss_mem;
    bit              use_iss = 1;

    int unsigned mem_size_bytes  = 16384;  // physical RAM of the SoC (R14: was 8192)
    int unsigned rsp_latency_min = 1;      // cycles from accept to rsp_valid
    int unsigned rsp_latency_max = 1;

    string     program_hex     = "verification/directed/directed_isa.hex";
    bit [31:0] halt_instr      = 32'h0000_006f;   // JAL x0,0
    int unsigned expected_retire = 0;             // 0 disables the check
    int unsigned timeout_cycles  = 200000;
    bit          check_pc_chain  = 1;

    `uvm_object_utils(core_cfg)

    function new(string name = "core_cfg");
        super.new(name);
    endfunction

endclass
