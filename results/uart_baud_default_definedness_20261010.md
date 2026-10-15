# UART baud undefined-default local proof

Two independent sequential Windows CLI executions prove that the single
pre-`setundef` GOLD UART baud `$pmux` default is never selected for any
Boolean two-bit configuration code. Their receipts are byte-identical and
equal in every decoded field, with no ignored fields. Separate independent
method review is pending; the remaining-line delta is conditional until it
passes.

The original cell `$procmux$25626` at RTLIL line98143 has `WIDTH=16`,
`S_WIDTH=4`, and `A=16'x`. Its actual selector support is exactly the two
low bits of the original 32-bit `u_soc.u_uart.cfg_reg`. Unsigned equality
selectors, including the actual logic-not zero selector, cover all00,01,10,11
exactly once. The original module connection binds source `set_baud` to
that same `cfg_reg[1:0]` slice.

Both current and signed baud sources are byte-identical. Their exact
`always_comb` case at source lines39-48 defines the four16-bit divisors:
20832,10416,5207,433 respectively. The checker also confirms the original
UART parent-source port connections and default parameter instantiation.
Interpreting the actual64-bit B SigSpec with the actual selector bit order
reproduces those source values for all four codes.

All configuration codes are free; no initial value, reset, legal-state
relation or invariant is assumed. All16 undefined-default bits remain
arbitrary. Because exactly one selector is active, the output expression
contains the selected actual B word and none of the A bits. No X is coerced
to zero. This is a local two-state Boolean result; source/event behavior,
four-state equivalence, whole-source abstraction and full sequential LEC
remain open.

The new checker was frozen by its exact-input control receipt before the
two CLI executions. Its controls evaluate actual copied raw SigSpecs:

- Replacing only the actual code3 selector with constant0 makes code3
  select A. Arbitrary default values0 and65535 then produce those distinct
  mutated outputs.
- Reversing the actual selected16-bit B slice keeps exactly one selector
  active but changes the code3 output from433 to36224, which contradicts
  the exact source case.

No mutation is written to source or IR, and neither control claims a
mutated frontend correspondence or a reachable whole-chip trace. Both
successful proof processes exited0 and peaked below39MiB under a hard
256MiB process cap. No WSL, synthesis/frontend, solver, simulator, install,
RTL change or flow was started.

After independent method review passes, this closes one additional GOLD
functional X/Z connect line: locally closed lines257 to258, remaining
lines101 to100. Counts describe connect lines, not bits, hardware defects,
or global equivalence obligations. Other UART, Icache and SRAM default
origins are outside this single-target proof.

Evidence:

- [Frozen checker](../scripts/verification/check_uart_baud_default_definedness.py).
- [Controls and input freeze](uart_baud_definedness_controls_20261010.json)
  with [control script](../scripts/verification/check_uart_baud_definedness_controls.py).
- [Pass1](uart_baud_default_definedness_20261010_p1.json) and
  [pass2](uart_baud_default_definedness_20261010_p2.json).
- [Paired byte/field/hash audit](uart_baud_default_definedness_20261010_verification.json).
- [Native execution record](uart_baud_definedness_execution_20261010.json).
- [Earlier independent BHT review/classification](bht_definedness_independent_review_20261010.md).
