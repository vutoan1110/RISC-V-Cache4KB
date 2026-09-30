# FLOW_JOURNAL Incident 91: design-rule violators (max slew / max cap / max fanout) of a signed-off
# run at one corner, with the driver cell of every violating pin, for classification.
# Output: $::env(SQ_OUT)/drv_<corner>.rpt (raw report) and drv_<corner>.tsv (pin, ref, net, fanout).
set out $::env(SQ_OUT)
set c $::env(_CURRENT_CORNER_NAME)
report_check_types -max_slew -max_capacitance -max_fanout -violators > $out/drv_$c.rpt
set f [open $out/drv_$c.rpt r]
set tsv [open $out/drv_$c.tsv w]
puts $tsv "check\tpin\tdirection\tref\tnet\tfanout\tvalue\tlimit\tdiode_loads"
set check ""
while {[gets $f line] >= 0} {
    if {[regexp {^max (slew|capacitance|fanout)} $line -> k]} { set check $k; continue }
    set t [regexp -all -inline {\S+} $line]
    if {[llength $t] < 4} { continue }
    set p [lindex $t 0]
    set pins [get_pins -quiet $p]
    if {[llength $pins] == 0} { set pins [get_ports -quiet $p] }
    if {[llength $pins] == 0} { continue }
    set ref "port"; set dir "?"; set net ""; set fo ""
    if {![catch {set cell [get_cells -of_objects $pins]}]} {
        catch { set ref [get_property $cell ref_name] }
    }
    catch { set dir [get_property $pins direction] }
    set nd ""
    catch { set n [get_nets -of_objects $pins]; set net [get_full_name $n]
            set loads [get_pins -of_objects $n -filter "direction == input"]
            set fo [llength $loads]
            set nd 0
            foreach l $loads {
                if {[string match "*diode*" [get_property [get_cells -of_objects $l] ref_name]]} { incr nd }
            } }
    puts $tsv "$check\t$p\t$dir\t$ref\t$net\t$fo\t[lindex $t 2]\t[lindex $t 1]\t$nd"
}
close $f
close $tsv
puts "SQ_DRV done: $out/drv_$c.tsv"
