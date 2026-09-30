read_db /mnt/e/Projects/RISCV-research/asic/pd_exp/hold_eco/eco3/after_grt.odb
set block [[[ord::get_db] getChip] getBlock]
set i [$block findInst wire11106]
puts "master [[$i getMaster] getName] status [$i getPlacementStatus] loc [$i getLocation] orient [$i getOrient] paidx [$i getPinAccessIdx]"
set it [$i findITerm A]
foreach m {getPrefAccessPoints getAccessPoints clearPrefAccessPoints} { puts "$m: [catch {set r [$it $m]} e] [expr {[info exists r] ? [llength $r] : {}}] $e" }
foreach ap [$it getPrefAccessPoints] { puts "pref ap [$ap getPoint]" }
puts "pin_access cmd: [info commands pin_access] [info commands drt::*pin_access*]"
