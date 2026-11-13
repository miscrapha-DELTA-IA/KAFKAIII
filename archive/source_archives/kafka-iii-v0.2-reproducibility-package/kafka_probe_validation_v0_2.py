#!/usr/bin/env python3
"""KAFKA III v0.2 -- conservative coverage / informativity audit.

Scientific scope: stationary, bounded binary outcomes, independent Bernoulli assignments
within exposure-month/stratum, fixed n, mature and complete follow-up. No clinical claim.
The two coexisting analysis families split the global alpha: monthly 2.5%,
final pooled 2.5%; every comparison below uses the SAME simulated patients.

Run: python kafka_probe_validation_v0_2.py --replications 10000 --output DIRECTORY
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from math import log, sqrt
import numpy as np

ALPHA = 0.05
M, B, N_PER_BLOCK_PER_STRATUM = 4, 20, 125
ALPHA_MONTHLY, ALPHA_FINAL = 0.025, 0.025
# alpha per arm; family 1: 4 strata * 20 months * 2 arms;
# family 2: 4 strata * 2 arms (ONE analysis at end, under stationarity).
A_MON = ALPHA_MONTHLY / (2*M*B)
A_FINAL = ALPHA_FINAL / (2*M)
HARM_MARGIN = 0.05 # ONLY an illustration, not a validated clinical threshold
SEED = 20261109
SCENARIOS = {
    'null': (0.55, 0.55),
    'benefit_5pp': (0.55, 0.60),
    'harm_5pp': (0.60, 0.55),
    'harm_25pp': (0.70, 0.45),
    'harm_60pp': (0.80, 0.20),
}


def interval_from_aggregates(n0: np.ndarray, y0: np.ndarray,
                             n1: np.ndarray, y1: np.ndarray,
                             alpha_arm: float):
    # For an empty arm, [0,1] is the appropriate vacuous interval.
    k = log(2.0 / alpha_arm) / 2.0
    with np.errstate(divide='ignore', invalid='ignore'):
        p0 = np.divide(y0, n0, out=np.zeros_like(y0, dtype=float), where=n0>0)
        p1 = np.divide(y1, n1, out=np.zeros_like(y1, dtype=float), where=n1>0)
        r0 = np.sqrt(np.divide(k, n0, out=np.full_like(p0, np.inf), where=n0>0))
        r1 = np.sqrt(np.divide(k, n1, out=np.full_like(p1, np.inf), where=n1>0))
    lo0 = np.maximum(0.0, p0 - r0)
    hi0 = np.minimum(1.0, p0 + r0)
    lo1 = np.maximum(0.0, p1 - r1)
    hi1 = np.minimum(1.0, p1 + r1)
    lo = lo1 - hi0
    hi = hi1 - lo0
    return lo, hi


def summarize(lo, hi, nrare, truth):
    harm = hi < -HARM_MARGIN
    noninferior = lo > -HARM_MARGIN
    benefit = lo > 0.0
    indeterminate = ~(harm | noninferior)
    return dict(
        coverage_percent=round(float(100*np.mean((lo<=truth)&(hi>=truth))),3),
        median_width=round(float(np.median(hi-lo)),4),
        p90_width=round(float(np.quantile(hi-lo,0.9)),4),
        empty_rare_arm_percent=round(float(100*np.mean(nrare==0)),3),
        harm_evidence_percent=round(float(100*np.mean(harm)),3),
        reentry_noninferiority_percent=round(float(100*np.mean(noninferior)),3),
        proven_benefit_percent=round(float(100*np.mean(benefit)),3),
        inconclusive_percent=round(float(100*np.mean(indeterminate)),3),
    )


def run(replications, seed):
    rng = np.random.default_rng(seed)
    rows = []
    annual = []
    for rare_side in ['withhold_Z0_rare', 'probe_Z1_rare']:
        for q in [0.01, 0.02, 0.05]:
            for scenario, (mu0, mu1) in SCENARIOS.items():
                shape = (replications, M, B)
                nrare = rng.binomial(N_PER_BLOCK_PER_STRATUM, q, size=shape)
                if rare_side == 'withhold_Z0_rare':
                    n0, n1 = nrare, N_PER_BLOCK_PER_STRATUM-nrare
                else:
                    n1, n0 = nrare, N_PER_BLOCK_PER_STRATUM-nrare
                y0 = rng.binomial(n0, mu0)
                y1 = rng.binomial(n1, mu1)
                truth = mu1-mu0
                lo_m, hi_m = interval_from_aggregates(n0,y0,n1,y1,A_MON)
                n0_f, n1_f = n0.sum(axis=2), n1.sum(axis=2)
                y0_f, y1_f = y0.sum(axis=2), y1.sum(axis=2)
                lo_f, hi_f = interval_from_aggregates(n0_f,y0_f,n1_f,y1_f,A_FINAL)
                month_ok = np.all((lo_m<=truth)&(hi_m>=truth),axis=(1,2))
                final_ok = np.all((lo_f<=truth)&(hi_f>=truth),axis=1)
                base = dict(mode=rare_side, q_percent=int(q*100), scenario=scenario,
                            true_delta=round(truth,4), replications=replications)
                for kind, lo, hi, nr in [('monthly',lo_m,hi_m,nrare),
                                          ('pooled_20m_stationary',lo_f,hi_f,nrare.sum(axis=2))]:
                    rows.append({**base, 'analysis':kind, **summarize(lo,hi,nr,truth)})
                annual.append({**base,
                   'simultaneous_monthly_coverage_percent':round(float(100*month_ok.mean()),3),
                   'simultaneous_pooled_coverage_percent':round(float(100*final_ok.mean()),3),
                   'simultaneous_both_families_coverage_percent':round(float(100*np.mean(month_ok & final_ok)),3),
                   'monthly_any_harm_evidence_percent':round(float(100*np.mean(np.any(hi_m< -HARM_MARGIN,axis=(1,2)))),3),
                   'monthly_any_noninferiority_percent':round(float(100*np.mean(np.any(lo_m> -HARM_MARGIN,axis=(1,2)))),3),
                })
    return rows,annual


def test_invariants():
    # 1. Empty arm cannot yield falsely decisive sign; observe informative other arm.
    for n, y in [(0,0),(5,5),(125,100)]:
        lo, hi = interval_from_aggregates(np.array([0]),np.array([0]),
                                          np.array([n]),np.array([y]),A_MON)
        assert lo[0] <= 0 <= hi[0]
    # 2. Known equal binary samples produce bounded intervals with expected direction.
    lo, hi = interval_from_aggregates(np.array([2500]),np.array([1500]),
                                      np.array([2500]),np.array([1375]),A_FINAL)
    assert -1 <= lo[0] <= hi[0] <= 1
    assert lo[0] < -0.05 < hi[0] # conservative interval includes the -0.05 truth
    # 3. No inferential decision before follow-up is mature, no silent alpha reset.
    assert reentry_transition('PROBE_WAIT',(-1,1),mature=False,clinical_clearance=True)=='PROBE_WAIT'
    assert reentry_transition('PROBE_WAIT',(-0.4,0.2),mature=True,clinical_clearance=True)=='P0'
    assert reentry_transition('PROBE_WAIT',(-0.01,0.15),mature=True,clinical_clearance=False)=='P0'
    assert reentry_transition('PROBE_WAIT',(-0.01,0.15),mature=True,clinical_clearance=True)=='REENTRY_RESTRICTED'


def reentry_transition(state, interval, *, mature, clinical_clearance, harm_margin=HARM_MARGIN):
    """Pure illustrative policy: not a medical recommendation; decision is NORMATIVE."""
    if state!='PROBE_WAIT':
        raise ValueError('Only a mature probe may be assessed for reentry')
    if not mature:
        return 'PROBE_WAIT'
    lo,hi=interval
    if hi < -harm_margin:
        return 'P0'
    if lo > -harm_margin and clinical_clearance:
        return 'REENTRY_RESTRICTED'
    return 'P0'  # equivocal / no authority to reenter; new probe needs preallocated alpha


def save_csv(path,rows):
    with open(path,'w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)



def drift_negative_control(replications, seed):
    """Counterexample: no treatment effect in ANY month, but p_rare and baseline shift.

    Retention: 1% in early months with favorable-outcome rate 5%; 5% in later
    months with favorable-outcome rate 95%. Naively pooling without blocking
    can create false evidence of effect even though Δ_b=0 for ALL 20 months.
    """
    rng = np.random.default_rng(seed+17)
    sh=(replications,M,B)
    q=np.array([0.01]*10+[0.05]*10, dtype=float)[None,None,:]
    mu=np.array([0.05]*10+[0.95]*10, dtype=float)[None,None,:]
    n0=rng.binomial(N_PER_BLOCK_PER_STRATUM,q,size=sh)
    n1=N_PER_BLOCK_PER_STRATUM-n0
    y0=rng.binomial(n0,mu)
    y1=rng.binomial(n1,mu)
    lo_m,hi_m=interval_from_aggregates(n0,y0,n1,y1,A_MON)
    lo_p,hi_p=interval_from_aggregates(n0.sum(axis=2),y0.sum(axis=2),
                                       n1.sum(axis=2),y1.sum(axis=2),A_FINAL)
    delta_naive=np.divide(y1.sum(axis=2), n1.sum(axis=2)) - np.divide(y0.sum(axis=2),n0.sum(axis=2))
    # Valid aggregation: take fixed-weight average of the simultaneously covered MONTHLY intervals.
    lo_weighted=lo_m.mean(axis=2)
    hi_weighted=hi_m.mean(axis=2)
    return dict(n_replications=replications,true_delta_every_month=0,
      monthly_simultaneous_coverage_percent=round(float(100*np.mean(np.all((lo_m<=0)&(hi_m>=0),axis=(1,2)))),3),
      pooled_naive_coverage_percent=round(float(100*np.mean((lo_p<=0)&(hi_p>=0))),3),
      blockwise_weighted_coverage_percent=round(float(100*np.mean((lo_weighted<=0)&(hi_weighted>=0))),3),
      blockwise_weighted_false_harm_percent=round(float(100*np.mean(hi_weighted < -HARM_MARGIN)),3),
      blockwise_weighted_median_width=round(float(np.median(hi_weighted-lo_weighted)),3),
      pooled_naive_false_harm_U_lt_minus_5pp_percent=round(float(100*np.mean(hi_p< -HARM_MARGIN)),3),
      pooled_naive_false_sign_U_lt_0_percent=round(float(100*np.mean(hi_p<0)),3),
      mean_naive_pooled_delta=round(float(np.mean(delta_naive)),4),
      note='Pooled Hoeffding is INAPPLICABLE: different months have different outcomes and rare-arm assignment rates. Monthly blockwise inference stays valid.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--replications',type=int,default=10000)
    parser.add_argument('--seed',type=int,default=SEED)
    parser.add_argument('--output',default=str(Path(__file__).parent))
    a=parser.parse_args()
    test_invariants()
    rows,global_rows = run(a.replications,a.seed)
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    save_csv(out/'resultados_intervalos_v0_2.csv',rows)
    save_csv(out/'cobertura_simultanea_v0_2.csv',global_rows)
    stress=drift_negative_control(a.replications,a.seed)
    (out/'contraexemplo_drift_v0_2.json').write_text(json.dumps(stress,indent=2,ensure_ascii=False),encoding='utf-8')
    details={"version":"v0.2", "replications":a.replications,"seed":a.seed,
      "M":M,"B":B,"n_per_stratum_per_month":N_PER_BLOCK_PER_STRATUM,
      "n_per_stratum_total":B*N_PER_BLOCK_PER_STRATUM,
      "alpha_global":ALPHA,"alpha_monthly_family":ALPHA_MONTHLY,
      "alpha_final_family":ALPHA_FINAL,"alpha_per_monthly_arm":A_MON,
      "alpha_per_pooled_arm":A_FINAL,"harm_margin_illustrative":HARM_MARGIN,
      "scenarios":SCENARIOS,"basis":"i.i.d. binary Bernoulli outcomes within and across 20 months, stationary",
      "endpoints":"fixed complete follow-up; rare arm independently randomized within stratum/month",
      "note":"Pooled 20m inference is valid only under stationarity; per-month analyses target month-specific effects. This is a diagnostic experiment, not a clinical trial."}
    (out/'configuracao_v0_2.json').write_text(json.dumps(details,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({"config":details,"rows":rows,"simultaneous":global_rows,"drift_stress":stress},ensure_ascii=False))

if __name__=='__main__':main()
