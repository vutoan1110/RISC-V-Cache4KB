# Cloud session tasks (text only)

The cloud has no PD / simulation / LEC / Quartus tools and no run data: work on text files only, never on scripts,
configs, RTL or numbers that come from a receipt. Deliver each task as one commit on its own branch
`cloud/<task>`; the owner merges. Keep the language of each file: NHAT_KY / QUY_TRINH Vietnamese without diacritics
(ASCII), RESULTS / REVIEW_RESPONSE / PROJECT_STATE / README English.

Context: research copy of an RV32I + Zmmul SoC, 4 KiB caches, 16 KiB RAM; configurations DM, SA2, DM_VC4, DM_DSE
(SA4 FPGA only). Current RTL = manifest 6c4ccffd. Since 2026-10-14 every PD run reads snapshot `asic/snapshots/rtl_rfbht`
(= 6c4ccffd); everything that ran on older RTL is historical (`results/rtl_consistency_audit_20261014.md`). Owner rules:
`QUY_TRINH.md`; current state: `PROJECT_STATE.md`.

## Task 1 - NHAT_KY rewrite (owner 2026-10-14: shorter, more scientific, no overlap)

- Write `NHAT_KY_v2.md` next to `NHAT_KY.md`; do not delete or edit the old file.
- Structure by topic, not by hour:
  1. RTL revisions: one table (manifest, date, change, proof, chain result, status), then one short paragraph each;
  2. verification sets (TB, UVM, ACT4, random / Spike, Embench, CoreMark): what, how, result, on which RTL;
  3. FPGA and board;
  4. ASIC per configuration (DM, SA2, DM_VC4): a run table (name, change, result, cause), then the causes found;
  5. LEC; 6. activity power; 7. known issues (one paragraph each, from section 9); 8. rename table (section 11).
- Keep every number and evidence path still referenced by RESULTS.md / REVIEW_RESPONSE.md / PROJECT_STATE.md.
- Drop hour-by-hour operations (queues, locks, retries, waits) unless they changed a result.
- Machine faults: one short neutral sentence, never a claim of a proven hardware fault.
- Mark every result that ran on RTL older than 6c4ccffd as historical.

## Task 2 - documentation mismatches (from the owner-side provenance audit of 2026-10-14)

Fix the wording only:
- Broad "ASIC netlist identical byte for byte" wording lacks the R16 / current boundary and can imply identity with
  the old R14 PD netlist (R14 PD synthesis sha256 fc555d6b..., R16 / 6c4ccffd synthesis da06d38f...).
- Some README / review / state paragraphs still say board NOT_RUN or two physical passes. The session data: 42 cases
  measured, 41 displays confirmed, one scheduled physical pass, 58 cases left.
- RESULTS and REVIEW describe the 42 board cases as ramsweep plus 10 fully completed kernels plus statemate DM / SA2.
  The arithmetic is 4 ramsweep + 9 complete kernels x 4 + 2 statemate = 42, so "10" is wrong.
- Old review text says SA2 exact-window power is pending; the 2026-10-14 GLS / STA receipts are complete but bind the
  old signed SA2 layout (R14).
- The current ASIC snapshot has 47 files (44 + the three frozen SA2 / DM_VC4 wrappers); an earlier state paragraph
  says 44 - keep both with their dates.
- The process paragraph that keeps the 2026-10-13 "never resume" rule is superseded by QUY_TRINH's 2026-10-14 rule
  (development may resume from the failing step; acceptance = one complete clean flow from step 1).
- Distinguish the stock Yosys EQY failures from the completed custom register-mapped LEC proofs; a proof against R14
  gold is not a proof of a 6c4ccffd layout.
