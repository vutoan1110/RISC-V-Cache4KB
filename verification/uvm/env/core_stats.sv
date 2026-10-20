// Counters collected by the monitors and evaluated by the scoreboard at
// check_phase. Kept in one object so every component sees the same numbers.
class core_stats extends uvm_object;

    // Retirement.
    longint unsigned n_retire;
    longint unsigned n_retire_before_halt;
    bit              halt_seen;
    bit [31:0]       halt_pc;
    uvm_event        halt_e;

    // Cycles counted while reset_n is high, plus the DUT architectural CSRs.
    longint unsigned n_cycle;
    bit [31:0]       mcycle_last;
    bit [31:0]       minstret_last;

    // Retired CSR writes that land on mcycle/minstret. This RTL commits the
    // write for CSRRS/CSRRC even when rs1 == x0, which costs one increment of
    // the targeted counter, so the identity check has to allow for them.
    longint unsigned n_csr_wr_mcycle;
    longint unsigned n_csr_wr_minstret;

    // One-cycle event pulses (docs/reference/02 section 3).
    longint unsigned ev_branch;
    longint unsigned ev_branch_taken;
    longint unsigned ev_branch_not_taken;
    longint unsigned ev_prediction;
    longint unsigned ev_prediction_correct;
    longint unsigned ev_mispredict;
    longint unsigned ev_load_use;
    longint unsigned ev_control_redirect;

    // Instruction port, measured by the agent.
    longint unsigned i_access;
    longint unsigned i_response;
    longint unsigned i_error;

    // Data port, measured by the agent.
    longint unsigned d_access;
    longint unsigned d_read;
    longint unsigned d_write;
    longint unsigned d_response;
    longint unsigned d_error;
    longint unsigned d_mmio;
    longint unsigned d_unmapped;

    // Memory operations seen on the retirement trace.
    longint unsigned r_mem_read;
    longint unsigned r_mem_write;

    // Sticky native-interface error flags of the DUT.
    bit if_error_sticky;
    bit d_error_sticky;

    // Architectural register file rebuilt from the retirement trace.
    bit [31:0] arch_regs[32];

    `uvm_object_utils(core_stats)

    function new(string name = "core_stats");
        super.new(name);
        halt_e = new("halt_e");
        foreach (arch_regs[i]) arch_regs[i] = 32'h0;
    endfunction

endclass
