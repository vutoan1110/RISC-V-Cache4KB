"""Unified metric table (rulebook K / directive 2026-09-30 "Embench metrics expansion").

One row per cache configuration (4 KiB caches, branch predictor on, FPGA view unless stated), built only from
result files on disk -- nothing typed in -- and every source named in the output:

  workload (12 upstream Embench-IoT kernels, results/rfbht_4kb_p{1,2}.csv, current RTL 6c4ccffd)
    CPI            sum(mcycle) / sum(minstret) over the 12 kernels
    I$ hit %       sum(i_hit_ev) / sum(i_access)
    D$ read hit %  sum(d_rd_hit) / sum(d_read)
    BP mispredict % sum(mispredict) / sum(predictions)
  Embench-IoT score (full original iteration counts, results/upfull_r14_4kb_p1.csv; reference = baseline
    speed.json of embench-iot 09c2ed8c, ms at 1 MHz -> reference cycles = ms x 1000)
    speed/MHz GM, GSD   per kernel ref_cycles / mcycle; geometric mean and geometric standard deviation
  code size (results/code_size_r14.csv; reference size.json .text) -- the same binaries for every configuration
    size GM, GSD        per kernel kernel-text / reference text (benchmark sources only: harness, support
                        code and libgcc are excluded, as Embench excludes its own support code)
  interrupts (results/irq_metrics.csv, steady state = median of the samples)
    IRQ entry           timer line -> first handler instruction retired, minimal handler, register work
    IRQ total           whole interruption with the minimal handler
    ctx switch          whole interruption with the full context switch (31 GPRs + mepc saved and restored)
  FPGA (results/fpga_points_fpga_common_seeds_continued_20261009_p{1,2}.csv):
    40 paired points at common seeds 1..10; the table uses common seed 2, fixed before the extension.
    LE, Fmax Slow 85C; recorded inputs, row origins and fit reports must retain their hashes.
  MCYCLE match: FPGA view vs ASIC view (results/upstream_asic_r15_p1.csv, results/dse_asic_view_p1.csv)
    -- the documented difference: the RAM macro wrapper ignores the MISS_PENALTY hooks; GLS and board columns
    are filled when those runs exist (physical board session: NOT RUN).
  ASIC: exact signed-off DM/SA2 tags; activity power only after independent second STA evidence is checked.
    Area/all-corner timing and artifact equality: results/asic_ppa_verified_subset_20261010.json.
  CoreMark: results/coremark_crc_checked_20261009/, 22 actual simulations / 11 independent pairs.
    Recorded source/artifact hashes, suite numerical CRCs and all 40 snapshot fields must match the current baseline.
    ITERATIONS=1, full-program window, simulation RAM 32 KiB; no official score or historical sweep promotion.

    python scripts/metrics/unified_table.py  -> results/unified_metrics.csv and results/unified_metrics.md
"""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from asic_ppa_audit import PAIRS, activity, paired_csv, last

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "results"
BASE = ROOT / "scripts" / "metrics" / "embench_baseline_09c2ed8c"
CONFIGS = ["DM", "SA2", "DM_VC4", "DM_DSE"]
FPGA_POINT = {"DM": "dm_4kb", "SA2": "sa2_4kb", "DM_VC4": "vc4_4kb", "DM_DSE": "dse_4kb"}
FPGA_TAG = "fpga_common_seeds_continued_20261009"
COREMARK_RESULTS = R / "coremark_crc_checked_20261009"
COREMARK_CONFIGS = {0: "DM", 1: "SA2", 2: "DM_VC4", 3: "DM_DSE", 4: "SA4", 5: "SA2N"}
COREMARK_CASES = [(0, cfg) for cfg in range(6)] + [(1, cfg) for cfg in range(1, 6)]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def checked_recorded_paths(records, label):
    if not isinstance(records, dict) or not records:
        raise RuntimeError(f"CoreMark receipt lacks recorded {label} hashes")
    for rel, expected in records.items():
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(ROOT.resolve()) or digest(path) != expected:
            raise RuntimeError(f"CoreMark recorded {label} differs: {rel}")


def verified_coremark(receipt_path=None):
    """Recheck the current 11-point CRC supplement; do not promote historic sweeps."""
    receipt_path = receipt_path or COREMARK_RESULTS / "verification.json"
    meta = json.loads(receipt_path.read_text(encoding="utf-8"))
    if meta.get("status") != "VERIFIED_11_PAIRED_CASES_CRC_AND_ALL_COUNTERS_EQUAL_REFERENCE":
        raise RuntimeError("CoreMark CRC supplement is not completed and independently paired")
    if (meta.get("ram_bytes"), meta.get("cache_bytes_each"), meta.get("official_score"),
            meta.get("cases_per_pass"), meta.get("method")) != (
            32768, 4096, False, 11, "accepted_apb_txdata_bytes_to_source_reference_crcs"):
        raise RuntimeError("Unexpected CoreMark measurement scope or validation method")
    manifest = json.loads((R / "rtl_manifest.json").read_text())
    if meta.get("rtl_id") != manifest["aggregate"]:
        raise RuntimeError("CoreMark evidence belongs to a different current RTL")
    inputs, artifacts = meta.get("inputs"), meta.get("artifacts")
    checked_recorded_paths(inputs, "source")
    checked_recorded_paths(artifacts, "artifact")
    required_inputs = set(manifest["files"]) | {
        "results/rtl_manifest.json", "sw/coremark/core_main.c", "tb/compile_active_design.do",
        "scripts/snapshot_fields.py", "scripts/verification/coremark_uart_observer.sv",
        "scripts/verification/coremark_crc_gate.py", "scripts/verification/run_coremark_crc.py"}
    if not required_inputs <= set(inputs) or any(inputs[rel] != sha for rel, sha in manifest["files"].items()):
        raise RuntimeError("CoreMark receipt does not cover the complete current frozen inputs")
    expected_cases = {(pass_no, COREMARK_CONFIGS[cfg], fast)
                      for pass_no in (1, 2) for fast, cfg in COREMARK_CASES}
    cases = meta.get("cases", [])
    actual_cases = {(case["pass"], case["config"], case["fast_hit"]) for case in cases}
    if len(cases) != 22 or actual_cases != expected_cases or any(
            case.get("crc_pass") is not True or case.get("counters_equal_current_reference") is not True for case in cases):
        raise RuntimeError("CoreMark receipt lacks 22 distinct independently verified cases")
    if len(meta.get("libraries", [])) != 2 or len(set(meta["libraries"])) != 2:
        raise RuntimeError("CoreMark supplement lacks two independent private libraries")

    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT / "scripts/verification"))
    from snapshot_fields import FIELDS, invariants, parse as parse_snapshot
    from coremark_crc_gate import known_crcs, validate_case
    if len(FIELDS) != 40:
        raise RuntimeError("Current CoreMark supplement expects all 40 snapshot fields")
    reference = known_crcs(ROOT / "sw/coremark/core_main.c")
    canonical = {}
    for fast in (0, 1):
        name = "coremark_rfbht" + ("f" if fast else "") + "_4kb"
        baseline_paths = [R / f"{name}_p{p}.csv" for p in (1, 2)]
        for path in baseline_paths:
            if path.relative_to(ROOT).as_posix() not in inputs:
                raise RuntimeError("CoreMark baseline is outside the receipt's hashed inputs")
        baseline = paired_csv(*baseline_paths, ["config_id"])
        ids = range(1, 6) if fast else range(6)
        if set(baseline) != {(str(cfg),) for cfg in ids}:
            raise RuntimeError("CoreMark canonical baseline has missing or unexpected configurations")
        for cfg in ids:
            row = baseline[(str(cfg),)]
            if row["kernel"] != "coremark" or row["config"] != COREMARK_CONFIGS[cfg]:
                raise RuntimeError("CoreMark canonical baseline context differs")
            canonical[(fast, cfg)] = {field: int(row[field]) for field in FIELDS}

    pair_paths = [COREMARK_RESULTS / f"results_p{p}.csv" for p in (1, 2)]
    required_artifacts = {path.relative_to(ROOT).as_posix() for path in pair_paths}
    paired = paired_csv(*pair_paths, ["fast_hit", "config_id"])
    if set(paired) != {(str(fast), str(cfg)) for fast, cfg in COREMARK_CASES}:
        raise RuntimeError("CoreMark CRC CSVs do not contain the current 11-point matrix")
    for pass_no in (1, 2):
        for fast, cfg in COREMARK_CASES:
            suffix = f"p{pass_no}_c{cfg}{'_fast' if fast else ''}"
            log, uart = COREMARK_RESULTS / f"{suffix}.log", COREMARK_RESULTS / f"{suffix}.uart.txt"
            required_artifacts.update(path.relative_to(ROOT).as_posix() for path in (log, uart))
            counters, numeric = validate_case(log, uart, reference, cfg, parse_snapshot, invariants)
            row = paired[(str(fast), str(cfg))]
            if row["kernel"] != "coremark" or row["config"] != COREMARK_CONFIGS[cfg] or \
                    counters != canonical[(fast, cfg)] or counters != {field: int(row[field]) for field in FIELDS}:
                raise RuntimeError("CoreMark raw snapshot/paired CSV/canonical baseline differ: " + suffix)
            if any(str(value) != row.get(field) for field, value in numeric.items()):
                raise RuntimeError("CoreMark raw CRC values/validation status differ from paired CSV: " + suffix)
    if not required_artifacts <= set(artifacts):
        raise RuntimeError("CoreMark receipt lacks required raw or paired artifacts")
    # Catch any concurrent input/result rewrite before publishing the new table.
    checked_recorded_paths(inputs, "source")
    checked_recorded_paths(artifacts, "artifact")
    print("[VERIFIED] CoreMark: 22 actual simulations, 11 pairs, suite CRCs and all 40 counters equal current baseline")
    return {COREMARK_CONFIGS[cfg]: paired[("0", str(cfg))] for cfg in range(6)}


def rows(path):
    p = R / path
    return list(csv.DictReader(open(p, encoding="utf-8"))) if p.is_file() else []


def gm_gsd(vals):
    logs = [math.log(v) for v in vals]
    m = sum(logs) / len(logs)
    sd = math.sqrt(sum((x - m) ** 2 for x in logs) / len(logs))   # population, as Embench reports
    return math.exp(m), math.exp(sd)


def ksum(rs, f):
    return sum(int(r[f]) for r in rs)


def fpga_hardware_pair(tables, cols, seeds):
    """Require the complete common-seed matrix, ignoring only fit runtime."""
    if len(tables) != 2 or len(cols) != 116 or len(set(cols)) != 116 or cols[-1] != "seconds":
        raise RuntimeError("Require two FPGA passes and the complete 115-hardware-field schema")
    expected = {(point, seed) for point in FPGA_POINT.values() for seed in seeds}
    maps = []
    for table in tables:
        one = {}
        for row in table:
            if list(row) != list(cols) or any(row[c] in ("", None) for c in cols if c != "seconds"):
                raise RuntimeError("Incomplete FPGA hardware measurement schema")
            point, seed = row["point"].split("@")[0], int(row["seed"])
            identity = point if seed == 2 else f"{point}@s{seed}"
            if row["point"] != identity or (point, seed) in one:
                raise RuntimeError("Wrong or duplicate FPGA point/seed identity")
            if point not in FPGA_POINT.values() or (
                    int(row["cache_config"]), int(row["capacity_bytes"]), int(row["line_bytes"]),
                    int(row["lines"]), int(row["l0"]), int(row["victim_entries"])) != (
                    list(FPGA_POINT.values()).index(point), 4096, 16, 256, 8, 4):
                raise RuntimeError("FPGA row belongs to a different cache configuration or geometry")
            one[point, seed] = row
        if set(one) != expected or len(table) != len(expected):
            raise RuntimeError("FPGA matrix is missing or adds common point/seed rows")
        maps.append(one)
    for key in expected:
        if any(maps[0][key][c] != maps[1][key][c] for c in cols if c != "seconds"):
            raise RuntimeError(f"Independent FPGA hardware fields differ: {key}")
    return maps


def check_fpga_completion(plan, progress, receipt, ppa, maps, baseline, cols, rtl_id, plan_sha):
    """Check completion/provenance metadata before rechecking recorded files."""
    expected_jobs = {f"p{n}/{p}/s{s}" for n in (1, 2) for p in FPGA_POINT.values()
                     for s in (*range(5, 11), 2)}
    expected_origins = {f"p{n}/{p}/s{s}" for n in (1, 2) for p in FPGA_POINT.values() for s in range(1, 11)}
    if (plan.get("rtl_id"), plan.get("common_seed"), plan.get("seeds"), plan.get("tag"),
            plan.get("source_tag"), plan.get("completed_preserved")) != (
            rtl_id, 2, list(range(1, 11)), FPGA_TAG, "paired10_6c4ccffd_20261009", 51):
        raise RuntimeError("FPGA continuation plan has different RTL or common-seed policy")
    if (progress.get("status"), progress.get("plan_sha256"), progress.get("physical_status"),
            progress.get("source_completed_preserved"), progress.get("original_source_tag")) != (
            "READY_FOR_PHYSICAL_SESSION", plan_sha, "NOT_RUN", 51, plan["source_tag"]):
        raise RuntimeError("FPGA continuation lacks its completed, plan-bound receipt")
    if set(progress.get("done", {})) != expected_jobs or set(progress.get("row_origins", {})) != expected_origins:
        raise RuntimeError("FPGA receipt lacks all 56 new fits or 80 distinct row origins")
    for point in FPGA_POINT.values():
        for seed in range(1, 11):
            origins = [progress["row_origins"][f"p{n}/{point}/s{seed}"] for n in (1, 2)]
            kind = "new_independent_measurement" if seed == 2 or seed >= 5 else "existing_independent_measurement"
            if any(origin.get("kind") != kind for origin in origins) or any(
                    origins[0].get(field) == origins[1].get(field) for field in ("source_csv", "reports")):
                raise RuntimeError("FPGA passes do not have the required independent measurement provenance")
            for n, origin in enumerate(origins, 1):
                if not origin.get("reports", "").replace("\\", "/").endswith(f"_p{n}/{point}/s{seed}"):
                    raise RuntimeError("FPGA report directory belongs to a different independent pass")
    csvs = [f"results/fpga_points_{FPGA_TAG}_p{n}.csv" for n in (1, 2)]
    if (receipt.get("rtl_id"), receipt.get("common_seed"), receipt.get("fit_p1"), receipt.get("fit_p2"),
            receipt.get("continuation_plan"), receipt.get("row_provenance")) != (
            rtl_id, 2, *csvs, f"results/{FPGA_TAG}_plan.json", f"results/{FPGA_TAG}_progress.json"):
        raise RuntimeError("FPGA seed-2 fit receipt is not bound to the completed matrix")
    settings = {**plan["original_inputs"], **plan["continuation_sources"], **plan["canonical_mifs"]}
    reports = {f"output_files_{p}/point_{p}.{ext}" for p in FPGA_POINT.values()
               for ext in ("map.rpt", "fit.rpt", "sta.rpt", "fit.summary")} | {
               f"point_{p}.qsf" for p in FPGA_POINT.values()}
    if receipt.get("settings") != settings or set(receipt.get("reports", {})) != reports:
        raise RuntimeError("FPGA seed-2 receipt lacks its complete settings or fit report hashes")
    if (ppa.get("rtl_id"), ppa.get("seeds"), ppa.get("paired_rows"), ppa.get("passes"),
            ppa.get("board_common_seed"), ppa.get("power_method"), ppa.get("timing_corner"),
            ppa.get("physical_status")) != (rtl_id, list(range(1, 11)), 40, 2, 2,
            "Quartus default toggle-rate estimate", "Slow 1200 mV 85 C", "NOT_RUN") or \
            set(ppa.get("sources", {})) != set(csvs):
        raise RuntimeError("FPGA published PPA scope or measurement method differs")
    if set(receipt.get("points", {})) != set(FPGA_POINT.values()) or \
            set(ppa.get("statistics", {})) != set(FPGA_POINT.values()):
        raise RuntimeError("FPGA receipt lacks all four common-seed configurations")
    for cfg, point in FPGA_POINT.items():
        selected = maps[1][point, 2]
        r, s = receipt["points"][point], ppa["statistics"][point]
        if (r.get("config"), r.get("seed"), r.get("reference"), s.get("config"), s.get("seed2")) != (
                cfg, 2, selected, cfg, selected):
            raise RuntimeError("FPGA published seed-2 row differs from the paired matrix")
        for n in (0, 1):
            if any(maps[n][point, 2][c] != baseline[n][point, 2][c] for c in cols if c != "seconds"):
                raise RuntimeError("FPGA independent seed-2 refit differs from the original four-seed evidence")


def verified_fpga():
    """Read-only provenance audit of the completed ten-common-seed experiment."""
    paths = {kind: R / f"{FPGA_TAG}_{kind}.json" for kind in ("plan", "progress", "board_fit_receipt", "ppa")}
    metadata = {kind: json.loads(path.read_text(encoding="utf-8")) for kind, path in paths.items()}
    plan, progress, receipt, ppa = (metadata[k] for k in ("plan", "progress", "board_fit_receipt", "ppa"))
    sys.path.insert(0, str(ROOT / "scripts/fpga"))
    sys.path.insert(0, str(ROOT / "scripts"))
    # Check the immutable helper code before importing its read-only validation functions.
    for group in ("original_inputs", "preserved_evidence", "continuation_sources", "canonical_mifs"):
        if not isinstance(plan.get(group), dict) or not plan[group]:
            raise RuntimeError("FPGA plan lacks recorded " + group)
        for rel, expected in plan[group].items():
            path = (ROOT / rel.replace("\\", "/")).resolve()
            if not path.is_relative_to(ROOT.resolve()) or digest(path) != expected:
                raise RuntimeError("FPGA frozen input/evidence hash differs: " + rel)
    import run_fpga_points
    import continue_common_seed_preparation as audit

    def load_tables(names):
        tables = []
        for name in names:
            with (R / name).open(newline="", encoding="utf-8") as stream:
                reader = csv.DictReader(stream)
                if reader.fieldnames != run_fpga_points.COLS:
                    raise RuntimeError("FPGA CSV header differs from the measured complete schema")
                tables.append(list(reader))
        return tables

    csv_paths = [R / f"fpga_points_{FPGA_TAG}_p{n}.csv" for n in (1, 2)]
    maps = fpga_hardware_pair(load_tables([p.name for p in csv_paths]), run_fpga_points.COLS, range(1, 11))
    baseline = fpga_hardware_pair(load_tables([f"fpga_points_rfbht_p{n}.csv" for n in (1, 2)]),
                                  run_fpga_points.COLS, range(1, 5))
    manifest = audit.manifest()
    check_fpga_completion(plan, progress, receipt, ppa, maps, baseline, run_fpga_points.COLS,
                          manifest["aggregate"], digest(paths["plan"]))
    # Original/continued row CSVs, archived QSF geometry, actual report seeds/device,
    # and every recorded report hash are checked by the unchanged experiment validator.
    evidence = audit.validate_progress(progress, maps, baseline, run_fpga_points.COLS)
    audit.verify_hashes(receipt["settings"])
    audit.verify_hashes(receipt["reports"])
    audit.verify_hashes(ppa["sources"])
    evidence.update({p.relative_to(ROOT).as_posix(): digest(p) for p in (*paths.values(), *csv_paths)})
    evidence.update({**receipt["settings"], **receipt["reports"]})
    for group in ("original_inputs", "preserved_evidence", "continuation_sources", "canonical_mifs"):
        evidence.update(plan[group])
    print("[VERIFIED] FPGA: 40 paired common-seed rows, all 115 hardware fields equal, plan/input/report hashes checked")
    return {point: maps[0][point, 2] for point in FPGA_POINT.values()}, evidence


def fpga_seed2():
    return verified_fpga()[0]


def main():
    speed = json.load(open(BASE / "speed.json"))
    size = json.load(open(BASE / "size.json"))
    std = list(paired_csv(R / "rfbht_4kb_p1.csv", R / "rfbht_4kb_p2.csv", ["config", "kernel"]).values())
    full = list(paired_csv(R / "upfull_r14_4kb_p1.csv", R / "upfull_r14_4kb_p2.csv", ["config", "kernel"]).values())
    cs = {r["image"]: r for r in rows("code_size_r14.csv")}
    irq = {(r["config"], int(r["phase"])): r for r in rows("irq_metrics.csv")}
    fpga = fpga_seed2()
    asic_dm = {r["kernel"]: r for r in rows("upstream_asic_r15_p1.csv")}
    asic_dse = {(r["kernel"], r["config"]): r for r in rows("dse_asic_view_p1.csv")}
    # CRCs are checked against suite references, separately from completion and
    # counter invariants. ITERATIONS=1 remains a full-program simulation count.
    cmk = verified_coremark()

    # code size: identical binaries for every configuration
    ratios = []
    for img, r in cs.items():
        if not img.startswith("up_"):
            continue
        k = img[3:]
        ratios.append(int(r["text_kernel"]) / size[k]["text"])
    size_gm, size_gsd = gm_gsd(ratios) if ratios else (float("nan"), float("nan"))

    out = []
    for cfg in CONFIGS:
        s = [r for r in std if r["config"] == cfg]
        f = [r for r in full if r["config"] == cfg]
        if len(s) != 12 or len(f) != 12 or any(r["result_pass"] != "1" or r["invariant_pass"] != "1" for r in s+f):
            raise RuntimeError(f"Incomplete or failed canonical Embench subset: {cfg}")
        row = {"config": cfg, "kernels": len(s)}
        if s:
            row["cpi"] = ksum(s, "mcycle") / ksum(s, "minstret")
            row["icache_hit_pct"] = 100.0 * ksum(s, "i_hit_ev") / ksum(s, "i_access")
            row["dcache_read_hit_pct"] = 100.0 * ksum(s, "d_rd_hit") / ksum(s, "d_read")
            row["bp_mispredict_pct"] = 100.0 * ksum(s, "mispredict") / ksum(s, "predictions")
        if f:
            sc = [speed[r["kernel"].replace("upfull_", "")] * 1000.0 / int(r["mcycle"]) for r in f]
            row["embench_speed_per_mhz_gm"], row["embench_speed_gsd"] = gm_gsd(sc)
            row["embench_kernels"] = len(sc)
        row["size_gm"], row["size_gsd"] = size_gm, size_gsd
        if cfg in cmk:
            row["coremark_1iter_mcycle"] = int(cmk[cfg]["mcycle"])
            row["coremark_crc_gate"] = "PASS"
        for name, ph, fld in (("irq_entry", 1, "entry_median"), ("irq_total", 1, "total_median"),
                              ("ctx_switch_total", 2, "total_median"), ("irq_entry_cold", 1, "entry_first")):
            if (cfg, ph) in irq:
                row[name] = float(irq[(cfg, ph)][fld])
        p = fpga.get(FPGA_POINT[cfg])
        if p:
            row["fpga_le"], row["fpga_fmax_mhz"] = int(p["le"]), float(p["fmax"])
        # MCYCLE: FPGA view vs ASIC view (kernels whose mcycle is identical / total)
        av = [(r, asic_dm.get(r["kernel"])) if cfg == "DM" else (r, asic_dse.get((r["kernel"], cfg))) for r in s]
        av = [(a, b) for a, b in av if b is not None]
        if av:
            row["asic_view_mcycle_sum_pct_vs_fpga"] = 100.0 * (sum(int(b["mcycle"]) for _, b in av)
                                                                / sum(int(a["mcycle"]) for a, _ in av) - 1.0)
            row["asic_view_kernels"] = len(av)
        # GLS / activity-based power of the signed-off final netlist (NHAT_KY.md 2026-09-30)
        tag = {"DM": PAIRS["DM"][1], "SA2": PAIRS["SA2"][1],
               "DM_VC4": "vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1"}.get(cfg)
        g = rows("gls_power_%s.csv" % tag) if tag else []
        p = []
        if cfg in PAIRS:
            design = PAIRS[cfg][0]
            run = ROOT / "asic" / design / "runs" / tag
            reference = R / ("upstream_asic_r15_p1.csv" if cfg == "DM" else "dse_asic_view_p1.csv")
            checked = activity(tag, run, reference, cfg)
            if checked["status"] == "VERIFIED_TWO_INDEPENDENT_STA_PASSES":
                p = checked["kernels"]
        if g:
            ok = sum(1 for r in g if r["match"] == "YES")
            row["gls_mcycle_match"] = "%d/%d kernels = ASIC-view RTL (%s)" % (ok, len(g), tag)
        else:
            row["gls_mcycle_match"] = "pending (after PD)" if tag else "N/A (no ASIC build)"
        row["board_mcycle_match"] = "NOT_RUN (physical session pending; common seed 2)"
        if p:
            tot = [float(r["total_mw"]) for r in p]
            epi = [float(r["epi_pj"]) for r in p]
            row["asic_power_saif"] = "%.1f-%.1f mW (mean %.1f), nom_tt, %d kernels" % (min(tot), max(tot), sum(tot) / len(tot), len(p))
            row["asic_epi_pj"] = "%.0f-%.0f pJ (GM %.0f)" % (min(epi), max(epi), gm_gsd(epi)[0])
        else:
            row["asic_power_saif"] = ("pending independent second STA evidence" if cfg in PAIRS else
                                      "pending sign-off + GLS + two STA passes" if tag else "N/A (no ASIC build)")
        out.append(row)

    cols = []
    for r in out:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(R / "unified_metrics.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(out)

    def fmt(v, nd=3):
        return ("%.*f" % (nd, v)) if isinstance(v, float) else str(v)

    md = ["# Unified metrics (4 KiB caches, BP on)", "",
          "Generated by scripts/metrics/unified_table.py. Current RTL: 6c4ccffd. Embench and CoreMark sources: "
          "results/rfbht_4kb_p{1,2}.csv and results/coremark_crc_checked_20261009/results_p{1,2}.csv; full iterations: "
          "results/upfull_r14_4kb_p{1,2}.csv. FPGA: results/fpga_points_" + FPGA_TAG + "_p{1,2}.csv. "
          "All 40 point/seed pairs agree on 115 hardware fields; runtime is excluded. The four configurations use "
          "the same seeds 1..10; this table uses common seed 2, fixed before the expanded experiment. "
          "Seeds 1, 3 and 4 retain the independent rfbht fits; seeds 5..10 and seed 2 were refitted twice. "
          "Seed-2 rows reproduce the original four-seed evidence exactly. The plan, completion receipt, row origins "
          "and report hashes are checked before publication. FPGA timing is Slow 1200 mV 85 C; power in the full "
          "matrix is a Quartus default toggle-rate estimate. "
          "Physical board session NOT RUN.", "",
          "ASIC sign-off gate: DM and SA2 PASS in both runs; DM_VC4 has no signed-off result. "
          "The full gate and all nine named timing corners are in results/asic_ppa_verified_subset_20261010.md. "
          "ASIC activity power uses GLS -> SAIF -> OpenSTA at nom_tt_025C_1v80 with RCX SPEF. DM and SA2 each "
          "have two independent raw STA report sets for all 12 kernels. Their power receipt and raw reports "
          "are rechecked before inclusion; the SA2 minimum die remains unproved. "
          "The later raw-window audit found one extra 20 ns period in all 24 preserved DM/SA2 SAIFs; "
          "legacy win_t*_ns timestamps actually contain picoseconds. These paired STA values reproduce "
          "their preserved inputs; exact-window recapture and paired STA remain pending. "
          "Evidence: results/embench_gls_evidence_audit_20261010/receipt.json.", "",
          "CoreMark is a CRC-validated full-program simulation counter with 32 KiB RAM; the window includes "
          "initialization, CRC validation and UART reporting. The supplement verifies source-known list/matrix/state "
          "CRCs from passive APB TXDATA captures in 22 actual simulations (11 independent pairs), with all 40 snapshot "
          "fields equal to the current reference. Its scope is the current six baseline points and five FAST_HIT points. "
          "Evidence: results/coremark_crc_checked_20261009/verification.json. ITERATIONS=1 is shorter than 10 seconds; "
          "these counts are not an official CoreMark score or an iterate-only measurement.", "",
          "| metric | " + " | ".join(CONFIGS) + " |", "|---|" + "---:|" * len(CONFIGS)]
    labels = [("cpi", "CPI (12 Embench-IoT kernels)", 4), ("icache_hit_pct", "I$ hit %", 2),
              ("dcache_read_hit_pct", "D$ read hit %", 2), ("bp_mispredict_pct", "branch mispredict %", 2),
              ("embench_speed_per_mhz_gm", "Embench speed / MHz, GM", 3), ("embench_speed_gsd", "Embench speed, GSD", 3),
              ("size_gm", "code size vs reference, GM", 3), ("size_gsd", "code size, GSD", 3),
              ("coremark_1iter_mcycle", "CoreMark program mcycle (CRC-validated simulation, RAM 32 KiB)", 0),
              ("coremark_crc_gate", "CoreMark numeric CRC gate (two independent simulations)", 0),
              ("irq_entry", "IRQ entry, cycles (steady)", 0), ("irq_entry_cold", "IRQ entry, cycles (first, cold)", 0),
              ("irq_total", "IRQ total, minimal handler", 0), ("ctx_switch_total", "context switch total, cycles", 0),
              ("fpga_le", "FPGA LE (seed 2)", 0), ("fpga_fmax_mhz", "FPGA Fmax Slow 85C, MHz", 2),
              ("asic_view_mcycle_sum_pct_vs_fpga", "ASIC-view mcycle vs FPGA view, %", 3),
              ("gls_mcycle_match", "GLS mcycle = ASIC-view RTL", 0), ("board_mcycle_match", "board mcycle", 0),
              ("asic_power_saif", "ASIC power (GLS->SAIF, OpenSTA nom_tt)", 0),
              ("asic_epi_pj", "ASIC energy per instruction", 0)]
    byc = {r["config"]: r for r in out}
    for key, lab, nd in labels:
        md.append("| %s | %s |" % (lab, " | ".join(fmt(byc[c].get(key, "-"), nd) for c in CONFIGS)))
    (R / "unified_metrics.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
