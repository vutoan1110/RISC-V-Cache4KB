"""Wait for the two active verified jobs, then assemble and audit common-seed SOFs.

No job is restarted, no board is programmed, and no PD flow is launched.
The existing Windows jobs remain independent. A failed or missing job stops
this continuation with its evidence preserved. Use --run to execute the plan.
"""
from __future__ import annotations

import argparse
import csv
import ctypes
import json
import statistics
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from board_common import ROOT, POINTS, MIFS, sha, manifest, validate_pair, check_idle, free_mb

FIT_TAG = "paired10_6c4ccffd_20261009"
REF_TAG = "board_reference_6c4ccffd_20261009"
OUT = ROOT / "output_files_board_matrix_6c4ccffd_seed2"
STATUS = ROOT / "results/board_preparation_6c4ccffd_seed2_20261009.json"


def now():
    return datetime.now(timezone(timedelta(hours=7)))


def write_status(value):
    temp = STATUS.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="ascii")
    temp.replace(STATUS)


def read_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # The reference job writes its completion metadata in one short write.
        return {}


class Job:
    """Hold a handle to the original Windows process, avoiding PID reuse."""
    def __init__(self, pid):
        from ctypes import wintypes
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.api.OpenProcess.restype = wintypes.HANDLE
        self.api.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.api.GetExitCodeProcess.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.OpenProcess(0x1000, False, pid)
        self.pid = pid
        if not self.handle:
            raise OSError(ctypes.get_last_error(), f"Cannot inspect original job PID {pid}; no restart is attempted")

    def alive(self):
        code = ctypes.c_ulong()
        if not self.api.GetExitCodeProcess(self.handle, ctypes.byref(code)):
            raise RuntimeError(f"Cannot read status of PID {self.pid}")
        return code.value == 259

    def close(self):
        self.api.CloseHandle(self.handle)


def journal(subject, body):
    path = ROOT / "NHAT_KY.md"
    text = path.read_text(encoding="utf-8")
    heading = f"### {now():%Y-%m-%d %H:%M} {subject}"
    entry = heading + "\n\n" + body + "\n\n"
    entry.encode("ascii")
    anchor = "## 8a."
    if anchor not in text:
        raise RuntimeError("History section anchor changed; completion evidence is kept in results")
    path.write_text(text.replace(anchor, entry + anchor, 1), encoding="utf-8")


def publish_fits():
    receipt_path = ROOT / f"results/{FIT_TAG}_board_fit_receipt.json"
    receipt = read_json(receipt_path)
    frozen = manifest()
    if receipt.get("rtl_id") != frozen["aggregate"] or receipt.get("common_seed") != 2:
        raise RuntimeError("Completed fit receipt has a different RTL or board seed")
    for rel, digest in {**receipt["reports"], **receipt["settings"]}.items():
        if sha(ROOT / rel) != digest:
            raise RuntimeError(f"Completed fit evidence changed: {rel}")
    pair = validate_pair(ROOT / receipt["fit_p1"], ROOT / receipt["fit_p2"], ["point", "seed"])
    expected = {(p if s == 2 else f"{p}@s{s}", str(s)) for p in POINTS for s in range(1, 11)}
    if set(pair) != expected:
        raise RuntimeError("Final fit comparison does not contain the common 1..10 seeds for all four points")
    stats = {}
    for p, cfg in POINTS.items():
        rows = [pair[p if s == 2 else f"{p}@s{s}", str(s)] for s in range(1, 11)]
        stats[p] = {"config": cfg, "seed2": pair[p, "2"], "metrics": {}}
        for field in ("le", "fmax_s85", "pow_total_mw"):
            values = [float(r[field]) for r in rows]
            stats[p]["metrics"][field] = {"min": min(values), "max": max(values),
                "mean": statistics.mean(values), "sample_sd": statistics.stdev(values)}
    fits = {"rtl_id": frozen["aggregate"], "seeds": list(range(1, 11)), "paired_rows": 40,
        "passes": 2, "board_common_seed": 2, "statistics": stats,
        "power_method": "Quartus default toggle-rate estimate", "timing_corner": "Slow 1200 mV 85 C",
        "sources": {rel: sha(ROOT / rel) for rel in (receipt["fit_p1"], receipt["fit_p2"])}}
    (ROOT / f"results/{FIT_TAG}_ppa.json").write_text(json.dumps(fits, indent=2) + "\n", encoding="ascii")
    table = ["### Ten common seeds on RTL 6c4ccffd\n",
        "The two independent passes match all hardware fields on 40 paired point/seed rows (wall time excluded). "
        "Every configuration uses the same seeds 1..10; comparisons are paired within seed. "
        "Seeds 1, 3 and 4 retain their original independent rfbht provenance; seeds 5..10 and common seed 2 "
        "were fitted in each new pass. The preceding four-seed table is retained as the earlier subset.\n",
        "Timing corner: Slow 1200 mV 85 C. Power method: Quartus default toggle-rate estimate. "
        "The physical board seed is 2 for all four configurations, fixed before the expanded results.\n",
        "| point | LE mean [min, max], SD | Fmax mean [min, max], SD, MHz | total power mean [min, max], SD, mW |",
        "|---|---|---|---|"]
    for p in POINTS:
        cells = []
        for field in ("le", "fmax_s85", "pow_total_mw"):
            d = stats[p]["metrics"][field]
            cells.append(f"{d['mean']:.2f} [{d['min']:g}, {d['max']:g}], {d['sample_sd']:.2f}")
        table.append(f"| {p} | " + " | ".join(cells) + " |")
    table += ["", f"Full field tables and within-seed differences: `results/fpga_seed_summary_{FIT_TAG}_p{{1,2}}.md`; "
        f"raw measurements: `results/fpga_points_{FIT_TAG}_p{{1,2}}.csv`. No physical board measurement is established here.", ""]
    path = ROOT / "RESULTS.md"
    text = path.read_text(encoding="utf-8")
    if "### Ten common seeds on RTL 6c4ccffd" in text or "## 4. ASIC" not in text:
        raise RuntimeError("RESULTS FPGA insertion anchor changed or already updated; inspect before republishing")
    path.write_text(text.replace("## 4. ASIC", "\n".join(table) + "\n## 4. ASIC", 1), encoding="utf-8")
    path = ROOT / "REVIEW_RESPONSE.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("FPGA 52-55 MHz at Slow 85C (four seeds);", "FPGA common ten-seed timing verified (RESULTS section 3);")
    text = text.replace("FPGA power four verified seeds (common ten-seed extension in progress);",
                        "FPGA power ten common seeds, paired and double-executed;")
    def ranges(field, unit):
        parts = []
        for p in POINTS:
            d = stats[p]["metrics"][field]
            parts.append(f"{POINTS[p]} {d['min']:.2f}-{d['max']:.2f}")
        return ", ".join(parts) + " " + unit

    a2_start = text.index("- FPGA (Cyclone IV E, four verified seeds,")
    a2_end = text.index("- ASIC (sky130A,", a2_start)
    text = text[:a2_start] + (
        "- FPGA (Cyclone IV E, ten common seeds, Slow 1200 mV 85 C, RTL 6c4ccffd): "
        + ranges("fmax_s85", "MHz") + ".\n"
        "  The same seeds 1..10 were fitted independently twice for all four configurations; 40/40 paired rows match\n"
        "  every hardware field. Full mean, range, sample SD and within-seed comparisons: RESULTS section 3.\n") + text[a2_end:]
    a9_start = text.index("- FPGA (Quartus Power Analyzer, default toggle-rate estimate, four verified seeds,")
    a9_end = text.index("- ASIC, activity-based", a9_start)
    text = text[:a9_start] + (
        "- FPGA (Quartus Power Analyzer, default toggle-rate estimate, ten common seeds, RTL 6c4ccffd): "
        + ranges("pow_total_mw", "mW total") + ".\n"
        "  All four configurations use the same seeds 1..10, compared within each seed and double-executed.\n"
        "  Board evidence uses common seed 2 fixed before the expanded results; no per-configuration best seed.\n") + text[a9_end:]
    path.write_text(text, encoding="utf-8")
    path = ROOT / "PROJECT_STATE.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("FPGA common-seed extension is running:", "FPGA common-seed extension is verified:")
    text = text.replace("The final matrix requires 40 paired rows. No ten-seed result yet.",
                        "The final matrix has 40/40 paired rows identical; all four board fits are at common seed 2.")
    path.write_text(text, encoding="utf-8")
    journal("FPGA: ma tran 10 seed chung da chay kep",
        f"- 40 / 40 cap point-seed khop moi truong phan cung; board giu seed 2 CHUNG, khong chon best seed rieng.\n"
        f"- Bang PPA va do lech chuan cap nhat RESULTS muc 3; bang du truong / chenh lech theo seed o\n"
        f"  results/fpga_seed_summary_{FIT_TAG}_p1.md va p2.md. Dau vao / report / nguon goc giu nguyen.\n"
        "- Day la ket qua Quartus, chua phai phep do board. Tham chieu board va SOF co cong xac minh rieng.")
    return fits


def audit_sofs():
    state = read_json(OUT / "BUILD_STATE.json")
    frozen = manifest()
    if state.get("state") != "READY_FOR_PHYSICAL_SESSION" or state.get("rtl_id") != frozen["aggregate"]:
        raise RuntimeError("SOF build is not ready on the frozen current RTL")
    if state.get("common_seed") != 2 or state.get("canonical_restoration") != "PASS":
        raise RuntimeError("SOF seed or canonical restoration check failed")
    reference = validate_pair(ROOT / f"results/{REF_TAG}_p1.csv", ROOT / f"results/{REF_TAG}_p2.csv",
                              ["kernel", "config"], ignore=())
    with (OUT / "INDEX.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    index = {(r["kernel"], r["config"]): r for r in rows}
    if len(rows) != 100 or set(index) != set(reference) or len({r["sha256"] for r in rows}) != 100:
        raise RuntimeError("SOF index is incomplete, duplicated or does not match the reference")
    for key, row in index.items():
        if row["fit_seed"] != "2" or row["rtl_aggregate"] != frozen["aggregate"]:
            raise RuntimeError(f"Wrong board seed/RTL: {key}")
        if sha(OUT / row["sof"]) != row["sha256"] or sha(ROOT / row["fw"]) != row["fw_sha256"]:
            raise RuntimeError(f"SOF or firmware checksum mismatch: {key}")
        for counter in ("mcycle", "minstret"):
            if int(row[f"expected_{counter}"]) != int(reference[key][counter]):
                raise RuntimeError(f"Expected {counter} differs: {key}")
    with (OUT / "BOARD_RESULTS_TEMPLATE.csv").open(newline="") as f:
        template = list(csv.DictReader(f))
    if len(template) != 200 or {(r["pass"], r["kernel"], r["config"]) for r in template} != {
            (str(p), k, c) for p in (1, 2) for k, c in index}:
        raise RuntimeError("Physical-results template does not have 200 unique cases")
    for r in template:
        if r["status"] != "NOT_RUN" or r["fit_seed"] != "2" or any(r[c] for c in
                ("observed_ledr_hex", "observed_mcycle_hex", "observed_minstret_hex", "uart_log", "photo")):
            raise RuntimeError("Prepared template contains observations or a wrong seed")
        expected = index[r["kernel"], r["config"]]
        if any(r[c] != expected[d] for c, d in (("sof_sha256", "sha256"),
                ("expected_mcycle_hex", "expected_mcycle_hex"), ("expected_minstret_hex", "expected_minstret_hex"))):
            raise RuntimeError("Physical-results template differs from the SOF index")
    if {p.name: sha(p) for p in MIFS} != state["canonical_mif_sha256"]:
        raise RuntimeError("Canonical MIFs differ after board assembly")
    return {"sof_count": 100, "reference_pairs": 100, "physical_template_rows": 200,
        "canonical_restoration": "PASS", "physical_status": "NOT_RUN", "index_sha256": sha(OUT / "INDEX.csv")}


def launch_continuation():
    """Continue only inspected incomplete measurements, in this foreground process tree."""
    check_idle()
    if free_mb() < 10000:
        raise RuntimeError("Less than 10 GB free before fit + reference continuation; owner scheduling required")
    archive = ROOT / "results/board_preparation_interrupted_20261009_1541/EVIDENCE.json"
    proof = read_json(archive)
    if proof.get("completed_fits") != 8 or len(proof.get("verified_completed_reference_cases", [])) != 38:
        raise RuntimeError("Expected interruption evidence is missing; no automatic continuation")
    plan = read_json(ROOT / f"results/{FIT_TAG}_plan.json")
    for rel, digest in plan["inputs"].items():
        if sha(ROOT / rel) != digest:
            raise RuntimeError(f"Fit continuation input changed: {rel}")
    for row in proof["verified_completed_reference_cases"]:
        if sha(ROOT / row["file"]) != row["sha256"]:
            raise RuntimeError(f"Completed reference case changed: {row['file']}")
    lock = ROOT / "results/.lock_paired_seed_matrix"
    if lock.exists():
        match = re.search(r"pid=(\d+)", lock.read_text())
        if not match:
            raise RuntimeError("Unrecognised fit lock; inspect before continuing")
        try:
            old_job = Job(int(match[1]))
        except OSError as exc:
            if exc.errno != 87:
                raise RuntimeError("Cannot prove the old fit process exited; keep the lock") from exc
        else:
            alive = old_job.alive()
            old_job.close()
            if alive:
                raise RuntimeError("Original fit process is still alive; no duplicate job")
        saved = archive.parent / "results/.lock_paired_seed_matrix"
        if sha(lock) != sha(saved):
            raise RuntimeError("Orphan lock differs from its archived copy")
        lock.unlink()  # Only the proved-orphaned lock; no run/result folder is removed.
    children, logs = [], []
    token = now().strftime("%Y%m%d_%H%M%S")
    specs = [("fit", FIT_TAG, "run_paired_seed_matrix.py"), ("reference", REF_TAG, "prepare_board_reference.py")]
    for label, tag, script in specs:
        path = ROOT / f"results/{tag}_continued_{token}.log"
        stream = path.open("xb")
        logs.append((path, stream))
        child = subprocess.Popen([sys.executable, "-u", f"scripts/fpga/{script}", "--run", "--resume"],
                                 cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        children.append(child)
        print(f"[CONTINUE] {label} PID={child.pid}; {path.relative_to(ROOT)}", flush=True)
    with (ROOT / "asic/gated_pd.log").open("a", encoding="ascii") as f:
        f.write(f"{now().isoformat()} NOTE board_prepare interrupted Windows sessions; input/report hashes checked; "
                "keep 8 completed fits and 38 verified reference cases; restart incomplete measurements with same inputs; "
                "evidence results/board_preparation_interrupted_20261009_1541/EVIDENCE.json; no hardware-fault claim\n")
    return children, logs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--launch-resume", action="store_true", help="Launch the two inspected interrupted jobs as foreground children")
    ap.add_argument("--fit-pid", type=int)
    ap.add_argument("--reference-pid", type=int)
    args = ap.parse_args()
    print("[PLAN] wait for verified common 10-seed fits and 100 paired references; then build/audit 100 seed-2 SOFs", flush=True)
    if not args.run:
        return 0
    if (not args.launch_resume and (not args.fit_pid or not args.reference_pid)) or STATUS.exists() or OUT.exists():
        raise RuntimeError("Require the original active job PIDs and new status/output paths; inspect existing evidence")
    jobs = []
    children, logs = [], []
    builder = ROOT / "scripts/fpga/build_board_matrix.py"
    frozen_builder = sha(builder)
    state = {"state": "WAITING_VERIFIED_JOBS", "started": now().isoformat(), "common_seed": 2,
        "rtl_id": manifest()["aggregate"], "fit_pid": args.fit_pid, "reference_pid": args.reference_pid,
        "physical_status": "NOT_RUN", "builder_sha256": frozen_builder}
    write_status(state)
    published = False
    try:
        if args.launch_resume:
            children, logs = launch_continuation()
            args.fit_pid, args.reference_pid = (child.pid for child in children)
            state.update(fit_pid=args.fit_pid, reference_pid=args.reference_pid,
                         continuation_logs=[p.relative_to(ROOT).as_posix() for p, stream in logs])
            write_status(state)
        for pid in (args.fit_pid, args.reference_pid):
            jobs.append(Job(pid))
        previous = None
        while True:
            fit = read_json(ROOT / f"results/{FIT_TAG}_progress.json")
            ref = read_json(ROOT / f"results/{REF_TAG}_inputs.json")
            fit_ready = fit.get("status") == "VERIFIED_40_PAIRED_ROWS"
            ref_ready = ref.get("status") == "VERIFIED_100_PAIRED_ROWS_EQUAL_R14"
            for label, obj in (("fits", fit), ("reference", ref)):
                if obj.get("status", "").startswith(("STOPPED", "ABORTED")):
                    raise RuntimeError(f"{label} job stopped: {obj.get('error', obj.get('status'))}; no retry")
            if (ROOT / "results/.abort_board_completion").exists():
                raise RuntimeError("Completion stopped between phases; active measurement jobs are left running")
            if not published and fit_ready and not (ROOT / "results/.lock_paired_seed_matrix").exists():
                state["fpga"] = publish_fits()
                published = True
                write_status(state)
                print("[VERIFIED] common ten-seed PPA published from 40 identical paired rows", flush=True)
            current = (len(fit.get("done", {})), fit.get("status"), ref.get("status"))
            if current != previous:
                print(f"[WAIT] new fits {current[0]}/56; fits={current[1]}; references={current[2]}", flush=True)
                previous = current
            if published and ref_ready:
                break
            for job, ready, path in ((jobs[0], fit_ready, ROOT / f"results/{FIT_TAG}_progress.json"),
                                     (jobs[1], ref_ready, ROOT / f"results/{REF_TAG}_inputs.json")):
                if not ready and not job.alive() and not read_json(path).get("status", "").startswith("VERIFIED_"):
                    raise RuntimeError(f"Original job PID {job.pid} exited without verified completion; no restart")
            time.sleep(30)
        if sha(builder) != frozen_builder:
            raise RuntimeError("Board builder changed while completion was waiting; inspect before assembly")
        check_idle()
        if free_mb() < 6000:
            raise RuntimeError("Less than 6 GB free before assembly; owner scheduling decision required")
        state["state"] = "ASSEMBLING_SOFS"
        write_status(state)
        log = ROOT / "results/board_matrix_6c4ccffd_seed2_20261009_build.log"
        with log.open("wb") as f:
            p = subprocess.run([sys.executable, "-u", str(builder), "--build"], cwd=ROOT,
                               stdout=f, stderr=subprocess.STDOUT)
        if p.returncode:
            raise RuntimeError(f"Board assembly failed rc={p.returncode}; inspect {log}; no restart")
        state["board_audit"] = audit_sofs()
        state["state"] = "READY_FOR_PHYSICAL_SESSION"
        state["completed"] = now().isoformat()
        write_status(state)
        journal("Board: 100 SOF 6c4ccffd seed 2 chung da chuan bi",
            "- Tham chieu 100 kernel-config tren RTL hien tai da mo phong kep, khop toan bo counter voi R14.\n"
            "- 100 SOF / SHA-256 / INDEX / checklist / template 200 dong da kiem; MIF chuan khoi phuc va manifest khop.\n"
            "- Bang chung: output_files_board_matrix_6c4ccffd_seed2/ va\n"
            "  results/board_preparation_6c4ccffd_seed2_20261009.json. Chua program board; phien vat ly hen sau.")
        path = ROOT / "PROJECT_STATE.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace("It has not built any SOFs yet.",
            "All 100 SOFs are built and audited; see results/board_preparation_6c4ccffd_seed2_20261009.json. Physical session NOT RUN.")
        text = text.replace("Current reference job running:", "Current reference job verified:")
        text = text.replace("No reference result yet.", "100/100 paired rows identical to R14.")
        path.write_text(text, encoding="utf-8")
        print("[READY] 100 audited SOFs at common seed 2; physical board session NOT RUN", flush=True)
        return 0
    except BaseException as exc:
        state["state"] = "STOPPED_REQUIRES_INSPECTION"
        state["error"] = str(exc)
        state["stopped"] = now().isoformat()
        write_status(state)
        journal("Board: buoc tiep tuc dung, giu bang chung",
            f"- Ly do: {str(exc).encode('ascii', 'backslashreplace').decode()}\n"
            "- Khong restart job, khong xoa output, khong program board; chi kiem tra read-only truoc khi xu ly tiep.\n"
            "- Trang thai: results/board_preparation_6c4ccffd_seed2_20261009.json.")
        raise
    finally:
        for job in jobs:
            job.close()
        for child in children:
            # A failure of the continuation is not permission to kill a healthy
            # measurement job. Keep the foreground host until children finish.
            child.wait()
        for path, stream in logs:
            stream.close()


if __name__ == "__main__":
    raise SystemExit(main())
