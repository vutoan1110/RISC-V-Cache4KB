# Copyright 2022-2023 Efabless Corporation
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
if { ![info exists ::grt_preamble] } {
    set ::grt_preamble 1

    source $::env(SCRIPTS_DIR)/openroad/common/set_routing_layers.tcl
    source $::env(SCRIPTS_DIR)/openroad/common/set_layer_adjustments.tcl

    set_macro_extension $::env(GRT_MACRO_EXTENSION)
}

# Global routing's timing-driven paths are where this host's memory fault lands.
# Four crashes, four different functions, all of them inside the GRT-to-STA
# interaction and nowhere else:
#
#   pdr::primDijkstra              Prim-Dijkstra Steiner trees (routing alpha>0)
#   FastRouteCore::CalculatePartialSlack -> sta::Corners::findPathAnalysisPt
#   MakeWireParasitics::estimateParasitcs -> sta::NetIdLess
#   (and a fourth on a re-test with the defaults restored)
#
# With GRT_ROUTING_ALPHA 0 and GRT_CRITICAL_NETS_PCT 0 the same design routed in
# 24 s, twice, byte-identical. With the defaults it segfaults. Both variables are
# optional and absent means stock behaviour, so no other design is affected.
if { [info exists ::env(GRT_ROUTING_ALPHA)] } {
    puts "\[INFO\] set_routing_alpha $::env(GRT_ROUTING_ALPHA)"
    set_routing_alpha $::env(GRT_ROUTING_ALPHA)
}

set arg_list [list]
lappend arg_list -congestion_iterations $::env(GRT_OVERFLOW_ITERS)
lappend arg_list -verbose
if { $::env(GRT_ALLOW_CONGESTION) == 1 } {
    lappend arg_list -allow_congestion
}
if { [info exists ::env(GRT_CRITICAL_NETS_PCT)] } {
    lappend arg_list -critical_nets_percentage $::env(GRT_CRITICAL_NETS_PCT)
}
puts $arg_list
global_route {*}$arg_list

write_guide $::env(STEP_DIR)/after_grt.guide