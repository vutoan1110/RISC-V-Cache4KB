"""Prepare the DM_VC4 register-mapped LEC front ends (2026-10-14); never runs tools.

Same method and generated Yosys scripts as prepare_sa2_lec.py (SA2), with the DM_VC4 top wrapper. Two phases, because
the DM_VC4 layout is not signed off yet while its synthesis is fixed (every DM_VC4 run has the byte-identical step-06
netlist):
  --write       new <output>/p1, p2: gold (RTL + fsm) and N1 (byte-exact single-hook replay of --replay-tag's step 06)
                scripts, lec_inputs.json. Enough for LEC steps A, Mul, Inv (gold == N1).
  --add-gates   existing <output>: gate front-end scripts of the two signed final netlists (--gate-tags A,B) in p1 and p2;
                refuses unless both runs have the same 42 RTL inputs, the step-06 netlist of the replay source and
                byte-identical final netlists. Enables steps B and NegB (N1 == final).
The proof acceptance rules are those of the SA2 LEC (results/completion_preparation_20261009/.../inputs_and_acceptance.json).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WSL_ROOT = "/mnt/e/Projects/RISCV-research"
DESIGN_DIR = ROOT / "asic/soc_vc4_4kb"
TOP = WSL_ROOT + "/asic/soc_vc4_4kb/soc_asic_top.v"
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


def fill_netlist(run):
    found = sorted(run.glob("*-openroad-fillinsertion/soc_asic_top.nl.v"))
    if len(found) != 1:
        raise ValueError(f"Expected exactly one fill-insertion netlist in {run}, found {len(found)}")
    return found[0]


def check_run(run, inputs=None):
    config = json.loads((run / "resolved.json").read_text())
    files = config["VERILOG_FILES"]
    if len(files) != 42 or files[-1] != TOP:
        raise ValueError(f"{run.name}: not the expected 42 DM_VC4 RTL inputs")
    if WSL_ROOT + "/asic/dse_sram/cache_dse_data_bank_sram.v" not in files:
        raise ValueError(f"{run.name}: missing the macro-backed DSE data bank")
    if inputs is not None and files != inputs:
        raise ValueError(f"{run.name}: RTL inputs differ from the replay source")
    return config


def common_scripts(inputs, macros):
    defs = "".join("verilog_defines -D" + d + "\n" for d in ("PDK_sky130A", "SCL_sky130_fd_sc_hd", "__openlane__", "__pnr__"))
    libs = "".join("read_verilog -sv -lib " + p + "\n" for p in macros) + "blackbox\n"
    return defs, libs


def flatten(source, target, n1=False):
    forbidden = ("t:$_DFF_PN0_ t:$_DFF_PN1_ t:$_DFFE_* t:$_SDFF* t:$_DFFSR* t:$_DLATCH* t:$dff t:$adff" if n1 else
                 "t:$adff t:$adffe t:$dffe t:$sdff t:$sdffe t:$sdffce t:$aldff t:$aldffe t:$dffsr t:$dffsre t:$dlatch t:$ff")
    return (f"read_ilang {source}\nhierarchy -top soc_asic_top\nasync2sync\ndffunmap\nopt_clean\n"
            f"select -assert-none {forbidden}\nwrite_ilang {target}\n")


def gold_scripts(inputs, macros):
    defs, libs = common_scripts(inputs, macros)
    gold_front = defs + libs + "read_verilog -formal -sv " + " ".join(inputs) + "\n"
    gold_front += "hierarchy -top soc_asic_top\nflatten\nrename -hide w:*.clk w:*.PCLK w:*.pclk\n"
    gold_pre = ("script gold_frontend.ys\nproc\nopt_expr\nopt_clean\nopt -nodffe -nosdff\nfsm\nhierarchy -top soc_asic_top\n"
                "proc\nprep -top soc_asic_top -flatten\nmemory -nomap\nmemory_map\nopt_clean\ncheck -assert -initdrv\n"
                "write_ilang gold_pre.il\n")
    fsm = (ROOT / "asic/equiv/fsm_recode/prove_fsm.ys").read_text()
    fsm = "\n".join(line for line in fsm.splitlines() if not line.lstrip().startswith("#"))
    fsm = fsm.replace("script front_end.ys", "script gold_frontend.ys") + "\n"
    return {"gold_frontend.ys": gold_front, "gold_pre.ys": gold_pre, "gold_flat.ys": flatten("gold_cut.il", "gold_flat.il"),
            "n1_flat.ys": flatten("n1_cut.il", "n1_flat.il", True), "prove_fsm.ys": fsm}


def gate_scripts(inputs, macros, ttlib, finals):
    defs, libs = common_scripts(inputs, macros)
    hide = ("rename -hide w:* x:* %d w:u_soc.* %d w:reset_meta_q %d w:reset_sync_q %d w:key1_sync_q* %d w:uart_rx_sync_q* %d "
            "w:soc_key1_n %d w:soc_reset_n %d w:soc_uart_rx %d\n")
    data = {}
    for n, net in enumerate(finals, 1):
        data[f"gate{n}_frontend.ys"] = (defs + libs + f"read_liberty -lib -ignore_miss_dir -setattr blackbox {ttlib}\n" +
            "read_verilog -formal -sv " + WSL_ROOT + "/asic/soc_dm_4kb/formal_pdk.v " + wsl(net) +
            "\nhierarchy -top soc_asic_top\nflatten\n" + hide)
        data[f"gate{n}_pre.ys"] = (f"script gate{n}_frontend.ys\nhierarchy -top soc_asic_top\nproc\nprep -top soc_asic_top -flatten\n"
                                   f"memory -nomap\nmemory_map\nopt_clean\ncheck -assert -initdrv\nwrite_ilang gate{n}_pre.il\n")
        data[f"gate{n}_flat.ys"] = flatten(f"gate{n}_cut.il", f"gate{n}_flat.il")
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--replay-tag", help="DM_VC4 full-flow run whose step 06 (config, extra, Liberty) is replayed")
    ap.add_argument("--gate-tags", help="two signed DM_VC4 runs, comma separated (with --add-gates)")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--add-gates", action="store_true")
    args = ap.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT / "results"):
        raise ValueError("Output must be under results/")
    formal = ROOT / "asic/soc_dm_4kb/formal_pdk.v"
    if sha(formal) != FORMAL_SHA:
        raise ValueError("Stable formal cell model differs from the proved DM model")
    if args.write:
        if out.exists() or not args.replay_tag:
            raise ValueError("--write needs a new output folder and --replay-tag")
        run = DESIGN_DIR / "runs" / args.replay_tag
        config = check_run(run)
        inputs = config["VERILOG_FILES"]
        macros = sorted({p for m in config["MACROS"].values() for p in m["nl"]})
        s06 = run / "06-yosys-synthesis"
        extra = json.loads((s06 / "extra.json").read_text())
        files = [local(p) for p in inputs + macros + extra["libs_synth"]] + [formal]
        files += [run / "resolved.json", s06 / "config.json", s06 / "extra.json", s06 / "soc_asic_top.nl.v"]
        replay = ROOT / "asic/equiv/lec/synth_replay_r14"
        files += [replay / n for n in ("synthesize_n1only.py", "synthesize_n1only_t1.py", "ys_common.py", "construct_abc_script.py")]
        helpers = ["evert.py", "const_check.py", "spec_manual.py", "mk_onehot_spec.py", "open_outputs.py", "aig_syms.py",
                   "aigsim.py", "macc_alg.py", "mulsub.py", "outsel.py", "free_spec.py", "inv_check.py", "aig_outputs_zero.py",
                   "sram_align.py", "run_frontends_vc4.ps1", "run_lec_vc4.ps1", "compare_lec_vc4_goldn1.py"]
        files += [ROOT / "asic/equiv/lec" / n for n in helpers]
        files += [ROOT / "asic/equiv/sec/sram_cut.py", ROOT / "asic/equiv/fsm_recode/prove_fsm.ys", ROOT / "results/rtl_manifest.json",
                  Path(__file__)]
        missing = [str(p) for p in files if not p.is_file()]
        if missing:
            raise ValueError("Missing inputs: " + ", ".join(missing))
        others = {}
        for r in sorted((DESIGN_DIR / "runs").iterdir()):
            net = r / "06-yosys-synthesis/soc_asic_top.nl.v"
            if net.is_file():
                others[r.name] = sha(net)
        data = gold_scripts(inputs, macros)
        out.mkdir()
        for p in ("p1", "p2"):
            (out / p).mkdir()
            for name, content in data.items():
                (out / p / name).write_text(content, encoding="ascii", newline="\n")
        record = {"status": "PREPARED_GOLD_N1_ONLY_NOT_A_LEC_RESULT", "design": "DM_VC4",
                  "replay_tag": args.replay_tag, "replay_step06_wsl": wsl(s06),
                  "replay_step06_netlist_sha256": sha(s06 / "soc_asic_top.nl.v"),
                  "step06_netlist_sha256_of_every_DM_VC4_run": others,
                  "rtl_inputs_ordered": inputs, "macro_models": macros,
                  "input_sha256": {p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p): sha(p) for p in files},
                  "gates": None,
                  "note": "Steps A, Mul, Inv prove gold == N1 and depend only on the synthesis; step B needs --add-gates with the "
                          "two signed runs, whose step-06 netlist must equal replay_step06_netlist_sha256."}
        (out / "lec_inputs.json").write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")
        print(f"[WROTE] {out.relative_to(ROOT)} p1, p2 gold/N1 scripts; replay source {args.replay_tag}; "
              f"{len(set(others.values()))} distinct step-06 netlist(s) over {len(others)} DM_VC4 runs")
        return 0
    record = json.loads((out / "lec_inputs.json").read_text())
    if record.get("gates") is not None or not args.gate_tags:
        raise ValueError("--add-gates needs --gate-tags and a folder without gates")
    tags = args.gate_tags.split(",")
    if len(tags) != 2 or tags[0] == tags[1]:
        raise ValueError("Exactly two distinct signed runs are required")
    runs = [DESIGN_DIR / "runs" / t for t in tags]
    configs = [check_run(r, record["rtl_inputs_ordered"]) for r in runs]
    for r in runs:
        if sha(r / "06-yosys-synthesis/soc_asic_top.nl.v") != record["replay_step06_netlist_sha256"]:
            raise ValueError(f"{r.name}: step-06 netlist differs from the replayed synthesis")
    finals = [fill_netlist(r) for r in runs]
    if sha(finals[0]) != sha(finals[1]):
        raise ValueError("The two signed final netlists differ")
    ttlib = configs[0]["LIB"]["*_tt_025C_1v80"][0]
    data = gate_scripts(record["rtl_inputs_ordered"], record["macro_models"], ttlib, finals)
    for p in ("p1", "p2"):
        for name, content in data.items():
            target = out / p / name
            if target.exists():
                raise ValueError(f"Refuse to overwrite {target}")
            target.write_text(content, encoding="ascii", newline="\n")
    record["gates"] = {"tags": tags, "final_netlists_wsl": [wsl(f) for f in finals], "final_netlist_sha256": sha(finals[0]),
                       "tt_liberty": ttlib}
    record["status"] = "PREPARED_GOLD_N1_AND_GATES_NOT_A_LEC_RESULT"
    (out / "lec_inputs.json").write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")
    print(f"[WROTE] gate scripts for {tags} in {out.relative_to(ROOT)} p1, p2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
