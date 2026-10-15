"""Prepare guarded unrestricted-state frontend recipes; never run a tool flow.

Reuses the exact frozen state-cut algorithm without a spec or decoder. Functional
X/Z and unresolved drivers block execution; no zero/initial-state substitution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from lec_onehot_boolean import ROOT, enforce_process_memory, sha
from lec_reset_base import check_pairs

UNKNOWN = re.compile(r"\b\d+'[01xXzZmM-]*[xXzZmM-][01xXzZmM-]*\b")


def inspect_flat(path):
    """Stream the normalized top module; never load a 478 MB file into RAM."""
    ports, examples, functional_unknown, init_attributes = [], [], 0, 0
    top_count, in_top, cells = 0, False, {}
    with path.open(encoding="latin1") as stream:
        for line_number, line in enumerate(stream, 1):
            line = line.rstrip("\n\r")
            if line == "module \\soc_asic_top":
                in_top = True
                top_count += 1
            elif in_top and line == "end":
                in_top = False
            if not in_top:
                continue
            if line.startswith("  attribute "):
                init_attributes += int("\\init " in line)
                continue
            if line.startswith("  cell "):
                kind = line.split()[1]
                cells[kind] = cells.get(kind, 0) + 1
            if line.startswith("  wire "):
                tokens = line.split()
                for direction in ("input", "output", "inout"):
                    if direction in tokens:
                        width = int(tokens[tokens.index("width") + 1]) if "width" in tokens else 1
                        ports.append({"name": tokens[-1], "direction": direction, "width": width})
            if line.lstrip().startswith(("connect ", "parameter ")) and UNKNOWN.search(line):
                functional_unknown += 1
                if len(examples) < 8:
                    examples.append({"line": line_number, "text": line.strip()})
    if top_count != 1 or len({p["name"] for p in ports}) != len(ports) or not ports:
        raise ValueError("Unique complete top port declarations required")
    return {"bytes": path.stat().st_size, "top_ports": sorted(ports, key=lambda p: p["name"]),
            "top_cell_types": cells, "functional_X_Z_or_marked_literal_lines": functional_unknown,
            "functional_unknown_examples": examples, "init_attributes_metadata_only": init_attributes,
            "source_is_untransformed_RTL": False,
            "model_stage": "After SRAM boundary cuts, async2sync and dffunmap; before state cuts/onehot/constant/duplicate restrictions",
            "guard_status": "BLOCKED_FUNCTIONAL_UNKNOWN_LITERALS" if functional_unknown else "UNDRIVEN_AND_TOOL_SEMANTICS_CHECKS_STILL_REQUIRED"}


def wsl(path):
    if path.drive.lower() != "e:":
        raise ValueError("Only the named research drive is permitted")
    return "/mnt/e/" + path.relative_to(Path("E:/")).as_posix()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out = Path(args.out_dir).resolve()
    if not out.is_relative_to(ROOT) or out.exists():
        raise ValueError("New preparation directory in research required")
    memory = enforce_process_memory()
    lec = ROOT / "asic/equiv/lec"
    models = ["gold_flat_r14.il", "n1_flat_r14.il", "gate_flat_R14FA.il", "gate_flat_R14FB.il"]
    auxiliary = ["evert.py", "pairsAR14.json", "pairsB_R14FA.json", "pairsB_R14FB.json",
                 "gold_flat_r14.ys", "n1_flat_r14.ys", "gate_flat_R14FA.ys", "gate_flat_R14FB.ys"]
    paths = [lec / name for name in models + auxiliary]
    paths += [ROOT / "asic/equiv/sec/sram_cut.py", Path(__file__).resolve()]
    hashes = {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    summaries = {}
    for name in models:
        summaries[name] = inspect_flat(lec / name)
        print(name, "streamed; functional unknown lines", summaries[name]["functional_X_Z_or_marked_literal_lines"], flush=True)
    pairs = {name: json.loads((lec / name).read_text())
             for name in ("pairsAR14.json", "pairsB_R14FA.json", "pairsB_R14FB.json")}
    for mapping in pairs.values():
        check_pairs(mapping)
    expected = {"pairsAR14.json": (19090, 368, 0),
                "pairsB_R14FA.json": (19087, 3, 0), "pairsB_R14FB.json": (19087, 3, 0)}
    for name, mapping in pairs.items():
        if (len(mapping["pairs"]), len(mapping["gold_only"]), len(mapping["gate_only"])) != expected[name]:
            raise ValueError("Exact current state mapping population required")
    combinations = [
        ("rtl_to_n1_gold", "gold_flat_r14.il", "gold", "pairsAR14.json"),
        ("rtl_to_n1_gate", "n1_flat_r14.il", "gate", "pairsAR14.json"),
        ("n1_to_final_a_gold", "n1_flat_r14.il", "gold", "pairsB_R14FA.json"),
        ("n1_to_final_a_gate", "gate_flat_R14FA.il", "gate", "pairsB_R14FA.json"),
        ("n1_to_final_b_gold", "n1_flat_r14.il", "gold", "pairsB_R14FB.json"),
        ("n1_to_final_b_gate", "gate_flat_R14FB.il", "gate", "pairsB_R14FB.json")]
    recipes = []
    out.mkdir()
    for label, source, side, pairfile in combinations:
        cut = out / (label + ".il")
        aig = out / (label + ".aig")
        ys = out / (label + ".ys")
        arguments = [sys.executable, str(lec / "evert.py"), "cut", str(lec / source),
                     side, str(lec / pairfile), str(cut)]
        if side == "gold":
            arguments.append("--gold-only-d")
        recipe = (f'read_ilang "{wsl(cut)}"\n'
                  'hierarchy -top soc_asic_top\n'
                  'check -assert\ntechmap\nopt_clean\naigmap\nopt_clean\ncheck -assert\n'
                  f'write_aiger -symbols "{wsl(aig)}"\n')
        if any(token in recipe for token in ("setundef", "-zero", "-zinit", "--spec", "--inv")):
            raise ValueError("Raw recipe must not change undefined or initial-state semantics")
        ys.write_text(recipe, encoding="ascii")
        recipes.append({"label": label, "side": side, "source": source,
                        "state_cut_argv_for_future_controlled_execution": arguments,
                        "yosys_recipe": ys.relative_to(ROOT).as_posix(),
                        "yosys_recipe_sha256": sha(ys),
                        "paired_Q_and_D_ports": len(pairs[pairfile]["pairs"]),
                        "own_unpaired_Q_ports": len(pairs[pairfile]["gold_only" if side == "gold" else "gate_only"]),
                        "extra_own_gold_D_exposed": side == "gold", "onehot_selectors": 0,
                        "constant_or_duplicate_Q_ties": 0,
                        "scope": "Unrestricted Q relative to the state-cut assumptions only; source-level X/reset semantics still require guards"})
    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Raw source/mapping/helper changed during preparation")
    receipt = {"status": "PREPARED_ONLY_BLOCKED_ON_FUNCTIONAL_UNKNOWN_AND_UNDRIVEN_GUARDS",
               "memory_enforcement": memory, "input_sha256": hashes,
               "model_summaries": summaries, "recipes": recipes,
               "source_model_gap_closed": False, "actual_frontend_or_proof_execution": False,
               "required_before_any_execution": [
                   "No healthy PD/FPGA/verification flow requiring machine resources; parent schedules the frontend after PD",
                   "Recheck all exact source/mapping/helper hashes, clock-edge metadata and SRAM boundary ports",
                   "Resolve every functional X/Z or marked literal by a proved guard/refinement contract; never silently set it to zero",
                   "Preserve nondeterministic unknown choices explicitly if an independently checked frontend contract permits them; do not assume anyseq or AIG support without pinned tool help",
                   "Native check -assert must reject undriven/unsupported logic before and after mapping",
                   "Each source flop Q must have its direct recorded fresh input connection; no decoder, alias or constant replacement",
                   "Post-cut port parity and exact clocks/reset/macro boundary metadata must be checked; nominal unused ports are not evidence of unconstrained effective state",
                   "Original evert loads entire final RTLIL; do not put its 478 MB inputs under the 512 MiB local proof cap or launch without measured frontend memory headroom",
                   "Two independent complete frontend runs and source/artifact hashes before proof promotion"],
               "coupled_reset_proof_contract": "Corresponding paired state starts as the SAME arbitrary symbol; all unpaired states remain explicit, with separately proved needed invariant relations. Reset cofactor D comparisons must hold for all remaining symbolic state and shared SRAM read inputs. No register/RAM zero-init assumption.",
               "lightweight_next_step": "A new bounded streaming/lazy evaluator of pre-setundef RTLIL may prove reset-masked D cones without a whole frontend only after all reached cell semantics, widths, aliases and unknown branches are explicitly supported and independently checked; unsupported cones remain UNKNOWN. No such evaluator/proof was executed here.",
               "full_sequential_LEC": "OPEN"}
    (out / "preparation.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print("PREPARED ONLY: six unrestricted-state recipes; no tool/solver executed, source guards block use")


if __name__ == "__main__":
    main()
