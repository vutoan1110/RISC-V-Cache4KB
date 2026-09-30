"""R14 board matrix: one SOF per firmware x cache configuration, for the interactive DE2-115 session.

The four 4 KiB points (dm_4kb, sa2_4kb, vc4_4kb, dse_4kb) are already fitted (Quartus pass 2, frozen RTL
3ea52396). A firmware image only changes the initial contents of the main RAM (M9K, ram_init_file =
hdl/riscv_full_byte{0..3}.mif), not the netlist, so each SOF is made by writing that firmware's MIFs,
`quartus_cdb --update_mif` and `quartus_asm` - no new synthesis or fit. The canonical MIFs are restored
(and every point re-assembled with them) when the script ends, even after an error or an abort.

    python scripts/fpga/build_board_matrix_r14.py            # ramsweep + 12 + 12 upstream kernels
    python scripts/fpga/build_board_matrix_r14.py --kernels crc32,up_crc32 --points dm_4kb

Output: output_files_board_matrix_r14/<kernel>_<CONFIG>.sof and INDEX.csv (md5, RTL id, fit seed, and the
simulated MCYCLE / MINSTRET the board must reproduce). Stop between SOFs: create results/.abort_board_build.
"""
import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RTL_ID = "3ea52396"
POINTS = {"dm_4kb": "DM", "sa2_4kb": "SA2", "vc4_4kb": "DM_VC4", "dse_4kb": "DM_DSE"}
UP = ("up_aha-mont64 up_crc32 up_depthconv up_edn up_huffbench up_matmult-int up_md5sum up_nettle-sha256 "
      "up_slre up_statemate up_tarfind up_ud").split()
# The same 12 upstream kernels at their ORIGINAL LOCAL_SCALE_FACTOR (no override), built into fw_board/ by
# scripts/metrics/build_upfull_fw.sh: the official iteration counts, too long for routine RTL simulation.
UPFULL = [k.replace("up_", "upfull_") for k in UP]
FW_DIRS = ("fw", "fw_board")
# Only the MIFs change; hdl/riscv_full.hex is a manifest file and is never touched.
MIFS = ["hdl/riscv_full_byte%d.mif" % i for i in range(4)]
EXPECTED_CSVS = ["results/upstream_r14_4kb_p1.csv", "results/ramsweep_r14_p1.csv",
                 "results/upfull_r14_4kb_p1.csv"]
ABORT = ROOT / "results" / ".abort_board_build"


def tool(name):
    root = Path(os.environ.get("QUARTUS_ROOTDIR", r"D:\altera\quartus")) / "bin64"
    found = shutil.which(name) or (root / (name + ".exe"))
    if not (found and Path(found).is_file()):
        sys.exit("[FAIL] %s not found; set QUARTUS_ROOTDIR" % name)
    return str(found)


def run(cmd, log, retries=3):
    """Run a Quartus tool; retry only a crash (this host's random faults), keeping each failed log."""
    for attempt in range(1, retries + 1):
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=3600)
        log.write_bytes(((p.stdout or "") + (p.stderr or "")).encode("utf-8", "replace"))
        if p.returncode == 0:
            return
        kept = log.with_name("%s.attempt%d.failed%s" % (log.stem, attempt, log.suffix))
        shutil.copy2(log, kept)
        print("        attempt %d failed (rc=%d), log kept as %s" % (attempt, p.returncode, kept.name), flush=True)
        time.sleep(5)
    raise RuntimeError("%s failed; see %s" % (Path(cmd[0]).name, log))


def md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def expected():
    exp = {}
    for rel in EXPECTED_CSVS:
        if not (ROOT / rel).is_file():
            continue
        with open(ROOT / rel, newline="") as fh:
            for r in csv.DictReader(fh):
                exp[(r["kernel"], r["config"])] = (int(r["mcycle"]), int(r["minstret"]))
    return exp


def fit_facts(point):
    """LE and slow-85C setup slack of the fit the SOF is assembled from (pass 2, last seed)."""
    rows = list(csv.DictReader(open(ROOT / "results" / "fpga_points_r14_p2.csv", newline="")))
    rows = [r for r in rows if r.get("point", "").split("@")[0] == point]
    r = rows[-1] if rows else {}
    return r.get("seed", ""), r.get("le", ""), r.get("setup_slack", "")


def assemble(point, logdir, bins):
    rev = "point_" + point
    run([bins["cdb"], rev, "-c", rev, "--update_mif"], logdir / ("%s_update_mif.log" % point))
    run([bins["asm"], rev, "-c", rev], logdir / ("%s_asm.log" % point))
    return ROOT / ("output_files_" + point) / (rev + ".sof")


def main():
    ap = argparse.ArgumentParser()
    # Standard kernels only: the project's own Embench-style kernels (OLD) were removed on 2026-09-30.
    ap.add_argument("--kernels", default=",".join(["ramsweep"] + UPFULL + UP))
    ap.add_argument("--points", default=",".join(POINTS))
    ap.add_argument("--out", default="output_files_board_matrix_r14")
    args = ap.parse_args()
    kernels = args.kernels.split(",")
    points = args.points.split(",")

    busy = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=30).stdout.lower().count("quartus_")
    if busy:
        sys.exit("[FAIL] %d quartus process(es) running; builds sharing db/ must be sequential" % busy)
    if subprocess.run(["git", "diff", "--quiet", "--", "hdl"], cwd=ROOT).returncode != 0:
        sys.exit("[FAIL] hdl/ differs from git HEAD; the board SOFs must come from the frozen RTL %s" % RTL_ID)
    fw = {}
    for k in kernels:
        found = [d for d in FW_DIRS if (ROOT / d / (k + ".hex")).is_file()]
        if not found:
            sys.exit("[FAIL] missing %s.hex in %s" % (k, "/".join(FW_DIRS)))
        fw[k] = "%s/%s.hex" % (found[0], k)

    out = ROOT / args.out
    logdir = out / "logs"
    backup = out / "canonical_mif"
    logdir.mkdir(parents=True, exist_ok=True)
    backup.mkdir(parents=True, exist_ok=True)
    for rel in MIFS:
        shutil.copy2(ROOT / rel, backup / Path(rel).name)
    bins = {s: tool("quartus_" + s) for s in ("cdb", "asm")}
    exp = expected()
    index = out / "INDEX.csv"
    cols = ["kernel", "config", "sof", "fw", "md5", "rtl_id", "fit_seed", "le", "setup_slack_slow85c_ns",
            "expected_mcycle", "expected_mcycle_hex", "expected_minstret", "expected_minstret_hex", "built"]
    rows = []
    total, n = len(kernels) * len(points), 0
    try:
        for k in kernels:
            subprocess.run([sys.executable, "scripts/fpga/hex_to_mif.py", "--input", fw[k],
                            "--output-dir", "hdl", "--depth", "4096"], cwd=ROOT, check=True,
                           capture_output=True)
            for p in points:
                if ABORT.exists():
                    print("[ABORT] %s present; stopping before %s_%s" % (ABORT.name, k, POINTS[p]), flush=True)
                    return 3
                t0 = time.time()
                sof = assemble(p, logdir, bins)
                name = "%s_%s.sof" % (k, POINTS[p])
                shutil.copy2(sof, out / name)
                mc, mi = exp.get((k, POINTS[p]), (None, None))
                seed, le, slack = fit_facts(p)
                rows.append({"kernel": k, "config": POINTS[p], "sof": name, "fw": fw[k], "md5": md5(out / name),
                             "rtl_id": RTL_ID, "fit_seed": seed, "le": le, "setup_slack_slow85c_ns": slack,
                             "expected_mcycle": mc if mc is not None else "",
                             "expected_mcycle_hex": "%08X" % mc if mc is not None else "",
                             "expected_minstret": mi if mi is not None else "",
                             "expected_minstret_hex": "%08X" % mi if mi is not None else "",
                             "built": time.strftime("%Y-%m-%d %H:%M:%S")})
                with open(index, "w", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=cols)
                    w.writeheader()
                    w.writerows(rows)
                n += 1
                print("[SOF] %s ready (%d/%d, %.0f s) expected MCYCLE %s"
                      % (name, n, total, time.time() - t0, rows[-1]["expected_mcycle_hex"] or "n/a"), flush=True)
    finally:
        # Put the canonical firmware back and re-assemble every point with it, so the project's own SOFs
        # and db/ match git again.
        for rel in MIFS:
            shutil.copy2(backup / Path(rel).name, ROOT / rel)
        for p in points:
            try:
                assemble(p, logdir, bins)
            except RuntimeError as exc:
                print("[WARN] restoring %s: %s" % (p, exc), flush=True)
        clean = subprocess.run(["git", "diff", "--quiet", "--", "hdl"], cwd=ROOT).returncode == 0
        print("[RESTORE] canonical MIFs back, points re-assembled; hdl/ %s git HEAD"
              % ("matches" if clean else "DIFFERS FROM"), flush=True)
    md5s = [r["md5"] for r in rows]
    print("[DONE] %d SOFs, %d distinct md5 -> %s" % (len(rows), len(set(md5s)), index), flush=True)
    return 0 if len(set(md5s)) == len(md5s) else 1


if __name__ == "__main__":
    sys.exit(main())
