"""Use the frozen isolated Verilator screen with a new APB observer/validator.

This changes only this process's Python callbacks. Existing live screen files,
RTL, TB, helpers and firmware are never modified.
"""
import json
from pathlib import Path
import re
import sys
import run_coremark_standard_verilator as runner
import coremark_standard_apb_gate as apb

def main():
    frozen = {p.relative_to(runner.ROOT).as_posix(): runner.sha(p)
              for p in (Path(__file__), Path(apb.__file__))}
    def check():
        if any(runner.sha(runner.ROOT / p) != h for p, h in frozen.items()):
            raise RuntimeError("APB runner/observer input changed")
    original_memory = runner.memory
    def memory():
        check()
        out = Path(sys.argv[sys.argv.index("--output") + 1]).resolve()
        log = out / "compile.log"
        if log.is_file():
            text = log.read_text(encoding="utf-8", errors="strict")
            kinds = set(re.findall(r"^%Warning-([A-Za-z0-9_]+):", text, re.M))
            if "%Error" in text or kinds - {"TIMESCALEMOD", "WIDTHEXPAND"}:
                raise RuntimeError("Unreviewed Verilator warnings; simulator will not start: " + str(sorted(kinds)))
        return original_memory()
    runner.memory = memory
    runner.wrapper = apb.wrapper
    runner.validate_case = apb.validate_case
    rc = runner.main()
    check()
    out = Path(sys.argv[sys.argv.index("--output") + 1]).resolve()
    receipt = out / "receipt.json"; record = json.loads(receipt.read_text())
    record["inputs"].update(frozen)
    record["timer"] = "APB_COUNT_INDEPENDENT_PHYSICAL_EDGE_AND_TIME_CHECK"
    receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")
    return rc

if __name__ == "__main__": raise SystemExit(main())
