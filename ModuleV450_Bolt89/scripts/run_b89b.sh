#!/bin/bash
# build -> DSN -> freerouting -> SES import -> zone fill -> DRC

cd /home/claude/work
B=b89b/ModuleV450_Bolt89.kicad_pcb
python3 build_b89b.py 2>&1 | grep -v leak; [ ${PIPESTATUS[0]} -eq 0 ] || exit 1
python3 dsn.py export $B b89b/board.dsn 2>&1 | grep -v leak || true
rm -f b89b/board.ses
timeout ${TMO:-900} java -jar /home/claude/tools/fr-2.0.1.jar -de b89b/board.dsn -do b89b/board.ses -mp ${MP:-30} --gui.enabled=false >/dev/null 2>&1 || true
grep -iE "unrouted" /tmp/freerouting/freerouting.log | tail -1 | grep -oE "score of.*violations\)" || true
python3 dsn.py import $B b89b/board.ses b89b/routed.kicad_pcb 2>&1 | grep -v leak
python3 - <<'E' 2>&1 | grep -v leak
import pcbnew
b=pcbnew.LoadBoard('/home/claude/work/b89b/routed.kicad_pcb')
pcbnew.WriteDRCReport(b,'/home/claude/work/b89b/drc.txt',pcbnew.EDA_UNITS_MILLIMETRES,True)
E
grep -E "^\[" b89b/drc.txt | sed 's/\].*/]/' | sort | uniq -c
