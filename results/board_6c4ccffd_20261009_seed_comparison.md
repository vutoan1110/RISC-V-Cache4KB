> SUPERSEDED: per-configuration seed selection was withdrawn before any fit or SOF build.
> Current method: common seeds 1..10; board seed 2 for all configurations.

# Board seed comparison

RTL: `6c4ccffd4257c224a537bd8d8e7b724ac8505bb19eb4d9e1361019af77341291`.

Independent Quartus passes: 16/16 rows identical on every field except elapsed time.
Approved policy: meet 50 MHz, minimise LE, then minimise total estimated power, then maximise Fmax.
Timing: Slow 1200 mV 85 C. Power: Quartus default toggle-rate estimate, not measured board power.

| configuration | seed | LE | Fmax, MHz | setup, ns | total power, mW | selected |
|---|---:|---:|---:|---:|---:|---|
| DM | 1 | 12823 | 55.18 | 1.876 | 254.94 |  |
| DM | 2 | 12815 | 52.27 | 0.87 | 255.48 |  |
| DM | 3 | 12810 | 55.52 | 1.987 | 255.53 | yes |
| DM | 4 | 12842 | 55.12 | 1.857 | 255.25 |  |
| SA2 | 1 | 16739 | 51.96 | 0.754 | 282.0 |  |
| SA2 | 2 | 16689 | 52.46 | 0.937 | 278.61 |  |
| SA2 | 3 | 16675 | 53.42 | 1.281 | 283.04 | yes |
| SA2 | 4 | 16735 | 52.48 | 0.945 | 280.67 |  |
| DM_VC4 | 1 | 17135 | 53.99 | 1.478 | 279.69 |  |
| DM_VC4 | 2 | 17130 | 54.29 | 1.58 | 278.64 | yes |
| DM_VC4 | 3 | 17130 | 54.09 | 1.511 | 282.35 |  |
| DM_VC4 | 4 | 17139 | 54.4 | 1.619 | 278.39 |  |
| DM_DSE | 1 | 14308 | 52.13 | 0.816 | 263.72 | yes |
| DM_DSE | 2 | 14340 | 55.21 | 1.887 | 264.76 |  |
| DM_DSE | 3 | 14353 | 54.54 | 1.665 | 267.77 |  |
| DM_DSE | 4 | 14364 | 53.75 | 1.395 | 262.46 |  |
