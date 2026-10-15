# BHT read undefined-default local proof

The single BHT read `$pmux` in the pre-`setundef` GOLD RTLIL cannot select its
undefined default for any Boolean eight-bit read address. Two independent
Windows CLI executions produced byte-identical, all-field-identical receipts.
Each execution checked all 256 addresses. No reset, invariant, legal-state,
or zero-initialization premise was used. Every table data bit and both default
data bits remain arbitrary symbolic values.

The result closes one additional local X/Z `connect` line. Together with the
earlier 256 BHT counter-update defaults, 257 of the historical 358 GOLD
functional X/Z connect lines now have this local Boolean definedness proof.
The remaining 101 lines are open. These counts describe classified connect
lines; they do not count bits or hardware defects and do not establish a
whole-source abstraction theorem.

## Exact inputs and checked structure

- Current ASIC source: [bht_2bit.v](../hdl/predictor/bht_2bit.v), table line25,
  fetch slice line28, and direct read line31, with `__openlane__` selected.
- Signed snapshot source:
  [bht_2bit.v](../asic/snapshots/rtl_r14/hdl/predictor/bht_2bit.v), table line20,
  fetch slice line22, and direct read line24. The local read contracts match.
- The original
  [gold_flat_r14.il](../asic/equiv/lec/gold_flat_r14.il) cell `$procmux$21089`
  at line87728 has `WIDTH=2`, `S_WIDTH=256`, default `A=2'x`, and result
  `u_soc.u_core.u_pipeline.datapath.bht_state_f`.
- Every selector is an actual unsigned eight-bit equality, or the exact
  unsigned eight-bit logic-not zero decoder. All compare the same original
  `pc_f[9:2]`; comparator constants cover 00 through FF exactly once.
- The corresponding B input words are the original two-bit
  `bht_mem[0]` through `bht_mem[255]`, paired with their actual selectors in
  RTLIL concat order. Each selector selects its matching table word.
  The complete 32-bit PC wire, all 256 two-bit data wires, and the three
  original BHT fetch module connections are checked in the same raw IR.

The exhaustive selector table proves one active selector for every address.
The output is therefore the selected original symbolic two-bit table word
for every assignment to all 512 table data bits. Neither undefined-default
bit is part of that output expression. The proof does not use `full_case`
attributes as an assumption; it examines the actual decoded signals.

## Controls, provenance, and scope

Each execution includes two semantic negative controls. Disabling only the
actual index255 selector in an in-memory copy makes address255 select the
arbitrary default. With the selected original table word set to2, defaults0
and3 produce the distinct local mutated outputs0 and3. A separate exact-source
copy changes the table upper bound from255 to254 while retaining the original
eight-bit read index; index255 becomes out of range. No mutated source or IR
is written, and no mutated frontend correspondence or reachable whole-chip
trace is claimed. Four additional malformed-input controls reject a seven-bit
selector, signed selector, changed PC slice, and swapped data words.

The first development preflight rejected unrelated later datapath attribute
macro directives before producing a result. Its error and deterministic
diagnosis are retained. The new checker was corrected while idle to inspect
only the source prefix through the exact BHT parent instance, and then frozen
before the two successful executions. No source/IR, proof premise, bound,
or existing helper was changed. No hardware or memory fault is asserted.

The two passes used a hard256MiB process memory limit and peaked below40MiB.
No simulator, solver, frontend, WSL process, or flow tool was started.
Original file hashes are checked before and after each execution.

This is a local two-state Boolean source/IR result. Four-state X/Z behavior,
whole-source undefined-value abstraction, raw N1/final initial-state coupling,
event-level asynchronous reset correspondence, and full sequential LEC remain
open. FPGA M9K behavior is outside this ASIC local-read proof. Historical
restricted `AR14_gate`/`BR14FA_gate` graphs remain insufficient as raw
initial-state proofs; any later raw frontend/cut work must preserve all paired
arbitrary states and undefined-value consumers without one-hot substitutions
or guessed zero initialization.

## Evidence

- [Proof checker](../scripts/verification/check_bht_read_default_definedness.py).
- [Pass1](bht_read_default_definedness_20261010_p1.json) and
  [pass2](bht_read_default_definedness_20261010_p2.json).
- [Paired source/hash/count audit](bht_read_default_definedness_20261010_verification.json)
  and [audit script](../scripts/verification/audit_bht_read_default_definedness.py).
- [Native execution record](bht_read_default_definedness_execution_20261010.json).
- [Retained failed preflight diagnosis](bht_read_definedness_development_attempt_20261010.json)
  and [traceback](bht_read_definedness_development_attempt_20261010_error.log).
- Earlier [BHT update/source-cut scope report](lec_source_definedness_20261010.md).

`source_read_lines` inside the original proof receipts refer to the selected,
uncommented local source view. Exact original file locations are separately
provided by `actual_original_source_line_evidence` in the paired audit.
The method review is separate from this receipt-comparison audit.
