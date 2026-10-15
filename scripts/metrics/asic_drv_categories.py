"""Report final routed DM/SA2 electrical violations from both PD executions.

DRV is reported, not a hard sign-off gate. Pin rows, unique pins and unique
nets have distinct counts. SRAM pins take category precedence; other pins on
a net with >=1 actual diode load form the diode-net category. Missing instance,
port or net evidence remains UNKNOWN. This script runs no implementation tool.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import ctypes
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
LIMIT = 256 * 1024 * 1024
JOB = None
CORNERS = tuple(f"{rc}_{pvt}" for rc in ("nom", "min", "max")
                for pvt in ("tt_025C_1v80", "ss_100C_1v60", "ff_n40C_1v95"))
SA2 = "sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin"
RUNS = {"DM": ("soc_dm_4kb", "r14F_A", "r14F_B"),
        "SA2": ("soc_sa2_4kb", SA2 + "_r1", SA2 + "_r2")}
TYPES = ("slew", "cap", "fanout")
CATEGORIES = ("SRAM_PINS", "DIODE_LADEN_NETS", "STANDARD_CELL_PINS", "UNKNOWN")
SRAMS = {"sky130_sram_1kbyte_1rw1r_32x256_8", "sky130_sram_2kbyte_1rw1r_32x512_8"}
HEADERS = {"max slew": "slew", "max capacitance": "cap", "max fanout": "fanout"}
NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
ROW = re.compile(r"^(\S+)\s+(" + NUM + r")\s+(" + NUM + r")\s+(" + NUM + r")\s+\(VIOLATED\)\s*$")
BLANK_FANOUT_SLACK = re.compile(r"^(\S+)\s+(\d+)\s+(\d+)\s+\(VIOLATED\)\s*$")
PIN_FIELDS = ("design", "corner", "constraint", "pin", "limit", "actual", "slack", "unit",
    "slack_status", "instance", "cell_master", "net", "diode_load_count", "pin_origin", "category")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for b in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def memory_limit():
    global JOB
    if os.name != "nt":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (LIMIT, LIMIT))
        return "RLIMIT_AS=256MiB"
    from ctypes import wintypes as w
    class Basic(ctypes.Structure):
        _fields_ = [("ProcessTime", ctypes.c_int64), ("JobTime", ctypes.c_int64), ("Flags", w.DWORD),
            ("MinWS", ctypes.c_size_t), ("MaxWS", ctypes.c_size_t), ("Active", w.DWORD),
            ("Affinity", ctypes.c_size_t), ("Priority", w.DWORD), ("Scheduling", w.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes", "OtherBytes")]
    class Extended(ctypes.Structure):
        _fields_ = [("Basic", Basic), ("IO", IO), ("ProcessLimit", ctypes.c_size_t),
            ("JobLimit", ctypes.c_size_t), ("PeakProcess", ctypes.c_size_t), ("PeakJob", ctypes.c_size_t)]
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
    k.CreateJobObjectW.restype = w.HANDLE
    k.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    k.SetInformationJobObject.restype = w.BOOL
    k.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    k.AssignProcessToJobObject.restype = w.BOOL
    k.GetCurrentProcess.restype = w.HANDLE
    JOB = k.CreateJobObjectW(None, None)
    info = Extended()
    info.Basic.Flags = 0x100
    info.ProcessLimit = LIMIT
    need(JOB and k.SetInformationJobObject(JOB, 9, ctypes.byref(info), ctypes.sizeof(info))
         and k.AssignProcessToJobObject(JOB, k.GetCurrentProcess()), "UNKNOWN_MEMORY_CAP_NOT_ENFORCED")
    return "Windows process commit JobObject limit=256MiB"


def peak_memory():
    if os.name != "nt":
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    from ctypes import wintypes as w
    class Info(ctypes.Structure):
        _fields_ = [("cb", w.DWORD), ("faults", w.DWORD)] + [(n, ctypes.c_size_t) for n in
            ("peakws", "ws", "peakpaged", "paged", "peaknonpaged", "nonpaged", "commit", "peakcommit")]
    c = Info()
    c.cb = ctypes.sizeof(c)
    k = ctypes.WinDLL("kernel32")
    k.GetCurrentProcess.restype = w.HANDLE
    p = ctypes.WinDLL("psapi")
    p.GetProcessMemoryInfo.argtypes = [w.HANDLE, ctypes.c_void_p, w.DWORD]
    need(p.GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(c), c.cb), "Cannot read process peak memory")
    return max(c.peakws, c.peakcommit)


def from_state_path(value, run):
    need(isinstance(value, str), "Missing physical netlist in final STA state")
    if value.startswith("/mnt/e/"):
        path = Path("E:/" + value[7:])
    else:
        path = Path(value)
    need(path.resolve().is_relative_to(run.resolve()) and path.is_file(), "STA evidence path outside/missing from selected run")
    return path


def final_sta(run):
    candidates = sorted((p for p in run.iterdir() if re.fullmatch(r"\d+-openroad-stapostpnr", p.name)),
                        key=lambda p: int(p.name.split("-", 1)[0]))
    need(candidates, "Missing final STAPostPNR: " + str(run))
    step = candidates[-1]
    need({p.name for p in step.iterdir() if p.is_dir() and re.match(r"^(nom|min|max)_", p.name)} == set(CORNERS),
         "Missing/unexpected named final STA corner")
    need(all((step / c / "checks.rpt").is_file() for c in CORNERS), "Missing checks.rpt in named corner")
    return step


def parse_checks(path, corner):
    rows, counts, names = [], {}, set()
    active, kind, marker_count = False, None, 0
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            s = line.strip()
            match = re.search(r"=+\s+(\S+) Corner\s+=+", s)
            if match:
                names.add(match[1])
            if s == "report_check_types -max_slew -max_cap -max_fanout -violators":
                active, marker_count = True, marker_count + 1
                continue
            if s.startswith("report_parasitic_annotation"):
                active, kind = False, None
            match = re.fullmatch(r"max (slew|cap|fanout) violation count (\d+)", s)
            if match:
                need(match[1] not in counts, "Duplicate DRV footer count")
                counts[match[1]] = int(match[2])
            if not active:
                continue
            if s in HEADERS:
                kind = HEADERS[s]
            if "(VIOLATED)" in s:
                match = ROW.fullmatch(s)
                blank = BLANK_FANOUT_SLACK.fullmatch(s) if kind == "fanout" else None
                need(kind is not None and (match is not None or blank is not None), "Unparsed DRV violation row: " + str(number))
                if match is not None:
                    pin, limit, actual, slack = match.groups()
                    slack_status = "REPORTED_NUMERIC"
                    need(Decimal(limit) >= 0 and Decimal(actual) >= Decimal(limit) and slack.startswith("-"), "Invalid DRV limit/actual/slack")
                else:
                    pin, limit, actual = blank.groups()
                    need(int(actual) > int(limit), "Blank-slack fanout row must still violate actual > limit")
                    slack, slack_status = "UNKNOWN_REPORTED_BLANK", "UNKNOWN_REPORTED_BLANK"
                rows.append(dict(constraint=kind, pin=pin, limit=limit, actual=actual, slack=slack,
                                 slack_status=slack_status, report_line=number))
    need(names == {corner} and marker_count == 1 and set(counts) == set(TYPES), "Missing/wrong corner/report/complete DRV footer")
    need(Counter(r["constraint"] for r in rows) == Counter({k: v for k, v in counts.items() if v}), "All-pin row counts differ from raw footer")
    return rows, counts


def net_name(expression):
    expr = expression.strip()
    if expr.startswith("\\"):
        expr = expr[1:].strip()
    if not expr or re.search(r"[\s{},():']", expr):
        return None
    return expr


def connections(body):
    result = {}
    for port, expression in re.findall(r"\.([A-Za-z_$][\w$]*)\s*\(([^()]*)\)", body, re.S):
        need(port not in result, "Duplicate netlist instance port")
        expr = expression.strip()
        if expr.startswith("{") and expr.endswith("}") and "{" not in expr[1:-1] and "}" not in expr[1:-1]:
            vector = [net_name(x) for x in expr[1:-1].split(",")]
            for bit, net in enumerate(reversed(vector)):
                result[f"{port}[{bit}]"] = net
        else:
            result[port] = net_name(expr)
    return result


def netlist_bindings(path, wanted):
    wanted_instances = {pin.rsplit("/", 1)[0] for pin in wanted if "/" in pin}
    bindings, diode_nets, masters, aliases = {}, Counter(), Counter(), {}
    def find(n):
        if n is None:
            return None
        while n in aliases and aliases[n] != n:
            n = aliases[n]
        return n
    def consume(master, instance, body):
        masters[master] += 1
        diode = master.startswith("sky130_fd_sc_hd__diode_")
        if instance not in wanted_instances and not diode:
            return
        ports = connections(body)
        if diode:
            need(ports.get("DIODE") is not None, "UNKNOWN_DIODE_LOAD_BINDING")
            diode_nets[ports["DIODE"]] += 1
        for port, net in ports.items():
            key = instance + "/" + port
            if key in wanted:
                need(key not in bindings, "Duplicate target instance/pin binding")
                bindings[key] = (instance, master, net)
    current, body = None, []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if current:
                body.append(line)
                need(sum(map(len, body)) <= 128 * 1024, "UNKNOWN_INSTANCE_BODY_BOUND")
                if ");" in line:
                    consume(*current, "".join(body))
                    current, body = None, []
                continue
            match = re.match(r"\s*(sky130_[A-Za-z0-9_]+)\s+(\\\S+|\S+)\s*\(", line)
            if match:
                current = match[1], match[2].lstrip("\\")
                body = [line]
                if ");" in line:
                    consume(*current, line)
                    current, body = None, []
                continue
            if line.lstrip().startswith("assign "):
                match = re.fullmatch(r"\s*assign\s+(.+?)\s*=\s*(.+?)\s*;\s*", line)
                need(match is not None, "UNKNOWN_NET_ALIAS_STATEMENT")
                a, b = net_name(match[1]), net_name(match[2])
                need(a is not None and b is not None, "UNKNOWN_NONSCALAR_NET_ALIAS")
                a, b = find(a), find(b)
                if a != b:
                    aliases[max(a, b)] = min(a, b)
    need(current is None and sum(masters[s] for s in SRAMS) == 16, "Truncated netlist/wrong SRAM macro count")
    canonical_diodes = Counter()
    for net, count in diode_nets.items():
        canonical_diodes[find(net)] += count
    return {pin: (instance, master, find(net)) for pin, (instance, master, net) in bindings.items()}, canonical_diodes, masters


def classify(pin, bindings, diodes):
    instance, master, net = bindings.get(pin, (pin.rsplit("/", 1)[0] if "/" in pin else "UNKNOWN", "UNKNOWN", None))
    loads = diodes[net] if net is not None else None
    if master in SRAMS:
        origin, category = "SRAM", "SRAM_PINS"
    elif master.startswith("sky130_fd_sc_hd__diode_"):
        origin, category = "DIODE", "DIODE_LADEN_NETS" if loads and pin.endswith("/DIODE") else "UNKNOWN"
    elif master.startswith("sky130_fd_sc_hd__"):
        origin = "STANDARD_CELL"
        category = "UNKNOWN" if loads is None else "DIODE_LADEN_NETS" if loads else "STANDARD_CELL_PINS"
    else:
        origin, category = "UNKNOWN", "UNKNOWN"
    return dict(instance=instance, cell_master=master, net=net or "UNKNOWN", diode_load_count="UNKNOWN" if loads is None else loads,
                pin_origin=origin, category=category)


def write_csv(path, fields, rows):
    with path.open("x", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def controls(output):
    directory = output / "controls_NOT_A_MEASUREMENT"
    directory.mkdir()
    checks = []
    def control(name, action, expected=True):
        try:
            value = action()
            verdict = bool(value)
        except (ValueError, OSError):
            verdict = False
        need(verdict == expected, "Negative/positive control failed: " + name)
        checks.append(dict(label=name, pass_=True))
    binds = {"s/a": ("s", next(iter(sorted(SRAMS))), "n"),
        "ANTENNA_spoof/A": ("ANTENNA_spoof", "sky130_fd_sc_hd__buf_2", "clean"),
        "a/X": ("a", "sky130_fd_sc_hd__buf_2", "n"),
        "d/DIODE": ("d", "sky130_fd_sc_hd__diode_2", "n"),
        "a/A": ("a", "sky130_fd_sc_hd__buf_2", None),
        "m/A": ("m", "unknown_macro", "n")}
    diodes = Counter(n=2)
    for pin, category in (("s/a", "SRAM_PINS"), ("ANTENNA_spoof/A", "STANDARD_CELL_PINS"),
        ("a/X", "DIODE_LADEN_NETS"), ("d/DIODE", "DIODE_LADEN_NETS"), ("missing/A", "UNKNOWN"), ("a/A", "UNKNOWN"), ("m/A", "UNKNOWN")):
        control("classification_" + pin.replace("/", "_") + "_" + category, lambda pin=pin, category=category: classify(pin, binds, diodes)["category"] == category)
    sample = directory / "checks.rpt"
    good = ("======= nom_tt_025C_1v80 Corner =======\n report_check_types -max_slew -max_cap -max_fanout -violators\n"
        "max slew\nPin Limit Slew Slack\na/X 0.75 0.85 -0.10 (VIOLATED)\n"
        "report_parasitic_annotation -report_unannotated\nmax slew violation count 1\nmax cap violation count 0\nmax fanout violation count 0\n")
    sample.write_text(good, encoding="ascii")
    control("complete_named_corner_pin_report", lambda: parse_checks(sample, "nom_tt_025C_1v80"), True)
    control("wrong_named_corner_rejected", lambda: parse_checks(sample, "max_tt_025C_1v80"), False)
    control("missing_report_rejected", lambda: parse_checks(directory / "absent.rpt", "nom_tt_025C_1v80"), False)
    for label, bad in (("missing_footer", good.replace("max cap violation count 0\n", "")),
                       ("missing_pin_row", good.replace("a/X 0.75 0.85 -0.10 (VIOLATED)\n", "")),
                       ("corrupt_row", good.replace("0.85", "INVALID")),
                       ("wrong_raw_count", good.replace("max slew violation count 1", "max slew violation count 2"))):
        path = directory / (label + ".rpt")
        path.write_text(bad, encoding="ascii")
        control(label + "_rejected", lambda p=path: parse_checks(p, "nom_tt_025C_1v80"), False)
    blank_path = directory / "blank_fanout_slack.rpt"
    blank_path.write_text(good.replace("max slew\n", "max fanout\n").replace("a/X 0.75 0.85 -0.10", "a/X 8 9").replace("max slew violation count 1", "max slew violation count 0").replace("max fanout violation count 0", "max fanout violation count 1"), encoding="ascii")
    control("blank_fanout_slack_preserved_as_UNKNOWN", lambda: parse_checks(blank_path, "nom_tt_025C_1v80")[0][0]["slack"] == "UNKNOWN_REPORTED_BLANK")
    record = dict(status="PASS", not_a_measurement=True, checks=checks)
    (directory / "verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")
    return record


def analyze(design, run, output, pass_no, inputs):
    step = final_sta(run)
    state_path = step / "state_out.json"
    state = json.loads(state_path.read_text())
    netlist = from_state_path(state["pnl"], run)
    paths = [state_path, netlist, *[step / c / "checks.rpt" for c in CORNERS]]
    for path in paths:
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    wanted = set()
    for corner in CORNERS:
        rows, counts = parse_checks(step / corner / "checks.rpt", corner)
        for kind in TYPES:
            metric = f"design__max_{kind}_violation__count__corner:{corner}"
            need(metric in state["metrics"] and counts[kind] == state["metrics"][metric], "Raw DRV count differs from named-corner final STA metric: " + metric)
        wanted.update(r["pin"] for r in rows)
    bindings, diodes, masters = netlist_bindings(netlist, wanted)
    summaries, identities = [], {}
    csv_path = output / f"{design.lower()}_p{pass_no}_pin_rows.csv"
    with csv_path.open("x", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=(*PIN_FIELDS, "report_line"))
        writer.writeheader()
        for corner in CORNERS:
            rows, counts = parse_checks(step / corner / "checks.rpt", corner)
            classified = []
            for row in rows:
                item = dict(design=design, corner=corner, **row, unit={"slew": "ns", "cap": "pF", "fanout": "loads"}[row["constraint"]], **classify(row["pin"], bindings, diodes))
                writer.writerow(item)
                classified.append(item)
            for kind in TYPES:
                selected = [r for r in classified if r["constraint"] == kind]
                canonical = sorted(tuple(str(r[k]) for k in PIN_FIELDS) for r in selected)
                identities[(corner, kind)] = hashlib.sha256(json.dumps(canonical, separators=(",", ":")).encode("ascii")).hexdigest()
                for category in CATEGORIES:
                    group = [r for r in selected if r["category"] == category]
                    summaries.append(dict(design=design, corner=corner, constraint=kind, category=category,
                        all_pin_rows=len(selected), unique_pins_all_categories=len({r["pin"] for r in selected}),
                        raw_metric_count=counts[kind], category_pin_rows=len(group), category_unique_pins=len({r["pin"] for r in group}),
                        category_unique_known_nets=len({r["net"] for r in group if r["net"] != "UNKNOWN"}),
                        unknown_net_rows=sum(r["net"] == "UNKNOWN" for r in group),
                        unknown_reported_slack_rows=sum(r["slack_status"] == "UNKNOWN_REPORTED_BLANK" for r in group),
                        direct_diode_pin_rows=sum(r["pin_origin"] == "DIODE" for r in group),
                        standard_cell_pin_rows=sum(r["pin_origin"] == "STANDARD_CELL" for r in group),
                        sram_pin_rows=sum(r["pin_origin"] == "SRAM" for r in group),
                        rows_on_diode_loaded_nets=sum(type(r["diode_load_count"]) is int and r["diode_load_count"] > 0 for r in group),
                        worst_reported_numeric_slack=min((r["slack"] for r in group if r["slack_status"] == "REPORTED_NUMERIC"), key=Decimal, default="NONE")))
    return dict(step=step.relative_to(ROOT).as_posix(), run=run.relative_to(ROOT).as_posix(),
        netlist=netlist.relative_to(ROOT).as_posix(), pin_rows_csv=csv_path.relative_to(ROOT).as_posix(),
        summaries=summaries, identities={corner + "/" + kind: v for (corner, kind), v in identities.items()},
        total_netlist_instances=sum(masters.values()), total_diodes=sum(diodes.values()), diode_loaded_nets=len(diodes),
        sram_macros=sum(masters[m] for m in SRAMS), unbound_violating_pins=sorted(wanted - set(bindings)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("results/asic_drv_categories_20261010"))
    parser.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    output = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    need(output.resolve().is_relative_to((ROOT / "results").resolve()) and not output.exists(), "Use a new output directory in research/results")
    memory = memory_limit()
    output.mkdir(parents=True, exist_ok=False)
    tested = controls(output)
    if args.controls_only:
        print("[PASS] focused DRV category/report controls; no measurement")
        return
    inputs = {Path(__file__).relative_to(ROOT).as_posix(): sha(Path(__file__))}
    all_summaries, executions = [], {}
    for design, (directory, first, second) in RUNS.items():
        pair = [analyze(design, ROOT / "asic" / directory / "runs" / tag, output, n, inputs)
                for n, tag in enumerate((first, second), 1)]
        fields = ("summaries", "identities", "total_netlist_instances", "total_diodes", "diode_loaded_nets", "sram_macros", "unbound_violating_pins")
        need(all(pair[0][k] == pair[1][k] for k in fields), "Independent final PD DRV identities/categories differ: " + design)
        executions[design] = pair
        all_summaries.extend(pair[0]["summaries"])
        print("[VERIFIED]", design, "both final PD executions,9 named corners,all DRV pin identities/values/categories", flush=True)
    for relative, digest in inputs.items():
        need(sha(ROOT / relative) == digest, "Input changed during DRV audit: " + relative)
    summary_csv = output / "paired_category_counts.csv"
    write_csv(summary_csv, tuple(all_summaries[0]), all_summaries)
    report = ["# Final routed DM / SA2 DRV categories", "", "DRV is reported, not a hard sign-off gate. This is evidence extraction; no new PD or STA execution.", "",
        "Both existing independent PD runs match every violation pin identity, limit, actual value, slack, cell master, connected net, diode load count and exclusive category at all9 named corners.", "",
        "Category priority: SRAM pins; otherwise pins on nets with >=1 connected sky130 HD diode DIODE load; otherwise known standard-cell pins; UNKNOWN for missing evidence. SRAM pins on diode-loaded nets remain SRAM and have a separate overlap count.", "",
        "Counts are violating pin rows; unique-pin and unique-known-net counts are separate columns. Diode-net pin counts are not counts of nets or diode instances. UNKNOWN net counts cannot be treated as unique physical nets.", "",
        "| Design | Corner | Constraint | Total pin rows | SRAM pins | Pins on diode-loaded nets | Standard-cell pins | UNKNOWN |", "|---|---|---|---:|---:|---:|---:|---:|"]
    for design in RUNS:
        for corner in CORNERS:
            for kind in TYPES:
                group = {r["category"]: r for r in all_summaries if (r["design"], r["corner"], r["constraint"]) == (design, corner, kind)}
                report.append("| " + " | ".join([design, corner, kind, str(group["SRAM_PINS"]["all_pin_rows"]), *[str(group[c]["category_pin_rows"]) for c in CATEGORIES]]) + " |")
    report.extend(["", "Source reports: final STAPostPNR checks.rpt only. Counts are reconciled against the report footer and the same step's corner-specific state metrics. STAMidPNR values are excluded.",
        "", "Max-slew values use ns, max-capacitance pF and fanout load units from the final STA report. A diode connection documents a load, not a causal proof that the diode created the violation.",
        "", "Some fanout rows leave the raw Slack column blank. Their limit and actual fanout are preserved; slack is UNKNOWN_REPORTED_BLANK, without substituting actual-minus-limit for a reported measurement.",
        "", "This report does not establish the final three-design PPA table or DM_VC4 sign-off. Electrical violations remain outside the hard sign-off gate.", ""])
    report_path = output / "report.md"
    report_path.write_text("\n".join(report), encoding="ascii")
    peak = peak_memory()
    need(peak <= LIMIT, "UNKNOWN_MEMORY_BOUND_EXCEEDED")
    record = dict(status="VERIFIED_PAIRED_FINAL_STAPOSTPNR_DRV_CATEGORIES_DM_SA2", drv_is_hard_signoff_gate=False,
        new_PD_or_STA_measurements=0, final_T6_completed=False, memory_enforcement=memory,
        process_memory_limit_bytes=LIMIT, peak_process_bytes=peak, named_corners=list(CORNERS),
        category_priority=list(CATEGORIES), diode_laden_definition="at_least_one_connected_HD_diode_DIODE_pin_load",
        violation_unit="pin_rows_not_nets", controls=tested, inputs=inputs, executions=executions,
        limitations=["Missing or unclassifiable pin/net evidence is UNKNOWN, never inferred from instance names.",
            "Known SRAM pins remain SRAM even when attached to a diode-loaded net; the separate overlap count preserves that fact.",
            "Duplicate pin rows, if any, are preserved as separate reported groups; unique pins/nets are counted separately.",
            "Category identifies actual cell and net connectivity, not the physical cause of a DRV."],
        artifacts={p.relative_to(ROOT).as_posix(): sha(p) for p in output.rglob("*") if p.is_file()})
    with (output / "receipt.json").open("x", encoding="ascii") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    print("[VERIFIED] 2designs x2 independent final runs x9corners; reporting only", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (MemoryError, RecursionError) as exc:
        print("UNKNOWN_RESOURCE_BOUND:" + type(exc).__name__, file=sys.stderr)
        raise SystemExit(2)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print("REJECTED_OR_UNKNOWN:" + str(exc), file=sys.stderr)
        raise SystemExit(1)
