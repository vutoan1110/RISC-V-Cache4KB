# Companion of sta_query.sh: load the design as STAPostPNR did, then source
# the query script named by SQ_QUERY.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
set_cmd_units -time ns -capacitance pF -current mA -voltage V -resistance kOhm -distance um
read_timing_info
read_spefs
source $::env(SQ_QUERY)
