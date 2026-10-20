#!/usr/bin/env python3
"""Negative controls for CSV schemas and random-differential completion gates.

Synthetic simulator cases run in an isolated fixture tree under results; they
never replace research measurements or launch Questa. Existing raw results
are checked read-only as positive controls.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/verification_runner_controls_20261009"
spec = importlib.util.spec_from_file_location("verify_case", ROOT / "scripts/verify_random_diff_case.py")
case = importlib.util.module_from_spec(spec)
spec.loader.exec_module(case)


def main() -> int:
    OUT.mkdir(exist_ok=True)
    fixture = Path(tempfile.mkdtemp(prefix="controls_", dir=OUT))
    checks = []

    def check(name, condition, detail=None):
        checks.append({"name": name, "pass": bool(condition), "detail": detail})
        print(f"[{'PASS' if condition else 'FAIL'}] {name}")

    def compare(name, a, b, expected):
        pa, pb = fixture / (name + "_a.csv"), fixture / (name + "_b.csv")
        pa.write_text(a, encoding="ascii")
        pb.write_text(b, encoding="ascii")
        p = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/verify_double.py"),
                            str(pa), str(pb)], capture_output=True, text=True)
        (fixture / (name + ".log")).write_text(p.stdout + p.stderr)
        check(name, (p.returncode == 0) == expected, {"rc": p.returncode})

    good = "point,le,seconds\ndm,10,1\nsa2,20,2\n"
    compare("same_complete_schema", good, good, True)
    compare("ignored_walltime", good, good.replace("dm,10,1", "dm,10,7"), True)
    compare("reordered_columns", good, "seconds,le,point\n1,10,dm\n2,20,sa2\n", True)
    compare("missing_column", good, "point,seconds\ndm,1\nsa2,2\n", False)
    compare("missing_ignored_column", good, "point,le\ndm,10\nsa2,20\n", False)
    compare("duplicate_header", good, "point,le,le\ndm,10,10\nsa2,20,20\n", False)
    compare("blank_header", good, "point,le,\ndm,10,1\nsa2,20,2\n", False)
    compare("truncated_row", good, "point,le,seconds\ndm,10\nsa2,20,2\n", False)
    compare("extra_row_field", good, "point,le,seconds\ndm,10,1,extra\nsa2,20,2\n", False)
    compare("blank_identity", good, "point,le,seconds\n,10,1\nsa2,20,2\n", False)
    compare("duplicate_identity", good, good + "dm,10,1\n", False)
    compare("missing_row", good, "point,le,seconds\ndm,10,1\n", False)
    compare("wrong_measurement", good, good.replace("sa2,20", "sa2,21"), False)
    compare("empty_measurement", good, "point,le,seconds\n", False)
    blank = "point,le,seconds\ndm,,1\nsa2,20,2\n"
    compare("both_missing_metric", blank, blank, False)
    whitespace = "point,le,seconds\ndm,  ,1\nsa2,20,2\n"
    compare("both_whitespace_metric", whitespace, whitespace, False)
    optional = "point,le,path,log\ndm,10,,\nsa2,20,,\n"
    compare("blank_ignored_path_log", optional, optional, True)

    header = ",".join(case.HEADER) + "\n"
    row0 = "0,00000000,00000013,0,0,00000000,0,00000000,00000000,0\n"
    row1 = "1,00000004,00000013,0,0,00000000,0,00000000,00000000,0\n"
    text = ("# [PASS] Random retirement traces generated seed=1 OFF=2 ON=2\n"
            "# [PASS] BP OFF/ON architectural state equivalent seed=1\n# Errors: 0, Warnings: 0\n")
    off, on, log = (fixture / x for x in ("off.csv", "on.csv", "sim.log"))

    def trace_check(name, a=header+row0+row1, b=header+row0+row1, transcript=text, rc=0, expected=False):
        off.write_text(a, encoding="ascii"); on.write_text(b, encoding="ascii"); log.write_text(transcript)
        report = case.verify(1, rc, log, off, on)
        (fixture / (name + ".json")).write_text(json.dumps(report, indent=2) + "\n")
        check(name, (report["status"] == "VERIFIED") == expected, report)

    trace_check("completed_matching_traces", expected=True)
    trace_check("simulator_nonzero_rc", rc=1)
    trace_check("fatal_even_with_pass", transcript=text+"# ** Fatal: checker failed\n")
    trace_check("error_count_even_with_pass", transcript=text+"# Errors: 1, Warnings: 0\n")
    trace_check("missing_completion_marker", transcript="")
    trace_check("missing_state_marker", transcript=text.splitlines()[0]+"\n")
    trace_check("wrong_seed_marker", transcript=text.replace("seed=1", "seed=2"))
    trace_check("duplicate_completion_marker", transcript=text+text)
    trace_check("identical_header_only", a=header, b=header)
    trace_check("identical_truncated_traces", a=header+row0, b=header+row0)
    trace_check("unterminated_trace", a=(header+row0+row1).rstrip("\n"))
    trace_check("unknown_trace_value", a=(header+row0+row1).replace("00000004", "xxxxxxxx"))
    trace_check("non_dense_retire_order", a=(header+row0+row1).replace("1,00000004", "3,00000004"))
    trace_check("different_complete_traces", b=(header+row0+row1).replace("00000004", "00000008"))
    trace_check("zero_retirements", a=header, b=header, transcript=text.replace("OFF=2 ON=2", "OFF=0 ON=0"))

    project = fixture / "isolated_project"
    sources = ("scripts/run_random_diff.sh", "scripts/verify_random_diff_case.py", "scripts/rtl_manifest.py",
               "verification/random/gen_rv32.py", "tb/run_random_trace.do", "tb/random_trace_tb.sv")
    for relative in sources:
        target = project / relative; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    (project / "results").mkdir()
    # This fixture has one real TB source; its manifest is built locally rather
    # than weakening the production manifest or replacing --check with a stub.
    tbhash = hashlib.sha256((project / "tb/random_trace_tb.sv").read_bytes()).hexdigest()
    files = {"tb/random_trace_tb.sv": tbhash}
    aggregate = hashlib.sha256(("tb/random_trace_tb.sv" + tbhash).encode()).hexdigest()
    (project / "results/rtl_manifest.json").write_text(json.dumps(
        {"generated": "synthetic runner controls", "count": 1, "aggregate": aggregate, "files": files}))
    fake = project / "fake_questa.sh"
    fake.write_text("#!/usr/bin/env bash\npython -B - <<'PY'\n" +
        "import os,sys\nfrom pathlib import Path\n" +
        f"header={header!r}; rows={row0+row1!r}\n" +
        "mode=os.environ['FAKE_MODE']; seed=os.environ['VERIFY_SEED']\n" +
        "data=header+(rows if mode!='truncated' else rows.splitlines(True)[0])\n" +
        "for k in ('VERIFY_TRACE_OFF','VERIFY_TRACE_ON'):Path(os.environ[k]).write_text(data)\n" +
        "if mode!='no_pass':\n" +
        " print(f'[PASS] Random retirement traces generated seed={seed} OFF=2 ON=2')\n" +
        " print(f'[PASS] BP OFF/ON architectural state equivalent seed={seed}')\n" +
        "if mode=='fatal':print('** Fatal: synthetic checker failure')\n" +
        "sys.exit(7 if mode=='rc' else 0)\nPY\n", encoding="ascii", newline="\n")
    bash = shutil.which("bash")
    gitbash = Path(r"C:/Program Files/Git/bin/bash.exe")
    if gitbash.exists(): bash = str(gitbash)
    if not bash: raise RuntimeError("Bash is required for runner integration controls")
    for mode, passno, expected in (("good",1,True),("good",2,True),("rc",1,False),
                                  ("fatal",1,False),("no_pass",1,False),("truncated",1,False)):
        env = dict(os.environ, QUESTA_VSIM=fake.as_posix(), FAKE_MODE=mode, PYTHON=sys.executable.replace("\\","/"))
        p = subprocess.run([bash, str(project / "scripts/run_random_diff.sh"), "1", "1", str(passno)],
                           cwd=project, env=env, capture_output=True, text=True)
        (fixture / f"runner_{mode}_p{passno}.log").write_text(p.stdout+p.stderr)
        check(f"runner_{mode}_p{passno}", (p.returncode == 0) == expected, {"rc": p.returncode})
    runs = list((project / "results/random_diff_runs").iterdir())
    good_runs = [p for p in runs if (p / "verified_1.json").exists()
                 and json.loads((p / "verified_1.json").read_text())["status"] == "VERIFIED"]
    check("independent_pass_raw_evidence_preserved", len(runs)==6 and len(good_runs)==2
          and all((p/"sim_1.log").exists() for p in runs)
          and {json.loads((p/"inputs.json").read_text())["pass"] for p in good_runs} == {"1","2"})

    raw = ROOT / "results/random_diff"
    if raw.exists():
        reports = [case.verify(s,0,raw/f"sim_{s}.log",raw/f"trace_{s}_off.txt",raw/f"trace_{s}_on.txt")
                   for s in range(1,51)]
        check("existing_50_completed_cases", all(r["status"]=="VERIFIED" for r in reports),
              {"verified":sum(r["status"]=="VERIFIED" for r in reports)})
    for stem in ("rfbht_4kb","rfbhtf_4kb","board_reference_6c4ccffd_20261009"):
        p = subprocess.run([sys.executable,"-B",str(ROOT/"scripts/verify_double.py"),
                           str(ROOT/f"results/{stem}_p1.csv"),str(ROOT/f"results/{stem}_p2.csv"),
                           "--key","kernel","--also","config"], capture_output=True,text=True)
        check("existing_pair_"+stem,p.returncode==0,{"output":p.stdout.strip()})

    result = {"status":"PASS" if all(c["pass"] for c in checks) else "FAIL", "controls":len(checks),
              "passed":sum(c["pass"] for c in checks), "fixture":str(fixture.relative_to(ROOT)),
              "method":"synthetic controls, stub simulator, existing results read-only; no new RTL measurements",
              "source_sha256":{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
                  ("scripts/verify_double.py","scripts/run_random_diff.sh","scripts/verify_random_diff_case.py")},
              "checks":checks}
    (fixture / "verification.json").write_text(json.dumps(result,indent=2)+"\n",encoding="ascii")
    (OUT / "verification.json").write_text(json.dumps(result,indent=2)+"\n",encoding="ascii")
    return 0 if result["status"]=="PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
