# FLOW_JOURNAL Incident 93: standalone test of macro_pin_buffers.tcl on x_E2's post-GPL repair output,
# then legalisation and a placement-estimate slew check at the SRAM pins. Writes only here.
source $::env(SCRIPTS_DIR)/openroad/macro_pin_buffers.tcl
source $::env(SCRIPTS_DIR)/openroad/common/dpl_cell_pad.tcl
detailed_placement -max_displacement [subst { $::env(PL_MAX_DISPLACEMENT_X) $::env(PL_MAX_DISPLACEMENT_Y) }]
check_placement -verbose
set ::LAYERS_RC_HERE 1 ;# calibrated (k=2) wire RC for the estimate
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
estimate_parasitics -placement
report_check_types -max_slew -max_capacitance -violators > mpb_drv.rpt
puts "MPB done"
