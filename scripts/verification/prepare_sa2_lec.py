"""Prepare isolated SA2 formal front ends and input provenance; never run tools.

The generated front-end batch is a preparation phase, not a completed LEC.
The complete proof must close every mapped output with independently proved
state restrictions and multiplier residuals, twice, with negative controls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WSL_ROOT = "/mnt/e/Projects/RISCV-research"
BASE = "sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r"
REPLAY_TAG = "sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1"
YOSYS = "/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys"
REPLAY_YOSYS = "/nix/store/zdhr86kv5rxlp0s58rzxk1aki1igankx-yosys-with-plugins-python3-3.11.9-env/bin/yosys"
FORMAL_SHA = "a895bb0fde320a4a95e6f0091e2aa76d7bc2fa2f335c7b0ad064df161ed69f84"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def local(path):
    prefix = WSL_ROOT + "/"
    if not path.startswith(prefix):
        raise ValueError("Input is outside the research project: " + path)
    return ROOT / path[len(prefix):]


def wsl(path):
    return WSL_ROOT + "/" + path.relative_to(ROOT).as_posix()


def inspect():
    runs = [ROOT / f"asic/soc_sa2_4kb/runs/{BASE}{n}" for n in (1, 2)]
    configs = [json.loads((run / "resolved.json").read_text()) for run in runs]
    inputs = configs[0]["VERILOG_FILES"]
    if len(inputs) != 42 or inputs != configs[1]["VERILOG_FILES"]:
        raise ValueError("SA2 signed runs do not share the expected42input sources")
    if inputs[-1] != WSL_ROOT + "/asic/soc_sa2_4kb/soc_asic_top.v":
        raise ValueError("Wrong SA2 top wrapper")
    adapter = WSL_ROOT + "/asic/dse_sram/cache_dse_data_bank_sram.v"
    if adapter not in inputs:
        raise ValueError("Missing SA2 macro-backed DSE data bank")
    macros = sorted({p for m in configs[0]["MACROS"].values() for p in m["nl"]})
    formal = ROOT / "asic/soc_dm_4kb/formal_pdk.v"
    if sha(formal) != FORMAL_SHA:
        raise ValueError("Stable formal cell model differs from the proved DM model")
    files = [local(p) for p in inputs + macros] + [formal]
    for run in runs:
        files += [run / "resolved.json", run / "06-yosys-synthesis/config.json",
                  run / "06-yosys-synthesis/extra.json", run / "06-yosys-synthesis/soc_asic_top.nl.v",
                  run / "56-openroad-fillinsertion/soc_asic_top.nl.v"]
    replay = ROOT / "asic/equiv/lec/synth_replay_r14"
    files += [replay / name for name in ("synthesize_n1only.py", "ys_common.py", "construct_abc_script.py")]
    existing_n1 = replay / "sa2_rsztf_r1_n1only"
    files += [existing_n1 / "n1_pre_abc_fast.il", existing_n1 / "soc_asic_top.nl.v"]
    # The ECO branch rewrites tmp paths but does not copy its parent's tmp.
    # Replay the retained original full-flow synthesis with real Liberty inputs.
    replay_source = ROOT / f"asic/soc_sa2_4kb/runs/{REPLAY_TAG}/06-yosys-synthesis"
    files += [replay_source / name for name in ("config.json", "extra.json", "soc_asic_top.nl.v")]
    extra = json.loads((replay_source / "extra.json").read_text())
    files += [local(p) for p in extra["libs_synth"]]
    helpers = ["evert.py", "const_check.py", "spec_manual.py", "mk_onehot_spec.py",
               "open_outputs.py", "aig_syms.py", "aigsim.py", "macc_alg.py", "mulsub.py", "outsel.py"]
    files += [ROOT / "asic/equiv/lec" / name for name in helpers]
    files += [ROOT / "asic/equiv/sec/sram_cut.py", ROOT / "results/rtl_manifest.json", Path(__file__)]
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in files}
    step06 = runs[0] / "06-yosys-synthesis/soc_asic_top.nl.v"
    if sha(replay_source / "soc_asic_top.nl.v") != sha(step06):
        raise ValueError("Original full-flow synthesis differs from signed branch synthesis")
    if sha(existing_n1 / "soc_asic_top.nl.v") != sha(step06):
        raise ValueError("Existing single-hook N1 replay lost its byte-exact link")
    if sha(runs[0] / "56-openroad-fillinsertion/soc_asic_top.nl.v") != sha(runs[1] / "56-openroad-fillinsertion/soc_asic_top.nl.v"):
        raise ValueError("Signed final SA2 netlists differ")
    return runs, configs[0], inputs, macros, hashes


def scripts(config, inputs, macros, runs, output):
    defs = "".join("verilog_defines -D" + define + "\n" for define in
                   ("PDK_sky130A", "SCL_sky130_fd_sc_hd", "__openlane__", "__pnr__"))
    libs = "".join("read_verilog -sv -lib " + path + "\n" for path in macros) + "blackbox\n"
    gold_front = defs + libs + "read_verilog -formal -sv " + " ".join(inputs) + "\n"
    gold_front += "hierarchy -top soc_asic_top\nflatten\nrename -hide w:*.clk w:*.PCLK w:*.pclk\n"
    gold_pre = """script gold_frontend.ys
proc
opt_expr
opt_clean
opt -nodffe -nosdff
fsm
hierarchy -top soc_asic_top
proc
prep -top soc_asic_top -flatten
memory -nomap
memory_map
opt_clean
check -assert -initdrv
write_ilang gold_pre.il
"""
    def flatten(source, target, n1=False):
        forbidden = "t:$_DFF_PN0_ t:$_DFF_PN1_ t:$_DFFE_* t:$_SDFF* t:$_DFFSR* t:$_DLATCH* t:$dff t:$adff" if n1 else "t:$adff t:$adffe t:$dffe t:$sdff t:$sdffe t:$sdffce t:$aldff t:$aldffe t:$dffsr t:$dffsre t:$dlatch t:$ff"
        return f"read_ilang {source}\nhierarchy -top soc_asic_top\nasync2sync\ndffunmap\nopt_clean\nselect -assert-none {forbidden}\nwrite_ilang {target}\n"
    fsm = (ROOT / "asic/equiv/fsm_recode/prove_fsm.ys").read_text()
    fsm = "\n".join(line for line in fsm.splitlines() if not line.lstrip().startswith("#"))
    fsm = fsm.replace("script front_end.ys", "script gold_frontend.ys") + "\n"
    gate_hide = "rename -hide w:* x:* %d w:u_soc.* %d w:reset_meta_q %d w:reset_sync_q %d w:key1_sync_q* %d w:uart_rx_sync_q* %d w:soc_key1_n %d w:soc_reset_n %d w:soc_uart_rx %d\n"
    ttlib = config["LIB"]["*_tt_025C_1v80"][0]
    data = {"gold_frontend.ys": gold_front, "gold_pre.ys": gold_pre,
            "gold_flat.ys": flatten("gold_cut.il", "gold_flat.il"),
            "n1_flat.ys": flatten("n1_cut.il", "n1_flat.il", True), "prove_fsm.ys": fsm}
    for n, run in enumerate(runs, 1):
        data[f"gate{n}_frontend.ys"] = defs + libs + f"read_liberty -lib -ignore_miss_dir -setattr blackbox {ttlib}\n" + \
            "read_verilog -formal -sv " + WSL_ROOT + "/asic/soc_dm_4kb/formal_pdk.v " + wsl(run / "56-openroad-fillinsertion/soc_asic_top.nl.v") + \
            "\nhierarchy -top soc_asic_top\nflatten\n" + gate_hide
        data[f"gate{n}_pre.ys"] = f"script gate{n}_frontend.ys\nhierarchy -top soc_asic_top\nproc\nprep -top soc_asic_top -flatten\nmemory -nomap\nmemory_map\nopt_clean\ncheck -assert -initdrv\nwrite_ilang gate{n}_pre.il\n"
        data[f"gate{n}_flat.ys"] = flatten(f"gate{n}_cut.il", f"gate{n}_flat.il")
    for pass_no in (1, 2):
        directory = output / f"p{pass_no}"
        directory.mkdir()
        for name, content in data.items():
            (directory / name).write_text(content, encoding="ascii")
        # All artifacts remain isolated; there is no shared LEC runs.log mutation.
        batch = f"""#!/usr/bin/env bash
set -euo pipefail
cd '{wsl(directory)}'
R='{WSL_ROOT}'
Y='{YOSYS}'
RY='{REPLAY_YOSYS}'
S='{WSL_ROOT}/asic/soc_sa2_4kb/runs/{REPLAY_TAG}/06-yosys-synthesis'
test ! -e replay
mkdir replay
export SYNTH_SNAP="$PWD/replay"
"$RY" -y "$R/asic/equiv/lec/synth_replay_r14/synthesize_n1only.py" -- --config-in "$S/config.json" --extra-in "$S/extra.json" --output "$PWD/replay/soc_asic_top.nl.v" > replay/replay.log 2>&1
cmp "$S/soc_asic_top.nl.v" replay/soc_asic_top.nl.v
"$Y" -l prove_fsm.log prove_fsm.ys > prove_fsm.stdout 2>&1
"$Y" -l gold_pre.log gold_pre.ys > gold_pre.stdout 2>&1
python3 "$R/asic/equiv/sec/sram_cut.py" gold_pre.il gold_cut.il > gold_cut.log
python3 "$R/asic/equiv/sec/sram_cut.py" replay/n1_pre_abc_fast.il n1_cut.il > n1_cut.log
"$Y" -l gold_flat.log gold_flat.ys > gold_flat.stdout 2>&1
"$Y" -l n1_flat.log n1_flat.ys > n1_flat.stdout 2>&1
python3 "$R/asic/equiv/lec/evert.py" pair gold_flat.il n1_flat.il pairs_a.json > pairs_a.log
for n in 1 2; do
    "$Y" -l "gate${{n}}_pre.log" "gate${{n}}_pre.ys" > "gate${{n}}_pre.stdout" 2>&1
    python3 "$R/asic/equiv/sec/sram_cut.py" "gate${{n}}_pre.il" "gate${{n}}_cut.il" > "gate${{n}}_cut.log"
    "$Y" -l "gate${{n}}_flat.log" "gate${{n}}_flat.ys" > "gate${{n}}_flat.stdout" 2>&1
    python3 "$R/asic/equiv/lec/evert.py" pair n1_flat.il "gate${{n}}_flat.il" "pairs_b${{n}}.json" > "pairs_b${{n}}.log"
done
printf '%s\\n' 'FRONT_ENDS_COMPLETE_ONLY: mapped SAT, state restrictions, multiplier closure and negative controls remain'
"""
        (directory / "run_frontends.sh").write_text(batch, encoding="ascii")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Create new preparation files only; no external tools")
    args = parser.parse_args()
    runs, config, inputs, macros, hashes = inspect()
    print(f"[PREPARED] {len(inputs)} exact ordered SA2 RTL inputs; signed final netlists identical; stable formal model verified")
    if not args.write:
        return 0
    output = ROOT / "results/completion_preparation_20261009/sa2_lec_20261009"
    output.mkdir(exist_ok=False)
    scripts(config, inputs, macros, runs, output)
    receipt = {"status": "PREPARED_NOT_EXECUTED_NOT_A_LEC_RESULT", "rtl_inputs_ordered": inputs,
               "macro_models": macros, "local_input_sha256": hashes,
               "external_tt_lib_requires_runtime_hash": config["LIB"]["*_tt_025C_1v80"],
               "existing_n1": "byte-exact single-hook replay; evidence only, not a second execution",
               "fresh_replay_source": f"asic/soc_sa2_4kb/runs/{REPLAY_TAG}/06-yosys-synthesis",
               "branch_tmp_trap": "Signed ecomaxmin branch extra.json refers to absent branch tmp Liberty; retained full-flow parent's synthesis inputs must be used. Its synthesis netlist is byte-identical to the signed branches.",
               "proof_boundary": "logic and every SRAM input pin; SRAM read data shared unconstrained inputs; macro analog timing excluded",
               "required_memory": "SoC formal proof runs alone; measured EQY use about13GB; no WSL launched by preparation",
               "acceptance": [
                   "Each proof pass starts with a fresh byte-exact single-hook synthesis replay from the same signed-run inputs.",
                   "SA2 FSM re-encoding must prove equiv_status -assert with zero unproven cells; mutation of its encoding must fail semantically.",
                   "Register mappings, constants and duplicate relations are derived on SA2; every reset/inductivity premise is proved.",
                   "One-hot restrictions require explicit gold reachability proof with evert --inv before restricted LEC acceptance.",
                   "Every output must be UNSAT/equivalent; nonzero open, SAT or unknown counts mean incomplete/failed.",
                   "Multiplier residuals require signed33 algebraic closure and CEC links to the exact mapped proof networks; unsigned-spec and partial-product mutations must fail.",
                   "N1 must prove equal to BOTH independently signed final56 netlists; a copied and2-to-or2 mutation must yield a counterexample.",
                   "Two fresh complete executions compare input hashes, mappings, interfaces, output classifications and all metrics; replaying the same result does not count.",
                   "New flow/model crashes are preserved and diagnosed; never discard unresolved outputs or weaken assumptions to obtain PASS."],
               "front_end_commands": [f"bash {wsl(output / f'p{n}/run_frontends.sh')}" for n in (1, 2)],
               "warning": "Generated front-end batches do not execute the complete LEC closure; no signed equivalence claim is permitted yet."}
    receipt["generated_artifact_sha256"] = {p.relative_to(ROOT).as_posix(): sha(p) for p in output.rglob("*") if p.is_file()}
    (output / "inputs_and_acceptance.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(f"[WROTE] {output}; no synthesis/formal tool was executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
