"""Read-only source/file/process metadata audit; never attach to a live process."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
VC4 = "vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1"
SA2 = "sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf"
PINNED = "edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6"
STORE = Path(r"\\wsl.localhost\Ubuntu\nix\store")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def evidence(path):
    st = path.stat()
    return {"path": str(path), "bytes": st.st_size,
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
            "sha256": sha(path)}


def matches(text, pattern):
    return [{"line": n, "text": line} for n, line in enumerate(text.splitlines(), 1)
            if re.search(pattern, line)]


def main():
    target = ROOT / "results/vc4_postdrt_antenna_comparison_20261010.json"
    md = target.with_suffix(".md")
    if target.exists() or md.exists():
        raise SystemExit("Refusing to overwrite an existing dated evidence receipt")
    old = ROOT / "results/vc4_postdrt_antenna_source_audit_20261010.json"
    old_sha = sha(old)
    drt = ROOT / "asic/openlane-local/openlane/scripts/openroad/drt.tcl"
    vcstep = ROOT / "asic/soc_vc4_4kb/runs" / VC4 / "43-openroad-detailedrouting"
    vc_log = vcstep / "openroad-detailedrouting.log"
    comparators = []
    for p in (1, 2):
        signed = ROOT / "asic/soc_sa2_4kb/runs" / f"{SA2}_ecomaxmin_r{p}" / "46-openroad-detailedrouting"
        base = ROOT / "asic/soc_sa2_4kb/runs" / f"{SA2}_r{p}" / "46-openroad-detailedrouting"
        log = signed / "openroad-detailedrouting.log"
        text = log.read_text(encoding="utf-8")
        artifact_paths = [signed / name for name in
                          ("_env.tcl", "runtime.txt", "openroad-detailedrouting.process_stats.json", "soc_asic_top.drc")]
        comparators.append({
            "pass": p, "signed_branch": str(signed), "original_full_flow": str(base),
            "copied_branch_is_not_an_extra_execution": True,
            "branch_and_original_log_sha256_equal": sha(log) == sha(base / log.name),
            "runtime": (signed / "runtime.txt").read_text().strip(),
            "main_reports": evidence(signed / "drc_iter_main" / "soc_asic_top.drc-45.rpt")
            if (signed / "drc_iter_main" / "soc_asic_top.drc-45.rpt").exists() else None,
            "antenna_markers": matches(text, r"ANT-000[12]|post-DRT antenna|Inserted \d+ diodes"),
            "last_wirelength_um": int(re.findall(r"^Total wire length = (\d+) um\.", text, re.M)[-1]),
            "phase_folders": [{"path": str(x), "mtime_utc": datetime.fromtimestamp(x.stat().st_mtime, timezone.utc).isoformat()}
                              for x in sorted(signed.glob("drc_iter_*"))],
            "artifacts": [evidence(log)] + [evidence(x) for x in artifact_paths],
            "process_stats": json.loads((signed / "openroad-detailedrouting.process_stats.json").read_text())})
    sources = []
    for name in ("AntennaChecker.cc", "Polygon.cc"):
        url = f"https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/{PINNED}/src/ant/src/{name}"
        with urllib.request.urlopen(url, timeout=10) as response:
            payload = response.read(256 * 1024 + 1)
        if len(payload) > 256 * 1024:
            raise RuntimeError("Source retrieval exceeds the metadata audit bound")
        text = payload.decode("utf-8")
        sources.append({"url": url, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                        "relevant_symbol_lines": matches(text, r"AntennaChecker::(?:checkAntennas|checkNet|buildLayerMaps|saveGates)|void wiresToPolygonSetMap|std::vector<int> findNodesWithIntersection|Found \{\} (?:net|pin) violations|omp_set_num_threads|pragma omp parallel")})
    drv_paths = [STORE / name for name in (
        "70rqdyaqqdh6m6pxc3q1cmgrsrgmighm-openroad.drv",
        "x6xaqsgv63bxjyxn4mlk2ksff9xi23xb-source.drv",
        "h3x57200hc83spgbkcrs9avayqwm5j5d-source.drv")]
    derivations = []
    for path in drv_paths:
        text = path.read_text()
        derivations.append({**evidence(path), "relevant_metadata": re.findall(r'\("(?:out|src|patches|urls|outputHash)","[^"]*"\)', text)})
    patch = STORE / "7gxckv9h975814gv699rgf640za1myn0-6743.patch"
    patch_files = re.findall(r"^diff --git a/(\S+) b/", patch.read_text(), re.M)
    command = "ps -p 669 -o pid,ppid,stat,etime,time,rss,nlwp,wchan:24; cat /proc/669/cmdline; printf '\\nMAIN_THREAD\\n'; cat /proc/669/task/669/stat; printf '\\nTICKS\\n'; getconf CLK_TCK"
    captured = subprocess.run(["wsl.exe", "-d", "Ubuntu", "-e", "bash", "-c", command],
                              capture_output=True, text=True, timeout=10)
    if VC4 not in captured.stdout or captured.returncode:
        raise RuntimeError("Exact live PID/run check failed; no current-process conclusion")
    record = {
        "status": "READ_ONLY_COMPARISON_AND_STAGE_INFERENCE_NOT_STACK_OR_SIGNOFF",
        "capture_utc": datetime.now(timezone.utc).isoformat(), "run": VC4,
        "previous_receipt": {"path": str(old), "sha256": old_sha},
        "current_vc4_files": [evidence(vc_log), evidence(vcstep / "soc_asic_top.drc"), evidence(vcstep / "COMMANDS"),
                              evidence(drt), evidence(vcstep / "_env.tcl"), evidence(vcstep.parent / "resolved.json")],
        "current_main_reports": [evidence(x) for x in sorted((vcstep / "drc_iter_main").glob("*.rpt"))],
        "current_post_antenna_folders": [str(x) for x in sorted(vcstep.glob("drc_iter_ant*"))],
        "current_antenna_console_markers": matches(vc_log.read_text(), r"ANT-000[12]|post-DRT antenna"),
        "current_runtime_or_state_out_saved": {name: (vcstep / name).exists() for name in ("runtime.txt", "state_out.json")},
        "main_thread_observations_transcribed_from_native_tool_results": [
            {"capture_utc": "2026-10-10T12:37:43Z", "tool_chunk": "f97a37", "native_rc": 0,
             "total_process_cpu": "16:19:03", "rss_kib": 10335352, "threads": 34,
             "main_state": "R", "main_user_ticks": 3683640, "main_system_ticks": 408,
             "other_threads_sleeping_futex": 33},
            {"capture_utc": "2026-10-10T12:39:02Z", "tool_chunk": "1399e9", "native_rc": 0,
             "total_process_cpu": "16:20:22", "rss_kib": 10335352, "threads": 34,
             "main_state": "R", "main_user_ticks": 3691558, "main_system_ticks": 408}],
        "main_user_cpu_delta_seconds": 79.18, "observation_wall_delta_seconds": 79,
        "process_vs_main_thread_cpu_counts_are_different_proc_scopes": True,
        "fresh_readonly_native_metadata": {"native_rc": captured.returncode,
                                            "stdout": captured.stdout, "stderr": captured.stderr},
        "source_provenance": {"running_source_commit": PINNED,
            "running_source_store_directory_locally_absent": not (STORE / "d19892l7lyfpd1wsw7lwwlh4svwax29v-source").exists(),
            "retained_local_source_commit_is_different": "87af90f72f3f9be1fdfa1d886f0dd8d8b8f34694",
            "derivations": derivations, "applied_patch": {**evidence(patch), "changed_files": patch_files},
            "exact_pinned_primary_sources": sources},
        "sa2_comparators": comparators,
        "source_analysis": [
            "The ordinary ANT net/pin summary is emitted only after all non-special nets finish; no ordinary per-net progress message is present.",
            "Per-net analysis builds layer polygons, scans layer graph nodes for each via/pin intersection, and loops over nodes, gate pins and neighbor entries when assigning connectivity.",
            "Therefore per-net geometry and fanout can affect cost strongly; total routed length alone cannot explain or predict this runtime.",
            "The Tcl wrapper switches to one thread before the first check and prints its round marker only after that call returns."],
        "conclusion": "Main-route reports reached iteration45 with an empty report and were moved into drc_iter_main. The first subsequent silent operation is consistent with the one-thread antenna check. Current CPU samples show one active main thread, but neither identify its actual function/net nor prove algorithm progress. No observed crash, proven hang, deadlock, machine fault or completed sign-off is claimed.",
        "safe_diagnosis": {
            "available_tools": ["/usr/bin/nm", "/usr/bin/readelf", "/usr/bin/objdump"],
            "unavailable_tools": ["perf", "gdb", "pstack", "eu-stack", "/usr/lib/linux-tools*/perf"],
            "perf_event_paranoid": 2, "kptr_restrict": 1, "effective_capabilities_hex": "0000000000000000",
            "actual_executable": "/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/.openroad-wrapped",
            "actual_executable_is_PIE_with_symtab": True,
            "suggested_only_not_executed": "A separate bounded perf_event_open software CPU-clock sampler of exact TID669, user-only (exclude_kernel/exclude_hv), about20Hz for at most5s, could read instruction addresses without stopping/signalling the target. Use /proc/669/maps load bias and the actual executable symbol table. Availability/permission on this WSL kernel is untested; failure would stop the probe. Statistical PCs still cannot identify a net or prove termination.",
            "read_only_observation": "Continue bounded CPU/RSS/thread-state/file-mtime observations without altering the running recipe."},
        "audit_source_sha256": sha(Path(__file__)),
        "process_control_operations": "NONE: no attach, profiling, signal, install, setting change, job launch, input mutation or deletion"}
    if sha(old) != old_sha:
        raise RuntimeError("Previous evidence unexpectedly changed")
    target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    primary = f"https://github.com/The-OpenROAD-Project/OpenROAD/blob/{PINNED}/src/ant/src/AntennaChecker.cc"
    lines = ["# VC4 post-routing read-only diagnosis", "",
             "Main route produced an empty iteration45 DRC report and its reports were moved into `drc_iter_main`. The post-route loop is enabled for five rounds despite the `antoff` tag. No first-round completion marker, runtime receipt, or state_out exists at capture.", "",
             "The sampled main thread consumed79.18userCPU seconds over79wall seconds; the other33threads were sleeping on futexes. This supports active serial computation. It does not identify the function/net or prove termination. No crash, proven hang, machine fault, or completed sign-off is inferred.", "",
             "Completed SA2 detailed-routing phases took36m45.497s and34m32.522s, including antenna repair. Their rounds found653,55,13,2,0 violating nets and inserted1453,83,14,2 diodes. Their final explicit check returned0. The signed branches copied those original phase artifacts and are not extra executions.", "",
             f"The running Nix derivation pins [`{PINNED}`]({primary}); its GUI patch does not change antenna code. A different retained local checkout is not substituted as the running source. Ordinary summaries occur only after all nets complete. Polygon connectivity uses nested scans over per-net geometry and pins, so total wirelength alone is insufficient to predict cost.", "",
             "No profiler is installed. `nm`/`readelf` confirm the actual wrapped executable is a PIE with antenna function symbols. A user-only, five-second software perf_event_open sampler is a possible next diagnostic, subject to a separate decision and a fail-closed permission check. It has not been executed.", "",
             "The JSON receipt records source URLs/hashes, immutable comparator artifacts, actual configuration, observed process metadata, inference limits and the preserved earlier receipt hash. No running input or job was changed."]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "out": str(target), "sa2_runtimes": [x["runtime"] for x in comparators],
                      "pinned_primary_source_sha256": {x["url"]: x["sha256"] for x in sources}}))


if __name__ == "__main__":
    main()
