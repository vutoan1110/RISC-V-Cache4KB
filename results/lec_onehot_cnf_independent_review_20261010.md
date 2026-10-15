# Independent review of bounded raw-model CNF proofs

PASS for the saved Boolean subobligations. Full sequential LEC and the
source-to-Boolean-model abstraction remain OPEN. This does not promote the
raw model into a full-chip RTL-to-PD proof.

The reviewer independently parsed the original binary AIG, retained every
unassigned raw Q/input as a free symbol, rebuilt each cofactored complemented-
edge DAG, encoded its one-hot violation into CNF, and replayed every saved
resolution derivation. No author parser, cofactor, resolution function, or
certificate verifier was used for those computations. The frozen author
encoder was compared against the independently constructed CNF and complete
variable map using a read-only adapter of each independently built cone.

All 14 ALU current codes in each of two independent saved executions passed:
28 terminal empty-clause certificates, each with 4958 variables and 12142
initial clauses. The paired proof receipts are byte- and field-identical.
Every recorded assignment was independently reconstructed from the raw state
partition: only external/internal deasserted resets and the group's own
current code were fixed; every other state/input remained free.

Both actual-model fault-control baseline certificates also passed replay.
The saved rare24-input counterexamples satisfy the independently built
mutated CNFs and their original raw-DAG evaluations. The baseline next code
has one active bit; the in-memory mutation has two. Source/AIG/RTL inputs did
not change.

Additional independent finite controls compare the frozen solver against
exhaustive enumeration on 256 two-variable CNF subsets, empty formula/clause,
2400 differently seeded random CNFs up to eight variables, and a learned
pigeonhole contradiction. Every UNSAT is replayed by the independent verifier;
every SAT assignment is checked against every original clause. Direct Boolean
formula truth tables test constants, complements, AND/OR/XOR and one-hot
encoding. Invalid certificates and malformed CNFs are rejected. Resource
limits stop computation; the public decision wrapper returns UNKNOWN.

Static kernel review covered signed literal/constant distinctions, watched
literal replacement, unit propagation, first-UIP conflict resolution,
asserting learned clauses, backtracking, exact proof replay and bounds. No
soundness defect was found in the reviewed saved proofs. This is not an
exhaustive proof of the solver for arbitrary inputs. A successful native
process return code means the bounded CLI completed; semantic acceptance must
inspect each case status and UNKNOWN count.

No new actual ALU solve, frontend, external formal tool or WSL process ran.
The process had a hard256MiB commit limit. Frozen source/evidence hashes were
checked before and after. Numeric details, memory observations, all control
rows and input digests are in the adjacent JSON receipt.
