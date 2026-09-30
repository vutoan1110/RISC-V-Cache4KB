# FLOW_JOURNAL Incident 93: every violating setup endpoint at one corner with its slack and the RTL name
# of the capturing register (the net on its Q pin), so runs can be compared per register group.
# Output: $::env(SQ_OUT)/endgroups_<corner>.tsv
set out $::env(SQ_OUT)
set c $::env(_CURRENT_CORNER_NAME)
set f [open $out/endgroups_$c.tsv w]
puts $f "endpoint\tqnet\tslack\tstartpoint\tstartnet"
foreach pe [find_timing_paths -path_delay max -group_count 20000 -endpoint_count 1 -slack_max 0.0] {
    set pin [get_property $pe endpoint]
    set pname [get_full_name $pin]
    set q ""
    if {![catch {set inst [get_cells -of_objects $pin]}]} {
        set iname [get_full_name $inst]
        foreach qp {Q Q_N} {
            set p [get_pins -quiet "$iname/$qp"]
            if {[llength $p]} {
                set n [get_nets -quiet -of_objects $p]
                if {[llength $n]} { set q [get_full_name $n]; break }
            }
        }
    }
    set spin [get_property $pe startpoint]
    set sp [get_full_name $spin]
    set sn ""
    catch { set sn [get_full_name [get_nets -of_objects $spin]] }
    puts $f "$pname\t$q\t[get_property $pe slack]\t$sp\t$sn"
}
close $f
puts "SQ_ENDGROUPS done: $out/endgroups_$c.tsv"
