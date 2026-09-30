"""FLOW_JOURNAL Incident 89: one-hot groups of the 4 FSM state registers synthesis re-encoded
(06-yosys-synthesis log, fsm_recode; the same encodings are applied to gold by `fsm`, proved in
../fsm_recode). LEC restricts their paired Q bits to reachable codes; `--inv` proves reachability
(one-hot is inductive + reset code one-hot) on gold with ALL gold bits.
usage: python mk_onehot_spec.py pairs.json spec_in.json spec_out.json"""
import json
import re
import sys

P = json.load(open(sys.argv[1]))
S = json.load(open(sys.argv[2]))
FSMS = [("lcd_en_phase", "\\u_soc.u_lcd.en_phase"), ("axi_last_grant", "\\u_soc.u_cache_axi_master.last_grant_q"),
        ("axi_source", "\\u_soc.u_cache_axi_master.source_q"),
        ("alu_ctrl_e", "\\u_soc.u_core.u_pipeline.controller.alu_ctrl_e")]
gold = P["gold"]


def bit_of(names, base):
    for n in names:
        m = re.match(re.escape(base) + r" \[(\d+)\]$", n)
        if m:
            return int(m.group(1))
    return None


S["onehot"], S["onehot_gold"] = [], []
for gname, base in FSMS:
    paired = sorted((bit_of(gold[i]["names"], base), k) for k, (i, j) in enumerate(P["pairs"])
                    if bit_of(gold[i]["names"], base) is not None)
    allg = sorted((bit_of(f["names"], base), i) for i, f in enumerate(gold) if bit_of(f["names"], base) is not None)
    nbits = len(allg)
    mode = "exact" if len(paired) == nbits else "atmost"
    # axi_source: synthesis removed one of its 3 one-hot bits, so on a synthesised side the remaining
    # bits can legitimately be all 0 (the removed bit's state) - always use the weaker "atmost".
    if gname == "axi_source":
        mode = "atmost"
    S["onehot"].append({"name": gname, "mode": mode, "pairs": [k for _, k in paired]})
    S["onehot_gold"].append({"name": gname, "gold": [i for _, i in allg]})
    print("%-15s gold bits %2d, paired %2d -> LEC mode %s" % (gname, nbits, len(paired), mode))
json.dump(S, open(sys.argv[3], "w"), indent=1)
