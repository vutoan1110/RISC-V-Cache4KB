# FLOW_JOURNAL Incident 96 (2026-10-06): where does a floorplan's global routing overflow sit?
# OpenLane's GlobalRouting step writes no congestion map. This replays the step's global_route exactly as
# openlane-local/openlane/scripts/openroad/common/grt.tcl builds it for these configs (met1-met5, global
# adjustment 0.2 then GRT_LAYER_ADJUSTMENTS li1 0.99 / met1-5 0, macro extension 1, allow_congestion; the step is
# not timing-driven: no critical-nets option, no routing alpha) on the same placed odb, adding only
# -congestion_report_file. Run in WSL:
#   ODB=<placed odb> RPT=<report> ITERS=50 openroad -exit fp_tools/grt_congestion.tcl
read_db $::env(ODB)
set_routing_layers -signal met1-met5 -clock met1-met5
set_global_routing_layer_adjustment * 0.2
set i 0
foreach adj {0.99 0 0 0 0 0} {
    set name [lindex {li1 met1 met2 met3 met4 met5} $i]
    set_global_routing_layer_adjustment $name $adj
    incr i
}
set_macro_extension 1
global_route -congestion_iterations $::env(ITERS) -verbose -allow_congestion -congestion_report_file $::env(RPT)
