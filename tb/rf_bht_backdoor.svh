// Testbench access to the register file and branch history table contents (2026-10-08, review A1).
// The ASIC view (__openlane__) keeps the flip-flop arrays regs / bht_mem. The FPGA view stores them in M9K with a
// registered read: hdl/regfile.v mem1 / mem2, hdl/predictor/bht_2bit.v cnt_f / cnt_u plus valid[] (an entry not
// written since reset reads BHT_RESET_STATE). A SET acts like a write to the old array: every copy, the reference
// array of the sim-only checker, and the registered read / bypass state that already holds the entry, so the next
// read returns the new value. p = hierarchical path of the regfile / bht_2bit instance; SET is a statement.
`ifndef RF_BHT_BACKDOOR_SVH
`define RF_BHT_BACKDOOR_SVH
`ifdef __openlane__
`define RF_GET(p, i)     p.regs[i]
`define RF_SET(p, i, v)  p.regs[i] = (v)
`define BHT_GET(p, i)    p.bht_mem[i]
`define BHT_SET(p, i, v) p.bht_mem[i] = (v)
`else
`define RF_GET(p, i)     p.mem1[i]
`define RF_SET(p, i, v)  begin p.mem1[i] = (v); p.mem2[i] = (v); p.ref_regs[i] = (v); if (p.rs1 == (i)) p.q1 = (v); if (p.rs2 == (i)) p.q2 = (v); if (p.rd_q == (i)) p.wd_q = (v); end
`define BHT_GET(p, i)    (p.valid[i] ? p.cnt_f[i] : p.BHT_RESET_STATE)
`define BHT_SET(p, i, v) begin p.cnt_f[i] = (v); p.cnt_u[i] = (v); p.valid[i] = 1'b1; p.ref_mem[i] = (v); if (p.fetch_index == (i)) p.qf = (v); if (p.update_index == (i)) p.qu = (v); if (p.upd_idx_q == (i)) p.upd_val_q = (v); end
`endif
`endif
