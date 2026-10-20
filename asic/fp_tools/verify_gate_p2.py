"""Regression and negative controls for the opt-in p2 route-data reader.

Existing PD runs are read-only. Small synthetic fixtures are not PD results.
The final sign-off code and its output must stay identical to the saved reader.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "results/gate_p2_no_repair_20261009"
BEFORE = HERE / "gate_check_before.py"
AFTER = ROOT / "asic/fp_tools/gate_check.py"


def invoke(script, run, gate, fallback=False, extra=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("P1_", "P2_")) and k != "FINAL_SS"}
    if fallback:
        env["P2_INITIAL_GRT_FALLBACK"] = "1"
    env.update(extra or {})
    p = subprocess.run([sys.executable, str(script), str(run), gate], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=60)
    return {"exit": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}


def main():
    checks = {}
    runs = {
        "DM_r1": "asic/soc_dm_4kb/runs/r14F_A",
        "DM_r2": "asic/soc_dm_4kb/runs/r14F_B",
        "SA2_r1": "asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1",
        "SA2_r2": "asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r2",
        "VC4_no_repair": "asic/soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1",
        "VC4_repair": "asic/soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_antoff_nogrtt_r1",
    }
    for label, rel in runs.items():
        assert (ROOT / rel).is_dir(), rel
        for gate in ("p1", "p2", "final"):
            old = invoke(BEFORE, ROOT / rel, gate)
            new = invoke(AFTER, ROOT / rel, gate)
            if old != new:
                raise AssertionError(f"Default behaviour changed: {label}/{gate}: {old} != {new}")
            checks[f"default_unchanged_{label}_{gate}"] = {"pass": True, "result": new}
        if label != "VC4_no_repair":
            new = invoke(AFTER, ROOT / rel, "p2", fallback=True)
            old = invoke(BEFORE, ROOT / rel, "p2")
            if new != old:
                raise AssertionError(f"Existing repaired-route behaviour changed: {label}")
            checks[f"repaired_route_unchanged_{label}"] = {"pass": True, "result": new}
    actual = invoke(AFTER, ROOT / runs["VC4_no_repair"], "p2", fallback=True, extra={"P2_MIN_SETUP": "0"})
    assert actual["exit"] == 1 and "initial GlobalRouting" in actual["stdout"]
    assert "setup nom_tt 0.046" in actual["stdout"] and "hold nom_tt -0.364" in actual["stdout"]
    checks["VC4_numbers_read_hold_still_fails"] = {"pass": True, "result": actual}
    # Isolate the final sign-off block; T9 must not edit it.
    old_text, new_text = BEFORE.read_text(), AFTER.read_text()
    assert old_text[old_text.index('if gate == "final":'):] == new_text[new_text.index('if gate == "final":'):]
    checks["final_signoff_code_identical"] = {"pass": True}

    with tempfile.TemporaryDirectory(prefix="p2_reader_fixture_", dir=ROOT / "results") as folder:
        run = Path(folder).resolve()
        assert run.is_relative_to((ROOT / "results").resolve())
        g = run / "39-openroad-globalrouting"
        s = run / "42-openroad-stamidpnr-3"
        g.mkdir()
        s.mkdir()
        route_log = g / "openroad-globalrouting.log"
        route_log.write_text("Total 0\n", encoding="ascii")
        state = {"metrics": {"timing__setup__ws__corner:nom_tt_025C_1v80": 0.5,
                            "timing__hold__ws__corner:nom_tt_025C_1v80": 0.02}}
        (s / "state_out.json").write_text(json.dumps(state))
        (g / "state_out.json").write_text(json.dumps({"metrics": {}}))
        config = run / "resolved.json"
        config.write_text(json.dumps({"RUN_POST_GRT_DESIGN_REPAIR": False}))

        def check(name, code, contains, enabled=True):
            result = invoke(AFTER, run, "p2", fallback=enabled)
            assert result["exit"] == code and contains in result["stdout"], (name, result)
            checks[name] = {"pass": True, "result": result}

        check("fallback_off_missing", 2, "MISSING", enabled=False)
        check("disabled_repair_complete_route_passes", 0, "initial GlobalRouting")
        config.write_text(json.dumps({"RUN_POST_GRT_DESIGN_REPAIR": True}))
        check("enabled_repair_missing_step_rejected", 2, "MISSING")
        config.write_text("{}")
        check("missing_repair_setting_rejected", 2, "MISSING")
        config.write_text(json.dumps({"RUN_POST_GRT_DESIGN_REPAIR": False}))
        (g / "state_out.json").write_text("{}")
        check("incomplete_global_route_rejected", 2, "MISSING")
        (g / "state_out.json").write_text(json.dumps({"metrics": {}}))
        state["metrics"]["timing__hold__ws__corner:nom_tt_025C_1v80"] = -0.001
        (s / "state_out.json").write_text(json.dumps(state))
        check("negative_hold_rejected", 1, "hold nom_tt -0.001")
        state["metrics"]["timing__hold__ws__corner:nom_tt_025C_1v80"] = 0.02
        state["metrics"]["timing__setup__ws__corner:nom_tt_025C_1v80"] = -0.001
        (s / "state_out.json").write_text(json.dumps(state))
        check("negative_setup_rejected", 1, "setup nom_tt -0.001")
        state["metrics"]["timing__setup__ws__corner:nom_tt_025C_1v80"] = 0.5
        (s / "state_out.json").write_text(json.dumps(state))
        route_log.write_text("Total 2001\n")
        check("initial_overflow_above_limit_rejected", 1, "2001")
        route_log.write_text("Total 0\n")
        later = run / "40-openroad-repairantennas"
        later.mkdir()
        (later / "reroute.log").write_text("Total 2001\n")
        check("latest_reroute_overflow_wins", 1, "last post-GRT reroute")

    report = {"scope": "T9 opt-in route-data reader only; no threshold changes", "checks": checks, "passed": True}
    (HERE / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"[PASS] {len(checks)} gate-reader checks; final gate unchanged -> {HERE / 'verification.json'}")


if __name__ == "__main__":
    main()
