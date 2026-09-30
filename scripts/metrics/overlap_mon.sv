// A4 (review): why minstret > retire_cycles.
// perf_counters.v charges every cycle to exactly ONE category, fixed priority
//   TRAP > CONTROL > MMIO > D$ > I$ > LOAD_USE > RETIRE > FILL/DRAIN > OTHER,
// while minstret counts EVERY cycle with a retire event. A cycle that retires an instruction while a
// higher-priority condition holds therefore adds to minstret but is charged to that other category.
// This monitor counts those cycles per category inside the same clear/freeze window the counters use,
// so  minstret - retire_cycles == trap + control + mmio + dcache + icache + load_use  must hold exactly.
// Compiled into its own library and elaborated as a second top next to the unchanged testbench:
//   vlib work_mon; vlog -work work_mon -sv scripts/metrics/overlap_mon.sv
//   vsim ... work.tb_benchmark_snapshot work_mon.overlap_mon
module overlap_mon;
`define PC tb_benchmark_snapshot.dut.u_observability.u_perf_counters
    integer n_ret = 0, n_trap = 0, n_ctrl = 0, n_mmio = 0, n_d = 0, n_i = 0, n_lu = 0;
    always @(posedge `PC.clk) begin
        if (!`PC.reset_n || `PC.counter_clear) begin
            n_ret = 0; n_trap = 0; n_ctrl = 0; n_mmio = 0; n_d = 0; n_i = 0; n_lu = 0;
        end
        else if (!`PC.counter_freeze && `PC.retire_event_q) begin
            n_ret = n_ret + 1;
            if      (`PC.cycle_reason_onehot[5]) n_trap = n_trap + 1;
            else if (`PC.cycle_reason_onehot[4]) n_ctrl = n_ctrl + 1;
            else if (`PC.cycle_reason_onehot[6]) n_mmio = n_mmio + 1;
            else if (`PC.cycle_reason_onehot[3]) n_d    = n_d + 1;
            else if (`PC.cycle_reason_onehot[2]) n_i    = n_i + 1;
            else if (`PC.cycle_reason_onehot[1]) n_lu   = n_lu + 1;
        end
    end
    final
        $display("OVERLAP retire_events=%0d charged_elsewhere=%0d trap=%0d control=%0d mmio=%0d dcache=%0d icache=%0d load_use=%0d",
                 n_ret, n_trap + n_ctrl + n_mmio + n_d + n_i + n_lu, n_trap, n_ctrl, n_mmio, n_d, n_i, n_lu);
endmodule
