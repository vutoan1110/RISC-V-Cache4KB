"""FLOW_JOURNAL Incident 89: add the RTL-justified duplicates that synthesis merged under a
different name (found by sensitivity.py: only these free gold-only flops reach a differing output).
Each tie is still PROVED by the LEC: the duplicate's D is compared with the partner's gate D
(lec_d_x output), with both Q tied together (induction; equal reset values 0).

  datapath.v:756-766  alu_result_m <= exec_result_e ; mem_byte_offset_m <= exec_result_e[1:0]
                      (same !stall_pipe enable, same reset 0)  -> mem_byte_offset_m[i] == alu_result_m[i]
  datapath.v:316-322  load_byte_offset_w <= mem_byte_offset_m (same enable/reset as alu_result_w
                      <= alu_result_m)                          -> load_byte_offset_w[i] == alu_result_w[i]
  datapath.v:310,507-531  pc_plus4_f = pc_f + 4 (low two bits = pc_f[1:0]); pc_d/pc_plus4_d and
                      pc_e/pc_plus4_e assigned together in every branch -> pc_plus4_{d,e}[i] == pc_{d,e}[i]

  uart_apb.v:58-64,98-102  start_tx_pulse and ctrl_reg both default to 0 every cycle and, on an
                      APB write to 0x0C with pstrb[0], take 1'b1-if-pwdata[0] / pwdata; reset 0 -> start_tx_pulse
                      == ctrl_reg[0] (the const analysis wrongly guessed it constant 0: random stimulus never
                      hit the address; the formal round demoted it - Incident 89)

usage: python spec_manual.py pairs.json spec.json spec3.json
"""
import json
import sys

P = json.load(open(sys.argv[1]))
S = json.load(open(sys.argv[2]))
DP = "\\u_soc.u_core.u_pipeline.datapath."
MAN = {}
for i in (0, 1):
    MAN[DP + "mem_byte_offset_m [%d]" % i] = DP + "alu_result_m [%d]" % i
    MAN[DP + "load_byte_offset_w [%d]" % i] = DP + "alu_result_w [%d]" % i
    MAN[DP + "pc_plus4_d [%d]" % i] = DP + "pc_d [%d]" % i
    MAN[DP + "pc_plus4_e [%d]" % i] = DP + "pc_e [%d]" % i
MAN["\\u_soc.u_uart.start_tx_pulse"] = "\\u_soc.u_uart.ctrl_reg [0]"
# axi_ram_32_asic_macro.v:226,235 rd_len_q <= s_axi_arlen on accept (reset 0); cache_axi_master.v:202
# m_axi_arlen = LINE_WORDS - 1 = 8'd3, so bits 0 and 1 are loaded with the same 1 under the same
# condition -> rd_len_q[1] == rd_len_q[0] (found by ABC &cec simulation, Incident 89).
MAN["\\u_soc.u_axi_ram.rd_len_q [1]"] = "\\u_soc.u_axi_ram.rd_len_q [0]"
# icache_controller.v:222-257 miss_line_base <= {req_addr[31:4],4'b0} and miss_tag <= request_tag
# (= req_addr[31:12], TAG_WIDTH 20) in the same branch, both reset 0 -> miss_tag[0] (tag_wr_tag[0])
# == miss_line_base[12] (icache_refill_req_addr[12]).
MAN["\\u_soc.u_icache.g_dm_baseline.tag_wr_tag [0]"] = "\\u_soc.icache_refill_req_addr [12]"
# datapath.v:385-404 B/J targets are pc_f + imm with imm[0] = 0, so predicted_target_f[0] = pc_f[0];
# predicted_target_d/e follow pc_d/e. These two ties are left to the LEC's lec_d_x check to confirm.
# soc_top.v:804 .trap_mcause(32'h8000_0007) is a constant, so perf_counters.v:216 trap_mcause_q,
# :440 last_mcause and apb_performance_monitor.v:254 snap_last_mcause carry the same value in bits
# 0, 1, 2 and 31 (0 after reset, then 1): synthesis kept bit 0 (found by ABC &sat, Incident 89).
for reg in ("\\u_soc.u_observability.u_perf_counters.trap_mcause_q", "\\u_soc.u_observability.last_mcause",
            "\\u_soc.u_observability.u_sysmon.snap_last_mcause"):
    for b in (1, 2, 31):
        MAN["%s [%d]" % (reg, b)] = "%s [0]" % reg
MAN[DP + "predicted_target_d [0]"] = DP + "pc_d [0]"
MAN[DP + "predicted_target_e [0]"] = DP + "pc_e [0]"
gold = P["gold"]
pair_by_gold_name = {}
for k, (i, j) in enumerate(P["pairs"]):
    for n in gold[i]["names"]:
        pair_by_gold_name[n] = k
added = 0
for g, i in enumerate(P["gold_only"]):
    for n in gold[i]["names"]:
        if n in MAN:
            tgt = MAN[n]
            assert tgt in pair_by_gold_name, "partner not paired: " + tgt
            assert str(g) not in S["const"], n
            S["dup"][str(g)] = pair_by_gold_name[tgt]
            S["free"] = [k for k in S["free"] if k != g]
            added += 1
            print("dup %-55s -> %s (pair %d)" % (n, tgt, pair_by_gold_name[tgt]))
            break
S["free"] = [k for k in S["free"] if str(k) not in S["dup"]]
json.dump(S, open(sys.argv[3], "w"), indent=1)
print("added %d; const %d, dup %d, free %d" % (added, len(S["const"]), len(S["dup"]), len(S["free"])))
