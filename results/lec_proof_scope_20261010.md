# LEC proof scope, 2026-10-10

Full sequential RTL-to-final-netlist equivalence is not established by the current audit. Preserved DM combinational SAT/algebra/CEC closure remains valid evidence, with additional sequential premises still open. SA2 has preparation and a byte-exact N1 replay, but no completed final-netlist LEC.

New computation: two independent exact Boolean cofactor executions on the unrestricted raw DM gold AIG prove reset base for 235 constant flops, 28 duplicate relations and four one-hot groups. External reset alone forces both synchronizer D bits to zero; only then are internal reset-Q values used. All remaining inputs are symbolic. All 19,458 gold Q bits in the source cut connect directly to separate unrestricted inputs.

Of 19,090 paired gold D bits, reset fixes 7,251 to zero and 279 to one; 11,560 remain symbolic. The proof does not establish their raw N1/final reset relation, clock/update-event correspondence, or the exact-source bridge to the older invariant proof. No full-chip PASS is inferred.

Checker controls: two positive fixtures and 24 rejection controls, including an exact all-ones witness for a synthetic 24-input rare reset bug. These are checker fixtures, not measurements of the chip.

| proof obligation | preserved/current DM evidence | SA2 work remaining | status |
|---|---|---|---|
| Signed SA2 input and preparation provenance | Unchanged preserved evidence | 42 ordered RTL sources, 77 local input hashes and 24 generated hashes rechecked; 16 unique SRAM instances | PREPARATION_VERIFIED_ONLY |
| Fresh N1/frontends and FSM re-encoding in two passes | Historical execution on disk; exact current FSM proof bridge not established | Byte-exact existing N1 replay exists; p1/p2 contain scripts only, no new replay or frontend result | OPEN |
| Mapped state partitions and every ambiguous/unpaired bit | 19090 pairs, 368 gold-only; 28 ambiguity records corresponding to merged duplicates need explicit classification | SA2 pair maps/constants/duplicates not generated; must derive from SA2 rather than copy DM | OPEN_FOR_SA2 |
| Gold constant/duplicate/one-hot reset base | NEW independent cofactor executions: 235 constants + 28 duplicates + 4 groups universally proved on raw unrestricted gold | No raw SA2 graph; universal reset base not executed | DM_GOLD_SUBOBLIGATIONS_PROVED_ONLY |
| Paired reset relation and unspecified initial state | 7530 gold paired D bits fixed by reset; 11560 remain symbolic. Raw N1/final reset relation and initialization contract not established | Requires raw graph for both sides and all paired states; unknown states require justified relation or explicit contract | OPEN |
| Clock/update event correspondence | Legacy cuts omit clock/polarity from pair records; separate exact-input clock-domain/edge proof required | Must check every paired clock/edge through buffered/inverted clock cones; D equality alone is insufficient | OPEN |
| Invariant inductivity and actual recoded FSM reachability | Current group tables equal old spec7, but old gold_inv/inv_sat source/cone bridge is not established | Discover groups from actual SA2 encoding; prove reset + induction for all restrictions; reject empty/overlapping groups | OPEN |
| Complete output and SRAM-boundary classification | 20124 outputs: 20090 literal0 +34 algebra/CEC-closed residuals; each final:20096=20064 literal0+32 CEC residuals | Mapped cuts/SAT not executed. Compare all16 macro instances and every input pin name/width/order; read outputs common arbitrary inputs | HISTORICAL_DM_COMBINATIONAL_CLOSURE_ONLY |
| Multiplier closure tied to exact proof networks | Signed33 algebra and pure-network CEC/substitution logs preserved | Needs fresh SA2 techmap iteration-1 replay, byte link, gold techmap2 algebra, exact pure-cone CEC links, complete residual target names | OPEN_FOR_SA2 |
| Negative controls and process/integrity gates | Historical unsigned/partial-product failures and184 SAT counterexamples exist; NEW reset checker24 controls only | FSM encoding, unsigned spec, partial product and copied and2-to-or2 controls unexecuted; capture real process exit and semantic failure | OPEN_FOR_SA2 |
| Two independent full proofs and evidence comparison | Historical21/24 proof objects byteequal;3 reduced solver graphs differ as documented, semantic counts/verdicts unchanged. New reset-subproof p1=p2 | Two isolated preparation directories exist, no complete proof execution in either | FULL_SEQUENTIAL_CLOSURE_NOT_ESTABLISHED |

SA2 preparation hashes: all 77 local inputs and 24 generated scripts match the earlier receipt. The two folders still contain 12 scripts each; no frontend/replay result has been generated. The final netlists match byte-for-byte and instantiate 16 unique SRAMs. Retain the original full-flow synthesis Liberty input: signed ECO branches refer to absent tmp Liberty paths. External PDK TT Liberty and tool binaries still require runtime hashes before a future proof.

Historical DM output accounting: step A has 20,090 literal-zero outputs plus 34 residuals closed by multiplier algebra/CEC. Each final-netlist comparison has 20,064 literal-zero outputs plus 32 CEC-closed residuals. The three reduced solver AIGs differ from pass1 hashes, as already documented; the other 21 of 24 recorded proof objects match, including pairs, specification, named networks and residual target lists. Initial UNDECIDED messages in CEC logs are followed by final equivalent verdicts.

Legacy shell/PowerShell wrappers can mask native failure; a future runner must retain each real exit code and reject timeout/crash/unknown separately from a semantic negative-control counterexample. No unresolved output may be omitted. All restriction premises must be proved on the exact unrestricted source graph before acceptance.

PD DRC/LVS/timing sign-off and paired activity-power evidence remain unchanged. This audit does not allege an RTL defect. Full SA2 and remaining DM sequential obligations need actual proof work after resources permit.

Sources and SHA-256 hashes, actual new reset computation commands, and the full obligation matrix are recorded in `lec_proof_scope_20261010.json`.
