# Current-gold sampled reset phase bridge

Two independent native runs prove all 1716 closures and reproduce every field and byte. Every reachable synchronizer phase after an established sampled reset base is covered, with arbitrary sampled external reset reassertion/release. The joint invariant retains all 235 constants, 28 duplicate equalities and four legal one-hot groups; all other raw state and inputs remain symbolic.

| External reset_n | Meta Q | Sync Q | Structural closures | CNF closures | UNKNOWN / counterexample |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 286 | 0 | 0 / 0 |
| 0 | 1 | 0 | 286 | 0 | 0 / 0 |
| 0 | 1 | 1 | 286 | 0 | 0 / 0 |
| 1 | 0 | 0 | 286 | 0 | 0 / 0 |
| 1 | 1 | 0 | 286 | 0 | 0 / 0 |
| 1 | 1 | 1 | 266 | 20 | 0 / 0 |

The raw equations are Dmeta=external_reset_n and Dsync=external_reset_n AND current_meta_Q. They preserve R=(not sync_Q) OR meta_Q. One sampled asserted edge establishes pair00 regardless of prior synchronizer state; the next sampled asserted edge invokes the pinned universal gold reset base. Initial pair01 is not assumed impossible before reset. No unreset RAM, tags or register array is assigned zero as an axiom.

This audit reconstructs all 1716 original conditional violations, checks literal-zero structural closures and replays every retained CNF resolution certificate without a new SAT solve. Premises are explicitly nonvacuous. Both actual semantic controls detect a rare 24-input in-memory Dsync fault during phase(0,1,1): original next pair00 becomes faulty01, with every I(Q) and R(Q) premise satisfied.

The result covers completed clock steps of the existing Boolean graph, including arbitrary external-reset changes between those steps. RTL asynchronous reset events between edges, the source X/Z-to-Boolean abstraction gap, raw GOLD-to-N1-to-final initial-state coupling and complete sequential LEC remain OPEN. Independent review is a separate pending receipt.

Actual proof processes were kernel-limited to512 MiB with10 seconds per obligation and fixed frozen CNF budgets. Both proof CLIs and both semantic control CLIs exited0. Complete proof process wall time was not captured when tool calls yielded and is not inferred from polling intervals. Input/source/artifact hashes and execution records are in the companion JSON.
