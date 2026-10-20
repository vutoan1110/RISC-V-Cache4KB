# which guide APIs does this odb Tcl binding have?
read_db /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E3/16-openroad-detailedrouting/soc_asic_top.odb
set block [[[ord::get_db] getChip] getBlock]
set net [[[$block findInst wire11106] findITerm A] getNet]
puts "name [$net getName]"
puts "net $net"
if {[catch {set g [$net getGuides]} e]} { puts "getGuides ERR: $e" } else { puts "getGuides n=[llength $g] first=[lindex $g 0]" }
if {[catch {$net clearGuides} e]} { puts "clearGuides ERR: $e" } else { puts "clearGuides OK; after: [llength [$net getGuides]]" }
puts "dbGuide procs: [info commands odb::dbGuide*]"
