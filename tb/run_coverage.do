transcript on
onerror {quit -code 1 -f}
do tb/compile_active_design.do

file mkdir verification/results
vsim -coverage -onfinish stop -voptargs=+acc work.tb_directed_isa
run -all
coverage save verification/results/directed_isa.ucdb
quit -sim

echo {[PASS] Directed ISA functional coverage database written}
