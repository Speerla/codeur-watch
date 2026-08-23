# -*- coding: utf-8 -*-
"""
Point d'entrée sans fenêtre, pour la tâche planifiée Windows.
Fait une passe et écrit tout dans veille.log.
"""

import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "veille.log")
sys.path.insert(0, HERE)

# on garde le journal court
if os.path.exists(LOG) and os.path.getsize(LOG) > 1_000_000:
    with open(LOG, encoding="utf-8", errors="replace") as f:
        fin = f.readlines()[-500:]
    with open(LOG, "w", encoding="utf-8") as f:
        f.writelines(fin)

journal = open(LOG, "a", encoding="utf-8", errors="replace")
sys.stdout = journal
sys.stderr = journal

sys.argv = ["watch.py", "--notify", "--max-age", "3",
            "--min-score", "8", "--min-budget", "500"]

try:
    import watch
    watch.main()
except Exception as e:
    print("%s  PLANTAGE : %s" % (datetime.now().strftime("%H:%M:%S"), e))
finally:
    journal.flush()
    journal.close()
