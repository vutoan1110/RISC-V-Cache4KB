# LEC model and initialization audit, 2026-10-10

This is a static source/model audit and bounded Boolean screening, not a complete LEC result. Full DM sequential RTL-to-final-netlist closure remains OPEN; SA2 final-netlist LEC remains unexecuted. The existing gold reset subproof and separate clock-domain/edge proof are retained unchanged. No RTL, sign-off threshold, prior evidence or running flow was changed.

## Reset and initial-state contract

The independently executed gold reset subproof fixes 7,251 paired D bits to zero and 279 to one. The remaining 11,560 stay symbolic, with this exact source classification:

| unreset state | bits |
|---|---:|
| I-cache tag memory | 5120 |
| D-cache tag memory | 5120 |
| Register array (32 physical 32-bit rows) | 1024 |
| I-cache SRAM held read data | 128 |
| D-cache SRAM held read data | 128 |
| I-cache synchronous tag read | 20 |
| D-cache synchronous tag read | 20 |

`asic/snapshots/rtl_r14/hdl/regfile.v:13` declares the array with no reset or initializer; its write process starts at line 15. x0 reads are hardwired zero. The tag arrays and tag-read registers similarly lack reset (`hdl/cache/icache_tag_ram.v:37` and `dcache_tag_ram.v:27`); separate valid vectors are reset. The SRAM adapter's `rd_hold_q` and `rd_live_q` at `asic/soc_dm_4kb/cache_data_ram_sram4.v:185` have no reset clause. `rd_live_q` updates from the read-enable and may settle during reset; no explicit reset on that source register is assumed here.

A full state-equality argument must couple corresponding unreset initial states as common arbitrary symbols and prove reset preserves the relation. An alternative validity-aware relation may allow independent stale cache contents, but must prove their observational irrelevance until valid/read. Neither requires guessing initial zeros. Legacy `asic/equiv/sec/miter.ys:19` uses `setundef -zero -init`, followed by `write_aiger -zinit` at line 26; that narrower initialized model does not establish universal arbitrary power-up equivalence.

## Undefined-value models

Counts below are functional `connect` lines containing X/Z, not bits, flops or defects. `attribute \src 0'x` metadata is excluded.

| raw flattened model | X/Z connect lines | classification |
|---|---:|---|
| gold_flat_r14.il | 358 | 324 $pmux, 7 $mux, 27 module connects|
| n1_flat_r14.il | 59 | 2 $_MUX_, 57 module connects|
| gate_flat_R14FA.il | 20800 | 19203 two-input UDP mux defaults and 1597 four-input UDP mux defaults|
| gate_flat_R14FB.il | 20800 | same categories, independently read|

The stable cell model `asic/soc_dm_4kb/formal_pdk.v` has SHA-256 `a895bb0fde320a4a95e6f0091e2aa76d7bc2fa2f335c7b0ad064df161ed69f84`. Exact local truth-table enumeration covers all 8 two-state inputs for each 2to1/2to1_N model and all 64 inputs for 4to2. No uncovered assignment, conflicting row or incorrect mux result exists. Thus the PDK model's default-X is unreachable for its own Boolean inputs. This local fact must still be linked to each instantiated cone; it is not a global four-state/undriven-signal audit.

In the gold model, 256 default-X $pmux lines originate in the complete 2-bit BHT update case, 49 in the AXI RAM wrapper, with the remaining cases in cache/UART/control logic. Seven $mux X connects include disabled register/tag-memory write data/address. Module connects include function temporaries and unused upper address bits. The N1 also has optimized-unused instruction/product/address/shift-temporary bits. These categories need cone and enable/observability checks before `setundef -undriven -zero`; the existing zero-coerced AIG `check -assert` cannot by itself establish that substitution is harmless.

The two N1 PC-low default-X muxes at lines 605115 and 605122 feed the low PC next-state path. The exact raw graph's write enable is `pipeline_advance AND other_enable AND (predict_redirect_f OR irq_flush OR pc_src_e)` (lines 411910-411931); the unknown branch is selected only if all three redirects are zero. Exhaustive local enumeration of 32 control assignments finds no enabled PC update with that branch selected. An occurrence scan finds no other consumers of the low `pc_next` bits beyond the IRQ mux feeding this enabled D path. This is a static local masking finding, not whole-chip equivalence.

## Current FSM restriction and older proof bridge

On the unrestricted current gold AIG, each of the 23 legal one-hot codes was assigned for its own group while reset was deasserted and every other state/input remained symbolic. Exact AND/NOT structural cofactoring reduces all three lcd_en_phase next-code violation functions to zero under those stated reset conditions. The other 20 obligations remain UNKNOWN (axi_last_grant 3, axi_source 3, alu_ctrl_e 14). These are local code screens; reset/protocol/source-bridge and independent-proof requirements remain. No counterexample or proof is inferred from UNKNOWN. Structural identities alone do not close the remaining three transition invariants.

The old/current snapshot files `controller.v`, `axi/cache_axi_master.v`, `lcd_1602_hex.v`, `datapath.v` and `alu.v` match byte-for-byte. `soc_top.v` and the ASIC wrapper differ. The older `asic/equiv/fsm_recode/front_end.ys:8` explicitly reads `rtl_r12b`. Identical local source files and identical group tables are useful for constructing a component/cone bridge, but do not prove whole-model identity or transfer the older `gold_inv.aig` invariant to the current source. Parameters, connected inputs and the actual recoded transition cones still need exact comparison or fresh proof.

## Concrete bounded next step

Create or interpret a fresh unrestricted raw N1/final graph exposing every paired D with independent Q inputs. Stream N1 scalar Boolean cells and aliases, assign corresponding unreset Q bits common arbitrary symbols, then cofactor reset only after proving the synchronizer protocol. Compare fixed D and symbolic reset relations with exact structural identities; keep unresolved cones UNKNOWN. For the final coarse graph, skip $scopeinfo metadata and bitblast only supported cell types under explicit node/RAM bounds. Slice the 23 FSM transition obligations for a later bounded exact BDD/SAT decision. Do not reuse restricted AR14/BR14 graphs as an independent base proof or force unreset states zero.

Every full acceptance still needs current-model invariant/undefined-cone closure, complete mapped output/SRAM boundaries and multiplier residual closure, semantic negative controls, and two independent complete proofs. This audit launched no external formal tools and did not execute the proposed paired-reset proof. Input hashes, per-origin counts and Boolean screen data are in the sibling JSON.
