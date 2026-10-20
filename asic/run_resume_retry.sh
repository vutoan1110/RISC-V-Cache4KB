#!/usr/bin/env bash
# NHAT_KY.md 2026-09-28: resume a PD tag from a step, retrying ONLY when the failure looks like this host's
# random fault (SIGSEGV / "Signal 11" / an odbpy Python traceback). Any other failure stops the loop.
#   bash run_resume_retry.sh <tag> <config> <from step> [to step]
# Only the part of error.log written by the current try is judged: OpenLane APPENDS to it across resumes,
# and the first version of this script retried a run that had already finished because of an old entry.
# A failure in the last step, Yosys.EQY, is the known stock-EQY verdict (NHAT_KY.md 2026-09-28), not a crash: done.
# Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
tag=$1 cfg=$2 frm=$3 to=$4
R=$A/soc_dm_4kb/runs/$tag
for try in 1 2 3 4 5 6; do
    [ -e $A/.abort_x_exps ] && { echo "$(date -Is) abort before $tag resume try $try" >> $A/x_exps.log; exit 0; }
    before=$(stat -c %s $R/error.log 2>/dev/null || echo 0)
    echo "$(date -Is) start $tag resume try $try (from $frm${to:+ to $to})" >> $A/x_exps.log
    if [ -n "$to" ]; then
        (cd $A && RESUME=1 CONFIG=$cfg bash run_pd_mk.sh soc_dm_4kb $tag --from $frm --to $to > $A/${tag}_resume.log 2>&1)
    else
        (cd $A && RESUME=1 CONFIG=$cfg bash run_pd_mk.sh soc_dm_4kb $tag --from $frm > $A/${tag}_resume.log 2>&1)
    fi
    rc=$?
    echo "$(date -Is) end $tag resume try $try rc=$rc" >> $A/x_exps.log
    [ $rc -eq 0 ] && exit 0
    last=$(ls -1d $R/[0-9]*/ | tail -1)
    # A SIGSEGV reported as "unexpected error" writes NOTHING to error.log (x_E3R): judge the try by its
    # return code and look for the signature in the new error.log bytes, this try's log and the step log.
    newerr=$(tail -c +$((before + 1)) $R/error.log 2>/dev/null; tail -c 4000 $A/${tag}_resume.log)
    case "$(basename $last)" in
        *-yosys-eqy)
            echo "$(date -Is) $tag: stopped in Yosys.EQY (known stock-EQY verdict), flow otherwise complete" >> $A/x_exps.log
            exit 0 ;;
    esac
    if echo "$newerr" | grep -qa "SIGSEGV\|Signal 11\|odbpy" || grep -qa "Signal 11" $last/*.log 2>/dev/null; then
        echo "$(date -Is) $tag: random-fault signature in $(basename $last) -> retry" >> $A/x_exps.log
        continue
    fi
    echo "$(date -Is) $tag: failure in $(basename $last) is NOT the random-fault signature, stopping" >> $A/x_exps.log
    exit 1
done
echo "$(date -Is) $tag: 6 tries exhausted" >> $A/x_exps.log
exit 1
