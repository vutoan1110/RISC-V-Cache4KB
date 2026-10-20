"""Supplemental current-source UVM: four cache points, stalled AXI and UART RX.

Original RTL, UVM sources and frozen manifest remain unchanged. Generated
adapters only select the DUT cache configuration and connect the existing
allocation assertion to the corresponding tag-write condition. Every case
has an independent invocation in each pass and retains logs and coverage.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VSIM = "C:/questasim64_2024.1/win64/vsim.exe"
UVM = "C:/questasim64_2024.1/uvm-1.2"
UVMSRC = "C:/questasim64_2024.1/verilog_src/uvm-1.2/src"
FAIL = re.compile(r"\*\*\s+(?:Error|Fatal):|\[FAIL\]|^#\s*Errors:\s*[1-9]", re.M | re.I)
COLS = ["test", "config", "seed", "line_words", "status", "summary"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="ascii")


def generate(out):
    src = ROOT / "verification/uvm/tb/tb_soc_top.sv"
    top = src.read_text(encoding="utf-8")
    old = "parameter integer CACHE_LINE_COUNT = 64"
    assert top.count(old) == 1
    top = top.replace(old, old + ",\n    parameter integer CACHE_CONFIG = 0")
    old = "        .MEMFILE               ("
    assert top.count(old) == 1
    top = top.replace(old, "        .CACHE_CONFIG          (CACHE_CONFIG),\n" + old)
    top = top.replace("    import soc_uvm_pkg::*;", "    import soc_uvm_pkg::*;\n    import uart_rx_matrix_pkg::*;")
    old = "    cache_assertions u_cache_assertions ("
    assert top.count(old) == 1
    # These are exactly the two guarded assignments to the DSE main tags.
    # None of the existing cache assertions is disabled for non-DM points.
    connection = """    wire d_tag_write_enable;
    generate if(CACHE_CONFIG == 0) begin : g_tag_dm
        assign d_tag_write_enable = dut.u_dcache.g_dm_baseline.u_controller.tag_wr_en;
    end else begin : g_tag_dse
        assign d_tag_write_enable =
            ((dut.u_dcache.g_dse.u_core.state == dut.u_dcache.g_dse.u_core.ST_SWAP_WRITE) &&
             (dut.u_dcache.g_dse.u_core.transfer_beat == dut.u_dcache.g_dse.u_core.LAST_WORD)) ||
            ((dut.u_dcache.g_dse.u_core.state == dut.u_dcache.g_dse.u_core.ST_REFILL_DATA) &&
             dut.u_dcache.g_dse.u_core.refill_rsp_valid &&
             dut.u_dcache.g_dse.u_core.refill_terminal &&
             dut.u_dcache.g_dse.u_core.refill_success);
    end endgenerate

"""
    top = top.replace(old, connection + old)
    old = ".d_tag_write_enable(dut.u_dcache.g_dm_baseline.u_controller.tag_wr_en)"
    assert top.count(old) == 1
    top = top.replace(old, ".d_tag_write_enable(d_tag_write_enable)")
    (out / "tb_soc_top.sv").write_text(top, encoding="ascii")
    package = r'''package uart_rx_matrix_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import soc_uvm_pkg::*;
    class uart_rx_pair_seq extends uvm_sequence #(uart_byte_item);
        `uvm_object_utils(uart_rx_pair_seq)
        function new(string name="uart_rx_pair_seq"); super.new(name); endfunction
        task body();
            uart_byte_item item;
            for(int k=0; k<2; k++) begin
                item = uart_byte_item::type_id::create($sformatf("rx_%0d",k));
                start_item(item);
                item.data = (k==0) ? 8'ha5 : 8'h3c;
                if(k==0 && $test$plusargs("RX_NEGATIVE")) item.data = 8'ha4;
                finish_item(item);
            end
        endtask
    endclass
    class soc_uart_rx_test extends soc_base_test;
        `uvm_component_utils(soc_uart_rx_test)
        function new(string name,uvm_component parent); super.new(name,parent); endfunction
        function void configure(); cfg.timeout_cycles=100000; cfg.uart_bit_cycles=448; endfunction
        task run_phase(uvm_phase phase);
            fork
                super.run_phase(phase);
                begin
                    uart_rx_pair_seq seq;
                    wait(cfg.obs_vif.reset_n === 1'b1);
                    repeat(400) @(posedge cfg.obs_vif.clk);
                    seq = uart_rx_pair_seq::type_id::create("rx_pair");
                    seq.start(env.serial_agent.sequencer);
                end
            join
        endtask
        function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if(cfg.stats.uart_rx_bytes != 2)
                `uvm_error("RXCOUNT",$sformatf("sent %0d frames, expected 2",cfg.stats.uart_rx_bytes))
            if(cfg.stats.arch_regs[10] !== 32'ha5 || cfg.stats.arch_regs[11] !== 32'h3c)
                `uvm_error("RXDATA",$sformatf("CPU read %08x %08x, expected a5 3c",
                           cfg.stats.arch_regs[10],cfg.stats.arch_regs[11]))
            if(cfg.stats.arch_regs[31] !== 32'd1)
                `uvm_error("RXSELFCHECK","firmware did not validate both received bytes")
        endfunction
    endclass
endpackage
'''
    (out / "uart_rx_matrix_pkg.sv").write_text(package, encoding="ascii")
    spec = importlib.util.spec_from_file_location("periph_program", ROOT / "verification/uvm/seq/gen_soc_periph_irq.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    words = [gen.lui(5, 0x40000), gen.lui(6, 0xc), gen.addi(6, 6, 0xc3),
             gen.sw(6, 5, 8), gen.addi(31, 0, 0)]
    for rd in (10, 11):
        words += [gen.lw(7, 5, 0x10), gen.andi(7, 7, 0x10), gen.beq(7, 0, -8),
                  gen.lw(rd, 5, 4), gen.addi(6, 0, 2), gen.sw(6, 5, 0xc)]
    words += [gen.addi(12, 0, 0xa5), gen.beq(10, 12, 8), gen.jal(0, 20),
              gen.addi(12, 0, 0x3c), gen.beq(11, 12, 8), gen.jal(0, 8),
              gen.addi(31, 0, 1), gen.HALT]
    (out / "uart_rx_pair.hex").write_text("".join(f"{w:08x}\n" for w in words), encoding="ascii")
    files = (ROOT / "verification/uvm/uvm.f").read_text(encoding="utf-8")
    files = files.replace("verification/uvm/tb/tb_soc_top.sv",
                          f"{out.relative_to(ROOT).as_posix()}/uart_rx_matrix_pkg.sv\n"
                          f"{out.relative_to(ROOT).as_posix()}/tb_soc_top.sv")
    (out / "uvm.f").write_text(files, encoding="ascii")


def tool(script, log):
    with log.open("w", encoding="utf-8") as fh:
        rc = subprocess.run([VSIM, "-c", "-do", script], cwd=ROOT, stdout=fh,
                            stderr=subprocess.STDOUT, timeout=300).returncode
    return rc, log.read_text(encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--tag", default="uvm_cache_uart_20261009")
    args = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9_]+", args.tag):
        ap.error("invalid tag")
    out = ROOT / "results" / args.tag
    if out.exists():
        raise RuntimeError("Output exists; preserve it and choose a new dated tag")
    subprocess.run(["python", "scripts/rtl_manifest.py", "--check"], cwd=ROOT, check=True,
                   stdout=subprocess.PIPE)
    out.mkdir()
    generate(out)
    frozen = json.loads((ROOT / "results/rtl_manifest.json").read_text())
    sources = {p: sha(ROOT / p) for p in frozen["files"]}
    extras = [Path(__file__), ROOT / "verification/uvm/rtl.f", ROOT / "verification/uvm/uvm.f"]
    sources.update({p.relative_to(ROOT).as_posix(): sha(p) for p in extras})
    generated = {p.relative_to(ROOT).as_posix(): sha(p) for p in out.iterdir() if p.is_file()}
    cases = [("axi_stress_test", -1, seed, lw) for seed in (1,2,3) for lw in (2,4,8,16)]
    cases += [(test, cfg, seed, 4) for test in ("soc_directed_test","soc_periph_test","soc_uart_rx_test")
              for cfg in range(4) for seed in (1,2,3)]
    receipt = {"status":"PREPARED", "rtl_id":frozen["aggregate"], "inputs":sources,
               "generated":generated, "cases_per_pass":len(cases), "created":datetime.now().astimezone().isoformat()}
    write_json(out / "verification.json", receipt)
    if not args.run:
        print(f"PREPARED: {len(cases)} cases/pass; two independent passes; one RX negative control/pass")
        return 0
    all_rows = []
    for n in (1,2):
        lib = f"work_{args.tag}_p{n}"
        compile_do = out / f"compile_p{n}.do"
        compile_do.write_text(f"""onerror {{quit -code 1 -f}}
vlib {lib}
vlog -work {lib} -sv -f verification/uvm/rtl.f
vlog -work {lib} -sv -L {UVM} +incdir+{UVMSRC} -f {out.relative_to(ROOT).as_posix()}/uvm.f
echo {{[PASS] UVM matrix compile}}
quit -code 0 -f
""", encoding="ascii")
        rc, txt = tool(f"do {compile_do.relative_to(ROOT).as_posix()}", out / f"compile_p{n}.log")
        if rc or FAIL.search(txt) or "[PASS] UVM matrix compile" not in txt:
            raise RuntimeError(f"Compile failed p{n}")
        rows = []
        for test, cfg, seed, lw in cases + [("soc_uart_rx_test",0,1,4)]:
            negative = len(rows) == len(cases)
            key = f"p{n}_{test}_c{cfg}_s{seed}_lw{lw}" + ("_negative" if negative else "")
            status = out / f"{key}.status"
            top = "tb_axi_top" if cfg == -1 else "tb_soc_top"
            extra = f"-gLINE_WORDS={lw}" if cfg == -1 else f"-gCACHE_LINE_COUNT=256 -gCACHE_CONFIG={cfg}"
            if test == "soc_periph_test":
                extra += " +SOC_HEX=verification/uvm/seq/soc_periph_irq.hex"
            if test == "soc_uart_rx_test":
                extra += f" +SOC_HEX={out.relative_to(ROOT).as_posix()}/uart_rx_pair.hex"
            if negative:
                extra += " +RX_NEGATIVE"
            run_do = out / f"{key}.do"
            run_do.write_text(f"""onerror {{quit -code 1 -f}}
vsim -coverage -L {UVM} -nodpiexports -onfinish stop -suppress 8634 -sv_seed {seed} {extra} {lib}.{top} +UVM_TESTNAME={test} +STATUS={status.relative_to(ROOT).as_posix()}
run -all
coverage save {out.relative_to(ROOT).as_posix()}/{key}.ucdb
quit -code 0 -f
""", encoding="ascii")
            rc, txt = tool(f"do {run_do.relative_to(ROOT).as_posix()}", out / f"{key}.log")
            verdict = status.read_text().strip() if status.exists() else "MISSING"
            if negative:
                if not verdict.startswith("FAIL soc_uart_rx_test ") or "[RXDATA]" not in txt:
                    raise RuntimeError(f"Negative control not detected: {key}")
                receipt[f"negative_p{n}"] = {"status":"EXPECTED_FAIL", "log":(out / f"{key}.log").relative_to(ROOT).as_posix()}
                print(f"[PASS] {key}: wrong UART byte detected", flush=True)
                continue
            if rc or FAIL.search(txt) or verdict != f"PASS {test} 0":
                raise RuntimeError(f"UVM case failed: {key}; rc={rc}, status={verdict}")
            summary = re.search(r"\[SUMMARY\].*?\n(.*?)(?=\n# UVM_|\n# \[PASS\])", txt, re.S)
            if not summary:
                raise RuntimeError(f"Missing scoreboard summary: {key}")
            measured = "|".join(s.strip().removeprefix("#").strip() for s in summary[1].splitlines() if s.strip())
            rows.append(dict(zip(COLS, [test,cfg,seed,lw,"PASS",measured])))
            print(f"[PASS] {key} {len(rows)}/{len(cases)}", flush=True)
        with (out / f"measurements_p{n}.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(rows)
        all_rows.append(rows)
    if all_rows[0] != all_rows[1]:
        raise RuntimeError("Independent UVM measurements differ")
    if any(sha(ROOT / p) != digest for p,digest in sources.items()):
        raise RuntimeError("Input source changed")
    receipt.update(status="VERIFIED_TWO_PASSES", paired_cases=len(cases),
                   artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in out.iterdir()
                              if p.is_file() and p.name != "verification.json"},
                   completed=datetime.now().astimezone().isoformat())
    write_json(out / "verification.json", receipt)
    print(f"[VERIFIED] {len(cases)} paired cases, identical scoreboard fields, UART negative controls caught")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
