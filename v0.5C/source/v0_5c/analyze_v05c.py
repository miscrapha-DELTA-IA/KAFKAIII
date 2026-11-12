#!/usr/bin/env python3
"""Summarize v0.5C Monte Carlo results (descriptive, not confirmatory)."""
from __future__ import annotations
import csv,json,statistics,math
from collections import defaultdict
from pathlib import Path
from scipy.stats import t
HERE=Path(__file__).resolve().parent

def read_rows(path):
    with Path(path).open(newline='') as f:return list(csv.DictReader(f))

def fmean(a):return sum(a)/len(a) if a else None

def mc_ci(vals):
    vals=list(map(float,vals))
    mean=fmean(vals)
    if len(vals)<=1:return [mean,None,None]
    sd=statistics.stdev(vals)
    d=t.ppf(.975,len(vals)-1)*sd/math.sqrt(len(vals))
    return [mean,mean-d,mean+d]

def main():
    root=HERE/'main'
    r=read_rows(root/'policy_results_v0_5c.csv')
    m=read_rows(root/'monthly_state_losses_v0_5c.csv')
    groups=defaultdict(list)
    for row in r:groups[(row['scenario'],row['policy'])].append(row)
    summary=[]
    for (scenario,policy),rs in sorted(groups.items()):
        c=mc_ci(float(x['loss_vs_fixed_oracle_per_1000']) for x in rs)
        summary.append(dict(scenario=scenario,policy=policy,reps=len(rs),
                            mean_loss_per_1000=c[0],MC95_low=c[1],MC95_high=c[2],
                            total_certified_decisions=sum(int(x['valid_decisions']) for x in rs),
                            mean_probe_exposures=fmean([int(x['probe_exposures']) for x in rs]),
                            mean_cohorts_evaluated=fmean([int(x['cohorts_evaluated']) for x in rs])))
    paired=defaultdict(dict)
    for row in r:paired[(row['scenario'],int(row['rep']))][row['policy']]=row
    pairs=[('EXTERNAL_P0_PROBE','EXTERNAL_P0_NO_PROBE'),
           ('EVIDENCE_GATED','ACTIVE_SENTINEL'),
           ('EVIDENCE_GATED','ALWAYS_ON'),
           ('EXTERNAL_P0_NO_PROBE','ACTIVE_SENTINEL')]
    comparisons=[]
    for sc in sorted(set(s for s,_ in paired)):
        runs=[p for (s,rep),p in sorted(paired.items()) if s==sc]
        for p1,p0 in pairs:
            diffs=[float(p[p1]['loss_vs_fixed_oracle_per_1000'])-
                   float(p[p0]['loss_vs_fixed_oracle_per_1000']) for p in runs]
            mn,lo,hi=mc_ci(diffs)
            comparisons.append(dict(scenario=sc,policy_a=p1,policy_b=p0,n=len(diffs),
                                    loss_A_minus_B_per_1000=mn,MC95_low=lo,MC95_high=hi))
    losses=defaultdict(list)
    for row in m:
        losses[(row['scenario'],row['policy'],row['loss_category'])].append(float(row['loss_vs_oracle_month_per_1000']))
    cats=[]
    for (s,p,k),ls in sorted(losses.items()):
        reps=int(len(groups[(s,p)]));
        cats.append(dict(scenario=s,policy=p,loss_category=k,
                         contribution_per_1000_over_horizon=sum(ls)/(reps*20),
                         occupied_months_per_trajectory=len(ls)/reps))
    meta=dict(version='0.5C-exploratory',n_trajectories=len(r),
              decision_events=sum(int(x['valid_decisions']) for x in r),
              n_monthly_records=len(m),
              share_inconclusive_during_decision_horizon=sum(int(x['inconclusive_intervals']) for x in r)/(len(r)*60),
              alpha_family_allocated=.025)
    out=HERE/'analysis_summary_v0_5c.json'
    out.write_text(json.dumps(dict(metadata=meta,summary=summary,paired_comparisons=comparisons,
                                   loss_decomposition=cats),indent=2,ensure_ascii=False))
    for name,records in [('scenario_policy_summary_v0_5c.csv',summary),
                         ('paired_comparisons_v0_5c.csv',comparisons),
                         ('loss_decomposition_v0_5c.csv',cats)]:
        with (HERE/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    print(json.dumps(meta,indent=2))
    for item in comparisons:
        if item['scenario'] in ('beneficial_alert','harmful_wlst','capacity_interference') and item['policy_a']=='EXTERNAL_P0_PROBE':
            print(item)

if __name__=='__main__':main()
