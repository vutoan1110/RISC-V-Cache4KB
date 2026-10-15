# Source-to-model bridge and SA2 LEC preparation, 2026-10-10

This is a bounded preparation and read-only source audit. It is **not a full
LEC result**, a new synthesis execution or a PD result. No HDL, frozen input,
existing frontend, gate threshold or running job was changed. Only this report
and its [machine-readable evidence](lec_source_model_preparation_20261010.json)
were created. No Yosys, ABC, EQY, simulator or WSL frontend was launched.

## Verified inputs and the exact source bridge

The retained [SA2 preparation receipt](completion_preparation_20261009/sa2_lec_20261009/inputs_and_acceptance.json)
still matches all **77 local input hashes and 24 generated script hashes**.
The current manifest's **227 files** were also rechecked. Both preparation
folders contain 12 scripts and no replay/frontend outputs.

All 42 ordered SA2 sources were compared with their current research-source
counterparts in two independent rereads. A small fail-closed lexical projection
resolves the observed nested `ifdef`/`ifndef`/`else`/`endif` and object-like
`define`/`undef` constructs under `__openlane__`, `__pnr__`, `PDK_sky130A` and
`SCL_sky130_fd_sc_hd`. It retains quoted strings, removes comments and compares
complete token sequences. Unsupported directives or incomplete conditionals
are rejected rather than guessed.

- 34/42 source entries are byte-identical; this includes the shared DSE SRAM
  adapter and SA2 ASIC wrapper, whose current paths already are the signed inputs.
- 37/42 token projections are identical. The three additional matches are
  `regfile.v`, `predictor/bht_2bit.v` and `datapath.v`: their FPGA M9K changes
  disappear from the ASIC view.
- Five files remain different: `icache_dse_core.v`, `icache.v`,
  `dcache_dse_core.v`, `dcache.v` and `soc_top.v`. Their FAST_HIT/N-way parameter
  interfaces require specialization or formal comparison. Preprocessing alone
  does not make those files equal.
- Seven controls pass: the three actual FPGA views differ; an in-memory
  write-data XOR-one mutation differs; missing `endif`, unknown `include` and
  an undefined macro are rejected. No mutation was written to any source.

This projection is a restricted lexical check, not an HDL elaborator. Its next
independent control is pinned Verilator `-E -P` on the same ordered inputs and
defines, with output captured in new dated evidence, twice. Preserve every
five-file difference rather than dropping parameter-dependent logic.

The preserved [ASIC M9K check log](../asic/rf_bht_m9k_asic_checks.log) records
earlier Verilator token identity and the DM synthesis netlist's byte equality.
The preserved [SA2 FAST_HIT=0 source status](../asic/equiv/r16_eq/soc_sa2_4kb_soc_fast0.status)
reports 36,741 proven and zero unproven cells. Its
[recipe](../asic/equiv/r16_eq/soc_sa2_4kb_soc_fast0.ys) uses the signed source list,
the five updated files, the two N-way definitions and `async2sync`; the
[FAST_HIT=1 control](../asic/equiv/r16_eq/soc_sa2_4kb_soc_fast1s.status) retains
1,824 unproven cells. These historical checks support the source-change
boundary. They do not establish a fresh source-to-final-netlist sequential
proof or remove initialization/undefined-value obligations.

## Exact SA2 frontend paths and dependencies

Prepared commands, retained for a later isolated session:

```bash
bash /mnt/e/Projects/RISCV-research/results/completion_preparation_20261009/sa2_lec_20261009/p1/run_frontends.sh
bash /mnt/e/Projects/RISCV-research/results/completion_preparation_20261009/sa2_lec_20261009/p2/run_frontends.sh
```

The scripts use standalone Yosys
`/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys`
and replay Yosys
`/nix/store/zdhr86kv5rxlp0s58rzxk1aki1igankx-yosys-with-plugins-python3-3.11.9-env/bin/yosys`.
Their executable hashes/versions and the external TT Liberty must be captured
at runtime before a proof. This preparation does not assert that external
resources were revalidated.

The fresh replay must use the full-flow parent:

```text
asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1/06-yosys-synthesis/
```

Its `config.json`, `extra.json` and synthesis netlist are hash-checked. Its
filtered Liberty is present and matches the preparation receipt:

```text
asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1/tmp/1af08e0acee14c1dbe8777723b18b107.lib
```

Both signed ECO branches' `extra.json` refer to absent branch-local temporary
Liberty files. Do not substitute those paths or fabricate a library. The parent
synthesis netlist and both signed synthesis netlists remain byte-identical.
The existing single-hook N1 replay under
`asic/equiv/lec/synth_replay_r14/sa2_rsztf_r1_n1only/` is one execution, not a
second independent proof.

Gate frontends use the two signed final netlists:

```text
asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1/56-openroad-fillinsertion/soc_asic_top.nl.v
asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r2/56-openroad-fillinsertion/soc_asic_top.nl.v
```

They are byte-identical and instantiate **16 unique SRAM macros**: eight
32x512 main-RAM banks and eight 32x256 cache-data banks. Both named-pin maps
match; sanitized cut-instance names have no collision. The JSON stores all
instance names, pin order, connections and declared widths. All 11 functional
pins are present: `clk0`, `csb0`, `web0`, `wmask0`, `addr0`, `din0`, `dout0`,
`clk1`, `csb1`, `addr1`, `dout1`. Address width is 9 or 8 bits respectively;
write mask is 4 bits and data width is 32 bits.

This is a raw netlist inventory. A fresh cut still must prove every pin width,
bit order, clock polarity and any dropped no-connect output's lack of consumers.
The cut compares all macro inputs and supplies corresponding read outputs as
common arbitrary inputs. It does not prove analog SRAM timing or allow omitted
input pins. `sram_cut.py`'s old “12 SRAM” header is a historical description;
the actual SA2 boundary has 16 instances.

## Source-to-Boolean semantics still open

The [model/initialization audit](lec_model_initialization_audit_20261010.md)
identifies unreset register/tag/read-hold state and X/Z origins. Its 11,560
symbolic reset-D bits and the gold reset/clock/BDD subproofs describe **DM**;
those counts and pair maps must not be copied to SA2.

The signed synthesis configuration uses `SYNTH_TIE_UNDEFINED=low`; the preserved
synthesis helper also performs undefined-aware simplification and `setundef`.
The old SEC recipe's `setundef -zero -init` and `write_aiger -zinit` impose a
narrower initial-state premise. A proof on a zero-coerced Boolean AIG needs an
explicit source-to-model bridge before its invariants are transferred to the
unrestricted source.

Unreset GPRs, tag arrays and read-hold state require an explicit relation:
couple corresponding initial values as common arbitrary symbols, or prove a
validity-aware relation that makes stale data observationally irrelevant.
Neither approach assumes power-up zeros. For every undefined combinational
bit, preserve a nondeterministic value until its compared-output/state/macro-pin
influence is proved absent under independently established premises.

`async2sync` and D-only cuts additionally require reset-event correspondence:
external asynchronous assertion, the two-stage synchronized release, internal
reset distribution and each clock/update event. Equal D functions alone do not
prove these events. Component text identity or equal FSM group names likewise
does not transfer an older reachability proof to a new graph.

## Bounded experiment order

Only one hypothesis is tested at a time; each accepted result is independently
executed twice with semantic negative controls.

| next experiment | hypothesis and acceptance |
|---|---|
| Exact ASIC preprocessing | Confirm the three M9K changes disappear under the signed defines; independently capture ordered Verilator token outputs and hashes. Wrong FPGA view and copied write-data mutation must differ. Keep all five parameter-dependent differences explicit. |
| BHT update definedness | Slice the exact unrestricted pre-`setundef` two-bit update case. Enumerate Boolean selectors and show its default-X branch cannot influence an observed update. A copied missing-case control must expose that branch. This closes one local origin only. |
| One disabled write/unused-bit cone | Give one undefined bit two independent arbitrary values and prove all affected compared sinks agree under proved enable/invariant conditions. A copied enable mutation must expose influence. Every unresolved cone remains UNKNOWN. |
| Fresh raw SA2 frontend | After resources permit, pin tools/libraries and independently replay the same parent inputs in fresh p1/p2. Retain pre-simplification IR, every Q state, reset/update semantics and undefined symbols; generate SA2-specific interfaces and mappings. |
| Complete sequential closure | Close paired reset, exact-source invariant induction, clocks/events, every top/SRAM boundary and exact multiplier residuals before two independent complete final-netlist proofs. |

For the first small cone, proposed hard execution bounds are one worker,
512 MiB RAM, 250,000 nodes and 120 seconds. Reaching a bound means UNKNOWN with
preserved evidence; it never means PASS or permission to remove a target. These
are proposed experiment limits, not changes to PD sign-off gates.

Full SoC formal is run alone; measured EQY use is about 13 GB. No prepared
frontend is launched while PD or CRC jobs remain active. Before a later session,
measure Windows and WSL free memory, reserve space for the owner programs and
run one frontend at a time. No unmeasured frontend peak-RAM guarantee is made.

Remaining prerequisites: external tool/TT-Liberty runtime hashes; fresh raw
SA2 gold/N1/final graphs; the source-definedness bridge; SA2-specific reset and
FSM/constant/duplicate induction; complete macro-cut liveness/width checks;
fresh techmap-iteration-1 multiplier replay, signed33 algebra and exact CEC
links; semantic unsigned/partial-product/FSM/and2-to-or2 controls; and a runner
that records real native exits and distinguishes crash, timeout and UNKNOWN
from a valid negative-control counterexample. The existing prepared batches
finish at frontend generation and pairing; they do not implement this complete
acceptance chain.
