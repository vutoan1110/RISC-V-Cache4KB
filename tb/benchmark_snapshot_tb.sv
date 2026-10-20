`timescale 1ns/1ps
// Full-SoC paper harness. Firmware owns CLEAR/FREEZE; this harness only exports
// the resulting atomic snapshot. It is compiled now but no unproven ELF is run.
module tb_benchmark_snapshot #(
 parameter integer CACHE_CONFIG=0,
 parameter integer ICACHE_LINE_COUNT=64,
 parameter integer DCACHE_LINE_COUNT=64,
 parameter integer VICTIM_ENTRIES=4,
 parameter integer CACHE_LINE_WORDS=4,
 parameter integer CACHE_FAST_HIT=0,   // R16 (review M1)
 parameter integer BRANCH_PREDICT_ENABLE=1,
 // Depth of the I-cache L0 hot buffer. Each entry is a whole 128-bit line
 // in flip-flops, so this is the largest single LE lever measured so far:
 // 8 -> 4 saves 721 LE and 616 registers. What it costs in cycles is what
 // this parameter exists to measure.
 parameter integer L0_ENTRIES=8,
 // RAM depth in 32-bit words per half. R14 (2026-09-29, RAM16K_CHANGES.md): 2048+2048 = 16 KiB,
 // was 1024+1024 = 8 KiB. CoreMark (16.4 KiB) still does not fit; scripts/run_coremark.py raises
 // these together with a matching linker script.
 parameter integer IMEM_DEPTH=2048,
 parameter integer DMEM_DEPTH=2048,
 parameter MEMFILE="riscv_full.hex"
);
reg clk=0, reset_n=0, uart_rx=1, key1_n=1;
always #10 clk=~clk;
wire uart_tx; wire[6:0] HEX0,HEX1,HEX2,HEX3,HEX4,HEX5,HEX6,HEX7;
wire[7:0] LEDR,LCD_DATA; wire LCD_EN,LCD_RS,LCD_RW,LCD_ON,LCD_BLON;
integer cycles,max_cycles; reg[8*80-1:0] benchmark;
localparam[31:0] DONE_MAGIC=32'hB16B00B5, FAIL_MAGIC=32'hDEADFA11;
soc_top #(.CACHE_CONFIG(CACHE_CONFIG),.ICACHE_LINE_COUNT(ICACHE_LINE_COUNT),.DCACHE_LINE_COUNT(DCACHE_LINE_COUNT),.VICTIM_ENTRIES(VICTIM_ENTRIES),.CACHE_LINE_WORDS(CACHE_LINE_WORDS),.CACHE_FAST_HIT(CACHE_FAST_HIT),.BRANCH_PREDICT_ENABLE(BRANCH_PREDICT_ENABLE),.L0_ENTRIES(L0_ENTRIES),.IMEM_DEPTH(IMEM_DEPTH),.DMEM_DEPTH(DMEM_DEPTH),.BHT_ENTRIES(256),.MEMFILE(MEMFILE)) dut(
 .clk(clk),.reset_n(reset_n),.key1_n(key1_n),.uart_rx(uart_rx),.uart_tx(uart_tx),
 .HEX0(HEX0),.HEX1(HEX1),.HEX2(HEX2),.HEX3(HEX3),.HEX4(HEX4),.HEX5(HEX5),.HEX6(HEX6),.HEX7(HEX7),
 .LEDR(LEDR),.LCD_DATA(LCD_DATA),.LCD_EN(LCD_EN),.LCD_RS(LCD_RS),.LCD_RW(LCD_RW),.LCD_ON(LCD_ON),.LCD_BLON(LCD_BLON));
// Optional cache access trace, for cross-validating the RTL counters against an
// independently written cache model (+trace_cache). Off by default, so the
// measured runs are unaffected.
integer trace_fd = 0;
reg clear_q = 1'b0, freeze_q2 = 1'b0, clear_pending = 1'b0;
initial begin
 if($test$plusargs("trace_cache")) trace_fd = $fopen("results/cache_trace.txt","w");
end
reg        i_fire_q = 1'b0, d_fire_q = 1'b0, d_wr_q = 1'b0;
reg [31:0] i_addr_q = 32'h0, d_addr_q = 32'h0;
wire trace_gate = !dut.u_observability.counter_freeze &&
                  !dut.u_observability.counter_clear;
always @(posedge clk) if(trace_fd != 0) begin
 // perf_counters registers every event before counting it, so the clear/freeze
 // gate that decides whether an access is counted is the one standing a cycle
 // AFTER the access. Accesses are therefore emitted one cycle late, carrying
 // the gate the counters actually saw.
 if(i_fire_q) $fdisplay(trace_fd, "I %08x %0d", i_addr_q, trace_gate ? 1 : 0);
 if(d_fire_q) $fdisplay(trace_fd, "D %08x %0d %0d", d_addr_q, d_wr_q,
                        trace_gate ? 1 : 0);
 if(dut.u_observability.counter_clear) $fdisplay(trace_fd, "MARK CLEAR");

 i_fire_q <= dut.u_icache.req_valid && dut.u_icache.req_ready;
 i_addr_q <= dut.u_icache.req_addr;
 d_fire_q <= dut.u_dcache.req_valid && dut.u_dcache.req_ready;
 d_addr_q <= dut.u_dcache.req_addr;
 d_wr_q   <= dut.u_dcache.req_write;
end

initial begin
 cycles=0; if(!$value$plusargs("max_cycles=%d",max_cycles))max_cycles=20000000;
 if(!$value$plusargs("benchmark=%s",benchmark))benchmark="UNKNOWN";
 repeat(5)@(posedge clk); reset_n=1;
 while(cycles<max_cycles && dut.disp_ctrl!=DONE_MAGIC && dut.disp_ctrl!=FAIL_MAGIC)begin @(posedge clk);cycles=cycles+1;end
 if(cycles>=max_cycles)$fatal(1,"FAIL_TIMEOUT benchmark=%0s cfg=%0d",benchmark,CACHE_CONFIG);
 if(dut.disp_ctrl!=DONE_MAGIC)$fatal(1,"firmware result failed benchmark=%0s cfg=%0d",benchmark,CACHE_CONFIG);
 if(!dut.perf_snapshot_valid_dbg)$fatal(1,"firmware did not create atomic snapshot");
 if(dut.u_observability.u_sysmon.snap_mcycle !==
   dut.u_observability.u_sysmon.snap_retire_cycle+
   dut.u_observability.u_sysmon.snap_load_use_cycle+
   dut.u_observability.u_sysmon.snap_icache_wait_cycle+
   dut.u_observability.u_sysmon.snap_dcache_wait_cycle+
   dut.u_observability.u_sysmon.snap_control_redirect_cycle+
   dut.u_observability.u_sysmon.snap_trap_redirect_cycle+
   dut.u_observability.u_sysmon.snap_mmio_wait_cycle+
   dut.u_observability.u_sysmon.snap_pipe_fill_drain_cycle+
   dut.u_observability.u_sysmon.snap_other_cycle)$fatal(1,"cycle reconstruction failed");
 if(dut.u_observability.u_sysmon.snap_icache_access !==
   dut.u_observability.u_sysmon.snap_icache_main_hit+
   dut.u_observability.u_sysmon.snap_icache_victim_hit+
   dut.u_observability.u_sysmon.snap_icache_true_miss)$fatal(1,"I-cache invariant failed");
 if(dut.u_observability.u_sysmon.snap_dcache_read_access+dut.u_observability.u_sysmon.snap_dcache_write_access !==
   dut.u_observability.u_sysmon.snap_dcache_main_hit+
   dut.u_observability.u_sysmon.snap_dcache_victim_hit+
   dut.u_observability.u_sysmon.snap_dcache_true_miss)$fatal(1,"D-cache invariant failed");
 $display("BENCHMARK_SNAPSHOT benchmark=%0s config=%0d mcycle=%0d minstret=%0d cycle_retire=%0d load_use=%0d i_wait=%0d d_wait=%0d control=%0d trap=%0d mmio=%0d fill_drain=%0d other=%0d i_access=%0d i_main=%0d i_victim=%0d i_miss=%0d d_read=%0d d_write=%0d d_main=%0d d_victim=%0d d_miss=%0d branches=%0d taken=%0d not_taken=%0d predictions=%0d correct=%0d mispredict=%0d axi_read=%0d axi_write=%0d i_hit_ev=%0d i_miss_ev=%0d d_rd_hit=%0d d_rd_miss=%0d d_wr_hit=%0d d_wr_miss=%0d control_ev=%0d trap_ev=%0d mcause=%0d snap_seq=%0d result_pass=1 invariant_pass=1",
  benchmark,CACHE_CONFIG,dut.u_observability.u_sysmon.snap_mcycle,dut.u_observability.u_sysmon.snap_minstret,
  dut.u_observability.u_sysmon.snap_retire_cycle,dut.u_observability.u_sysmon.snap_load_use_cycle,
  dut.u_observability.u_sysmon.snap_icache_wait_cycle,dut.u_observability.u_sysmon.snap_dcache_wait_cycle,
  dut.u_observability.u_sysmon.snap_control_redirect_cycle,dut.u_observability.u_sysmon.snap_trap_redirect_cycle,
  dut.u_observability.u_sysmon.snap_mmio_wait_cycle,dut.u_observability.u_sysmon.snap_pipe_fill_drain_cycle,
  dut.u_observability.u_sysmon.snap_other_cycle,dut.u_observability.u_sysmon.snap_icache_access,
  dut.u_observability.u_sysmon.snap_icache_main_hit,dut.u_observability.u_sysmon.snap_icache_victim_hit,
  dut.u_observability.u_sysmon.snap_icache_true_miss,dut.u_observability.u_sysmon.snap_dcache_read_access,
  dut.u_observability.u_sysmon.snap_dcache_write_access,dut.u_observability.u_sysmon.snap_dcache_main_hit,
  dut.u_observability.u_sysmon.snap_dcache_victim_hit,dut.u_observability.u_sysmon.snap_dcache_true_miss,
  dut.u_observability.u_sysmon.snap_conditional_branch,dut.u_observability.u_sysmon.snap_branch_taken,
  dut.u_observability.u_sysmon.snap_branch_not_taken,dut.u_observability.u_sysmon.snap_branch_prediction,
  dut.u_observability.u_sysmon.snap_branch_correct_prediction,dut.u_observability.u_sysmon.snap_mispredict_event,
  dut.u_observability.u_sysmon.snap_axi_read_txn,dut.u_observability.u_sysmon.snap_axi_write_txn,
  // The nine snapshot registers the line did not carry before 2026-09-25
  // (NHAT_KY_RTL.md, M5), plus the snapshot sequence number.
  dut.u_observability.u_sysmon.snap_icache_hit,dut.u_observability.u_sysmon.snap_icache_miss,
  dut.u_observability.u_sysmon.snap_dcache_read_hit,dut.u_observability.u_sysmon.snap_dcache_read_miss,
  dut.u_observability.u_sysmon.snap_dcache_write_hit,dut.u_observability.u_sysmon.snap_dcache_write_miss,
  dut.u_observability.u_sysmon.snap_control_redirect_event,dut.u_observability.u_sysmon.snap_trap_event,
  dut.u_observability.u_sysmon.snap_last_mcause,dut.u_observability.u_sysmon.snapshot_sequence_q);
 $display("[PASS] Atomic benchmark snapshot");$finish;
end
endmodule
