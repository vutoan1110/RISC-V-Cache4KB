"""Passive APB timer observer and physical interval gate; no measurements here."""
from pathlib import Path
import re
from run_coremark_standard import wrapper as common_wrapper, validate_case as common_validate

def wrapper():
    text = common_wrapper()
    anchor = "    integer uart_fd = 0;"
    if text.count(anchor) != 1: raise ValueError("Unexpected observer anchor")
    block = r'''
    reg [63:0] timer_edges = 0;
    integer timer_reads = 0;
    always @(negedge bench.clk) begin
        if (!bench.reset_n) timer_edges = 0;
        else timer_edges = timer_edges + 1;
    end
    always @(posedge bench.clk) begin
        if (bench.reset_n && bench.dut.u_timer.PSEL && bench.dut.u_timer.PENABLE &&
            bench.dut.u_timer.PREADY && !bench.dut.u_timer.PWRITE &&
            bench.dut.u_timer.PADDR[7:0] == 8'h08) begin
            if ($isunknown(bench.dut.u_timer.PRDATA))
                $fatal(1, "Unknown accepted timer count value");
            $display("COREMARK_APB_READ index=%0d edges=%0d time_ps=%0.0f value=%0d enabled=%0d compare=%0d",
                timer_reads, timer_edges, $realtime * 1000.0,
                bench.dut.u_timer.PRDATA, bench.dut.u_timer.ctrl_reg[0], bench.dut.u_timer.cmp_reg);
            timer_reads = timer_reads + 1;
        end
    end
'''
    return text.replace(anchor, block + "\n" + anchor)

def validate_case(log, uart, profile, cfg, build, max_cycles):
    if build.get("timer_method") != "APB_TIMER_COUNT" or build.get("timer_compare") != 0xffffffff:
        raise ValueError("Wrong/missing bounded APB timer firmware recipe")
    result = common_validate(log, uart, profile, cfg, build, max_cycles)
    text = Path(log).read_text(encoding="utf-8", errors="strict")
    reads = re.findall(r"COREMARK_APB_READ index=(\d+) edges=(\d+) time_ps=(\d+) value=(\d+) enabled=(\d+) compare=(\d+)\s*$", text, re.M)
    samples = result["timer_intervals"]
    if len(reads) != len(samples) * 2: raise ValueError("Incomplete/extra accepted timer reads")
    for j, sample in enumerate(samples):
        a, b = [tuple(map(int, x)) for x in reads[2*j:2*j+2]]
        if (a[0], b[0]) != (2*j, 2*j+1) or a[4:] != (1, 0xffffffff) or b[4:] != (1, 0xffffffff):
            raise ValueError("Timer not independently observed enabled and unbounded")
        if (a[3], b[3]) != (sample["start"], sample["stop"]):
            raise ValueError("Firmware timestamps differ from actual accepted APB values")
        physical_edges = b[1] - a[1]
        physical_ps = b[2] - a[2]
        if physical_edges != sample["ticks"] or physical_ps != sample["ticks"] * 20000:
            raise ValueError("Timer count delta differs from independent physical cycles/20ns time")
    result["timer_method"] = "APB_COUNT_DELTA_EQUALS_INDEPENDENT_PHYSICAL_EDGES_AND_20NS_TIME"
    result["accepted_apb_reads"] = [list(map(int, x)) for x in reads]
    result["physical_final_interval_ps"] = result["timer_ticks"] * 20000
    return result
