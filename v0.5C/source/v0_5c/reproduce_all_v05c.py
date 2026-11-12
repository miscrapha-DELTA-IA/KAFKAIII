#!/usr/bin/env python3
"""Reproduce synthetic v0.5C tables; run from the v0_5c folder."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
from kafka_v05c_decision import run_v05c,Scenario

HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--full',action='store_true',help='25 repetitions as in the released results; otherwise 2')
    ap.add_argument('--seed',type=int,default=20261110)
    a=ap.parse_args()
    reps=25 if a.full else 2
    subprocess.run([sys.executable,'-m','unittest','-v','test_kafka_v05c.py'],cwd=HERE,check=True)
    run_v05c(HERE/'main',reps=reps,seed=a.seed,q=.05)
    scs=[Scenario('beneficial_alert',alert_wlst_shift=-1.5),
         Scenario('harmful_wlst',alert_wlst_shift=1.8,hidden_u=False)]
    for q in (.01,.02):
        run_v05c(HERE/f'q{int(q*100):02}',reps=reps,seed=a.seed,q=q,scenarios=scs)
    subprocess.run([sys.executable,'analyze_v05c.py'],cwd=HERE,check=True)
    print(f'Finished reproducible v0.5C runs, reps={reps}')
if __name__=='__main__':main()
