# NHAT_KY.md 2026-09-28: q_whatif_from.tcl followed by the endpoint/startpoint dump of q_endgroups.tcl,
# so the paths that survive the cuts can be grouped by where they start.
set here [file dirname $::env(SQ_QUERY)]
source [file join $here q_whatif_from.tcl]
source [file join $here q_endgroups.tcl]
