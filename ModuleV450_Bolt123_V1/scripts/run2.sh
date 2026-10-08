#!/bin/bash
# build -> DSN -> freerouting -> SES import -> zone fill -> DRC

cd /home/claude/work
B=out2/ModuleV450_Bolt123.kicad_pcb
python3 build2.py 2>&1 | grep -v leak; [ ${PIPESTATUS[0]} -eq 0 ] || exit 1
python3 dsn.py export $B out2/board.dsn 2>&1 | grep -v leak || true
rm -f out2/board.ses
timeout ${TMO:-900} java -jar /home/claude/tools/fr-2.0.1.jar -de out2/board.dsn -do out2/board.ses -mp ${MP:-30} --gui.enabled=false >/dev/null 2>&1 || true
grep -iE "unrouted" /tmp/freerouting/freerouting.log | tail -1 | grep -oE "score of.*violations\)" || true
python3 dsn.py import $B out2/board.ses out2/routed.kicad_pcb 2>&1 | grep -v leak
python3 - <<'E' 2>&1 | grep -v leak
import pcbnew
b=pcbnew.LoadBoard('/home/claude/work/out2/routed.kicad_pcb')
pcbnew.WriteDRCReport(b,'/home/claude/work/out2/drc.txt',pcbnew.EDA_UNITS_MILLIMETRES,True)
E
grep -E "^\[" out2/drc.txt | sed 's/\].*/]/' | sort | uniq -c
