"""Use the existing isolated builder with an explicit APB timing port.

No old helper/input is edited. Existing APB timer semantics require CMP to be
raised to UINT32_MAX; original timing-port source is included in provenance.
"""
import json
from pathlib import Path
import sys
import build_coremark_standard as build

def main():
    original_run = build.run
    build.PORTS = ("coremark_standard_apb_port.c", "coremark_standard_printf.c", "coremark_standard_main.c")
    def same_flags(command, cwd, output):
        if "-c" in command and any(command[command.index("-c") + 1].endswith(p) for p in build.PORTS[:2]):
            command = [*command[:1], "-Dmain=coremark_main", *command[1:]]
        return original_run(command, cwd, output)
    build.run = same_flags
    if "--integer-time" not in sys.argv: sys.argv.append("--integer-time")
    rc = build.main()
    out = Path(sys.argv[sys.argv.index("--output") + 1]).resolve()
    path = out / "build.json"; metadata = json.loads(path.read_text())
    for source in (Path(__file__), build.ROOT / "sw/coremark/core_portme.c", build.ROOT / "hdl/apb_timer.v"):
        metadata["inputs"][source.relative_to(build.ROOT).as_posix()] = build.sha(source)
    metadata.update(timer_csr=None, timer_method="APB_TIMER_COUNT", timer_compare=0xffffffff,
                    timer_hypothesis="configure compare above every bounded interval; observer verifies count delta equals physical edges",
                    common_coremark_c_macro="-Dmain=coremark_main")
    path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="ascii")
    if any(build.sha(build.ROOT / p) != h for p, h in metadata["inputs"].items()):
        raise RuntimeError("Frozen APB build inputs changed")
    return rc

if __name__ == "__main__": raise SystemExit(main())
