# Independent sampled reset-phase review

PASS on the existing raw-gold Boolean completed-clock-step model. All six phases
of R=(not syncQ) OR metaQ were independently reconstructed, with286 exact joint
targets in each phase and1716 per independent saved execution. There are1696
structural-zero targets and20 exact CNF targets per pass. Every saved CNF proof
is independently encoded and replayed for both passes. No actual SoC solve ran.

The original raw protocol equations were independently checked for all eight
external/meta/sync codes, including startup01: Dmeta=external and
Dsync=external AND meta. They establish00 on an asserted sampled edge and
preserve R for arbitrary later sampled external values. The already independently
reviewed reset base establishes I on a subsequent asserted sampled step. Both
free-state0/1 completions demonstrate premise nonvacuity only; neither imposes
zero initialization. The exact all-other-state-symbolic contract is retained.

Both rare24 actual-model controls were independently replayed through CNF and
original raw graph evaluation, satisfying I(Q) and R(Q), and changing next
meta/sync00 into01 solely through an in-memory copied Dsync mutation.

The sampled phase bridge is closed within this model and stated reset base.
Source undefined-to-zero abstraction, asynchronous events between clock edges,
raw N1/final reset coupling and full sequential LEC remain OPEN. This result
must not be described as complete chip equivalence or four-state RTL closure.
No source, old helper, PD input, global environment or prior evidence changed.
Detailed targets, hashes, counts and the hard256MiB process limit are recorded
in the adjacent JSON.
