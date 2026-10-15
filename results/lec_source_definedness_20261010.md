# Local source-definedness and restricted-cut audit, 2026-10-10

Two independent native Python executions confirm the same local result. The
[paired verification receipt](lec_source_definedness_20261010_verification.json)
checks every field and byte of both BHT proof receipts and both source/cut audit
receipts. No RTL, existing model, legacy recipe or running job changed. No WSL,
Yosys, simulator, installer or actual SoC solver ran; every process was limited
to256MiB. Full sequential LEC and whole-source undefined-value abstraction
remain OPEN; four-state X/Z behavior equivalence is not claimed.

## Exact local BHT result

All256 pre-`setundef` gold `$pmux` update cells have a two-bit undefined default
input. Each actual selector cone compares the same `bht_mem[entry]` state against
00,01,10 and11. Exhaustive enumeration of all four Boolean state codes for every
entry proves exactly one selector active: the undefined default is never
selected, regardless of its two arbitrary bit values. No reset, FSM reachability,
initial zero or joint-invariant premise is used.

The current source counter function and the signed ASIC snapshot function have
equal normalized bodies. Their eight state/taken cases implement the two-bit
saturating counter. The current function is at
[`hdl/predictor/bht_2bit.v:36`](../hdl/predictor/bht_2bit.v), and the snapshot
function at [`bht_2bit.v:27`](../asic/snapshots/rtl_r14/hdl/predictor/bht_2bit.v).
The first actual IR mux is `$procmux$15970` at
[`gold_flat_r14.il:71344`](../asic/equiv/lec/gold_flat_r14.il); the JSON records
all256 cells and every exact comparator, source line and truth-table row.

Negative controls operate only on copies in memory. Removing the actual11
source branch selects the default01 at state3/taken1, whereas the original
function returns3. Removing that comparator from the copied actual selector
population selects the mux default; choosing arbitrary default values0 and3
changes the local mux output. These are local semantic faults, not a claim of a
reachable whole-chip hardware defect. All checks and controls executed twice;
receipts are byte- and field-identical.

Evidence: [BHT pass1](bht_default_definedness_20261010_p1.json),
[pass2](bht_default_definedness_20261010_p2.json),
[source/cut pass1](lec_source_definedness_audit_20261010_p1.json),
[pass2](lec_source_definedness_audit_20261010_p2.json).
The reproducible checkers are
[`check_bht_default_definedness.py`](../scripts/verification/check_bht_default_definedness.py)
and [`audit_lec_source_definedness.py`](../scripts/verification/audit_lec_source_definedness.py).

## Why the existing gate AIGs cannot prove raw initial-state coupling

Both `AR14_gate.aig` and `BR14FA_gate.aig` contain ten used `lec_oh_*` input
selectors. Their22 corresponding paired raw Q input ports remain declared but
have no support in any compared output: their actual state is supplied by the
one-hot decoder. This is verified by traversing every output cone of each
original AIG, not inferred from filenames or Markdown.

| preserved comparison | paired states | restricted paired Q | actual common arbitrary Q connections verified | gold-side constant ties | gold-side duplicate aliases |
|---|---:|---:|---:|---:|---:|
| RTL gold to N1 (`AR14`) |19090|22|19068|235|28|
| N1 to final DM (`BR14FA`) |19087|22|19065|0|3|

The AR14 gold-only partition also contains105 free states. The gate AIGs use no
gold-only Q input in any compared output. Constants/duplicates are applied by
[`evert.py:310`](../asic/equiv/lec/evert.py) on the gold side; the gate side does
not acquire arbitrary gold-only state merely because those interface ports exist.
The paired unrestricted Q connections above were checked against the exact
gate-flop Q mapping and the appended IR cut connections. For the very large IR
files, only the final8MiB were read and fragment-hashed; the receipt explicitly
records offsets and does not claim the whole raw IR was read or hashed.

The cut helper's header still describes all flops starting at zero
[`evert.py:21`](../asic/equiv/lec/evert.py). That historical claim cannot describe
the current unreset RAM/tag/register-state contract. Common arbitrary paired
symbols, or a fully proved validity-aware relation, are required. The existing
restricted graphs provide combinational evidence under their restrictions; they
cannot substitute for a fresh unrestricted paired reset/initialization proof.

## Concrete remaining source bridge

The gold model has358 functional X/Z connect-line origins. This local result
closes256 BHT update-default origins within two-state Boolean semantics. The
remaining102 origins comprise68 other `$pmux` lines, seven X-bearing `$mux`
connect lines in six cells, and27 module connects. These counts are lines,
not undefined bits or RTL defects. The other BHT read mux,49 AXI-RAM defaults
and18 cache/UART/control defaults need their own selector or observability
proofs. Disabled regfile/tag-write data/address need the exact consumer and
write-enable relation; a source `if` guard alone does not close every downstream
sink. The N1 has two PC-low mux defaults and57 module connects still requiring
exact cone closure. Final-cell UDP defaults have complete local Boolean truth
tables, but their20,800 instances/consumers and undriven boundaries remain a
separate binding obligation.

The source gap exists before the final AIG conversion: synthesis replay uses
`opt_expr -mux_undef` before memory mapping/technology mapping
[`synthesize.py:183`](../asic/equiv/lec/synth_replay_r14/synthesize.py), and its
configured undefined tie runs after mapped ABC at
[`synthesize.py:435`](../asic/equiv/lec/synth_replay_r14/synthesize.py).
All existing AIG conversion recipes also use `setundef -undriven -zero` before
`check -assert`. A passing check on the already coerced Boolean graph cannot
establish that each earlier unknown was irrelevant to all compared sinks.

After resources permit, the missing raw reset-coupling graphs are:

- **N1 against the existing unrestricted gold graph:** cut
  `n1_flat_r14.il` on the gate side with `pairsAR14.json`, without `--spec` or
  `--inv`, into a new dated output. Every paired D remains exposed; no one-hot
  decoder or zero initialization is allowed.
- **N1/final reset relation:** cut the N1 gold side with
  `pairsB_R14FA.json` and `--gold-only-d`, and cut each final gate side with its
  own pair map, all without `--spec`/`--inv`. Expose the three N1-only D bits too.
- **Source-definedness bridge:** retain the pre-optimization/pre-`setundef`
  source IR and classify every undefined symbol with exact guarded consumers.
  Unsupported/unresolved values must stay arbitrary or UNKNOWN. A freshly
  zero-coerced AIG would still leave this obligation open. Exact tool options
  for retaining these symbols must be checked against the pinned runtime before
  any frontend runs; no new frontend command was executed in this audit.

All paired reset relations, SRAM/top-output boundaries and update-event
correspondence still need their own exact evidence. Current reset/induction
subproofs are reported separately; no full-chip equivalence follows from this
local definedness result.
