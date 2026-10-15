# VC4 post-routing read-only diagnosis

Main route produced an empty iteration45 DRC report and its reports were moved into `drc_iter_main`. The post-route loop is enabled for five rounds despite the `antoff` tag. No first-round completion marker, runtime receipt, or state_out exists at capture.

The sampled main thread consumed79.18userCPU seconds over79wall seconds; the other33threads were sleeping on futexes. This supports active serial computation. It does not identify the function/net or prove termination. No crash, proven hang, machine fault, or completed sign-off is inferred.

Completed SA2 detailed-routing phases took36m45.497s and34m32.522s, including antenna repair. Their rounds found653,55,13,2,0 violating nets and inserted1453,83,14,2 diodes. Their final explicit check returned0. The signed branches copied those original phase artifacts and are not extra executions.

The running Nix derivation pins [`edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6`](https://github.com/The-OpenROAD-Project/OpenROAD/blob/edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6/src/ant/src/AntennaChecker.cc); its GUI patch does not change antenna code. A different retained local checkout is not substituted as the running source. Ordinary summaries occur only after all nets complete. Polygon connectivity uses nested scans over per-net geometry and pins, so total wirelength alone is insufficient to predict cost.

No profiler is installed. `nm`/`readelf` confirm the actual wrapped executable is a PIE with antenna function symbols. A user-only, five-second software perf_event_open sampler is a possible next diagnostic, subject to a separate decision and a fail-closed permission check. It has not been executed.

The JSON receipt records source URLs/hashes, immutable comparator artifacts, actual configuration, observed process metadata, inference limits and the preserved earlier receipt hash. No running input or job was changed.
