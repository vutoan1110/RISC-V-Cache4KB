#!/usr/bin/env bash
# Negative control for eq.sh: a +2 mutant of one counter must NOT be proven.
cd "$(dirname "$0")"
sed -e 's|^eq perf_counters .*|eq perf_counters perf_counters_old.v perf_counters_mutant.v|' -e 's|^eq datapath .*||' eq.sh > eq_neg_body.sh
sed -i 's/eq_\$m\./eqneg_$m./g' eq_neg_body.sh
bash eq_neg_body.sh
