## QuestaSim macro: compile the core UVM environment and run exactly one test.
##
## Usage, from the project root:
##   vsim -c -do "do verification/uvm/run_uvm.do"                   ;# smoke, compile
##   vsim -c -do "do verification/uvm/run_uvm.do core_smoke_test 0" ;# reuse work/
##   vsim -c -do "do verification/uvm/run_uvm.do core_smoke_test 1 7" ;# seed 7
##
## One vsim process per test. Running several tests inside one vsim session
## races with on-access virus scanning and shows up as "(vopt-19) Failed to
## access library 'work'" or a codegen "code 12", neither of which is an RTL or
## UVM problem.

transcript on
onerror {quit -code 1 -f}

if {[info exists 1]} { set test_name $1 } else { set test_name core_smoke_test }
if {[info exists 2]} { set do_compile $2 } else { set do_compile 1 }
if {[info exists 3]} { set seed $3 }      else { set seed 1 }
## Words per cache line for tb_axi_top. The testbench passes it to
## cache_axi_master and publishes it to the checkers, so one value drives both.
if {[info exists 4]} { set line_words $4 } else { set line_words 4 }
## Cache lines per way for tb_soc_top: 64 is 1 KiB, 256 is 4 KiB.
if {[info exists 5]} { set line_count $5 } else { set line_count 64 }

## Questa 2024.1 maps the logical library mtiUvm to uvm-1.1d, so UVM 1.2 has to
## be selected explicitly with -L on both vlog and vsim.
if {[info exists ::env(QUESTA_HOME)]} {
    set questa_home $::env(QUESTA_HOME)
} else {
    set questa_home C:/questasim64_2024.1
}
set uvm_lib $questa_home/uvm-1.2
set uvm_src $questa_home/verilog_src/uvm-1.2/src

## Each test class belongs to one top level.
if {[string match "axi_*" $test_name]} {
    set tb_top tb_axi_top
} elseif {[string match "soc_*" $test_name]} {
    set tb_top tb_soc_top
} else {
    set tb_top tb_core_top
}

## Tests that need a program image other than the one compiled into the DUT.
set extra_args {}
if {$tb_top eq "tb_axi_top"} { lappend extra_args "-gLINE_WORDS=$line_words" }
if {$tb_top eq "tb_soc_top"} { lappend extra_args "-gCACHE_LINE_COUNT=$line_count" }
if {$test_name eq "soc_periph_test"} {
    lappend extra_args "+SOC_HEX=verification/uvm/seq/soc_periph_irq.hex"
}

set out_dir  verification/uvm/out
set status_f $out_dir/$test_name.status

file mkdir $out_dir
if {[file exists $status_f]} { file delete -force $status_f }

if {$do_compile} {
    if {[file exists work]} { vdel -lib work -all }
    vlib work
    vlog -sv -f verification/uvm/rtl.f
    vlog -sv -L $uvm_lib +incdir+$uvm_src -f verification/uvm/uvm.f
}

## -onfinish stop hands control back to this script after the UVM $finish, so
## the verdict below actually runs and sets the exit code. Without it vsim -c
## exits straight from $finish and always returns 0.
##
## No +acc is needed: the hierarchical paths in tb_core_top and the bind in
## core_bind.sv are written in the source, so vopt keeps them.
##
## -nodpiexports: this Questa install ships no C compiler, and only the library
## mapped to mtiUvm (uvm-1.1d here) has a prebuilt DPI export wrapper. Loading
## uvm-1.2 through -L therefore stops at "(vsim-7019) Can't locate a C/C++
## compiler". The environment uses no DPI export, so turning the wrapper off is
## safe; uvm_dpi.dll still provides the DPI imports UVM needs. Revisit when
## phase 5 adds uvm_reg backdoor access.
## Built as a list and eval'd, the way tb/run_random_trace.do does it: this
## Questa Tcl does not expand {*} inside a vsim command line.
## The covergroups in env/*_func_coverage.sv are saved to a UCDB that vcover
## merges across tests and seeds. No vlog +cover switch is used: this collects
## functional coverage only, not code coverage, so vsim notes that the code was
## not compiled with coverage options. Add +cover to the vlog lines above if
## code coverage is ever wanted as well.
set sim_args [list -c -coverage -L $uvm_lib -nodpiexports -onfinish stop -sv_seed $seed]
lappend sim_args -suppress 8634
lappend sim_args "+UVM_TESTNAME=$test_name"
lappend sim_args "+STATUS=$status_f"
foreach arg $extra_args { lappend sim_args $arg }
lappend sim_args -l "$out_dir/$test_name.log"
lappend sim_args $tb_top
eval vsim $sim_args

run -all

## Functional coverage. A missing coverage licence must not fail the test, so
## the save is guarded.
if {[catch {coverage save $out_dir/$test_name.ucdb} cov_err]} {
    echo "coverage save skipped: $cov_err"
} else {
    catch {coverage report -detail -output $out_dir/$test_name.cover.txt}
}

set rc 1
if {[file exists $status_f]} {
    set fh [open $status_f r]
    set verdict [string trim [read $fh]]
    close $fh
    echo "UVM status: $verdict"
    if {[string match "PASS*" $verdict]} { set rc 0 }
} else {
    echo "\[FAIL\] $test_name finished without writing a status file"
}

quit -f -code $rc
