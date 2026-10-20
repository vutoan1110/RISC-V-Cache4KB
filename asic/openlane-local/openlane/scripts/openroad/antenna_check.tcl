# Copyright 2020-2022 Efabless Corporation
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

# start checking antennas and generate a detailed report
# Pin the antenna code to one thread.
#
# repair_antennas runs ant::AntennaChecker across nets inside an OpenMP region
# (__kmpc_fork_call -> __kmp_invoke_microtask -> checkNetViolations), and it
# segfaulted eight times out of eight inside boost::polygon under
# ant::wiresToPolygonSetMap. OMP_NUM_THREADS from the environment does not
# reach it: OpenROAD calls omp_set_num_threads() itself, which takes
# precedence. Neither script set a thread count -- the logs have no
# "ORD-0030 Using N thread(s)" line at all.
#
# The same nets are checked with the same thresholds and the same violations
# are reported; only the parallelism changes.
set_thread_count 1

puts "%OL_CREATE_REPORT $::env(_ANTENNA_REPORT)"
check_antennas -verbose
puts "%OL_END_REPORT"
