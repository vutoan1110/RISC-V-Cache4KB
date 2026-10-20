"""Build isolated standard-size performance/validation firmware, never run it.

Run with WSL Python and its existing RV32 cross compiler. One compiler at a
time; all outputs are new. No original firmware/source/manifest is overwritten.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ALGORITHMS = ("core_main.c", "core_list_join.c", "core_matrix.c", "core_state.c", "core_util.c", "coremark.h")
PORTS = ("coremark_standard_port.c", "coremark_standard_printf.c", "coremark_standard_main.c")

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(command, cwd, output):
    p = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    with output.open("a", encoding="utf-8") as f:
        f.write(json.dumps(command) + "\n" + p.stdout + f"\nNATIVE_EXIT={p.returncode}\n")
    if p.returncode: raise RuntimeError("Failed: " + " ".join(command))
    return p.stdout

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True)
    ap.add_argument("--cross", default="riscv64-unknown-elf-")
    ap.add_argument("--optimization", choices=("O2", "Os"), default="O2")
    ap.add_argument("--integer-time", action="store_true", help="EEMBC HAS_FLOAT=0; exact throughput must be calculated externally from ticks")
    ap.add_argument("--profiles", default="performance,validation")
    ap.add_argument("--iterations", type=int, default=0, help="0 uses unchanged upstream automatic calibration")
    args = ap.parse_args()
    profiles = args.profiles.split(",")
    if not profiles or len(set(profiles)) != len(profiles) or any(p not in ("performance", "validation") for p in profiles):
        ap.error("Distinct performance/validation profiles required")
    if args.iterations < 0 or args.iterations > 0x7fffffff: ap.error("Bad iteration count")
    out = Path(args.output).resolve()
    if not out.is_relative_to(ROOT / "results"): ap.error("Output must be inside research results")
    if not shutil.which(args.cross + "gcc"): ap.error("Existing cross compiler not found")
    out.mkdir(parents=True, exist_ok=False)
    sources = [ROOT / "sw/coremark" / p for p in ALGORITHMS]
    sources += [ROOT / "sw/coremark/core_portme.h", ROOT / "sw/coremark/coremark_link.ld",
                ROOT / "sw/startup.S", *sorted((ROOT / "sw").glob("platform*.h")),
                ROOT / "sw/fix_hex.py", ROOT / "results/rtl_manifest.json", Path(__file__)]
    sources += [HERE / p for p in PORTS]
    frozen = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    metadata = {"status": "BUILDING_NOT_MEASUREMENT", "started": datetime.now(timezone.utc).isoformat(),
                "inputs": frozen, "ram_bytes": 32768, "stack_reserved_bytes": 1024,
                "clock_hz": 50000000, "timer_csr": "0xB00", "timer_bits": 32,
                "iterations": args.iterations, "profiles": {}, "commands_log": "build.log",
                "algorithm_changes": False, "physical_chip_execution": False,
                "minimum_valid_ticks": 500000000, "official_score_measured": False}
    metadata["has_float"] = int(not args.integer_time)
    receipt = out / "build.json"
    def save(): receipt.write_text(json.dumps(metadata, indent=2) + "\n", encoding="ascii")
    save()
    log = out / "build.log"
    try:
        version = run([args.cross + "gcc", "--version"], ROOT, log).splitlines()[0]
        flags = ["-" + args.optimization, "-march=rv32i_zmmul_zicsr", "-mabi=ilp32",
                 "-ffreestanding", "-fno-builtin", "-msmall-data-limit=0",
                 "-ffunction-sections", "-fdata-sections", "-Wall", "-Wextra"]
        metadata["compiler_version"] = version
        metadata["compiler_macro_version"] = run([args.cross + "gcc", "-dumpfullversion"], ROOT, log).strip()
        metadata["compiler_flags"] = flags
        metadata["multilib"] = run([args.cross + "gcc", *flags, "-print-multi-directory"], ROOT, log).strip()
        old = run([args.cross + "size", str(ROOT / "sw/coremark/coremark.elf")], ROOT, log)
        metadata["old_elf_size_output"] = old
        for profile in profiles:
            dest = out / profile; dest.mkdir(); src = dest / "source"; src.mkdir(); obj = dest / "obj"; obj.mkdir()
            for name in ALGORITHMS: shutil.copyfile(ROOT / "sw/coremark" / name, src / name)
            for name in (*[p.name for p in sorted((ROOT / "sw").glob("platform*.h"))], "startup.S"):
                shutil.copyfile(ROOT / "sw" / name, src / name)
            shutil.copyfile(ROOT / "sw/coremark/coremark_link.ld", src / "link.ld")
            for name in PORTS: shutil.copyfile(HERE / name, src / name)
            header = (ROOT / "sw/coremark/core_portme.h").read_text()
            changes = {"#define HAS_FLOAT 0": "#define HAS_FLOAT " + str(int(not args.integer_time)),
                       '#define COMPILER_FLAGS "-O2 -march=rv32i_zmmul -mabi=ilp32"':
                           '#define COMPILER_FLAGS ' + json.dumps(" ".join(flags)),
                       "#define ITERATIONS 1": "#define ITERATIONS 0"}
            for before, after in changes.items():
                if header.count(before) != 1: raise RuntimeError("Header anchor mismatch: " + before)
                header = header.replace(before, after)
            (src / "core_portme.h").write_text(header, encoding="ascii")
            profile_flags = [f"-DPERFORMANCE_RUN={int(profile == 'performance')}",
                             f"-DVALIDATION_RUN={int(profile == 'validation')}",
                             "-DPROFILE_RUN=0", "-DTOTAL_DATA_SIZE=2000", f"-DITERATIONS={args.iterations}"]
            objects = []
            for name in (*ALGORITHMS[:-1], *PORTS, "startup.S"):
                op = obj / (Path(name).stem + ".o"); objects.append(op)
                mainflag = ["-Dmain=coremark_main"] if name in ALGORITHMS[:-1] else []
                run([args.cross + "gcc", *flags, *profile_flags, *mainflag, "-I", str(src),
                     "-c", str(src / name), "-o", str(op)], ROOT, log)
            elf = dest / "coremark.elf"
            run([args.cross + "gcc", *flags, "-nostdlib", "-nostartfiles", "-Wl,--gc-sections",
                 "-Wl,-Map=" + str(dest / "coremark.map"), "-T", str(src / "link.ld"),
                 *map(str, objects), "-lgcc", "-o", str(elf)], ROOT, log)
            sizes = run([args.cross + "size", str(elf)], ROOT, log)
            nm = run([args.cross + "nm", "-n", str(elf)], ROOT, log)
            symbols = {m[2]: int(m[0], 16) for m in re.findall(r"^([0-9a-fA-F]+)\s+(\w)\s+(\S+)$", nm, re.M)}
            required = ("_start", "__image_end", "__bss_start", "__bss_end", "__stack_bottom", "__stack_top")
            if any(k not in symbols for k in required) or symbols["_start"] != 0:
                raise RuntimeError("Missing/bad linker layout")
            if symbols["__image_end"] > symbols["__stack_bottom"] or symbols["__stack_top"] != 32768:
                raise RuntimeError("Image overlaps stack or changed physical simulation RAM")
            disassembly = run([args.cross + "objdump", "-d", str(elf)], ROOT, log)
            if re.search(r"\t(?:divu?|remu?|amo\w*|lr\.w|sc\.w)\s", disassembly):
                raise RuntimeError("ELF contains instructions unsupported by RV32I + Zmmul + CSR subset")
            bytehex = dest / "bytes.hex"; wordhex = dest / "coremark.hex"
            run([args.cross + "objcopy", "-O", "verilog", str(elf), str(bytehex)], ROOT, log)
            run([sys.executable, str(ROOT / "sw/fix_hex.py"), "--input", str(bytehex), "--output", str(wordhex),
                 "--ram-bytes", "32768"], ROOT, log)
            size_values = re.search(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+\d+", sizes, re.M)
            if not size_values: raise RuntimeError("Missing ELF size output")
            text, data, bss = map(int, size_values.groups())
            metadata["profiles"][profile] = {"status": "BUILT_NOT_RUN", "text_bytes": text, "data_bytes": data,
                "bss_bytes": bss, "image_end_bytes": symbols["__image_end"],
                "image_plus_reserved_stack_bytes": symbols["__image_end"] + 1024,
                "could_fit_16k_by_static_footprint_only": symbols["__image_end"] + 1024 <= 16384,
                "symbols": {k: symbols[k] for k in required}, "size_output": sizes,
                "artifacts": {p.relative_to(ROOT).as_posix(): sha(p) for p in dest.rglob("*") if p.is_file()}}
            save()
        if any(sha(ROOT / rel) != h for rel, h in frozen.items()): raise RuntimeError("Original inputs changed during build")
        metadata["status"] = "BUILT_NOT_RUN_NOT_A_SCORE"; save(); print(receipt); return 0
    except BaseException as exc:
        metadata["status"] = "FAILED_BUILD_NOT_MEASUREMENT"; metadata["error"] = str(exc); save(); raise

if __name__ == "__main__": raise SystemExit(main())
