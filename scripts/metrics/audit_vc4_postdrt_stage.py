"""Read-only stage-boundary evidence; no process inspection or control."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAG = "vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1"


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    run = ROOT / "asic/soc_vc4_4kb/runs" / TAG
    step = run / "43-openroad-detailedrouting"
    source = ROOT / "asic/openlane-local/openlane/scripts/openroad/drt.tcl"
    config = json.loads((run / "resolved.json").read_text(encoding="utf-8"))
    env = (step / "_env.tcl").read_text(encoding="utf-8")
    report_dir = step / "drc_iter_main"
    reports = [{"name": p.name, "bytes": p.stat().st_size,
                "mtime_utc": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
                "sha256": sha(p)} for p in sorted(report_dir.glob("*.rpt"))]
    files = (run / "resolved.json", step / "_env.tcl", step / "COMMANDS", source)
    record = {"status": "READ_ONLY_STAGE_BOUNDARY_INFERENCE_NOT_PROCESS_STACK",
              "capture_utc": datetime.now(timezone.utc).isoformat(), "run": TAG,
              "configured_postDRT_antenna_repair_rounds": config["DRT_ANTENNA_REPAIR_ITERS"],
              "actual_step_env_relevant_lines": [line for line in env.splitlines() if "DRT_ANTENNA_REPAIR" in line or "DRT_THREADS" in line],
              "main_detailed_route_iteration_reports": reports,
              "post_antenna_report_folders": sorted(p.name for p in step.glob("drc_iter_ant*")),
              "source_sequence": [
                  "Main detailed_route returns, then keep_iter_reports main moves its iteration reports.",
                  "If configured rounds>0, set_thread_count1 then check_antennas occurs before the next console puts.",
                  "A violating round may insert diodes and perform another detailed_route; a final single-thread antenna check follows the loop.",
                  "write_views is after the antenna loop, so no new state_out is expected before that code completes."],
              "conclusion": "Main route produced a zero-byte iteration45 DRC report and the keep_iter_reports main folder. The first silent post-main operation is plausibly single-thread check_antennas. This is an inference from source and files, not a sampled stack or proof of the live function, progress, deadlock or machine fault.",
              "tag_interpretation": "antoff does not disable this post-detailed-routing loop: the actual configuration enables five rounds. Post-GRT repair is disabled separately.",
              "input_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in files},
              "audit_source_sha256": sha(Path(__file__)),
              "process_operations": "NONE: no attach, debugger, signal, install, kernel setting, job launch or source mutation"}
    target = ROOT / "results/vc4_postdrt_antenna_source_audit_20261010.json"
    target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "out": str(target),
                      "configured_rounds": record["configured_postDRT_antenna_repair_rounds"]}))


if __name__ == "__main__":
    main()
