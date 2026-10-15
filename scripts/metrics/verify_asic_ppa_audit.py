"""Check rejection of incomplete or mismatched evidence in the T6 audit."""
import json
import tempfile
from pathlib import Path

import asic_ppa_audit as audit


def main():
    checks = {}
    def rejects(name, fn):
        try:
            fn()
        except RuntimeError:
            checks[name] = True
        else:
            checks[name] = False
    rejects("missing_metric_field", lambda: audit.equal_metrics({"area": 1, "hold": 0}, {"area": 1}))
    rejects("changed_metric_value", lambda: audit.equal_metrics({"hold": 0}, {"hold": -0.1}))
    rejects("empty_measurements", lambda: audit.equal_metrics({"runtime__x": 1}, {"runtime__x": 2}))
    checks["runtime_difference_only_excluded"] = audit.equal_metrics(
        {"area": 1, "runtime__x": 1}, {"area": 1, "runtime__x": 2}) == {"area": 1}
    first = [{"step": "47-openroad-postrouteholdeco", "inserted_hold_buffers": 139},
             {"step": "48-openroad-postrouteholdeco", "inserted_hold_buffers": 11}]
    second = [{"step": "51-openroad-postrouteholdeco", "inserted_hold_buffers": 139},
              {"step": "52-openroad-postrouteholdeco", "inserted_hold_buffers": 11}]
    checks["ECO_directory_numbers_are_provenance"] = audit.equal_eco_sequence(first, second) is None
    rejects("ECO_changed_insertion_count", lambda: audit.equal_eco_sequence(first, [dict(first[0], inserted_hold_buffers=140), first[1]]))
    rejects("ECO_reversed_passes", lambda: audit.equal_eco_sequence(first, second[::-1]))
    rejects("ECO_missing_pass", lambda: audit.equal_eco_sequence(first, second[:1]))
    with tempfile.TemporaryDirectory(prefix="ppa_audit_control_", dir=audit.ROOT / "results") as name:
        folder = Path(name)
        a, b = folder / "a.csv", folder / "b.csv"
        a.write_text("kernel,metric\nk1,1\n", encoding="ascii")
        b.write_text("kernel,metric\nk1,2\n", encoding="ascii")
        rejects("changed_csv_field", lambda: audit.paired_csv(a, b, ["kernel"]))
        b.write_text("kernel,metric\nk1,1\nk1,1\n", encoding="ascii")
        rejects("duplicate_csv_key", lambda: audit.paired_csv(a, b, ["kernel"]))
        b.write_text("kernel,metric\nk2,1\n", encoding="ascii")
        rejects("different_csv_key_set", lambda: audit.paired_csv(a, b, ["kernel"]))
        a.write_bytes(b'*SPEF "IEEE 1481-1998"\n*DATE "a"\n*D_NET A 1\n')
        b.write_bytes(b'*SPEF "IEEE 1481-1998"\n*DATE "b"\n*D_NET A 1\n')
        checks["spef_date_only_ignored"] = audit.sha(a, spef=True) == audit.sha(b, spef=True)
        b.write_bytes(b'*SPEF "IEEE 1481-1998"\n*DATE "b"\n*D_NET A 2\n')
        checks["spef_non_date_change_detected"] = audit.sha(a, spef=True) != audit.sha(b, spef=True)
        b.write_bytes(b'*SPEF "IEEE 1481-1998"\n*D_NET A 1\n')
        rejects("missing_spef_date_not_normalized", lambda: audit.sha(b, spef=True))
        rejects("missing_signoff_gate", lambda: audit.final_gate(folder))
    vc4 = audit.ROOT / "asic/soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1"
    rejects("stopped_vc4_not_accepted_as_signed_off", lambda: audit.final_gate(vc4))
    checks["missing_second_power_receipt_excluded"] = audit.activity("missing_power_receipt_control", None, None, "DM")["status"] == "NOT_DOUBLE_VERIFIED"
    out = audit.ROOT / "results/asic_ppa_audit_controls_20261009.json"
    out.write_text(json.dumps({"checks": checks, "passed": all(checks.values()),
        "scope": "report-integrity controls, not new hardware measurements"}, indent=2) + "\n", encoding="ascii")
    print(f"[{ 'PASS' if all(checks.values()) else 'FAIL' }] {sum(checks.values())}/{len(checks)} evidence guards")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
