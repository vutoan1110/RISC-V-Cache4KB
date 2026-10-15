# Exact Boolean CNF hypothesis for current ALU transition invariants

One hypothesis: exact Tseitin CNF and bounded SAT search can decide the fourteen current `alu_ctrl_e` violation cones that exceeded the BDD support limit, without adding state or reachability assumptions.

Inputs are the same unrestricted-Q raw DM gold AIG, mapping and group specification as the paired Boolean cofactor checks. Only `reset_n=1`, both recorded reset synchronizer Q inputs equal 1, and the selected ALU group's own current one-hot code are assigned. Every other raw state/input remains symbolic, including gold-only constant candidates. The original AIG's undefined-zero source-model gap remains OPEN. No complete sequential LEC conclusion follows from this subproof.

No installed Windows SAT executable was found on PATH (minisat, cadical, kissat, glucose, cryptominisat5, picosat, z3, yices, boolector); Python has no z3, pysat, pyeda or pycosat module. No package, environment, binary or kernel setting will be changed.

The new internal solver uses watched-literal conflict-driven DPLL. Every learned clause must be an exact resolution of existing clauses, and terminal UNSAT requires an independently checked resolution derivation of the empty clause. SAT requires a full CNF assignment plus independent reevaluation of the original cofactored AND/NOT DAG and next-state code. Missing outputs, solver crashes, timeout and resource limits cannot count as either semantic verdict.

Bounds: 512 MiB on the new proof process only, 10 seconds per obligation, 10000 decisions/conflicts/learned clauses, 100000 resolution steps, 20000 CNF variables and 60000 input clauses. Hitting any bound yields UNKNOWN. Existing proof inputs/helpers, RTL, gates, PD/benchmark jobs and global settings stay unchanged.

Before actual execution, controls must compare the solver and Tseitin encoding against exhaustive small truth tables, detect a rare 24-input fault, reject corrupted resolution certificates and false witnesses, and detect a fault injected only in memory into an actually proved raw-model cone. Actual complete ALU computations and actual-model fault controls will execute twice independently and be compared field by field. Independent review remains necessary.
