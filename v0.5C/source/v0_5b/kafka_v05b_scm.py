#!/usr/bin/env python3
"""KAFKA III v0.5B: modular, *exploratory* synthetic causal simulator.

NOT clinical software. No causal or ethical authorization to suppress/show real alerts.

Patient-level exogenous uniforms are shared across compared policies (common random
numbers). Only the offline evaluator can use potential outcomes and latent U.
The observed monitor only sees counts from mature cohorts; no future data, U or
counterfactuals. The test suite checks those restrictions.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
import numpy as np
from scipy.stats import beta

B = 20
M = 4
N_STRATUM = 125
HORIZON_MONTHS = 3  # 90-day fixed endpoint in this schematic monthly model
MAX_ADMIN_LAG = 2
FULL_MATURITY_LAG = HORIZON_MONTHS + MAX_ADMIN_LAG
ALPHA_MONTHLY_FAMILY = .025
ALPHA_ARM = ALPHA_MONTHLY_FAMILY / (B*M*2)
POLICIES = ('ALWAYS_ON', 'ALWAYS_OFF', 'ACTIVE_SENTINEL',
            'P0_PROBE_ONCE', 'TRIGGER_P0_NO_PROBE', 'TRIGGER_P0_WITH_PROBE',
            'EVIDENCE_GATED')

@dataclass(frozen=True)
class Scenario:
    name: str
    alert_wlst_shift: float = 0.0  # change in log-odds of WLST upon seeing alert
    hidden_u: bool = True
    mnar: bool = False
    mcar: bool = False
    hysteresis: bool = False
    capacity_fraction: float = 1.0
    mislabel: bool = False
    delay_differential: bool = False
    drift: bool = False

SCENARIOS = [
    Scenario('neutral'),
    Scenario('beneficial_alert', alert_wlst_shift=-1.5),
    Scenario('harmful_wlst', alert_wlst_shift=1.8, hidden_u=False),
    Scenario('harmful_hidden_U', alert_wlst_shift=1.8, hidden_u=True),
    Scenario('harmful_MNAR', alert_wlst_shift=1.8, mnar=True, delay_differential=True),
    Scenario('benefit_with_hysteresis', alert_wlst_shift=-1.5, hysteresis=True),
    Scenario('capacity_interference', alert_wlst_shift=-1.5, capacity_fraction=.44),
    Scenario('harmful_record_bias', alert_wlst_shift=1.8, mislabel=True),
    Scenario('neutral_drift', drift=True),
]

@dataclass(frozen=True)
class ObservedCohort:
    cohort_id: str
    month: int
    stratum: int
    ready_month: int
    n0: int
    n1: int
    o0: int
    o1: int
    g0: int
    g1: int
    # No latent U, untreated potential outcomes, truth effect or future results.

@dataclass(frozen=True)
class Evidence:
    lower: float
    upper: float
    n0: int
    n1: int
    mode: str

class ObservedMonitor:
    """No access to world truth. Analyses at most once per cohort."""
    def __init__(self):
        self._pending: list[ObservedCohort] = []
        self._seen: set[str] = set()
        self.evaluations: list[tuple[str, int, Evidence]] = []

    def receive(self, cohort: ObservedCohort, current_month: int):
        if current_month < cohort.ready_month:
            raise ValueError('Future outcome data cannot enter monitor')
        if cohort.cohort_id in self._seen or any(c.cohort_id == cohort.cohort_id for c in self._pending):
            raise ValueError('Duplicate cohort')
        self._pending.append(cohort)

    def evaluate_ready(self, month: int) -> list[tuple[ObservedCohort, Evidence]]:
        ready = [c for c in self._pending if c.ready_month <= month]
        self._pending = [c for c in self._pending if c.ready_month > month]
        out = []
        for c in ready:
            if c.cohort_id in self._seen:
                raise AssertionError('Cohort evaluated twice')
            self._seen.add(c.cohort_id)
            v = effect_interval(c)
            self.evaluations.append((c.cohort_id, month, v))
            out.append((c, v))
        return out


def exact_binom_ci(n: int, success: int, alpha: float) -> tuple[float, float]:
    if not 0 <= success <= n:
        raise ValueError('Bad binomial counts')
    if n == 0: return 0., 1.
    low = 0. if success == 0 else float(beta.ppf(alpha/2, success, n-success+1))
    high = 1. if success == n else float(beta.ppf(1-alpha/2, success+1, n-success))
    return low, high


def exact_one_sided_lower(n: int, success: int, alpha: float) -> float:
    return 0. if success == 0 else float(beta.ppf(alpha, success, n-success+1))


def exact_one_sided_upper(n: int, success: int, alpha: float) -> float:
    return 1. if success == n else float(beta.ppf(1-alpha, success+1, n-success))


def effect_interval(c: ObservedCohort) -> Evidence:
    """Binomial sampling model only (conditional iid patients within stratum-month).

    When outcomes are missing use worst-case partial identification with four
    one-sided bounds, each allocated alpha_arm/2 (two in each arm). Conservative.
    """
    if c.n0 == c.o0 and c.n1 == c.o1:
        l0, u0 = exact_binom_ci(c.n0, c.g0, ALPHA_ARM)
        l1, u1 = exact_binom_ci(c.n1, c.g1, ALPHA_ARM)
        method = 'CP_full'
    else:
        # Within each arm, lower bound on E(OY), upper bound on E(OY+1-O).
        # Two one-sided failures per arm; each gets alpha_arm/2.
        l0 = exact_one_sided_lower(c.n0, c.g0, ALPHA_ARM/2)
        u0 = exact_one_sided_upper(c.n0, c.g0+c.n0-c.o0, ALPHA_ARM/2)
        l1 = exact_one_sided_lower(c.n1, c.g1, ALPHA_ARM/2)
        u1 = exact_one_sided_upper(c.n1, c.g1+c.n1-c.o1, ALPHA_ARM/2)
        method = 'Manski_CP_worstcase'
    return Evidence(max(-1., l1-u0), min(1., u1-l0), c.n0, c.n1, method)


def stable_seed(seed: int, scenario: str, rep: int, month: int) -> int:
    raw = f'{seed}/{scenario}/{rep}/{month}'.encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], 'big')


def sigmoid(x):
    return 1/(1+np.exp(-np.clip(x,-30,30)))


def exogenous(seed: int, sc: Scenario, rep: int, t: int, n: int) -> dict[str, np.ndarray]:
    """Inputs generated without policy name: identical across policy worlds."""
    rng = np.random.default_rng(stable_seed(seed,sc.name,rep,t))
    return dict(x=rng.random(n), u=rng.random(n)<.5,
                z_uniform=rng.random(n), wl_uniform=rng.random(n),
                indicated_uniform=rng.random(n), y_uniform=rng.random(n),
                o_uniform=rng.random(n), lag_uniform=rng.random(n),
                label_uniform=rng.random(n), priority_uniform=rng.random(n))


def exposure(policy: str, q: float, t: int, state: str, probe_authorized: bool) -> tuple[float, str]:
    if policy == 'ALWAYS_ON': return 1., 'ACTIVE'
    if policy == 'ALWAYS_OFF': return 0., 'P0'
    if policy == 'ACTIVE_SENTINEL': return 1-q, 'ACTIVE'
    if policy == 'P0_PROBE_ONCE':
        if t == 7 and probe_authorized: return q, 'PROBE_WAIT'
        return 0., 'P0'
    if policy in ('TRIGGER_P0_NO_PROBE','TRIGGER_P0_WITH_PROBE'):
        if t < 6: return 1-q,'ACTIVE'
        if policy == 'TRIGGER_P0_WITH_PROBE' and t == 8 and probe_authorized:
            return q, 'PROBE_WAIT'
        return 0.,'P0'
    if policy == 'EVIDENCE_GATED':
        if state == 'P0': return 0., 'P0'
        return 1-q,'ACTIVE'
    raise ValueError(policy)


def patient_process(ex: dict, z: np.ndarray, sc: Scenario, history: float,
                    capacity_fraction: float, t: int) -> dict:
    """Patient-level SCM; all mechanisms consume only current/pre-existing causes.

    p0 and p1 are *biological* survival probabilities under T=0 and T=1,
    respectively, not under Z=0/1. The treatment decision mediates Z->Y.
    """
    x=ex['x']; u=ex['u']; n=len(x)
    S=.63+.32*x  # all patients qualify for the selected high-risk-alert cohort
    A=S>=.60
    if not np.all(A): raise AssertionError('Eligibility unexpectedly failed')
    z=np.asarray(z,dtype=bool)
    if len(z)!=n: raise ValueError('wrong length')
    R=np.where(z,S,np.nan)
    # Physician has clinical information U absent from the predictor/controller.
    # Alert can suppress WLST or increase it depending on scenario; H is past only.
    u_term=(-.75*u.astype(float)) if sc.hidden_u else np.zeros(n)
    history_term=(1.4*history) if sc.hysteresis else 0.
    p_wlst=sigmoid(-1.9 + .75*x + u_term + sc.alert_wlst_shift*z + history_term)
    indicated=ex['indicated_uniform']<.96
    W=indicated & (ex['wl_uniform']<p_wlst)
    requested=indicated & ~W
    # Competing requests are rationed only if needed; lack of a bed is never WLST.
    cap=max(0,min(n,int(round(capacity_fraction*n))))
    Q=np.zeros(n,dtype=bool)
    T=requested.copy()
    if np.sum(requested)>cap:
        idx=np.where(requested)[0]
        # In Z=0, physicians use U to prioritize high-expected-gain patients;
        # in Z=1, alert priority depends on an imperfect score unrelated to U.
        priority=np.where(z, .5+S, u.astype(float)*2. + .1*x) + .001*ex['priority_uniform']
        winners=idx[np.argsort(priority[idx],kind='stable')[-cap:]] if cap>0 else np.array([],dtype=int)
        T=np.zeros(n,dtype=bool)
        T[winners]=True
        Q=requested & ~T
    if np.any(W & Q): raise AssertionError('Resource denial falsely labeled WLST')
    if np.any(Q & (~requested)): raise AssertionError('Q without request')
    if np.any(T & (W|Q)): raise AssertionError('Inconsistent support')
    # Biological potential favorable outcome given actually received support.
    # U=1 is high reserve and gets larger physiological benefit from support.
    base=np.clip(.08+.06*u-.025*x + (.11 if sc.drift and t>=10 else 0.),.01,.6)
    support_gain=np.where(u,.55,.17)
    p_y=np.clip(base + support_gain*T,0,1)
    Y=ex['y_uniform']<p_y
    # Objective 90d result; reporting lag and censoring are distinct.
    extra_lag=(ex['lag_uniform']*3).astype(int)
    if sc.delay_differential: extra_lag=np.where(z & (ex['lag_uniform']>.25),2,extra_lag)
    if sc.mnar:
        # Deliberately outcome- and arm-dependent missingness.
        p_observed=np.where(z,np.where(Y,.92,.24),np.where(Y,.32,.94))
    elif sc.mcar:
        p_observed=np.full(n,.80)
    else:
        p_observed=np.ones(n)
    O=ex['o_uniform']<p_observed
    C_obs=np.full(n,np.nan)
    flip=(ex['label_uniform'] < (.08 if sc.mislabel else 0.)) & O
    C_obs[O]=np.logical_xor(Y[O],flip[O]).astype(float)
    return dict(X=x,U=u,S=S,A=A,Z=z,R=R,D=requested,W=W,B_req=requested,
                Q=Q,T=T,Y=Y,O=O,C_obs=C_obs,report_lag=extra_lag,
                p_y=p_y,decision_wlst_prob=p_wlst)


def observed_cohort(process: dict, month: int, stratum: int, run_id: str) -> ObservedCohort:
    z=process['Z']; O=process['O']; C=process['C_obs']
    n0=int(np.sum(~z));n1=int(np.sum(z))
    o0=int(np.sum((~z)&O));o1=int(np.sum(z&O))
    # Inferential comparator operates on RECORDED labels: misspecified under mislabel.
    g0=int(np.sum((~z)&O&(C==1)))
    g1=int(np.sum(z&O&(C==1)))
    return ObservedCohort(f'{run_id}-{month}-{stratum}',month,stratum,
                          month+FULL_MATURITY_LAG,n0,n1,o0,o1,g0,g1)


def simulate_policy(sc: Scenario, policy: str, rep: int, seed: int,
                    q: float=.05, n_stratum: int=N_STRATUM,
                    months: int=B, authorize_probe: bool=True) -> dict:
    if not (0<q<1): raise ValueError('q must be between zero and one')
    n=M*n_stratum
    mon=ObservedMonitor()
    state='ACTIVE' if policy not in ('ALWAYS_OFF','P0_PROBE_ONCE') else 'P0'
    history=0.
    total_y=total_y_expected=0.
    cum_wlst=cum_q=cum_t=cum_z=cum_missing=cum_errors=0
    unexposed_benefit=exposed_harm=0
    individual_truth_available=not (sc.capacity_fraction<1.)
    discoveries=0; false_signals=0; evaluated=0; inconclusive=0
    probe_patients=0; unauthorized_exposure=0
    decisions:list[dict]=[]
    observations:list[dict]=[]
    sealed_cohorts:list[ObservedCohort]=[]  # held by offline data system; never exposed to monitor early
    # release cohorts and make decisions at beginnings of each month, before exposure
    for t in range(months):
        released=[c for c in sealed_cohorts if c.ready_month<=t]
        sealed_cohorts=[c for c in sealed_cohorts if c.ready_month>t]
        for c in released: mon.receive(c,current_month=t)
        due=mon.evaluate_ready(t)
        for co, ev in due:
            evaluated+=1
            if ev.lower<=0<=ev.upper:inconclusive+=1
            if ev.upper<0 or ev.lower>0:
                discoveries+=1
                if policy=='EVIDENCE_GATED' and state=='ACTIVE' and ev.upper<0:
                    state='P0'
                    decisions.append(dict(month=t,action='P0_from_negative_CI',cohort=co.cohort_id))
        p, st=exposure(policy,q,t,state,authorize_probe)
        if st=='PROBE_WAIT' and not authorize_probe:
            raise AssertionError('probe exposure without scenario authorization')
        # Generate the full hospital cohort once per month. Resource allocation
        # operates across ALL four strata; no artificial stratum-specific beds.
        ex=exogenous(seed,sc,rep,t,n)
        z=ex['z_uniform']<p
        process=patient_process(ex,z,sc,history,sc.capacity_fraction,t)
        for m in range(M):
            sel=slice(m*n_stratum,(m+1)*n_stratum)
            pr={k:(v[sel] if isinstance(v,np.ndarray) and len(v)==n else v)
                for k,v in process.items()}
            sealed_cohorts.append(observed_cohort(pr,t,m,f'{sc.name}-{rep}-{policy}'))
        total_y+=int(np.sum(process['Y']))
        total_y_expected+=float(np.sum(process['p_y']))
        cum_wlst+=int(np.sum(process['W']))
        cum_q+=int(np.sum(process['Q']))
        cum_t+=int(np.sum(process['T']))
        cum_z+=int(np.sum(z))
        cum_missing+=int(np.sum(~process['O']))
        cum_errors+=int(np.sum(process['O'] & (process['C_obs']!=process['Y'])))
        if st=='PROBE_WAIT':probe_patients+=int(np.sum(z))
        if st=='PROBE_WAIT' and not authorize_probe:unauthorized_exposure+=int(np.sum(z))
        if individual_truth_available:
            # Off-line, policy-coupled potential outcomes; never passed to monitor.
            p0=patient_process(ex,np.zeros(n,dtype=bool),sc,history,1.,t)
            p1=patient_process(ex,np.ones(n,dtype=bool),sc,history,1.,t)
            y0=p0['Y'];y1=p1['Y']
            unexposed_benefit+=int(np.sum((~z)&y1&(~y0)))
            exposed_harm+=int(np.sum(z&y0&(~y1)))
        if sc.hysteresis:
            history=.8*history+.2*float(np.mean(z))
        observations.append(dict(month=t,policy=policy,exposure_probability=p,
                                 state=st,monitor_seen=len(mon.evaluations)))
    # Outcomes with administrative lag are evaluated only *after* last exposure
    for t in range(months,months+FULL_MATURITY_LAG+1):
        released=[c for c in sealed_cohorts if c.ready_month<=t]
        sealed_cohorts=[c for c in sealed_cohorts if c.ready_month>t]
        for c in released: mon.receive(c,current_month=t)
        due=mon.evaluate_ready(t)
        for co,ev in due:
            evaluated+=1
            if ev.lower<=0<=ev.upper:inconclusive+=1
            if ev.upper<0 or ev.lower>0:discoveries+=1
    if sealed_cohorts or len(mon._seen) != months*M: raise AssertionError('lost or repeated cohort')
    if unauthorized_exposure:raise AssertionError('unauthorized probe')
    total_patients=months*n
    return dict(scenario=sc.name,policy=policy,rep=rep,seed=seed,q=q,
                n=total_patients,good=total_y,expected_good=total_y_expected,
                good_rate=total_y/total_patients,
                wlsts=cum_wlst,capacity_denials=cum_q,treated=cum_t,
                alerts_shown=cum_z,missing=cum_missing,mislabels=cum_errors,
                probe_exposures=probe_patients,
                missed_benefit=unexposed_benefit if individual_truth_available else None,
                exposed_harm=exposed_harm if individual_truth_available else None,
                monitoring_evaluated=evaluated,monitoring_inconclusive=inconclusive,
                monitoring_conclusive=discoveries,observations=observations,
                decisions=decisions)


def run_experiment(out: Path, reps: int=25, seed: int=20261110,
                   q: float=.05, months: int=B, n_stratum: int=N_STRATUM,
                   scenarios: list[Scenario]|None=None, policies:tuple[str,...]|None=None):
    out.mkdir(parents=True,exist_ok=True)
    scenarios=scenarios or SCENARIOS
    policies=policies or POLICIES
    rows=[];examples={}
    for sc in scenarios:
        for rep in range(reps):
            for policy in policies:
                r=simulate_policy(sc,policy,rep,seed,q,n_stratum,months)
                examples.setdefault(sc.name+'|'+policy,dict(states=r['observations'][:11],
                                                            decisions=r['decisions']))
                rows.append({k:v for k,v in r.items() if k not in ('observations','decisions')})
    fields=list(rows[0])
    with (out/'results_patient_policy_v0_5b.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader();w.writerows(rows)
    summaries=[]
    for sc in scenarios:
        for policy in policies:
            matching=[x for x in rows if x['scenario']==sc.name and x['policy']==policy]
            item=dict(scenario=sc.name,policy=policy,reps=len(matching))
            for k in ['good_rate','wlsts','capacity_denials','treated','alerts_shown',
                      'missing','mislabels','probe_exposures','monitoring_conclusive',
                      'monitoring_inconclusive','missed_benefit','exposed_harm']:
                values=[float(r[k]) for r in matching if r[k] is not None]
                item[k+'_mean']=float(np.mean(values)) if values else None
            summaries.append(item)
    # Best fixed comparator is evaluated on same synthetic candidates and exogenous
    # streams; do not describe as cluster randomized identification.
    for s in scenarios:
        sn=[x for x in summaries if x['scenario']==s.name]
        best=max(next(x for x in sn if x['policy']==p)['good_rate_mean'] for p in ('ALWAYS_ON','ALWAYS_OFF'))
        for x in sn:x['gap_to_best_fixed_pp']=100*(best-x['good_rate_mean'])
    (out/'summary_v0_5b.json').write_text(json.dumps(summaries,indent=2))
    (out/'state_trace_examples.json').write_text(json.dumps(examples,indent=2))
    cfg=dict(version='0.5B-exploratory',seed=seed,reps=reps,q=q,months=months,
             strata=M,patients_per_stratum_month=n_stratum,horizon_months=HORIZON_MONTHS,
             max_admin_lag=MAX_ADMIN_LAG,alpha_monthly_family=ALPHA_MONTHLY_FAMILY,
             alpha_arm=ALPHA_ARM,scenarios=[asdict(s) for s in scenarios],policies=list(policies))
    (out/'configuration_v0_5b.json').write_text(json.dumps(cfg,indent=2))
    return summaries


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--reps',type=int,default=25)
    ap.add_argument('--seed',type=int,default=20261110)
    ap.add_argument('--q',type=float,default=.05)
    ap.add_argument('--n-stratum',type=int,default=N_STRATUM)
    ap.add_argument('--months',type=int,default=B)
    args=ap.parse_args()
    out=run_experiment(args.out,args.reps,args.seed,args.q,args.months,args.n_stratum)
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
