# Current DM ALU Boolean CNF subproof

The fourteen raw-model ALU next-state one-hot obligations are UNSAT under exactly the recorded reset-deasserted conditions and each own current one-hot code. Two independent native CLI invocations reproduce every field and byte. This audit reconstructs all fourteen original cones and separately replays their exact resolution derivations of the empty clause.

The original source's undefined-zero Boolean abstraction gap and full sequential RTL-to-netlist equivalence remain OPEN. No assumptions on other state groups, gold-only constant candidates or unreset memory contents were added. Independent kernel review is a separate pending receipt.

All cases contain 4958 CNF variables and 12142 initial clauses; the proof search used 694-762 decisions, 38-41 conflicts and 2538-2685 resolution steps per case. The process had a kernel-enforced 512 MiB limit and a 10-second deadline per obligation.

Twenty checker control groups include exhaustive small CNF/encoding truth tables, malformed resolution certificates and explicit UNKNOWN limits. Two independently executed actual-model controls prove the unchanged AXI baseline and detect an in-memory fault activating only when 24 free input bits all equal 1. At the raw-DAG witness the original code is `[1, 0, 0]` and the mutated code is `[1, 1, 0]`.

| Current ALU bit | Resolution steps |
|---:|---:|
| 0 | 2629 |
| 1 | 2569 |
| 2 | 2663 |
| 3 | 2685 |
| 4 | 2649 |
| 5 | 2645 |
| 6 | 2560 |
| 7 | 2631 |
| 8 | 2538 |
| 9 | 2648 |
| 10 | 2594 |
| 11 | 2593 |
| 12 | 2574 |
| 13 | 2565 |

Both actual native invocations exited 0. The second completed within the tool-reported 9.5508768 seconds. The first yielded its tool call; a complete native wall time was not captured and is not inferred from the polling interval.

Source, input, execution and control hashes are recorded in the companion JSON. The retained AIG and RTL files were not modified.
