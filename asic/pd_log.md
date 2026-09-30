
- START `dmdse_synth` (soc_dm_dse) args: ` --to Yosys.Synthesis` at 2026-09-16T18:59:27+00:00
- DONE `dmdse_synth` rc=0 last=`final` final/ present

- START `dmdse_synth_fixed` (soc_dm_dse) args: ` --to Yosys.Synthesis` at 2026-09-16T19:14:46+00:00
- STOP `dmdse_synth_fixed` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/nix/store/zdhr86kv5rxlp0s58rzxk1aki1igankx-yosys-with-plugins-python3-3.11.9-env/lib/yosys-`

- START `vc4_synth` (soc_vc4_check) args: ` --to Yosys.Synthesis` at 2026-09-16T19:40:36+00:00
- DONE `vc4_synth` rc=0 last=`final` final/ present

- START `dm_ctl_synth` (soc_dm_control) args: ` --to Yosys.Synthesis` at 2026-09-16T19:46:37+00:00
- DONE `dm_ctl_synth` rc=0 last=`final` final/ present

- START `vc1_probe` (soc_dse_vc1) args: ` --to Yosys.Synthesis` at 2026-09-16T20:07:42+00:00
- DONE `vc1_probe` rc=0 last=`final` final/ present

- START `dmdse_clean` (soc_dm_dse) args: ` --to Yosys.Synthesis` at 2026-09-16T20:12:54+00:00
- DONE `dmdse_clean` rc=0 last=`final` final/ present

- START `relaxed_30ns` (soc_dm_control) args: ` -c CLOCK_PERIOD=30` at 2026-09-17T06:56:59+00:00
- STOP `relaxed_30ns` rc=2 last=`55-magic-streamout` err: `Error while reading cell "sky130_fd_bd_sram__openram_dp_cell" (byte position 83930): Unknown layer/datatype in boundary, layer=33 type=42  Error while reading cell "sky130_fd_bd_sram__openram_dp_cell"`
- STOP `relaxed_30ns` treo o 55-magic-streamout sau khi 54-openroad-stapostpnr da xong; da lay duoc timing sau route

- START `frozen_30ns` (soc_frozen) args: ` -c CLOCK_PERIOD=30 --to OpenROAD.STAPostPNR` at 2026-09-17T10:39:41+00:00

- START `fixed_dm_full` (soc_dm_control) args: `full flow` at 2026-09-17T10:47:30+00:00

- START `fixed_dm_v2` (soc_dm_control) args: `full flow` at 2026-09-17T11:42:22+00:00
- STOP `fixed_dm_v2` rc=2 last=`47-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sanitized_synth` (soc_dm_control) args: ` --to Yosys.Synthesis` at 2026-09-17T14:43:39+00:00
- DONE `sanitized_synth` rc=0 last=`final` final/ present

- START `csb_fixed_synth` (soc_dm_control) args: ` --to Yosys.Synthesis` at 2026-09-17T15:16:07+00:00
- DONE `csb_fixed_synth` rc=0 last=`final` final/ present

- START `repeat_control` (soc_dm_control) args: ` --to Yosys.Synthesis` at 2026-09-17T15:22:19+00:00
- DONE `repeat_control` rc=0 last=`final` final/ present

- START `probe_csb2` (soc_dm_control) args: ` --to Yosys.Synthesis` at 2026-09-17T15:28:29+00:00
- DONE `probe_csb2` rc=0 last=`final` final/ present

- START `strat_area1` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_STRATEGY=AREA\ 1` at 2026-09-17T15:43:02+00:00
- DONE `strat_area1` rc=0 last=`final` final/ present

- START `strat_area2` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_STRATEGY=AREA\ 2` at 2026-09-17T15:51:44+00:00
- DONE `strat_area2` rc=0 last=`final` final/ present

- START `strat_area3` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_STRATEGY=AREA\ 3` at 2026-09-17T16:04:49+00:00
- DONE `strat_area3` rc=0 last=`final` final/ present

- START `strat_mfs3` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_ABC_USE_MFS3=true` at 2026-09-17T16:06:41+00:00
- DONE `strat_mfs3` rc=0 last=`final` final/ present

- START `nf_en` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_ABC_AREA_USE_NF=true` at 2026-09-17T16:12:44+00:00
- DONE `nf_en` rc=0 last=`final` final/ present

- START `a2_en` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_STRATEGY=AREA\ 2` at 2026-09-17T16:17:02+00:00
- DONE `a2_en` rc=0 last=`final` final/ present

- START `a2_br` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_STRATEGY=AREA\ 2` at 2026-09-17T16:29:36+00:00
- DONE `a2_br` rc=0 last=`final` final/ present

- START `a1_en` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_STRATEGY=AREA\ 1` at 2026-09-17T16:42:07+00:00
- DONE `a1_en` rc=0 last=`final` final/ present

- START `a1_br` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_STRATEGY=AREA\ 1` at 2026-09-17T16:50:26+00:00
- ODD `a1_br` rc=1 last=`06-yosys-synthesis` empty error.log, suspect a native crash

- START `hier_def_en` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_HIERARCHY_MODE=deferred_flatten` at 2026-09-17T17:00:24+00:00
- ODD `hier_def_en` rc=1 last=`06-yosys-synthesis` empty error.log, suspect a native crash

- START `hier_def_br` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_HIERARCHY_MODE=deferred_flatten` at 2026-09-17T17:01:53+00:00
- DONE `hier_def_br` rc=0 last=`final` final/ present

- START `share_off_en` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_SHARE_RESOURCES=false` at 2026-09-17T17:04:37+00:00
- DONE `share_off_en` rc=0 last=`final` final/ present

- START `share_off_br` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_SHARE_RESOURCES=false` at 2026-09-17T17:09:29+00:00
- DONE `share_off_br` rc=0 last=`final` final/ present

- START `hier_def_en2` (soc_dm_control) args: ` --to Yosys.Synthesis -c SYNTH_HIERARCHY_MODE=deferred_flatten` at 2026-09-17T17:14:51+00:00
- STOP `hier_def_en2` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): ABC RESULTS:        internal signals:     8291 ABC RESULTS:           input signals:     8239 ABC RESULTS:          output signals:     8320 Removing t`

- START `dedup_en` (soc_dm_control) args: ` --to Yosys.Synthesis` at 2026-09-17T17:15:45+00:00
- DONE `dedup_en` rc=0 last=`final` final/ present

- START `keep_en` (soc_dm_control) args: ` --to Yosys.Synthesis` at 2026-09-17T17:20:35+00:00
- DONE `keep_en` rc=0 last=`final` final/ present

- START `keep_br` (soc_dm_control) args: ` --to Yosys.Synthesis` at 2026-09-17T17:26:07+00:00
- DONE `keep_br` rc=0 last=`final` final/ present

- START `dedup_br` (soc_dm_control) args: ` --to Yosys.Synthesis` at 2026-09-17T17:31:02+00:00
- DONE `dedup_br` rc=0 last=`final` final/ present

- START `both_en` (soc_dm_control) args: ` --to Yosys.Synthesis` at 2026-09-17T17:35:54+00:00

- START `dedup_full` (soc_dm_control) args: `full flow` at 2026-09-17T17:38:20+00:00
- DONE `both_en` rc=0 last=`final` final/ present

- START `dedup_full` (soc_dm_control) args: `full flow` at 2026-09-17T17:42:59+00:00
- ODD `dedup_full` rc=2 last=`06-yosys-synthesis` empty error.log, suspect a native crash
- STOP `dedup_full` rc=2 last=`47-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_full` (soc_dm_control) args: `full flow` at 2026-09-17T20:24:07+00:00
- STOP `sync_full` rc=2 last=`37-openroad-globalrouting` err: `[GRT-0118] Routing congestion too high. Check the congestion heatmap in the GUI. `

- START `sync_full_d40` (soc_dm_control) args: ` -c PL_TARGET_DENSITY_PCT=40` at 2026-09-18T00:34:22+00:00
- ODD `sync_full_d40` rc=1 last=`37-openroad-globalrouting` empty error.log, suspect a native crash

- START `__pathcheck__` (soc_dm_control) args: ` --help` at 2026-09-18T02:39:59+00:00
- ODD `__pathcheck__` rc=141 last=`` empty error.log, suspect a native crash

- START `sync_d40` (soc_dm_control) args: ` -c PL_TARGET_DENSITY_PCT=40` at 2026-09-18T02:59:26+00:00
- STOP `sync_d40` rc=2 last=`37-openroad-globalrouting` err: `[GRT-0118] Routing congestion too high. Check the congestion heatmap in the GUI. `

- START `sync_corners` (soc_dm_control) args: `full flow` at 2026-09-18T03:22:28+00:00
- ODD `sync_corners` rc=1 last=`38-openroad-checkantennas` empty error.log, suspect a native crash

- START `sync_corners2` (soc_dm_control) args: ` --skip OpenROAD.CheckAntennas` at 2026-09-18T03:41:28+00:00
- ODD `sync_corners2` rc=143 last=`27-openroad-globalplacement` empty error.log, suspect a native crash

- START `sync_antenna` (soc_dm_control) args: `full flow` at 2026-09-18T03:52:19+00:00
- STOP `sync_antenna` rc=2 last=`47-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: `full flow` at 2026-09-18T04:57:02+00:00
- STOP `sync_final` rc=2 last=`47-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_local` (soc_dm_control) args: ` --from OpenROAD.CheckAntennas` at 2026-09-18T06:21:08+00:00
- ODD `sync_local` rc=1 last=`01-openroad-checkantennas` empty error.log, suspect a native crash

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T06:21:48+00:00
- STOP `sync_final` rc=2 last=`48-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T06:23:23+00:00
- STOP `sync_final` rc=2 last=`49-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T06:24:53+00:00
- STOP `sync_final` rc=2 last=`50-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T06:26:48+00:00
- STOP `sync_final` rc=2 last=`51-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T06:29:30+00:00
- STOP `sync_final` rc=1 last=`52-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T07:35:27+00:00
- STOP `sync_final` rc=2 last=`53-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T07:36:47+00:00
- STOP `sync_final` rc=2 last=`54-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: `full flow` at 2026-09-18T08:46:36+00:00
- STOP `sync_final` rc=2 last=`60-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: `full flow` at 2026-09-18T08:48:24+00:00
- STOP `sync_final` rc=1 last=`66-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T08:49:09+00:00
- STOP `sync_final` rc=1 last=`67-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T08:49:23+00:00
- STOP `sync_final` rc=2 last=`68-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T08:49:34+00:00
- STOP `sync_final` rc=2 last=`74-odb-cellfrequencytables` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.CellFrequencyTables` at 2026-09-18T08:50:35+00:00
- STOP `sync_final` rc=2 last=`75-odb-cellfrequencytables` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.CellFrequencyTables` at 2026-09-18T08:50:51+00:00
- STOP `sync_final` rc=2 last=`76-odb-cellfrequencytables` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.CellFrequencyTables` at 2026-09-18T08:51:09+00:00
- STOP `sync_final` rc=139 last=`76-odb-cellfrequencytables` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.CellFrequencyTables` at 2026-09-18T08:51:17+00:00
- STOP `sync_final` rc=2 last=`77-odb-cellfrequencytables` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Odb.CellFrequencyTables` at 2026-09-18T08:51:31+00:00
- STOP `sync_final` rc=2 last=`81-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T08:59:25+00:00
- STOP `sync_final` rc=2 last=`82-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T09:03:59+00:00
- STOP `sync_final` rc=2 last=`83-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T09:07:11+00:00
- STOP `sync_final` rc=2 last=`84-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T09:09:53+00:00
- STOP `sync_final` rc=2 last=`85-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T09:13:20+00:00
- STOP `sync_final` rc=2 last=`86-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T09:16:24+00:00
- STOP `sync_final` rc=2 last=`87-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T09:19:34+00:00
- STOP `sync_final` rc=2 last=`88-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T09:23:40+00:00
- STOP `sync_final` rc=2 last=`89-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T09:29:41+00:00

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T11:11:39+00:00
- STOP `sync_final` rc=2 last=`91-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T11:39:37+00:00
- STOP `sync_final` rc=1 last=`91-magic-streamout` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T11:39:48+00:00
- STOP `sync_final` rc=2 last=`96-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:47:11+00:00
- STOP `sync_final` rc=2 last=`97-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:47:23+00:00
- STOP `sync_final` rc=2 last=`98-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:47:35+00:00
- STOP `sync_final` rc=1 last=`98-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:47:38+00:00
- STOP `sync_final` rc=139 last=`98-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:47:42+00:00
- STOP `sync_final` rc=139 last=`98-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:47:46+00:00
- STOP `sync_final` rc=2 last=`99-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:47:59+00:00
- STOP `sync_final` rc=2 last=`99-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:48:07+00:00
- STOP `sync_final` rc=2 last=`99-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:48:17+00:00
- STOP `sync_final` rc=139 last=`99-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:48:21+00:00
- STOP `sync_final` rc=1 last=`99-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:48:28+00:00
- STOP `sync_final` rc=2 last=`99-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:48:37+00:00
- STOP `sync_final` rc=2 last=`99-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --from KLayout.XOR` at 2026-09-18T11:49:51+00:00
- STOP `sync_final` rc=1 last=`99-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --to Magic.StreamOut --from Magic.StreamOut` at 2026-09-18T11:50:03+00:00
- STOP `sync_final` rc=1 last=`99-klayout-xor` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/home/toanl/tools/openlane-patched/openlane/scripts/odbpy/reader.py", line 217, in wrapper     function(`

- START `sync_final` (soc_dm_control) args: ` --to Magic.StreamOut --from Magic.StreamOut` at 2026-09-18T11:50:16+00:00
- DONE `sync_final` rc=0 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:24:04+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:25:01+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:25:34+00:00
- DONE `sync_final` rc=139 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:26:01+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:27:02+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:27:55+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:28:48+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:29:48+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:30:47+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:31:14+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:31:30+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:31:44+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:32:00+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:32:15+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:32:31+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-18T12:32:47+00:00

- START `sync_final` (soc_dm_control) args: ` --from OpenROAD.STAPostPNR` at 2026-09-18T12:35:50+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.WriteLEF` at 2026-09-18T12:46:22+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.WriteLEF` at 2026-09-18T12:50:48+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.WriteLEF` at 2026-09-18T12:51:02+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.WriteLEF` at 2026-09-18T12:55:26+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.WriteLEF` at 2026-09-18T12:55:31+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.WriteLEF` at 2026-09-18T12:59:49+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.WriteLEF` at 2026-09-18T13:04:14+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.WriteLEF` at 2026-09-18T13:08:36+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.WriteLEF` at 2026-09-18T13:13:06+00:00

- START `sync_final` (soc_dm_control) args: ` --from Magic.WriteLEF` at 2026-09-18T13:14:32+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.DRC` at 2026-09-18T13:59:29+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.DRC` at 2026-09-18T14:36:29+00:00
- DONE `sync_final` rc=1 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.DRC` at 2026-09-18T14:36:35+00:00
- DONE `sync_final` rc=2 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.DRC` at 2026-09-18T15:17:00+00:00

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T15:18:34+00:00
- DONE `sync_final` rc=139 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.DRC` at 2026-09-18T15:18:40+00:00

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T15:20:16+00:00
- DONE `sync_final` rc=139 last=`final` final/ present

- START `sync_final` (soc_dm_control) args: ` --from Magic.StreamOut` at 2026-09-18T15:20:26+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-18T16:27:03+00:00
- STOP `synth4kb` rc=2 last=`03-checker-linterrors` err: `1 Lint errors found. `

- START `synth4kb` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-18T16:42:56+00:00
- STOP `synth4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/synth4kb/06-yosys-synthesis/AREA_0.abc'…  221. Executing ABC `

- START `synth4kb` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-18T16:44:21+00:00
- ODD `synth4kb` rc=1 last=`06-yosys-synthesis` empty error.log, suspect a native crash

- START `synth4kb` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-18T16:44:43+00:00
- DONE `synth4kb` rc=0 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:23:01+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:25:40+00:00
- ODD `fp4kb` rc=1 last=`` empty error.log, suspect a native crash

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:25:47+00:00
- STOP `fp4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): 66. Executing OPT_CLEAN pass (remove unused cells and wires). Finding unused cells or wires in module \soc_asic_top.. Removed 4129 unused cells and 128`

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:26:11+00:00
- STOP `fp4kb` rc=139 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): 66. Executing OPT_CLEAN pass (remove unused cells and wires). Finding unused cells or wires in module \soc_asic_top.. Removed 4129 unused cells and 128`

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:26:11+00:00
- ODD `fp4kb` rc=1 last=`06-yosys-synthesis` empty error.log, suspect a native crash

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:26:36+00:00
- STOP `fp4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/pyosys/synthesize.py", line 349, in `

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:27:16+00:00
- STOP `fp4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/nix/store/zdhr86kv5rxlp0s58rzxk1aki1igankx-yosys-with-plugins-python3-3.11.9-env/lib/yosys-`

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:28:19+00:00
- STOP `fp4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/pyosys/synthesize.py", line 349, in synthesize     openlane_synth(   File "`

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:28:44+00:00
- STOP `fp4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/pyosys/synthesize.py", line 349, in synthesize     openlane_synth(   File "`

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:29:18+00:00
- STOP `fp4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/06-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:30:24+00:00
- STOP `fp4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):   Creating internal representation of mux trees.   No muxes found in this module. Removed 0 multiplexer ports.  212.11. Executing OPT_REDUCE pass (cons`

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:31:17+00:00
- ODD `fp4kb` rc=1 last=`05-yosys-jsonheader` empty error.log, suspect a native crash

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:31:31+00:00
- ODD `fp4kb` rc=1 last=`06-yosys-synthesis` empty error.log, suspect a native crash

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:32:29+00:00
- STOP `fp4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/06-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `synthprobe` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-18T17:34:33+00:00
- STOP `synthprobe` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/pyosys/synthesize.py", line 349, in `

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:44:41+00:00
- ODD `fp4kb` rc=1 last=`27-openroad-globalplacement` empty error.log, suspect a native crash

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:53:32+00:00
- STOP `fp4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):   Optimizing cells in module \soc_asic_top. Performed a total of 0 changes.  101. Executing OPT_MERGE pass (detect identical cells). Finding identical `

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:53:50+00:00
- STOP `fp4kb` rc=2 last=`06-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/pyosys/synthesize.py", line 349, in `

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:54:23+00:00
- ODD `fp4kb` rc=139 last=`05-yosys-jsonheader` empty error.log, suspect a native crash

- START `fp4kb` (soc_dm_4kb) args: ` --to OpenROAD.GlobalPlacement` at 2026-09-18T17:54:31+00:00

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T17:55:28+00:00
- ODD `fp4kb` rc=1 last=`07-yosys-synthesis` empty error.log, suspect a native crash

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T17:55:58+00:00
- ODD `fp4kb` rc=1 last=`08-yosys-synthesis` empty error.log, suspect a native crash

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T17:56:19+00:00
- ODD `fp4kb` rc=1 last=`09-yosys-synthesis` empty error.log, suspect a native crash

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T17:56:39+00:00
- STOP `fp4kb` rc=2 last=`10-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/10-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T17:57:39+00:00
- STOP `fp4kb` rc=1 last=`11-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/10-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T17:58:01+00:00
- STOP `fp4kb` rc=1 last=`12-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/10-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T17:58:17+00:00
- STOP `fp4kb` rc=1 last=`13-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/10-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T17:58:30+00:00
- STOP `fp4kb` rc=2 last=`14-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/10-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T17:59:40+00:00
- STOP `fp4kb` rc=1 last=`14-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/10-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T17:59:42+00:00
- STOP `fp4kb` rc=2 last=`15-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/10-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T18:00:01+00:00
- STOP `fp4kb` rc=1 last=`16-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/10-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T18:00:17+00:00
- STOP `fp4kb` rc=2 last=`17-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/10-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `fp4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.GlobalPlacement` at 2026-09-18T18:00:38+00:00
- STOP `fp4kb` rc=2 last=`18-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s):  [INFO] Using generated ABC script '/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/fp4kb/10-yosys-synthesis/AREA_0.abc'…  221. Executing ABC pas`

- START `synth4kb` (soc_dm_4kb) args: ` --from Checker.YosysUnmappedCells --to OpenROAD.GlobalPlacement` at 2026-09-18T18:02:27+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from Checker.YosysUnmappedCells --to OpenROAD.GlobalPlacement` at 2026-09-18T18:12:00+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from Checker.YosysUnmappedCells --to OpenROAD.GlobalPlacement` at 2026-09-18T18:22:10+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from Checker.YosysUnmappedCells --to OpenROAD.GlobalPlacement` at 2026-09-18T18:30:14+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from Checker.YosysUnmappedCells --to OpenROAD.GlobalPlacement` at 2026-09-18T18:32:56+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from Checker.YosysUnmappedCells --to OpenROAD.GlobalPlacement` at 2026-09-18T18:34:29+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from Checker.YosysUnmappedCells --to OpenROAD.GlobalPlacement` at 2026-09-18T18:35:27+00:00
- DONE `synth4kb` rc=0 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from Odb.WriteVerilogHeader` at 2026-09-18T18:45:16+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:47:07+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:49:13+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:49:59+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:51:41+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:53:08+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:54:35+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:55:42+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:56:37+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:57:41+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:58:25+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T18:59:34+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:00:15+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:01:18+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:02:40+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:03:55+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:05:30+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalPlacement` at 2026-09-18T19:06:51+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:11:43+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:13:45+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:15:10+00:00
- DONE `synth4kb` rc=2 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:16:56+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:17:44+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T19:25:30+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.ResizerTimingPostCTS` at 2026-09-18T19:27:41+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.ResizerTimingPostCTS` at 2026-09-18T19:30:31+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T19:34:44+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T19:36:05+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T19:41:36+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T19:44:39+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T19:48:27+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T19:50:16+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T19:55:46+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T19:57:26+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:01:48+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:05:22+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:09:24+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:10:26+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:12:46+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:14:13+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:17:59+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:21:21+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:23:39+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:24:38+00:00
- DONE `synth4kb` rc=139 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:25:04+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:29:40+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:31:34+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:35:23+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:38:18+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:39:24+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:40:22+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:43:25+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:44:43+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:46:25+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:48:19+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:48:26+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:50:18+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:52:17+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:54:30+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:58:25+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:58:30+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T20:59:04+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T21:02:24+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T21:06:21+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.Floorplan` at 2026-09-18T21:07:18+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T21:09:16+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T21:16:23+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T21:17:38+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T21:20:32+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T21:22:42+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T21:24:21+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T21:26:27+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.Floorplan` at 2026-09-18T21:27:31+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL` at 2026-09-18T21:41:26+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.STAMidPNR` at 2026-09-18T21:47:44+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.STAMidPNR` at 2026-09-18T21:49:24+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS` at 2026-09-18T21:53:43+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS` at 2026-09-18T21:54:41+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.ResizerTimingPostCTS` at 2026-09-18T21:57:53+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:01:44+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:04:39+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:05:51+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:27:55+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:30:49+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:33:30+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:35:45+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:41:46+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:46:03+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:48:25+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:49:45+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:52:40+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:55:57+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T22:58:38+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:00:56+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:03:52+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:07:43+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:08:35+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:10:34+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:11:05+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:11:22+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:13:08+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:14:10+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:17:32+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:18:53+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:20:47+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting` at 2026-09-18T23:23:46+00:00

- START `synth4kb` (soc_dm_4kb) args: ` --from OpenROAD.Floorplan` at 2026-09-19T11:55:13+00:00
- DONE `synth4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --to OpenROAD.CTS` at 2026-09-19T11:56:41+00:00
- ODD `ch4kb` rc=139 last=`05-yosys-jsonheader` empty error.log, suspect a native crash

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.JsonHeader --to OpenROAD.CTS` at 2026-09-19T11:57:45+00:00
- ODD `ch4kb` rc=1 last=`07-yosys-synthesis` empty error.log, suspect a native crash

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:57:56+00:00
- ODD `ch4kb` rc=1 last=`08-yosys-synthesis` empty error.log, suspect a native crash

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:58:09+00:00
- ODD `ch4kb` rc=1 last=`09-yosys-synthesis` empty error.log, suspect a native crash

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:58:22+00:00
- STOP `ch4kb` rc=2 last=`10-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:58:28+00:00
- STOP `ch4kb` rc=1 last=`11-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:58:37+00:00
- STOP `ch4kb` rc=139 last=`11-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:58:42+00:00
- STOP `ch4kb` rc=1 last=`11-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:58:45+00:00
- STOP `ch4kb` rc=1 last=`11-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:58:48+00:00
- STOP `ch4kb` rc=139 last=`11-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:58:51+00:00
- STOP `ch4kb` rc=1 last=`12-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:59:21+00:00
- STOP `ch4kb` rc=1 last=`13-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:59:30+00:00
- STOP `ch4kb` rc=1 last=`14-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:59:50+00:00
- STOP `ch4kb` rc=1 last=`15-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:59:55+00:00
- STOP `ch4kb` rc=1 last=`16-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T11:59:59+00:00
- STOP `ch4kb` rc=2 last=`17-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:00:04+00:00
- STOP `ch4kb` rc=2 last=`18-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:00:17+00:00
- STOP `ch4kb` rc=139 last=`19-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:00:21+00:00
- STOP `ch4kb` rc=1 last=`20-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:00:28+00:00
- STOP `ch4kb` rc=1 last=`21-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:00:36+00:00
- STOP `ch4kb` rc=139 last=`22-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:00:40+00:00
- STOP `ch4kb` rc=139 last=`22-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:00:43+00:00
- STOP `ch4kb` rc=139 last=`22-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:00:46+00:00
- STOP `ch4kb` rc=1 last=`23-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:08+00:00
- STOP `ch4kb` rc=1 last=`24-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:17+00:00
- STOP `ch4kb` rc=1 last=`24-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:20+00:00
- STOP `ch4kb` rc=2 last=`25-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:28+00:00
- STOP `ch4kb` rc=1 last=`26-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:37+00:00
- STOP `ch4kb` rc=139 last=`26-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:38+00:00
- STOP `ch4kb` rc=1 last=`26-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:41+00:00
- STOP `ch4kb` rc=1 last=`26-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:44+00:00
- STOP `ch4kb` rc=139 last=`26-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:47+00:00
- STOP `ch4kb` rc=1 last=`27-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:54+00:00
- STOP `ch4kb` rc=139 last=`27-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:01:57+00:00
- STOP `ch4kb` rc=139 last=`28-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:02:01+00:00
- STOP `ch4kb` rc=1 last=`29-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:02:10+00:00
- STOP `ch4kb` rc=1 last=`30-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:02:15+00:00
- STOP `ch4kb` rc=139 last=`30-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:02:18+00:00
- STOP `ch4kb` rc=2 last=`31-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:02:22+00:00
- STOP `ch4kb` rc=139 last=`31-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.Synthesis --to OpenROAD.CTS` at 2026-09-19T12:02:25+00:00
- STOP `ch4kb` rc=139 last=`32-yosys-synthesis` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `t1fresh` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-19T12:02:52+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from Checker.YosysUnmappedCells --to OpenROAD.CTS` at 2026-09-19T12:04:17+00:00
- ODD `t1fresh` rc=1 last=`06-yosys-synthesis` empty error.log, suspect a native crash
- STOP `ch4kb` rc=1 last=`50-openroad-globalplacementskipio` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalPlacementSkipIO --to OpenROAD.CTS` at 2026-09-19T12:06:03+00:00
- STOP `ch4kb` rc=1 last=`53-odb-customioplacement` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:06:33+00:00
- STOP `ch4kb` rc=139 last=`53-odb-customioplacement` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:06:38+00:00
- STOP `ch4kb` rc=1 last=`54-odb-customioplacement` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:06:48+00:00
- STOP `ch4kb` rc=1 last=`54-odb-customioplacement` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:06:58+00:00
- STOP `ch4kb` rc=1 last=`54-odb-customioplacement` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:07:08+00:00
- STOP `ch4kb` rc=139 last=`54-odb-customioplacement` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:07:16+00:00
- STOP `ch4kb` rc=1 last=`54-odb-customioplacement` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:07:24+00:00
- STOP `ch4kb` rc=2 last=`55-odb-customioplacement` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:07:36+00:00
- STOP `ch4kb` rc=1 last=`55-odb-customioplacement` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:07:50+00:00
- STOP `ch4kb` rc=2 last=`56-odb-customioplacement` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:08:01+00:00
- STOP `ch4kb` rc=1 last=`62-openroad-stamidpnr` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.STAMidPNR --to OpenROAD.CTS` at 2026-09-19T12:09:28+00:00
- STOP `ch4kb` rc=139 last=`63-openroad-stamidpnr` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.STAMidPNR --to OpenROAD.CTS` at 2026-09-19T12:09:45+00:00
- STOP `ch4kb` rc=1 last=`64-openroad-stamidpnr` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.STAMidPNR --to OpenROAD.CTS` at 2026-09-19T12:10:33+00:00
- STOP `ch4kb` rc=1 last=`65-openroad-stamidpnr` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.STAMidPNR --to OpenROAD.CTS` at 2026-09-19T12:10:51+00:00
- STOP `ch4kb` rc=143 last=`66-openroad-stamidpnr` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.STAMidPNR --to OpenROAD.CTS` at 2026-09-19T12:17:06+00:00
- STOP `ch4kb` rc=1 last=`68-openroad-repairdesignpostgpl` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL --to OpenROAD.CTS` at 2026-09-19T12:18:21+00:00
- STOP `ch4kb` rc=143 last=`69-openroad-repairdesignpostgpl` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL --to OpenROAD.CTS` at 2026-09-19T12:24:00+00:00
- STOP `ch4kb` rc=1 last=`70-openroad-repairdesignpostgpl` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL --to OpenROAD.CTS` at 2026-09-19T12:24:41+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGPL --to OpenROAD.CTS` at 2026-09-19T12:25:58+00:00
- STOP `ch4kb` rc=1 last=`75-openroad-cts` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS --to OpenROAD.CTS` at 2026-09-19T12:27:38+00:00
- STOP `ch4kb` rc=1 last=`75-openroad-cts` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS --to OpenROAD.CTS` at 2026-09-19T12:27:52+00:00
- STOP `ch4kb` rc=1 last=`76-openroad-cts` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS --to OpenROAD.CTS` at 2026-09-19T12:28:19+00:00
- STOP `ch4kb` rc=1 last=`77-openroad-cts` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS --to OpenROAD.CTS` at 2026-09-19T12:28:44+00:00
- STOP `ch4kb` rc=139 last=`77-openroad-cts` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS --to OpenROAD.CTS` at 2026-09-19T12:29:03+00:00
- STOP `ch4kb` rc=1 last=`78-openroad-cts` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS --to OpenROAD.CTS` at 2026-09-19T12:29:28+00:00
- STOP `ch4kb` rc=139 last=`78-openroad-cts` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS --to OpenROAD.CTS` at 2026-09-19T12:29:44+00:00
- STOP `ch4kb` rc=1 last=`79-openroad-cts` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS --to OpenROAD.CTS` at 2026-09-19T12:30:10+00:00
- STOP `ch4kb` rc=1 last=`80-openroad-cts` err: `Subprocess had a non-zero exit. Last 10 line(s): Found and cleaned up 1 empty switch in `\maindec.$proc$/mnt/e/Projects/RISCV-research/hdl/maindec.v:17$6746'. Removing empty process `maindec.$proc$/mn`

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS --to OpenROAD.CTS` at 2026-09-19T12:30:39+00:00
- DONE `ch4kb` rc=0 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.Floorplan --to OpenROAD.CTS` at 2026-09-19T12:42:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ManualMacroPlacement --to OpenROAD.CTS` at 2026-09-19T12:42:51+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.CustomIOPlacement --to OpenROAD.CTS` at 2026-09-19T12:44:00+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalPlacement --to OpenROAD.CTS` at 2026-09-19T12:45:30+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:16:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:16:19+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:17:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:17:49+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:17:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:18:27+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:18:34+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:18:35+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:19:26+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:20:09+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:20:43+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:21:16+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:21:56+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:21:59+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:22:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:23:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:23:53+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:23:59+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:24:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:25:18+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:25:21+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:25:53+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:26:25+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:27:34+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:28:06+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:28:39+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:29:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:29:51+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:30:29+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:31:22+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:31:56+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:32:29+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:33:17+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:33:21+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:33:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:34:28+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:35:20+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:35:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:36:28+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:37:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:37:51+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:38:28+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:39:20+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:39:56+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:40:00+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:40:33+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:41:16+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:41:57+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:42:37+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:43:19+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:44:06+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:45:24+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:46:01+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:46:41+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:47:28+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:48:11+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:49:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:49:23+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T13:49:27+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:13:16+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:14:24+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:15:24+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:16:11+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:17:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:18:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:18:45+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:19:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:19:54+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:20:26+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:21:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:21:53+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:22:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:23:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:23:53+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:24:20+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:25:16+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:25:20+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:25:23+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:25:34+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:26:07+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:26:10+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:26:39+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:26:42+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:27:21+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:28:09+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:28:44+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:34:21+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:35:20+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:35:54+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:35:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:36:30+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:37:23+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:42:26+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:43:19+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:43:52+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:44:41+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:45:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:45:54+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:45:57+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:46:00+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:46:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:47:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:47:51+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:48:26+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:48:29+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:48:34+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:48:37+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:48:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:49:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:49:54+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:50:27+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:50:33+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:50:37+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:56:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:57:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:58:07+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to Misc.ReportManufacturability` at 2026-09-19T14:59:41+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:00:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:01:20+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:01:26+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:01:34+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:01:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:02:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:02:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:03:22+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:03:27+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:03:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:03:47+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:04:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:05:24+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:06:03+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-19T15:24:37+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGRT --to Misc.ReportManufacturability` at 2026-09-19T15:26:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGRT --to Misc.ReportManufacturability` at 2026-09-19T15:27:42+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGRT --to Misc.ReportManufacturability` at 2026-09-19T15:28:22+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGRT --to Misc.ReportManufacturability` at 2026-09-19T15:29:30+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGRT --to Misc.ReportManufacturability` at 2026-09-19T15:30:15+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGRT --to Misc.ReportManufacturability` at 2026-09-19T15:31:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGRT --to Misc.ReportManufacturability` at 2026-09-19T15:31:24+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGRT --to Misc.ReportManufacturability` at 2026-09-19T15:32:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGRT --to Misc.ReportManufacturability` at 2026-09-19T15:32:44+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairDesignPostGRT --to Misc.ReportManufacturability` at 2026-09-19T15:32:48+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to Misc.ReportManufacturability` at 2026-09-22T16:49:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.ResizerTimingPostGRT --to Misc.ReportManufacturability` at 2026-09-22T17:02:50+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.ResizerTimingPostGRT --to Misc.ReportManufacturability` at 2026-09-22T17:21:53+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.ResizerTimingPostGRT --to Misc.ReportManufacturability` at 2026-09-22T17:25:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.ResizerTimingPostGRT --to Misc.ReportManufacturability` at 2026-09-22T17:33:29+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.STAMidPNR --to Misc.ReportManufacturability` at 2026-09-22T17:54:10+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.DetailedRouting --to Misc.ReportManufacturability` at 2026-09-22T18:03:15+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-22T18:12:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CheckAntennas --to Misc.ReportManufacturability` at 2026-09-22T18:12:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Checker.TrDRC --to Misc.ReportManufacturability` at 2026-09-22T18:13:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:14:10+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:14:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:14:36+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:14:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:14:45+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:14:56+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:15:01+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:15:05+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:15:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:15:26+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:15:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:15:50+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:16:02+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:16:14+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:16:25+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:16:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:16:44+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:16:52+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:00+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:04+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:11+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:15+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:19+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:23+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:27+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:36+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:47+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:17:52+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:18:03+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:18:10+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:18:14+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:18:21+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:18:32+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:18:39+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:18:45+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:18:50+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:18:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:19:06+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:19:10+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:19:21+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:19:27+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:19:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:19:44+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:19:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:20:01+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:20:05+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:20:11+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:20:15+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:20:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:21:58+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:22:09+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:22:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:22:33+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:22:45+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:22:51+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:22:56+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:23:05+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:23:15+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:23:20+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:23:26+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:23:36+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:23:43+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:23:47+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:23:58+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:24:03+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:24:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:24:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:24:29+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:24:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:24:51+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:25:01+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:25:05+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:25:09+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:25:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:25:23+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:25:34+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:25:45+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:25:49+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:25:53+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:25:58+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:26:03+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:26:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:26:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:26:24+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:26:35+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:26:41+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:26:45+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:26:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:27:07+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:27:15+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-22T18:27:20+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-23T06:25:13+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T06:31:23+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T06:36:32+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T06:41:41+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T06:49:54+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T06:58:01+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T07:05:51+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T07:13:41+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T07:21:41+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T07:29:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T07:37:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T07:45:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T07:53:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T08:01:35+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T08:09:37+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T08:17:49+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T08:25:49+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T08:33:48+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T08:42:03+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T08:50:03+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T08:58:07+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T09:06:11+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T09:14:11+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T09:22:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T09:30:27+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T09:38:31+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T09:46:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T09:54:53+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T09:55:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T10:03:24+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T10:11:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T10:19:32+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T10:27:46+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport --to Misc.ReportManufacturability` at 2026-09-23T10:36:02+00:00
- DONE `ch4kb` rc=137 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Magic.StreamOut --to Misc.ReportManufacturability` at 2026-09-23T10:38:23+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Checker.MagicDRC --to Misc.ReportManufacturability` at 2026-09-23T12:45:23+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T12:58:54+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T12:59:37+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:00:14+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:00:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:00:59+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:01:16+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:01:25+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:01:44+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:01:50+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:02:07+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:02:25+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:02:36+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:02:54+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:03:04+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:03:21+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:03:27+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:03:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:03:44+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:03:47+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:04:05+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:04:23+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:04:37+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:04:50+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:04:58+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:05:05+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:05:09+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:05:28+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:05:47+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:05:52+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:06:01+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:06:06+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:06:26+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:06:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:07:04+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:07:15+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:07:21+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:07:28+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:07:37+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:07:43+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:07:57+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:08:11+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:08:32+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:08:52+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:09:04+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:09:25+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:09:35+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:09:43+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:09:50+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:10:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:10:09+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:10:21+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:10:41+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:10:49+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:10:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:11:07+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:11:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:11:34+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:11:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:11:47+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:11:53+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:12:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:12:37+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:12:43+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:13:05+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:13:28+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:13:46+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:14:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:14:16+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:14:38+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:14:51+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:14:58+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:15:23+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:15:29+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:15:42+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:15:57+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:16:10+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:16:16+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:16:39+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:16:48+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:16:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:17:17+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:17:24+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:17:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:17:38+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:17:47+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:17:58+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:18:09+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:18:19+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:18:33+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:18:57+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:19:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:19:15+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:19:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:19:45+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:20:10+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:20:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:20:29+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:20:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:20:56+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:21:13+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:21:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:21:54+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:22:18+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:22:43+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:23:01+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:23:11+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:23:37+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:23:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:24:10+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:24:17+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:24:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:25:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:25:18+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:25:24+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:25:50+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:26:01+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:26:27+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:26:54+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:27:02+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:27:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:27:18+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:27:44+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:27:55+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:28:11+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:28:33+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:28:40+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:29:00+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:29:25+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:29:52+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:29:59+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:30:27+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:30:34+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:30:41+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:30:48+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:30:56+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:31:07+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:31:14+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:31:39+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:32:07+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:32:36+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:32:44+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:32:52+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:33:01+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:33:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:33:21+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:33:29+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:33:58+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:34:04+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:34:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:34:39+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:35:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:35:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:35:33+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:35:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:36:08+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:36:35+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:36:48+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:37:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:37:31+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:38:01+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:38:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:38:39+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:39:09+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:39:16+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:39:24+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:39:31+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:39:42+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:39:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:40:27+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:40:57+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:41:05+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:41:31+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:42:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:42:27+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:42:40+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:43:03+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:43:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:43:24+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:43:55+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:44:09+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:44:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:45:01+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:45:12+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:45:30+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:45:45+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:45:53+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:46:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:46:26+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:46:57+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:47:05+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:47:37+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:47:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:48:17+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:48:48+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:48:59+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:49:07+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:49:22+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Misc.ReportManufacturability` at 2026-09-23T13:49:39+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:27:25+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:28:05+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:28:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:28:50+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:29:06+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:29:18+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:29:52+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:30:04+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:30:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:30:23+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:30:31+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:31:09+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:31:20+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:31:26+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:31:48+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:31:54+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:32:01+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:32:12+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:32:24+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:32:30+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:32:39+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:33:08+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:33:14+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:33:28+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:33:37+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:33:49+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:34:02+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:34:11+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:34:17+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T14:34:25+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:01:03+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:01:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:06:18+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:06:58+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:07:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:07:25+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:12:17+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:17:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:17:54+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:18:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:18:24+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:18:32+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:18:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:23:41+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:24:25+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:25:26+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:30:45+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:31:25+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:31:36+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:36:45+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:44:06+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:44:36+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:45:09+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:45:21+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:45:27+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:45:41+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Yosys.EQY --to Yosys.EQY` at 2026-09-23T16:46:03+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.CTS --to OpenROAD.STAPostPNR` at 2026-09-23T16:49:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to OpenROAD.STAPostPNR` at 2026-09-23T17:16:19+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.STAMidPNR --to OpenROAD.STAPostPNR` at 2026-09-23T17:16:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.ResizerTimingPostCTS --to OpenROAD.STAPostPNR` at 2026-09-23T17:22:09+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:07:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:07:36+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:08:01+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:08:07+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:08:23+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:08:33+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:09:10+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:09:22+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:09:36+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:10:14+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:10:52+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:11:16+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:11:25+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:11:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:12:28+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:12:41+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:12:48+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:13:05+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:13:12+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:13:22+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:13:28+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:13:42+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:14:01+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:14:28+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:14:37+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:14:48+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:15:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:15:33+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:15:39+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:15:51+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:16:29+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:16:50+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:17:11+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:17:23+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:17:41+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:18:22+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:18:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:19:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:19:10+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:19:18+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:19:24+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:20:12+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:20:46+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:20:54+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:21:06+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:21:14+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:21:27+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:21:44+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:21:53+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:22:05+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:22:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:22:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:22:54+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:23:15+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:23:22+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:23:30+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:24:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:24:19+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:24:52+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:25:04+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:25:16+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:25:49+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:25:56+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:26:06+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:26:21+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:26:34+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:26:48+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:27:06+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:27:12+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:27:20+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:27:27+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:27:41+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:27:50+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:27:59+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:28:15+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:28:26+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:28:52+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:29:03+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:29:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:29:19+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:29:27+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:29:36+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:29:54+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:30:16+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:30:22+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:30:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:31:05+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:31:17+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:31:27+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:32:10+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:32:27+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:32:54+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:33:04+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:33:12+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:33:31+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:34:12+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:34:20+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:35:00+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:35:09+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:35:19+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:35:25+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:35:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:36:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:36:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:37:04+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:37:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:37:19+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:37:29+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:38:04+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:38:29+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:38:47+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:38:56+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:39:03+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:39:11+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:39:28+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:39:43+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:39:50+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:40:05+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:40:48+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:40:57+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:41:11+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:41:18+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:41:28+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:42:16+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:42:23+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:42:41+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:42:52+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:43:30+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:43:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:43:54+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:44:32+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:45:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:45:25+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:45:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:45:48+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:45:54+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:46:33+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:46:46+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:47:16+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:47:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:48:35+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:48:43+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:49:09+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:49:20+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T18:49:48+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:52:30+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:52:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:53:04+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:53:21+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:55:05+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:55:16+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:55:22+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:55:30+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:55:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:57:26+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:59:10+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:59:20+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:59:27+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:59:34+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T18:59:47+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:00:02+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:00:24+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:00:35+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:00:48+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:00:58+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:01:05+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:01:12+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:01:33+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:03:26+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:03:49+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:03:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:05:39+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:07:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:09:07+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:09:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:09:24+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:09:38+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:09:46+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:09:58+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:10:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:11:59+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:12:23+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:12:33+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:14:01+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:14:14+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:14:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:14:42+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:14:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:15:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:15:16+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:15:24+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:15:50+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:16:01+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:16:12+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:16:19+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:16:27+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-23T19:16:39+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:18:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:18:51+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:40:45+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:41:27+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:41:39+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:41:46+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:41:58+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:42:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:42:24+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:42:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:42:56+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:43:03+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:43:15+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:43:26+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:43:33+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:44:04+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:44:11+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:44:18+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:44:29+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:44:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:44:47+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:45:02+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:45:10+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:45:33+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:45:45+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:45:52+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:45:59+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:46:12+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:46:20+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:46:26+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:46:40+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:46:48+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:47:05+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:47:12+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:47:22+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:47:32+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:47:41+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:47:57+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:48:16+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:48:24+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:48:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:48:42+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:48:49+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:49:02+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:49:13+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:49:23+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:49:30+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:49:43+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:50:29+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:50:36+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:50:58+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:51:05+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:51:15+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:51:22+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:52:04+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:52:15+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:52:43+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:52:50+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:52:59+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:53:10+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:53:21+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:53:29+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:53:36+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:53:48+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:53:54+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:54:10+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:54:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:54:26+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:54:33+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:54:44+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:55:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:55:14+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:55:23+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:55:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:55:37+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:55:45+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:55:55+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:56:17+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:56:23+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:56:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:56:49+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:56:57+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:57:08+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:57:14+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:57:25+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:57:38+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:57:49+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:58:00+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:58:12+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:58:22+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:58:34+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:58:42+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:58:54+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T19:59:05+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.DiodesOnPorts --to OpenROAD.STAPostPNR` at 2026-09-23T20:03:46+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.DiodesOnPorts --to OpenROAD.STAPostPNR` at 2026-09-23T20:04:28+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.DiodesOnPorts --to OpenROAD.STAPostPNR` at 2026-09-23T20:05:08+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:07:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:09:29+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:11:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:12:57+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:13:08+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:14:51+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:16:34+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:17:01+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:18:55+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:20:39+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:22:23+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:24:07+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:25:48+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:27:31+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:29:16+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:30:57+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:32:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:34:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:36:04+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:37:47+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:39:31+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:39:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:41:28+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:43:17+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:44:59+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:46:43+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:48:27+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:50:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:52:06+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:53:51+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:54:18+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:55:59+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:57:43+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T20:59:27+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:01:14+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:02:57+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:04:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:06:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:08:05+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:09:49+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:09:57+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:11:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:13:38+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:15:23+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:17:08+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:18:57+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:19:13+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:20:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:22:38+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:24:21+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:26:05+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:27:48+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:28:06+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:29:50+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:31:35+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:33:31+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:35:14+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:36:57+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:38:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:40:26+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:41:02+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:41:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:42:57+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:43:17+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:45:02+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:46:49+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:48:32+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:50:17+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:52:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:54:02+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:55:47+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:57:30+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T21:59:16+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:01:01+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:02:46+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:04:33+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:06:17+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:08:01+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:09:45+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:11:33+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:13:27+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:15:12+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:16:27+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:18:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:20:02+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:21:48+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:23:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:25:25+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:27:09+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:28:52+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:30:38+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:32:33+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:34:17+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:36:02+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:37:45+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:39:29+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:41:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:43:01+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:43:07+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:43:23+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:45:07+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:46:52+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:48:36+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:50:19+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:52:08+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:53:52+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:55:37+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:57:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T22:59:06+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:00:51+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:02:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:04:28+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:06:11+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:07:54+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:09:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:11:26+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:13:13+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:14:57+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:16:43+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:17:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:18:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:20:50+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:22:49+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:24:34+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:26:19+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:28:03+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:29:48+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:31:33+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:31:59+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:34:04+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:35:53+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:37:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:39:24+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:41:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:42:57+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:44:43+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:46:30+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:48:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:50:00+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:51:47+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:53:47+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:55:30+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:57:14+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:58:59+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-23T23:59:11+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:00:56+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:01:03+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:03:01+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:04:46+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:06:29+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:08:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:10:02+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:11:47+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:13:45+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:15:31+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:17:17+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:19:04+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:20:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:22:54+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:24:39+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:26:33+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:28:18+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:30:04+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:31:51+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:33:49+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:35:34+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:37:19+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:39:05+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:40:50+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:41:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:43:10+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:45:13+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:46:59+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:48:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:50:30+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:52:16+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:54:04+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:55:49+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:57:36+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T00:59:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:01:08+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:03:05+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:03:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:04:55+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:06:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:08:25+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:10:11+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:11:54+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:13:45+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:13:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:15:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:17:26+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:19:10+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:21:01+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:22:59+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:24:45+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:25:06+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:26:51+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:28:35+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:30:19+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:32:02+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:33:50+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:34:41+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:36:26+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:38:11+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:39:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:41:41+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:43:27+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:45:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:46:58+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:48:43+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:50:29+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:52:13+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:54:12+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:55:58+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:57:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T01:59:35+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:01:21+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:03:18+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:05:03+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:06:48+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:08:35+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:10:20+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:12:06+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:13:51+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:15:36+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:17:22+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:19:09+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:20:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:22:46+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:24:31+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:26:15+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:28:02+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:29:48+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:31:34+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:33:25+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:35:10+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:36:54+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:38:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:40:24+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:42:10+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:43:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:45:42+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:47:28+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:49:13+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:50:58+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:52:43+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:54:28+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:56:13+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:58:00+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T02:59:46+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:01:34+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:03:29+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:05:14+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:07:00+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:08:46+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:10:34+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:12:18+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:14:03+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:15:50+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:17:35+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:19:20+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:21:06+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:22:59+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:24:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:26:29+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:28:14+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:29:59+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:31:45+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:33:39+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:35:26+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:37:10+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:38:56+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:40:40+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:42:26+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:44:13+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:45:58+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:47:45+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:49:32+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:51:19+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:53:07+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:54:52+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:56:38+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T03:58:24+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T04:00:11+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T04:01:55+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T04:03:45+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T04:05:31+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T04:07:16+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T04:09:03+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T04:10:48+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T04:12:34+00:00
- DONE `ch4kb` rc=143 last=`final` final/ present
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to OpenROAD.STAPostPNR` at 2026-09-24T04:13:35+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:14:22+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:15:04+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:15:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:17:35+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:19:27+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:20:46+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:21:21+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:21:43+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:22:02+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:22:17+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:24:00+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:25:44+00:00
- DONE `ch4kb` rc=2 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.RepairAntennas --to OpenROAD.STAPostPNR` at 2026-09-24T04:27:30+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to OpenROAD.STAPostPNR` at 2026-09-24T04:29:48+00:00

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to OpenROAD.STAPostPNR` at 2026-09-24T04:34:56+00:00
- DONE `ch4kb` rc=139 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to OpenROAD.STAPostPNR` at 2026-09-24T04:35:14+00:00
- DONE `ch4kb` rc=1 last=`final` final/ present

- START `ch4kb` (soc_dm_4kb) args: ` --from OpenROAD.GlobalRouting --to OpenROAD.STAPostPNR` at 2026-09-24T04:35:22+00:00

- START `ch4kb_clean` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/ch4kb/105-openroad-detailedplacement/state_out.json --from OpenROAD.CTS --to Checker.LVS` at 2026-09-24T04:42:18+00:00

- START `ch4kb_clean` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/ch4kb/105-openroad-detailedplacement/state_out.json --from OpenROAD.CTS --to Checker.LVS` at 2026-09-24T04:51:13+00:00

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Verilator.Lint --to Misc.ReportManufacturability` at 2026-09-24T05:20:14+00:00
- ODD `ch4kb_full` rc=1 last=`49-odb-reportdisconnectedpins` empty error.log, suspect a native crash

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-24T07:13:26+00:00
- ODD `ch4kb_full` rc=1 last=`50-odb-reportdisconnectedpins` empty error.log, suspect a native crash

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-24T07:13:42+00:00
- STOP `ch4kb_full` rc=2 last=`51-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):     return __callback(*args, **kwargs)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scrip`

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to Misc.ReportManufacturability` at 2026-09-24T07:13:51+00:00
- STOP `ch4kb_full` rc=1 last=`75-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s):     return __callback(*args, **kwargs)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scrip`

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Checker.MagicDRC --to Misc.ReportManufacturability` at 2026-09-24T08:06:15+00:00
- STOP `ch4kb_full` rc=1 last=`82-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s):     return __callback(*args, **kwargs)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scrip`

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Checker.MagicDRC --to Misc.ReportManufacturability` at 2026-09-24T08:19:21+00:00
- STOP `ch4kb_full` rc=1 last=`89-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s):     return __callback(*args, **kwargs)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scrip`

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Checker.MagicDRC --to Misc.ReportManufacturability` at 2026-09-24T08:32:43+00:00
- STOP `ch4kb_full` rc=1 last=`96-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s):     return __callback(*args, **kwargs)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scrip`

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Checker.MagicDRC --to Misc.ReportManufacturability` at 2026-09-24T08:45:48+00:00
- STOP `ch4kb_full` rc=1 last=`99-magic-spiceextraction` err: `Subprocess had a non-zero exit. Last 10 line(s):     return __callback(*args, **kwargs)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scrip`

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Checker.MagicDRC --to Misc.ReportManufacturability` at 2026-09-24T08:59:11+00:00
- STOP `ch4kb_full` rc=1 last=`99-magic-spiceextraction` err: `Subprocess had a non-zero exit. Last 10 line(s):     return __callback(*args, **kwargs)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scrip`

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Checker.MagicDRC --to Misc.ReportManufacturability` at 2026-09-24T09:12:23+00:00
- STOP `ch4kb_full` rc=139 last=`99-magic-spiceextraction` err: `Subprocess had a non-zero exit. Last 10 line(s):     return __callback(*args, **kwargs)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scrip`

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Checker.MagicDRC --to Misc.ReportManufacturability` at 2026-09-24T09:12:43+00:00
- STOP `ch4kb_full` rc=1 last=`99-magic-spiceextraction` err: `Subprocess had a non-zero exit. Last 10 line(s):     return __callback(*args, **kwargs)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scrip`

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Checker.MagicDRC --to Misc.ReportManufacturability` at 2026-09-24T09:16:02+00:00
- STOP `ch4kb_full` rc=1 last=`99-magic-spiceextraction` err: `Subprocess had a non-zero exit. Last 10 line(s):     return __callback(*args, **kwargs)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scrip`

- START `ch4kb_full` (soc_dm_4kb) args: ` --from Checker.MagicDRC --to Misc.ReportManufacturability` at 2026-09-24T09:29:37+00:00

- START `lintcheck` (soc_dm_4kb) args: ` --to Checker.LintWarnings` at 2026-09-24T17:22:23+00:00
- STOP `lintcheck` rc=2 last=`04-checker-lintwarnings` err: `112 Lint warnings found. `

- START `lintcheck` (soc_dm_4kb) args: ` --to Checker.LintWarnings` at 2026-09-24T17:26:07+00:00
- STOP `lintcheck` rc=2 last=`04-checker-lintwarnings` err: `111 Lint warnings found. `

- START `rtlfix_c235` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability` at 2026-09-24T18:37:09+00:00
- ODD `rtlfix_c235` rc=1 last=`36-openroad-resizertimingpostcts` empty error.log, suspect a native crash

- START `rtlfix_c235` (soc_dm_4kb) args: ` --from OpenROAD.ResizerTimingPostCTS --to Misc.ReportManufacturability` at 2026-09-24T18:58:59+00:00
- ODD `rtlfix_c235` rc=1 last=`37-openroad-resizertimingpostcts` empty error.log, suspect a native crash

- START `rtlfix_c235` (soc_dm_4kb) args: ` --from OpenROAD.ResizerTimingPostCTS --to Misc.ReportManufacturability` at 2026-09-24T19:18:39+00:00
- ODD `rtlfix_c235` rc=1 last=`45-openroad-resizertimingpostgrt` empty error.log, suspect a native crash

- START `rtlfix_c235` (soc_dm_4kb) args: ` --from Odb.HeuristicDiodeInsertion --to Misc.ReportManufacturability` at 2026-09-24T20:37:58+00:00

- START `rtlfix_c235` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability --from OpenROAD.ResizerTimingPostGRT` at 2026-09-24T20:42:39+00:00
- STOP `rtlfix_c235` rc=2 last=`74-yosys-eqy` err: `4187 Magic DRC errors found. - deferred Subprocess had a non-zero exit. Last 10 line(s): EQY 22:15:47 \[/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/rtlfix_c235/74-yosys-eqy/scratch] read_gate:`

- START `r8_a0c4` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability` at 2026-09-24T23:30:05+00:00
- ODD `r8_a0c4` rc=1 last=`30-openroad-stamidpnr` empty error.log, suspect a native crash

- START `r8_a0c4` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability --from OpenROAD.STAMidPNR` at 2026-09-24T23:36:37+00:00
- ODD `r8_a0c4` rc=1 last=`72-yosys-eqy` empty error.log, suspect a native crash

- START `r8_a0c4` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability --from Yosys.EQY` at 2026-09-25T02:38:52+00:00
- STOP `r8_a0c4` rc=2 last=`72-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s): Traceback (most recent call last):   File "/nix/store/gna3lkpzc7wjcmqfwqv7lcv4syjl86rl-yosys-eqy/bin/.eqy-wrapped", line 1260, in <module>     main()  `

- START `r8_a0c4` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability --from Yosys.EQY` at 2026-09-25T02:44:26+00:00
- STOP `r8_a0c4` rc=2 last=`72-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s): Traceback (most recent call last):   File "/nix/store/gna3lkpzc7wjcmqfwqv7lcv4syjl86rl-yosys-eqy/bin/.eqy-wrapped", line 1260, in <module>     main()  `

- START `r8x_E1` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r8_a0c4/42-openroad-repairantennas/state_out.json --from OpenROAD.ResizerTimingPostGRT --to OpenROAD.STAPostPNR` at 2026-09-25T02:50:09+00:00

- START `r8x_E2` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r8_a0c4/42-openroad-repairantennas/state_out.json --from OpenROAD.ResizerTimingPostGRT --to OpenROAD.STAPostPNR` at 2026-09-25T02:50:29+00:00
- STOP `r8x_E1` rc=2 last=`07-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `r8x_E3` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r8_a0c4/42-openroad-repairantennas/state_out.json --from OpenROAD.ResizerTimingPostGRT --to OpenROAD.STAPostPNR` at 2026-09-25T03:05:34+00:00

- START `r8x_E1` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-25T03:20:32+00:00
- STOP `r8x_E1` rc=1 last=`12-odb-cellfrequencytables` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `r8x_E1` (soc_dm_4kb) args: ` --from Odb.CellFrequencyTables --to OpenROAD.STAPostPNR` at 2026-09-25T03:23:21+00:00
- DONE `r8x_E3` rc=0 last=`final` final/ present

- START `r8x_E4` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r8_a0c4/26-odb-applydeftemplate/state_out.json --from OpenROAD.GlobalPlacement --to OpenROAD.STAPostPNR` at 2026-09-25T03:25:21+00:00
- DONE `r8x_E1` rc=0 last=`final` final/ present
- STOP `r8x_E2` rc=2 last=`07-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `r8x_E2` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-25T03:42:28+00:00
- STOP `r8x_E2` rc=2 last=`07-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `r8_clk215` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability` at 2026-09-25T04:04:28+00:00

- START `r8x_E2` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-25T04:15:18+00:00
- DONE `r8x_E2` rc=0 last=`final` final/ present
- DONE `r8x_E4` rc=0 last=`final` final/ present
- ODD `r8_clk215` rc=1 last=`39-openroad-checkantennas` empty error.log, suspect a native crash

- START `r8_clk215` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability --from OpenROAD.CheckAntennas` at 2026-09-25T05:41:01+00:00

- START `r8_clk22` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability` at 2026-09-25T06:39:00+00:00

- START `syn_A2` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-1` at 2026-09-25T06:54:40+00:00

- START `syn_A1` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-1` at 2026-09-25T06:54:40+00:00

- START `syn_A3` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-1` at 2026-09-25T06:54:40+00:00
- DONE `syn_A1` rc=0 last=`final` final/ present

- START `syn_D0` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-1` at 2026-09-25T07:08:48+00:00
- DONE `syn_A3` rc=0 last=`final` final/ present

- START `syn_D1` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-1` at 2026-09-25T07:11:05+00:00
- DONE `syn_A2` rc=0 last=`final` final/ present

- START `syn_D2` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-1` at 2026-09-25T07:11:42+00:00
- DONE `syn_D0` rc=0 last=`final` final/ present

- START `syn_D3` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-1` at 2026-09-25T07:23:16+00:00
- DONE `syn_D2` rc=0 last=`final` final/ present

- START `syn_D4` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-1` at 2026-09-25T07:28:16+00:00
- DONE `syn_D1` rc=0 last=`final` final/ present
- DONE `syn_D3` rc=0 last=`final` final/ present
- DONE `syn_D4` rc=0 last=`final` final/ present

- START `r8_a3` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability` at 2026-09-25T07:43:50+00:00

- START `syn_D1R` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-3` at 2026-09-25T09:05:45+00:00

- START `syn_A3RB` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-3` at 2026-09-25T09:05:45+00:00

- START `syn_A1R` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-3` at 2026-09-25T09:05:45+00:00
- STOP `r8_a3` rc=2 last=`38-openroad-globalrouting` err: `[GRT-0118] Routing congestion too high. Check the congestion heatmap in the GUI. `

- START `syn_R7A0` (soc_dm_4kb) args: ` --to OpenROAD.STAMidPNR-1` at 2026-09-25T09:22:50+00:00
- DONE `syn_R7A0` rc=0 last=`final` final/ present
- DONE `syn_A3RB` rc=0 last=`final` final/ present

- START `r7r8_358c` (soc_dm_4kb) args: ` --to Misc.ReportManufacturability` at 2026-09-25T11:38:22+00:00
- DONE `syn_A1R` rc=0 last=`final` final/ present
- STOP `syn_D1R` rc=2 last=`38-openroad-globalrouting` err: `[GRT-0118] Routing congestion too high. Check the congestion heatmap in the GUI. `
- STOP `r7r8_358c` rc=2 last=`72-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s): EQY 14:58:40 \[/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r7r8_358c/72-yosys-eqy/scratch] read_gate: /mnt/e/Projects/RISCV-research/asic/soc_d`

- START `ant_AN1` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r7r8_358c/37-openroad-stamidpnr-2/state_out.json --from OpenROAD.GlobalRouting --to OpenROAD.STAPostPNR` at 2026-09-25T16:06:34+00:00

- START `ss_SS1` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-25T16:24:44+00:00
- DONE `ant_AN1` rc=0 last=`final` final/ present

- START `ant_AN2` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r7r8_358c/37-openroad-stamidpnr-2/state_out.json --from OpenROAD.GlobalRouting --to OpenROAD.STAPostPNR` at 2026-09-25T16:54:09+00:00

- START `ss_SS3` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-25T17:12:55+00:00

- START `r9_ecf4` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-25T17:13:03+00:00
- STOP `ss_SS1` rc=2 last=`38-openroad-globalrouting` err: `[GRT-0118] Routing congestion too high. Check the congestion heatmap in the GUI. `

- START `ss_SS2` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-25T17:20:26+00:00
- DONE `ant_AN2` rc=0 last=`final` final/ present

- START `ant_AN3` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r7r8_358c/37-openroad-stamidpnr-2/state_out.json --from OpenROAD.GlobalRouting --to OpenROAD.STAPostPNR` at 2026-09-25T17:44:48+00:00
- STOP `ss_SS2` rc=2 last=`38-openroad-globalrouting` err: `[GRT-0118] Routing congestion too high. Check the congestion heatmap in the GUI. `
- DONE `ant_AN3` rc=0 last=`final` final/ present
- DONE `r9_ecf4` rc=0 last=`final` final/ present
- DONE `ss_SS3` rc=0 last=`final` final/ present

- START `syn_R10` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-25T19:44:42+00:00
- DONE `syn_R10` rc=0 last=`final` final/ present

- START `r10A` (soc_dm_4kb) args: `full flow` at 2026-09-25T19:55:20+00:00

- START `r10B` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-25T20:25:20+00:00

- START `syn_R10f2` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-25T21:06:15+00:00
- DONE `syn_R10f2` rc=0 last=`final` final/ present

- START `syn_R11cand` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-25T21:16:02+00:00
- DONE `syn_R11cand` rc=0 last=`final` final/ present
- DONE `r10B` rc=0 last=`final` final/ present

- START `r10C` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-25T21:48:05+00:00

- START `syn_R10p12` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-25T21:48:30+00:00
- DONE `syn_R10p12` rc=0 last=`final` final/ present
- DONE `r10C` rc=0 last=`final` final/ present
- STOP `r10A` rc=2 last=`73-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s): EQY 23:37:34 \[/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r10A/73-yosys-eqy/scratch] Skipping strategy 'sat' for partition 'soc_asic_top.HEX2'`

- START `r10D` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-26T10:38:51+00:00

- START `r10E` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-26T11:18:51+00:00
- DONE `r10D` rc=0 last=`final` final/ present

- START `r12_d40` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-26T11:51:34+00:00

- START `syn_R12` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-26T12:34:32+00:00
- DONE `r10E` rc=0 last=`final` final/ present

- START `syn_R10f2b` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-26T12:48:31+00:00
- DONE `syn_R10f2b` rc=0 last=`final` final/ present

- START `syn_R12b` (soc_dm_4kb) args: ` --to Yosys.Synthesis` at 2026-09-26T13:06:37+00:00
- DONE `syn_R12b` rc=0 last=`final` final/ present

- START `r12b_d38` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-26T13:10:02+00:00

- START `r12b_d42` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-26T13:25:02+00:00
- ODD `r12_d40` rc=143 last=`06-yosys-synthesis` empty error.log, suspect a native crash
- DONE `r12b_d38` rc=0 last=`final` final/ present
- DONE `r12b_d42` rc=0 last=`final` final/ present

- START `final_A` (soc_dm_4kb) args: `full flow` at 2026-09-26T14:47:16+00:00

- START `final_B` (soc_dm_4kb) args: ` --to OpenROAD.STAPostPNR` at 2026-09-26T14:57:16+00:00
- DONE `final_B` rc=0 last=`final` final/ present
- STOP `final_A` rc=2 last=`73-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s): EQY 18:57:47 \[/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final_A/73-yosys-eqy/scratch] run: Terminated EQY 18:57:47 \[/mnt/e/Projects/RISCV-r`

- START `final_B` (soc_dm_4kb) args: ` --from OpenROAD.IRDropReport` at 2026-09-26T18:59:38+00:00
- DONE `final_B` rc=1 last=`final` final/ present

- START `final_B` (soc_dm_4kb) args: ` --from Yosys.EQY` at 2026-09-26T19:58:11+00:00
- DONE `final_B` rc=1 last=`final` final/ present

- START `final_B` (soc_dm_4kb) args: ` --from Yosys.EQY` at 2026-09-26T20:04:35+00:00
- DONE `final_B` rc=2 last=`final` final/ present

- START `final_B` (soc_dm_4kb) args: ` --from Yosys.EQY` at 2026-09-26T20:11:12+00:00
- DONE `final_B` rc=2 last=`final` final/ present

- START `final_B` (soc_dm_4kb) args: ` --from Yosys.EQY` at 2026-09-26T20:20:01+00:00
- DONE `final_B` rc=1 last=`final` final/ present

- START `final_B` (soc_dm_4kb) args: ` --from Yosys.EQY` at 2026-09-26T20:26:31+00:00
- DONE `final_B` rc=1 last=`final` final/ present

- START `final_B` (soc_dm_4kb) args: ` --from Yosys.EQY` at 2026-09-26T20:33:20+00:00
- DONE `final_B` rc=1 last=`final` final/ present

- START `x1_nohd` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final_A/40-openroad-repairdesignpostgrt/state_out.json --from Odb.DiodesOnPorts --to OpenROAD.STAPostPNR` at 2026-09-27T08:33:49+00:00
- DONE `x1_nohd` rc=0 last=`final` final/ present

- START `x2_rc2` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final_A/26-odb-applydeftemplate/state_out.json --from OpenROAD.GlobalPlacement --to OpenROAD.STAPostPNR` at 2026-09-27T09:28:40+00:00
- DONE `x2_rc2` rc=0 last=`final` final/ present

- START `x3_fix` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x2_rc2/04-openroad-stamidpnr/state_out.json --from OpenROAD.RepairDesignPostGPL --to OpenROAD.STAPostPNR` at 2026-09-27T11:33:20+00:00
- DONE `x3_fix` rc=0 last=`final` final/ present

- START `x4_hold` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x2_rc2/04-openroad-stamidpnr/state_out.json --from OpenROAD.RepairDesignPostGPL --to OpenROAD.STAPostPNR` at 2026-09-27T13:33:20+00:00
- DONE `x4_hold` rc=0 last=`final` final/ present

- START `final2_A` (soc_dm_4kb) args: `full flow` at 2026-09-27T15:19:29+00:00
- STOP `final2_A` rc=2 last=`72-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s): EQY 19:05:54 \[/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final2_A/72-yosys-eqy/scratch] run: Running strategy 'sat' on 'soc_asic_top.HEX0'.. `

- START `final3_A` (soc_dm_4kb) args: `full flow` at 2026-09-27T19:06:30+00:00
- STOP `final3_A` rc=2 last=`72-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s): EQY 22:39:12 \[/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final3_A/72-yosys-eqy/scratch] run: Running strategy 'sat' on 'soc_asic_top.HEX0'.. `

- START `final3_B` (soc_dm_4kb) args: `full flow` at 2026-09-27T22:39:17+00:00
- ODD `final3_B` rc=1 last=`36-openroad-resizertimingpostcts` empty error.log, suspect a native crash

- START `final3_B` (soc_dm_4kb) args: `full flow` at 2026-09-27T23:09:42+00:00
- ODD `final3_B` rc=1 last=`45-openroad-detailedrouting` empty error.log, suspect a native crash

- START `final3_B` (soc_dm_4kb) args: ` --from OpenROAD.DetailedRouting` at 2026-09-28T00:05:21+00:00
- ODD `final3_B` rc=1 last=`55-odb-cellfrequencytables` empty error.log, suspect a native crash

- START `final3_B` (soc_dm_4kb) args: ` --from Odb.CellFrequencyTables` at 2026-09-28T00:29:44+00:00
- STOP `final3_B` rc=2 last=`74-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s):   File "/nix/store/7hnr99nxrd2aw6lghybqdmkckq60j6l9-python3-3.11.9/lib/python3.11/shlex.py", line 315, in split     return list(lex)            ^^^^^^^`

- START `final3_eqy` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final3_A/71-checker-lvs/state_out.json --from Yosys.EQY --to Yosys.EQY` at 2026-09-28T19:45:02+00:00
- STOP `final3_eqy` rc=2 last=`01-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s): EQY 20:00:51 \[/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final3_eqy/01-yosys-eqy/scratch] run: Elapsed clock time [H:MM:SS (secs)]: 0:00:00 (`

- START `x_E1` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final3_A/30-openroad-stamidpnr/state_out.json --from OpenROAD.RepairDesignPostGPL --to OpenROAD.STAPostPNR` at 2026-09-28T20:01:51+00:00
- DONE `x_E1` rc=0 last=`final` final/ present

- START `x_E2` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final3_A/30-openroad-stamidpnr/state_out.json --from OpenROAD.RepairDesignPostGPL --to OpenROAD.STAPostPNR` at 2026-09-28T21:59:11+00:00

- START `x_E1H` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E1/15-openroad-detailedrouting/state_out.json --from OpenROAD.PostRouteHoldECO --to OpenROAD.STAPostPNR` at 2026-09-28T22:11:21+00:00
- STOP `x_E1H` rc=2 last=`01-openroad-postrouteholdeco` err: `Subprocess had a non-zero exit. Last 10 line(s): [INFO ODB-0127] Reading DEF file: /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E1/15-openroad-detailedrouting/soc_asic_top.def [INFO ODB-0128]`
- DONE `x_E2` rc=0 last=`final` final/ present

- START `r13a_A` (soc_dm_4kb) args: `full flow` at 2026-09-28T23:38:05+00:00

- START `x_E1H` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E1/15-openroad-detailedrouting/state_out.json --from OpenROAD.PostRouteHoldECO --to OpenROAD.STAPostPNR` at 2026-09-29T01:22:14+00:00
- ODD `x_E1H` rc=1 last=`01-openroad-postrouteholdeco` empty error.log, suspect a native crash

- START `x_E1H` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E1/15-openroad-detailedrouting/state_out.json --from OpenROAD.PostRouteHoldECO --to OpenROAD.STAPostPNR` at 2026-09-29T01:46:22+00:00
- DONE `x_E1H` rc=0 last=`final` final/ present

- START `x_E3` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final3_A/30-openroad-stamidpnr/state_out.json --from OpenROAD.RepairDesignPostGPL --to OpenROAD.STAPostPNR` at 2026-09-29T01:56:19+00:00

- START `x_E4_A` (soc_dm_4kb) args: `full flow` at 2026-09-29T02:00:24+00:00
- STOP `r13a_A` rc=2 last=`72-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s): EQY  3:09:57 \[/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r13a_A/72-yosys-eqy/scratch] run: Running strategy 'sat' on 'soc_asic_top.HEX0'.. EQ`
- ODD `x_E3` rc=1 last=`21-odb-reportdisconnectedpins` empty error.log, suspect a native crash

- START `x_E3` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-29T03:52:27+00:00
- STOP `x_E3` rc=2 last=`22-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `x_E3` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-29T03:53:14+00:00
- STOP `x_E3` rc=1 last=`23-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`
- STOP `x_E4_A` rc=2 last=`49-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `x_E3` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-29T03:59:34+00:00
- DONE `x_E3` rc=0 last=`final` final/ present

- START `x_E3` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-29T04:03:07+00:00
- DONE `x_E3` rc=2 last=`final` final/ present

- START `x_E3` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-29T04:03:22+00:00
- DONE `x_E3` rc=2 last=`final` final/ present

- START `x_E3` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-29T04:03:34+00:00
- DONE `x_E3` rc=2 last=`final` final/ present

- START `x_E3` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-29T04:03:47+00:00
- DONE `x_E3` rc=0 last=`final` final/ present

- START `x_E3` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-29T04:07:38+00:00
- DONE `x_E3` rc=1 last=`final` final/ present

- START `x_E4_A` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-29T04:07:51+00:00
- STOP `x_E4_A` rc=2 last=`50-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `x_E4_A` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-29T04:08:01+00:00
- STOP `x_E4_A` rc=1 last=`51-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `x_E4_A` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-29T04:08:14+00:00
- STOP `x_E4_A` rc=2 last=`52-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `x_E4_A` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-29T04:08:24+00:00
- STOP `x_E4_A` rc=1 last=`53-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `x_E4_A` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-29T04:08:33+00:00
- STOP `x_E4_A` rc=2 last=`77-yosys-eqy` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `x_E4_A` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins` at 2026-09-29T05:19:51+00:00
- STOP `x_E4_A` rc=1 last=`83-odb-cellfrequencytables` err: `Subprocess had a non-zero exit. Last 10 line(s):            ^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/odbpy/reader.py", line 217, in wrapp`

- START `x_E3R` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E3/16-openroad-detailedrouting/state_out.json --from OpenROAD.PostRouteHoldECO --to OpenROAD.STAPostPNR` at 2026-09-29T05:30:28+00:00

- START `x_E5` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final3_A/30-openroad-stamidpnr/state_out.json --from OpenROAD.RepairDesignPostGPL --to OpenROAD.STAPostPNR` at 2026-09-29T05:30:33+00:00
- STOP `x_E3R` rc=2 last=`01-openroad-postrouteholdeco` err: `[DRT-0218] Guide is not connected to design. `
- STOP `x_E5` rc=2 last=`07-openroad-resizertimingpostcts` err: `[ODB-0370] Attempt to disconnect iterm of dont_touch instance macro_pin_pre_245 `

- START `x_E3R` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E3/16-openroad-detailedrouting/state_out.json --from OpenROAD.PostRouteHoldECO --to OpenROAD.STAPostPNR` at 2026-09-29T06:02:27+00:00

- START `x_E5` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final3_A/30-openroad-stamidpnr/state_out.json --from OpenROAD.RepairDesignPostGPL --to OpenROAD.STAPostPNR` at 2026-09-29T06:02:30+00:00
- ODD `x_E3R` rc=1 last=`03-openroad-checkantennas-1` empty error.log, suspect a native crash

- START `x_E3R` (soc_dm_4kb) args: ` --from Odb.RemoveRoutingObstructions --to OpenROAD.STAPostPNR` at 2026-09-29T06:27:17+00:00
- ODD `x_E3R` rc=1 last=`07-odb-reportdisconnectedpins` empty error.log, suspect a native crash

- START `x_E3R` (soc_dm_4kb) args: ` --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR` at 2026-09-29T06:28:47+00:00
- DONE `x_E3R` rc=0 last=`final` final/ present

- START `x_E3R2` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E3/16-openroad-detailedrouting/state_out.json --from OpenROAD.PostRouteHoldECO --to OpenROAD.STAPostPNR` at 2026-09-29T06:33:23+00:00
- DONE `x_E3R2` rc=0 last=`final` final/ present

- START `x_E6` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final3_A/30-openroad-stamidpnr/state_out.json --from OpenROAD.RepairDesignPostGPL --to OpenROAD.STAPostPNR` at 2026-09-29T07:02:58+00:00

- START `x_E5b` (soc_dm_4kb) args: ` --with-initial-state /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E5/16-openroad-detailedrouting/state_out.json --from OpenROAD.PostRouteHoldECO --to OpenROAD.STAPostPNR` at 2026-09-29T07:44:49+00:00
- DONE `x_E5b` rc=0 last=`final` final/ present
- DONE `x_E5` rc=0 last=`final` final/ present
- ODD `x_E6` rc=1 last=`21-odb-reportdisconnectedpins` empty error.log, suspect a native crash

- START `x_E6` (soc_dm_4kb) args: ` --from Odb.RemoveRoutingObstructions --to OpenROAD.STAPostPNR` at 2026-09-29T08:40:18+00:00
- STOP `x_E6` rc=2 last=`25-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):     return ctx.invoke(self.callback, **ctx.params)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/nix/store/alhgaybdgmv706469rp57ggcyg3750`

- START `x_E6` (soc_dm_4kb) args: ` --from Odb.RemoveRoutingObstructions --to OpenROAD.STAPostPNR` at 2026-09-29T08:41:20+00:00
- STOP `x_E6` rc=1 last=`29-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):     return ctx.invoke(self.callback, **ctx.params)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/nix/store/alhgaybdgmv706469rp57ggcyg3750`

- START `x_E6` (soc_dm_4kb) args: ` --from Odb.RemoveRoutingObstructions --to OpenROAD.STAPostPNR` at 2026-09-29T08:42:21+00:00
- STOP `x_E6` rc=1 last=`33-odb-reportdisconnectedpins` err: `Subprocess had a non-zero exit. Last 10 line(s):     return ctx.invoke(self.callback, **ctx.params)            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/nix/store/alhgaybdgmv706469rp57ggcyg3750`

- START `x_E6` (soc_dm_4kb) args: ` --from Odb.RemoveRoutingObstructions --to OpenROAD.STAPostPNR` at 2026-09-29T08:43:22+00:00
- DONE `x_E6` rc=0 last=`final` final/ present

