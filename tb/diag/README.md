# Diagnostic probes

Second-top modules used to localise the ASIC-view failures of 2026-09-24
(see `NHAT_KY.md`, "2026-09-24 Dot sua RTL va view ASIC", 11:50 to 12:40). None of them is part of a regression; each
is elaborated next to tb_benchmark_snapshot by hand:

| File | Reports |
|---|---|
| `x_origin_probe.sv` | stores carrying X data; first X in a valid D-cache L0 line (both views) |
| `retire_trace_dump.sv` | the architectural retirement stream to a file, for diffing two builds |
| `addr_watch_probe.sv` | every CPU access to one word and its exact response (both views) |
| `ram_r_probe.sv` | ASIC main-memory R channel: X beats versus backpressure |
| `ram_word_probe.sv` | ASIC main memory: writes, stored value and read beats of one word |
| `dcache_line_probe.sv` | ASIC D-cache SRAM: writes, stored words and reads of one line |
