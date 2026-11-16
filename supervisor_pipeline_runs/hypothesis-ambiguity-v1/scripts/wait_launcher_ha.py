#!/opt/miniconda3/bin/python
"""Blocks until the single-run launcher log contains '== launcher finished' (poll 20 s, max 4 h). Usage: wait_launcher_ha.py <log>"""
import sys, time, os
log = sys.argv[1]; t0 = time.time()
while time.time() - t0 < 4 * 3600:
    if os.path.exists(log) and '== launcher finished' in open(log, errors='replace').read(): print('launcher finished after %.0f s' % (time.time() - t0)); sys.exit(0)
    time.sleep(20)
print('waiter gave up after 4 h'); sys.exit(1)
