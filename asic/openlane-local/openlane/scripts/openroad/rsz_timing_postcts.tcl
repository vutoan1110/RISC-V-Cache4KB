# Copyright 2020-2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl

load_rsz_corners
read_current_odb

set_propagated_clock [all_clocks]

set_dont_touch_objects

# Local (2026-10-15): LAYERS_RC_SCOPE "repair" applies the per-layer RC of LAYERS_RC in this timing repair too (the
# calibrated values are 1.19x of RCX on placement estimates; the tech-LEF RC underestimates wire capacitance ~2x, so
# the repair stops at slacks that are optimistic by 1-4 ns at ss). GPL, CTS and the STA steps keep the tech-LEF RC.
if { [info exists ::env(LAYERS_RC_SCOPE)] && $::env(LAYERS_RC_SCOPE) eq "repair" } {
    set ::LAYERS_RC_HERE 1
}

# set rc values
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl

# CTS and detailed placement move instances, so update parastic estimates.
# estimate wire rc parasitics
estimate_parasitics -placement

# Resize
set setup_args [list]
lappend setup_args -verbose
lappend setup_args -setup
lappend setup_args -setup_margin $::env(PL_RESIZER_SETUP_SLACK_MARGIN)
lappend setup_args -max_buffer_percent $::env(PL_RESIZER_SETUP_MAX_BUFFER_PCT)
if { $::env(PL_RESIZER_GATE_CLONING) != 1 } {
    lappend setup_args -skip_gate_cloning
}

set hold_args [list]
lappend hold_args -verbose
lappend hold_args -hold
lappend hold_args -setup_margin $::env(PL_RESIZER_SETUP_SLACK_MARGIN)
lappend hold_args -hold_margin $::env(PL_RESIZER_HOLD_SLACK_MARGIN)
lappend hold_args -max_buffer_percent $::env(PL_RESIZER_HOLD_MAX_BUFFER_PCT)
if { $::env(PL_RESIZER_ALLOW_SETUP_VIOS) == 1 } {
    lappend hold_args -allow_setup_violations
}

if { $::env(PL_RESIZER_FIX_HOLD_FIRST) == 1 } {
    repair_timing {*}$hold_args
    repair_timing {*}$setup_args
} else {
    repair_timing {*}$setup_args
    repair_timing {*}$hold_args
}

# Legalize
source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl

unset_dont_touch_objects

source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
estimate_parasitics -placement


write_views
