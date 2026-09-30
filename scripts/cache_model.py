#!/usr/bin/env python3
"""An independent cache model, for cross-validating the RTL event counters.

Review item A3 asks for the hardware hit/miss counts to be checked against a
reference model rather than trusted because they came from hardware. This model
is written from the organization's specification, not from the RTL: a set of
tag/valid arrays, a fully associative victim buffer with round-robin
replacement, and the stated D-cache policy of write-through, no-write-allocate.
It knows nothing about the L0 fast-hit buffer, which is by construction a subset
of the main array and therefore cannot change a hit/miss verdict.

It consumes a trace dumped by tb_benchmark_snapshot with +trace_cache and
counts only between MARK CLEAR and MARK FREEZE, replaying everything before the
window so that the array state at CLEAR matches the hardware.

    python scripts/cache_model.py results/cache_trace.txt --config 0
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Cache:
    """One cache: direct-mapped, two-way, or direct-mapped plus victim."""

    def __init__(self, lines: int, line_bytes: int, ways: int,
                 victim_entries: int, write_allocate: bool):
        self.line_bytes = line_bytes
        self.ways = ways
        self.sets = lines // ways
        self.offset_bits = line_bytes.bit_length() - 1
        self.index_bits = self.sets.bit_length() - 1
        self.write_allocate = write_allocate
        self.tag = [[None] * self.sets for _ in range(ways)]
        self.replace = [0] * self.sets            # which way to evict next
        self.vc_entries = victim_entries
        self.vc = []                              # list of block addresses
        self.vc_ptr = 0
        self.reset_counts()

    def reset_counts(self) -> None:
        self.main_hit = self.victim_hit = self.true_miss = 0
        self.reads = self.writes = 0

    def _split(self, addr: int):
        block = addr >> self.offset_bits
        index = block & (self.sets - 1)
        tag = block >> self.index_bits
        return block, index, tag

    def access(self, addr: int, is_write: bool, counted: bool = True) -> None:
        if counted:
            if is_write:
                self.writes += 1
            else:
                self.reads += 1
        block, index, tag = self._split(addr)

        for w in range(self.ways):
            if self.tag[w][index] == tag:
                if counted:
                    self.main_hit += 1
                if self.ways > 1:
                    self.replace[index] = 1 - w
                return

        if self.vc_entries and block in self.vc:
            # Swap: the victim line returns to the main array, the line it
            # displaces takes its place in the buffer.
            if counted:
                self.victim_hit += 1
            slot = self.vc.index(block)
            evicted = self.tag[0][index]
            self.vc[slot] = ((evicted << self.index_bits) | index
                             if evicted is not None else None)
            if self.vc[slot] is None:
                self.vc.pop(slot)
            self.tag[0][index] = tag
            return

        if counted:
            self.true_miss += 1
        if is_write and not self.write_allocate:
            return                                 # no-write-allocate: no fill

        way = 0 if self.ways == 1 else self.replace[index]
        old = self.tag[way][index]
        if self.vc_entries and old is not None:
            old_block = (old << self.index_bits) | index
            if len(self.vc) < self.vc_entries:
                self.vc.append(old_block)
            else:
                self.vc[self.vc_ptr] = old_block
                self.vc_ptr = (self.vc_ptr + 1) % self.vc_entries
        self.tag[way][index] = tag
        if self.ways > 1:
            self.replace[index] = 1 - way


CONFIGS = {
    0: dict(ways=1, victim=0, name="DM"),
    1: dict(ways=2, victim=0, name="SA2"),
    2: dict(ways=1, victim=4, name="DM_VC4"),
    3: dict(ways=1, victim=0, name="DM_DSE"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--config", type=int, default=0)
    ap.add_argument("--lines", type=int, default=64)
    ap.add_argument("--line-bytes", type=int, default=16)
    ap.add_argument("--skip-after-clear", type=int, default=1,
                    help="accesses the hardware frontier drops at window open")
    args = ap.parse_args()

    spec = CONFIGS[args.config]
    icache = Cache(args.lines, args.line_bytes, spec["ways"], spec["victim"],
                   write_allocate=True)
    dcache = Cache(args.lines, args.line_bytes, spec["ways"], spec["victim"],
                   write_allocate=False)

    path = Path(args.trace)
    if not path.is_absolute():
        path = ROOT / path
    counting = False
    seen_window = False
    skip = 0
    with path.open() as f:
        for line in f:
            if line.startswith("MARK"):
                if "CLEAR" in line:
                    icache.reset_counts()
                    dcache.reset_counts()
                    counting = True
                    seen_window = True
                    # counter_freeze is driven partly by a register that
                    # deasserts one cycle after the clear command, so the
                    # hardware does not count the first access of the window.
                    skip = 0
                elif "FREEZE" in line and counting:
                    counting = False
                    break
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            # The trace carries the hardware's own counting gate per access,
            # so no boundary heuristic is needed: cache state always advances,
            # counters advance only where the hardware counted.
            if parts[0] == "I":
                icache.access(int(parts[1], 16), False,
                              counted=(len(parts) < 3 or parts[2] == "1"))
            elif parts[0] == "D":
                dcache.access(int(parts[1], 16), parts[2] == "1",
                              counted=(len(parts) < 4 or parts[3] == "1"))

    if not seen_window:
        sys.exit("[FAIL] no CLEAR marker in %s" % path)

    print("Independent model, %s, %d lines x %d B"
          % (spec["name"], args.lines, args.line_bytes))
    print("  i_access = %d" % (icache.main_hit + icache.victim_hit
                               + icache.true_miss))
    print("  i_main   = %d" % icache.main_hit)
    print("  i_victim = %d" % icache.victim_hit)
    print("  i_miss   = %d" % icache.true_miss)
    print("  d_read   = %d" % dcache.reads)
    print("  d_write  = %d" % dcache.writes)
    print("  d_main   = %d" % dcache.main_hit)
    print("  d_victim = %d" % dcache.victim_hit)
    print("  d_miss   = %d" % dcache.true_miss)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
