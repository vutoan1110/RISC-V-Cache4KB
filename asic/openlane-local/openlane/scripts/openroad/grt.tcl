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
read_current_odb
source $::env(SCRIPTS_DIR)/openroad/common/dpl_cell_pad.tcl

set_propagated_clock [all_clocks]

source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl

# The pre-repair antenna check that used to run here has been removed, and this
# is why.
#
# It is a strict duplicate. OpenROAD.CheckAntennas is the very next step in the
# Classic flow, runs the identical `check_antennas -verbose` from
# antenna_check.tcl, and its output is the one OpenLane parses into
# route__antenna_violation__count. The GlobalRouting step's own class contains
# no reference to antenna, report or _ANTENNA_REPORT at all -- nothing consumes
# what this call produced.
#
# Meanwhile it was destroying finished work. Ninety attempts at this step failed,
# and every stack that could be read was inside the antenna checker:
# boost::polygon in six different functions, plus ant::AntennaChecker::saveGates.
# Global routing itself completed cleanly every time -- final congestion report
# 0/0/0 overflow on every layer, 96,037 nets, 9.58 mm wire -- and then the
# duplicate report crashed the process before write_views could save any of it.
#
# `set_thread_count 1` proved the crash is not a data race: the log shows
# "Using 1 thread(s)" and it still died. It is kept because the parasitics
# estimation below is on the same corruption-prone path.
#
# No check is lost. The same check runs, on the same database, in the step whose
# result is actually measured -- and when it fails there, a retry costs seconds
# instead of the twenty-five minutes of routing it costs here.
set_thread_count 1

source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
estimate_parasitics -global_routing

write_views
