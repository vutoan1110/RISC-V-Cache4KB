#!/usr/bin/env bash
# FLOW_JOURNAL Incident 91: retry the step of final3_B that died of a random native crash (SIGSEGV in
# detailed routing, attempt 2; steps 1-44 of this independent run are complete), continuing the same run.
cd "$(dirname "$0")"
echo "$(date -Is) resume final3_B --from Odb.CellFrequencyTables" >> final3_pd.log
RESUME=1 CONFIG=config_FINAL3.json bash run_pd_mk.sh soc_dm_4kb final3_B --from Odb.CellFrequencyTables > final3_B_resume2.log 2>&1
echo "$(date -Is) end final3_B (resume2) rc=$?" >> final3_pd.log
