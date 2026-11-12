#!/usr/bin/env python3
"""KAFKA III v0.5C: exploratory dynamic authority states and paired policy losses.

Synthetic research only. Never a clinical-decision system. Reuses the v0.5B SCM,
with its assumptions, flaws and uncalibrated parameters. An independent design
certificate must be passed; controller never sees causal truths or scenario name.
"""
from __future__ import annotations
import argparse, csv, json, math, sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'v0_5b'))
from kafka_v05b_scm import (  # type: ignore
    Scenario, SCENARIOS, ObservedMonitor, ObservedCohort, Evidence,
    exogenous, patient_process, observed_cohort, FULL_MATURITY_LAG,
    N_STRATUM, M, B, ALPHA_ARM,
)

POLICIES = ('ALWAYS_ON','ALWAYS_OFF','ACTIVE_SENTINEL','EVIDENCE_GATED',
            'EXTERNAL_P0_NO_PROBE','EXTERNAL_P0_PROBE','P0_PROBE_ONCE')

@dataclass(frozen=True)
class Governance:
    q: float = .05
    restricted_exposure: float = .25
    external_suspend_month: int = 6
    external_probe_month: int = 7
    proactive_p0_probe_month: int = 7
    probe_approval: bool = True  # synthetic authorization; NOT real ethics approval
    certified_individual_inference: bool = True # design certificate, not causal truth
    max_probes: int = 1
    require_positive_all_strata: bool = True
    extra_operating_cost_per_alert: float = 0.0 # hypothetical utility add-on; 0 in primary
    def __post_init__(self):
        if not (0 < self.q <= .5):raise ValueError('q outside supported range')
        if not (0 < self.restricted_exposure < 1):raise ValueError('restricted exposure outside 0..1')
        if self.max_probes<0:raise ValueError('negative probes')

@dataclass(frozen=True)
class ControllerInput:
    month: int
    cohort_id: str
    cohort_month: int
    cohort_stratum: int
    lower: float
    upper: float
    mode: str
    n0: int
    n1: int

class Controller:
    """Finite state governance; only gets observed confidence intervals.

    ACTIVE -> P0 only on certified evidence of harm from an ACTIVE/RESTRICTED cohort.
    P0 -> PROBE_WAIT only via explicit synthetic authorization (one enrollment month).
    PROBE_WAIT -> REENTRY_RESTRICTED only if certified benefit across all strata of
       the *probe cohort*, after every outcome has matured. Otherwise -> P0.
    REENTRY_RESTRICTED -> ACTIVE only if certified benefit across all strata of a
       newly matured restricted-exposure cohort. Otherwise stay restricted; harm -> P0.
    Certifying a causal sign from individual CP is DISALLOWED under interference or
    outcome-label corruption in this implementation.
    """
    def __init__(self, governance: Governance, initial: str='ACTIVE'):
        if initial not in ('ACTIVE','P0'):raise ValueError(initial)
        self.gov=governance
        self.state=initial
        self.p0_since=0 if initial=='P0' else None
        self.probe_count=0
        self.probe_month:Optional[int]=None
        self.probe_enroll_this_month=False
        self.probe_armed=False
        self.restricted_since: Optional[int]=None
        self.evidence_history: dict[int,dict[int,ControllerInput]]={}
        self.cohort_origin: dict[int,str]={}
        self.events=[]
        self.valid_decisions=0
        self.invalid_evidence_blocked=0
        self.inconclusive_evals=0
        self.seen_cohorts=set()

    def _record(self,month:int,action:str,**attrs):
        self.events.append(dict(month=month, action=action,**attrs))

    def consume(self,month:int, reports:list[ControllerInput]):
        for r in reports:
            if r.month!=month:raise AssertionError('wrong report time')
            if r.cohort_id in self.seen_cohorts:raise AssertionError('repeated outcome cohort')
            self.seen_cohorts.add(r.cohort_id)
            if r.cohort_month >= month:raise AssertionError('future cohort')
            if not (-1<=r.lower<=r.upper<=1):raise AssertionError('invalid CI')
            if r.lower<=0<=r.upper:self.inconclusive_evals+=1
            if not self.gov.certified_individual_inference:
                # Data may establish completion of a probe, but the inferred sign
                # is NOT decision-eligible under interference/label corruption.
                if r.upper<0 or r.lower>0:self.invalid_evidence_blocked+=1
                if self.state=='PROBE_WAIT' and r.cohort_month==self.probe_month:
                    self.evidence_history.setdefault(r.cohort_month,{})[r.cohort_stratum]=r
                continue
            origin=self.cohort_origin.get(r.cohort_month,'UNKNOWN')
            if origin=='UNKNOWN': raise AssertionError('unregistered cohort origin')
            if origin=='ACTIVE' and self.state=='ACTIVE' and r.upper<0:
                self.state='P0';self.p0_since=month
                self._record(month,'SUSPEND_ON_CERTIFIED_NEGATIVE',cohort=r.cohort_id)
                self.valid_decisions+=1
            if origin=='REENTRY_RESTRICTED' and self.state=='REENTRY_RESTRICTED' and r.upper<0:
                self.state='P0';self.p0_since=month;self.restricted_since=None
                self._record(month,'ROLLBACK_ON_CERTIFIED_NEGATIVE',cohort=r.cohort_id)
                self.valid_decisions+=1
            if self.state=='PROBE_WAIT' and r.cohort_month==self.probe_month:
                self.evidence_history.setdefault(r.cohort_month,{})[r.cohort_stratum]=r
            if self.state=='REENTRY_RESTRICTED' and origin=='REENTRY_RESTRICTED':
                self.evidence_history.setdefault(r.cohort_month,{})[r.cohort_stratum]=r
        if self.state=='PROBE_WAIT' and self.probe_month is not None:
            c=self.evidence_history.get(self.probe_month,{})
            if len(c)==M:
                positive=(self.gov.certified_individual_inference and all(v.lower>0 for v in c.values()))
                if positive:
                    self.state='REENTRY_RESTRICTED';self.restricted_since=month
                    self._record(month,'REENTRY_ON_CERTIFIED_POSITIVE',from_probe=self.probe_month)
                    self.valid_decisions+=1
                else:
                    self.state='P0';self.p0_since=month
                    why=('PROBE_NOT_DECISION_ELIGIBLE' if not self.gov.certified_individual_inference
                         else 'PROBE_INCONCLUSIVE_OR_NONPOSITIVE')
                    self._record(month,why,from_probe=self.probe_month)
                self.probe_month=None
        if self.state=='REENTRY_RESTRICTED' and self.restricted_since is not None:
            eligible=[t for t,rs in self.evidence_history.items() if t>=self.restricted_since and len(rs)==M and self.cohort_origin.get(t)=='REENTRY_RESTRICTED']
            if eligible:
                t0=min(eligible)
                if all(v.lower>0 for v in self.evidence_history[t0].values()):
                    self.state='ACTIVE';self._record(month,'FULL_REENTRY_ON_CERTIFIED_POSITIVE',cohort_month=t0)
                    self.valid_decisions+=1
                # nonpositive is not claimed as evidence of harm; remain restricted

    def decide_exposure(self, month:int, policy:str) -> tuple[float,str,bool]:
        if policy=='ALWAYS_ON':return 1.0,'ACTIVE',False
        if policy=='ALWAYS_OFF':return 0.0,'P0',False
        if policy=='ACTIVE_SENTINEL':return 1-self.gov.q,'ACTIVE',False
        if policy in ('EXTERNAL_P0_NO_PROBE','EXTERNAL_P0_PROBE') and month==self.gov.external_suspend_month and self.state!='P0':
            self.state='P0';self.p0_since=month
            self._record(month,'SUSPENSION_EXTERNAL_SCHEDULE_NOT_CAUSALLY_DETECTED')
        if policy=='P0_PROBE_ONCE' and month==0:
            self.state='P0';self.p0_since=0
        self.probe_enroll_this_month=False
        # Authorized clinical investigation is simulated, not assumed ethically permissible.
        authorizable=(policy in ('EXTERNAL_P0_PROBE','P0_PROBE_ONCE','EVIDENCE_GATED'))
        allowed_time=(month==self.gov.external_probe_month if policy=='EXTERNAL_P0_PROBE'
                      else month==self.gov.proactive_p0_probe_month if policy=='P0_PROBE_ONCE'
                      else self.p0_since is not None and month>self.p0_since)
        if (authorizable and self.state=='P0' and allowed_time and self.gov.probe_approval
                and self.probe_count < self.gov.max_probes):
            self.state='PROBE_WAIT';self.probe_enroll_this_month=True
            self.probe_month=month;self.probe_count+=1
            self._record(month,'SYNTHETIC_AUTHORIZED_PROBE_ENROLL',probe_number=self.probe_count)
            return self.gov.q,'PROBE_WAIT',True
        if self.state=='PROBE_WAIT':return 0.0,'PROBE_WAIT',False
        if self.state=='P0':return 0.0,'P0',False
        if self.state=='REENTRY_RESTRICTED':return self.gov.restricted_exposure,'REENTRY_RESTRICTED',False
        return 1-self.gov.q,'ACTIVE',False


def default_design_certificate(sc: Scenario)->bool:
    """Protocol-level synthetic certification, not inferred hidden harm or benefit.

    Capacity interference violates the individual estimand; mislabels invalidate
    interpretation for biological Y. We flag those settings as not certified.
    In real data, an unknown mislabel mechanism would not be detectable this way.
    """
    return sc.capacity_fraction>=1 and not sc.mislabel


def simulate_v05c(sc:Scenario,policy:str,rep:int,seed:int,gov:Governance,
                  months:int=B,n_stratum:int=N_STRATUM) ->dict:
    if policy not in POLICIES:raise ValueError(policy)
    if months > B:raise ValueError('More months than pre-allocated alpha family; revise spending plan')
    initial='P0' if policy in ('ALWAYS_OFF','P0_PROBE_ONCE') else 'ACTIVE'
    ctl=Controller(gov,initial=initial)
    monitor=ObservedMonitor()
    sealed:list[ObservedCohort]=[]
    monthly=[]
    n=M*n_stratum
    history=0.
    for t in range(months):
        to_release=[c for c in sealed if c.ready_month<=t]
        sealed=[c for c in sealed if c.ready_month>t]
        for c in to_release: monitor.receive(c,current_month=t)
        due=monitor.evaluate_ready(t)
        inputs=[ControllerInput(t,c.cohort_id,c.month,c.stratum,ev.lower,ev.upper,ev.mode,ev.n0,ev.n1) for c,ev in due]
        ctl.consume(t,inputs)
        p,origin,is_probe=ctl.decide_exposure(t,policy)
        if is_probe and not gov.probe_approval:raise AssertionError('probe without authorization')
        if origin=='PROBE_WAIT' and not is_probe and p!=0:raise AssertionError('probe wait cannot enroll patients')
        if is_probe and p!=gov.q:raise AssertionError('probe q is reexposure, not retention')
        ctl.cohort_origin[t]=origin
        ex=exogenous(seed,sc,rep,t,n)
        z=ex['z_uniform']<p
        pr=patient_process(ex,z,sc,history,sc.capacity_fraction,t)
        for m in range(M):
            s=slice(m*n_stratum,(m+1)*n_stratum)
            partial={k:v[s] if isinstance(v,np.ndarray) and len(v)==n else v for k,v in pr.items()}
            sealed.append(observed_cohort(partial,t,m,f'{sc.name}-{rep}-{policy}-q{gov.q:.3f}'))
        if sc.hysteresis:history=.8*history+.2*float(np.mean(z))
        monthly.append(dict(month=t,policy=policy,scenario=sc.name,rep=rep,
                            state=origin,probe_enrollment=is_probe,
                            exposure_probability=p,
                            n=n,expected_good=float(np.sum(pr['p_y'])),
                            observed_good=int(pr['Y'].sum()),shown=int(z.sum()),
                            wlsts=int(pr['W'].sum()),capacity_denials=int(pr['Q'].sum()),
                            missing=int((~pr['O']).sum()),
                            new_cohorts_evaluated=len(inputs),
                            positive_intervals=sum(x.lower>0 for x in inputs),
                            negative_intervals=sum(x.upper<0 for x in inputs),
                            inference_certified=gov.certified_individual_inference))
    # These late reports may be audited but CANNOT change actions in past months.
    for t in range(months,months+FULL_MATURITY_LAG+1):
        to_release=[c for c in sealed if c.ready_month<=t]
        sealed=[c for c in sealed if c.ready_month>t]
        for c in to_release:monitor.receive(c,current_month=t)
        due=monitor.evaluate_ready(t)
        inputs=[ControllerInput(t,c.cohort_id,c.month,c.stratum,ev.lower,ev.upper,ev.mode,ev.n0,ev.n1) for c,ev in due]
        # Administrative audit only: posthorizon results never trigger a
        # counterfactual 'reentry' after the simulated decision horizon.
    if sealed or len(monitor._seen)!=M*months:raise AssertionError('lost or duplicated cohort')
    return dict(scenario=sc.name,policy=policy,q=gov.q,rep=rep,seed=seed,
                n=n*months,expected_good=sum(x['expected_good'] for x in monthly),
                observed_good=sum(x['observed_good'] for x in monthly),
                alerts_shown=sum(x['shown'] for x in monthly),
                wlsts=sum(x['wlsts'] for x in monthly),
                capacity_denials=sum(x['capacity_denials'] for x in monthly),
                missing=sum(x['missing'] for x in monthly),
                probe_exposures=sum(x['shown'] for x in monthly if x['probe_enrollment']),
                probe_enrollment_months=sum(x['probe_enrollment'] for x in monthly),
                state_months={s:sum(x['state']==s for x in monthly)
                              for s in ('ACTIVE','P0','PROBE_WAIT','REENTRY_RESTRICTED')},
                certified=gov.certified_individual_inference,
                decisions=ctl.events,valid_decisions=ctl.valid_decisions,
                inconclusive_intervals=ctl.inconclusive_evals,
                invalid_signs_blocked=ctl.invalid_evidence_blocked,
                cohorts_evaluated=len(monitor._seen),monthly=monthly)


def run_v05c(out:Path,reps:int=20,seed:int=20261110,q:float=.05,
             months:int=B,n_stratum:int=N_STRATUM,
             scenarios:list[Scenario]|None=None,policies:tuple[str,...]=POLICIES,
             allow_synthetic_probe:bool=True,
             extra_operating_cost_per_alert:float=0.) -> tuple[list[dict],list[dict]]:
    out.mkdir(parents=True,exist_ok=True)
    if scenarios is None:scenarios=SCENARIOS
    rows=[];trace=[];moments=[]
    for sc in scenarios:
        for rep in range(reps):
            for policy in policies:
                gov=Governance(q=q,probe_approval=allow_synthetic_probe,
                               certified_individual_inference=default_design_certificate(sc),
                               extra_operating_cost_per_alert=extra_operating_cost_per_alert)
                r=simulate_v05c(sc,policy,rep,seed,gov,months,n_stratum)
                moments.extend(r['monthly'])
                rows.append({k:v for k,v in r.items() if k not in ('decisions','monthly') and k!='state_months'}
                            |{'state_months':json.dumps(r['state_months'],sort_keys=True)})
                if rep==0:trace.append(dict(scenario=sc.name,policy=policy,
                                            decisions=r['decisions'],state_months=r['state_months'],
                                            exposure=[(x['month'],x['state'],x['exposure_probability'])
                                                      for x in r['monthly']]))
    # Fixed-policy oracle: *same synthetic replication*, same patient exogenous uniforms.
    reference={(r['scenario'],r['rep'],r['policy']):r for r in rows
               if r['policy'] in ('ALWAYS_ON','ALWAYS_OFF')}
    for r in rows:
        on=reference[(r['scenario'],r['rep'],'ALWAYS_ON')]
        off=reference[(r['scenario'],r['rep'],'ALWAYS_OFF')]
        best=max(on['expected_good'],off['expected_good'])
        r['oracle_fixed']='ALWAYS_ON' if on['expected_good']>=off['expected_good'] else 'ALWAYS_OFF'
        r['fixed_oracle_expected_good']=best
        r['loss_vs_fixed_oracle_per_1000']=1000*(best-r['expected_good'])/r['n']
        r['extra_alert_cost_per_1000']=1000*extra_operating_cost_per_alert*r['alerts_shown']/r['n']
        # A utility oracle must also pay its own alert burden. Subtracting only
        # the candidate's burden from the clinical-oracle comparison would
        # double count or misattribute costs when the oracle uses alerts.
        utility_on=on['expected_good']-extra_operating_cost_per_alert*on['alerts_shown']
        utility_off=off['expected_good']-extra_operating_cost_per_alert*off['alerts_shown']
        utility_candidate=r['expected_good']-extra_operating_cost_per_alert*r['alerts_shown']
        r['utility_oracle_fixed']='ALWAYS_ON' if utility_on>=utility_off else 'ALWAYS_OFF'
        r['utility_loss_vs_fixed_oracle_per_1000']=1000*(max(utility_on,utility_off)-utility_candidate)/r['n']
        r['lost_vs_on_per_1000']=1000*(on['expected_good']-r['expected_good'])/r['n']
        r['lost_vs_off_per_1000']=1000*(off['expected_good']-r['expected_good'])/r['n']
    # State-based additive decomposition using identical fixed-oracle month outcomes.
    monthly_idx={(m['scenario'],m['rep'],m['policy'],m['month']):m for m in moments}
    row_idx={(r['scenario'],r['rep'],r['policy']):r for r in rows}
    for m in moments:
        this_row=row_idx[(m['scenario'],m['rep'],m['policy'])]
        target=this_row['oracle_fixed']
        ref=monthly_idx[(m['scenario'],m['rep'],target,m['month'])]
        m['loss_vs_oracle_month_per_1000']=1000*(ref['expected_good']-m['expected_good'])/m['n']
        # Each monthly loss belongs to exactly one state; probes are a subset of
        # PROBE_WAIT months, not an additional term in the total.
        m['loss_category']='PROBE_ENROLL' if m['probe_enrollment'] else m['state']
    rows_path=out/'policy_results_v0_5c.csv'
    with rows_path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with (out/'monthly_state_losses_v0_5c.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(moments[0]));w.writeheader();w.writerows(moments)
    (out/'state_traces_v0_5c.json').write_text(json.dumps(trace,indent=2),encoding='utf-8')
    cfg=dict(version='0.5C-exploratory',seed=seed,reps=reps,q=q,months=months,
             n_stratum=n_stratum,strata=M,alpha_arm=ALPHA_ARM,
             ready_lag_months=FULL_MATURITY_LAG,
             policies=list(policies),scenarios=[asdict(s) for s in scenarios],
             allow_synthetic_probe=allow_synthetic_probe,
             extra_operating_cost_per_alert=extra_operating_cost_per_alert)
    (out/'configuration_v0_5c.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    return rows,moments


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,default=HERE)
    ap.add_argument('--reps',type=int,default=20)
    ap.add_argument('--q',type=float,default=.05)
    ap.add_argument('--months',type=int,default=20)
    ap.add_argument('--n-stratum',type=int,default=125)
    ap.add_argument('--seed',type=int,default=20261110)
    ap.add_argument('--no-probe-approval',action='store_true')
    args=ap.parse_args()
    rows,_=run_v05c(args.out,args.reps,args.seed,args.q,args.months,args.n_stratum,
                    allow_synthetic_probe=not args.no_probe_approval)
    print(json.dumps(dict(n_trajectories=len(rows),n_scenarios=len(set(r['scenario'] for r in rows)),
                          n_policies=len(set(r['policy'] for r in rows))),indent=2))
if __name__=='__main__':main()
