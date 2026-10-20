"""Validate an existing single diagnostic; never open another perf event."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "results/vc4_cpu_sampling_20261010"
EXE = "/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/.openroad-wrapped"
COMMIT = "edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6"
FUNCTION = "grt::FastRouteCore::mazeRouteMSMD(int, int, float, int, int, bool, int, float, int, int, int, float&)"


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def executable_maps(text):
    result=[]
    for line in text.splitlines():
        fields=line.split(maxsplit=5)
        if len(fields)==6 and fields[5]==EXE and "x" in fields[1]:
            low,high=(int(x,16) for x in fields[0].split("-"))
            result.append((low,high,int(fields[2],16),fields[1],fields[4]))
    return result


def validate(record, symbol):
    native=record["native_sample"]
    event=record["sampling_receipt"]
    if native["rc"] or not 0<native["wall_seconds"]<=5:
        raise ValueError("Native return/whole-invocation wall bound")
    if event["status"]!="COMPLETED_BOUNDED_USER_PC_SAMPLING" or event["actual_executable"]!=EXE:
        raise ValueError("Native completion/executable")
    if event["lost"] or not event["samples"] or event["target_tid"]!=669:
        raise ValueError("Missing samples/loss/target")
    if not event["exclude_kernel"] or not event["exclude_hv"] or event["inherit"]:
        raise ValueError("User-only single-thread scope")
    start=event["start_proc_stat"]
    end=event["end_proc_stat"]
    expected_comm=f"669 ({Path(EXE).name[:15]}"
    if start.split(")",1)[0]!=expected_comm or end.split(")",1)[0]!=expected_comm:
        raise ValueError("Exact process identity")
    if start.rsplit(")",1)[1].split()[19]!=end.rsplit(")",1)[1].split()[19]:
        raise ValueError("Starttime/PID reuse")
    before=executable_maps(record["maps_before"]["stdout"])
    after=executable_maps(record["maps_after"]["stdout"])
    if not before or before!=after:
        raise ValueError("Executable mappings changed")
    biases={low-offset for low,high,offset,perms,inode in before}
    if len(biases)!=1:
        raise ValueError("Ambiguous executable load bias")
    bias=biases.pop()
    previous=None
    for sample in event["samples"]:
        if sample["pid"]!=669 or sample["tid"]!=669 or sample["misc"]&7!=2:
            raise ValueError("Wrong user-mode sampled PID/TID")
        pc=int(sample["ip"],16)
        if not any(low<=pc<high for low,high,offset,perms,inode in before):
            raise ValueError("IP outside pinned executable xmap")
        linked=pc-bias
        if not symbol["address"]<=linked<symbol["address"]+symbol["size"]:
            raise ValueError("IP outside exact pinned function SIZE range")
        if previous is not None and sample["time_ns"]<previous:
            raise ValueError("Sample timestamps moved backward")
        previous=sample["time_ns"]
    return {"load_bias":hex(bias),"sample_count":len(event["samples"]),
            "function_linked_range":[hex(symbol["address"]),hex(symbol["address"]+symbol["size"])],
            "sample_timestamp_span_seconds":(event["samples"][-1]["time_ns"]-event["samples"][0]["time_ns"])/1e9}


def main():
    out=FOLDER/"diagnostic_audit.json"
    if out.exists() or out.with_suffix(".md").exists():
        raise SystemExit("Refusing to overwrite an existing diagnostic audit")
    receipt=FOLDER/"receipt.json"
    receipt_hash=sha(receipt)
    record=json.loads(receipt.read_text())
    command=["wsl.exe","-d","Ubuntu","-e","nm","-S","-n","--defined-only","-C",EXE]
    symbols=subprocess.run(command,capture_output=True,text=True,timeout=10)
    if symbols.returncode:
        raise RuntimeError("Read-only symtab reread failed")
    matches=[]
    for line in symbols.stdout.splitlines():
        m=re.match(r"^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([tT])\s+(.+)$",line)
        if m and m[4]==FUNCTION:
            matches.append({"address":int(m[1],16),"size":int(m[2],16),"type":m[3],"name":m[4]})
    if len(matches)!=1:
        raise RuntimeError("Exact pinned function symbol missing/ambiguous")
    checked=validate(record,matches[0])
    binary=Path(r"\\wsl.localhost\Ubuntu")/EXE.lstrip("/")
    if sha(binary)!=record["actual_executable_sha256"]:
        raise RuntimeError("Pinned binary changed")
    sources=(ROOT/"scripts/metrics/read_only_perf_sampler.c",ROOT/"scripts/metrics/sample_vc4_antenna_cpu.py")
    expected=(record["sampler_source_sha256"],record["runner_source_sha256"])
    archived=[]
    inputs=FOLDER/"executed_inputs"
    inputs.mkdir(exist_ok=False)
    for source,value in zip(sources,expected):
        if sha(source)!=value:
            raise RuntimeError("Executed source changed")
        target=inputs/source.name
        target.write_bytes(source.read_bytes())
        if sha(target)!=value:
            raise RuntimeError("Executed source archive differs")
        archived.append({"path":str(target),"sha256":value})
    controls=[]
    variants=[]
    for label in ("lost_samples","empty_samples","wrong_tid","outside_function","over_wall_budget","changed_xmap"):
        changed=copy.deepcopy(record)
        if label=="lost_samples": changed["sampling_receipt"]["lost"]=1
        elif label=="empty_samples": changed["sampling_receipt"]["samples"]=[]
        elif label=="wrong_tid": changed["sampling_receipt"]["samples"][0]["tid"]=670
        elif label=="outside_function": changed["sampling_receipt"]["samples"][0]["ip"]=hex(int(checked["load_bias"],16)+matches[0]["address"]+matches[0]["size"])
        elif label=="over_wall_budget": changed["native_sample"]["wall_seconds"]=5.001
        elif label=="changed_xmap": changed["maps_after"]["stdout"]=""
        variants.append((label,changed))
    for label,changed in variants:
        try: validate(changed,matches[0])
        except ValueError as exc: controls.append({"control":label,"status":"REJECTED","reason":str(exc)})
        else: raise RuntimeError("Metadata rejection control failed: "+label)
    upstream=[]
    for path in ("src/grt/src/GlobalRouter.cpp","src/grt/src/fastroute/src/FastRoute.cpp","src/grt/src/fastroute/src/maze.cpp"):
        url=f"https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/{COMMIT}/{path}"
        with urllib.request.urlopen(url,timeout=10) as response:
            payload=response.read(512*1024+1)
        if len(payload)>512*1024: raise RuntimeError("Pinned source exceeds audit retrieval bound")
        text=payload.decode()
        upstream.append({"url":url,"bytes":len(payload),"sha256":hashlib.sha256(payload).hexdigest(),
                         "relevant_lines":[{"line":n,"text":line} for n,line in enumerate(text.splitlines(),1)
                                           if re.search(r"(?:GlobalRouter::repairAntennas|IncrementalGRoute::updateRoutes|GlobalRouter::updateDirtyRoutes|FastRouteCore::run\(|FastRouteCore::mazeRouteMSMD\(|setVerbose\(false\)|setCongestionReportIterStep\(0\)|mazeRound =|add_max =|incr_groute.updateRoutes\(|fastroute_->run\(|while \(fastroute_->has2Doverflow|findRouting\(dirty_nets)",line)]})
    if sha(receipt)!=receipt_hash: raise RuntimeError("Original execution receipt changed")
    result={"status":"VERIFIED_SINGLE_STATISTICAL_PC_DIAGNOSTIC",
            "capture_utc":datetime.now(timezone.utc).isoformat(),
            "diagnostic_scope":"One already-completed user-only software CPU-clock sample; this audit rereads files/symbols only and opens no perf event.",
            "original_execution_receipt":{"path":str(receipt),"sha256":receipt_hash},
            "verified":checked,"lost_samples":0,"native_whole_invocation_wall_seconds":record["native_sample"]["wall_seconds"],
            "exact_function_symbol":matches[0],"actual_binary_sha256":record["actual_executable_sha256"],
            "symtab_reread_native_rc":symbols.returncode,"symtab_reread_stdout_sha256":hashlib.sha256(symbols.stdout.encode()).hexdigest(),
            "executed_source_archives":archived,"metadata_negative_controls":controls,
            "pinned_primary_sources":upstream,
            "static_possible_callchain":"drt.tcl repair_antennas -> GlobalRouter::repairAntennas -> IncrementalGRoute::updateRoutes -> GlobalRouter::updateDirtyRoutes -> findRouting -> FastRouteCore::run -> mazeRouteMSMD",
            "observed_vs_inferred":"All 98 sampled IPs lie inside the exact pinned mazeRouteMSMD SIZE range. The source shows a possible post-antenna incremental-routing caller with verbose/congestion-report settings disabled. No actual caller stack, active net, routing iteration, or congestion state was sampled.",
            "supersedes_previous_stage_inference":"The earlier first-silent-check inference cannot identify the current live stage from a buffered log. This actual sampled window is in global maze routing, not the antenna-checker function.",
            "timing_review_limit":"The executed draft starts its internal timer after enable and stops before disable. The separately recorded WHOLE native invocation, including startup and event lifetime, is 4.968s, which bounds this actual probe below 5s. The source should measure around enable/disable in any future tool revision. No second probe or code change was made.",
            "identity_review_limit":"Executed C checked starttime after capture but did not reread endexe/cmdline. Independently reread executable xmaps_before/after are byte-equal, and the actual pinned binary hash is unchanged. Any future tool revision should check endexe/cmdline too. This audit does not claim stronger exec-event monitoring than recorded.",
            "completion_review_limit":"Executed runner did not require positive samples and zero loss generally; this audit explicitly verifies 98 samples and zero loss for the actual evidence and rejects both corrupted cases. No rerun.",
            "project_wording_limit":"The original receipt field owner_approved_scope is retained as historical bytes. This supplement uses plain diagnostic_scope and makes no persona-dependent technical assumption.",
            "conclusion_limit":"Single statistical function diagnosis only; no net, termination/progress, hang, machine fault, timing, antenna or sign-off result is proved.",
            "audit_source_sha256":sha(Path(__file__))}
    out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    primary=f"https://github.com/The-OpenROAD-Project/OpenROAD/blob/{COMMIT}/src/grt/src/GlobalRouter.cpp#L4330"
    lines=["# VC4 actual CPU-location diagnostic", "",
           "One native user-only CPU-clock probe collected 98 samples with zero lost records. The whole native invocation took 4.968s, including launch and event cleanup, within the 5s limit. All samples fall within the SIZE range of the exact pinned executable's `grt::FastRouteCore::mazeRouteMSMD` symbol. Executable xmaps and PID starttime agree before/after; the source and binary hashes remain unchanged.", "",
           f"The pinned [`GlobalRouter.cpp`]({primary}) has a post-antenna path through `repairAntennas` and incremental dirty-net routing to FastRoute. That incremental path disables verbose output and congestion iteration reports. It can expand the congestion-net set and retry routing. This is a possible static caller; the probe did not capture a call stack, net or iteration.", "",
           "The earlier stage-boundary report inferred that the first silent post-route operation could be `check_antennas`. Buffered log text cannot locate the current phase; the actual sampled window was in global maze routing. Prior receipts remain unchanged as dated inferences.", "",
           "The supplemental audit rereads the symbol range/maps and rejects lost, empty, wrong-TID, out-of-range, over-budget and changed-map fixtures. These are checker controls, not extra process samples or scientific runs.", "",
           "The original draft's internal timer excludes enable/disable overhead; the separately recorded whole native wall interval bounds this actual probe below 5s. Its original end-identity and generic completion guards were weaker than proposed later review changes; the existing actual evidence satisfies the supplemental checks. No second probe or sampler source revision was performed.", "",
           "No process was paused, signalled, attached with ptrace, restarted, killed or otherwise changed. No permission/kernel setting, source input, routing recipe or active tool was altered. The finding proves a statistical user-space function location only, without attributing a net, progress, hang, fault or sign-off."]
    out.with_suffix(".md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"out":str(out),"samples":checked["sample_count"],
                      "native_whole_wall":result["native_whole_invocation_wall_seconds"],"function":FUNCTION}))


if __name__=="__main__": main()
