#!/usr/bin/env python3
"""KAFKA III v0.4 exploratory synthetic decision/loss simulator.

NOT a clinical decision algorithm. Synthetic authorization is assumed only for testing.
Each policy is simulated separately; it receives only mature randomized cohorts.
No unadjusted pooling. Family error for 20x4x2 arm-level monthly CIs = .025.
State transitions use CP for sign (L>0, U<0), never an arbitrary 5pp safety margin.
Hysteresis/capacity simulations intentionally VIOLATE the simple static-policy oracle
model and are compared to the best fixed-trajectory benchmark instead.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse, csv, json, hashlib
import numpy as np
from scipy.stats import beta

B, M, N_BASE = 20, 4, 125
ALPHA_FAMILY = 0.025
ALPHA_ARM = ALPHA_FAMILY / (B * M * 2)
STATE_ACTIVE, STATE_PROBE, STATE_REENTRY, STATE_P0 = 0, 1, 2, 3
POLICIES = ('ALWAYS_ON','ALWAYS_OFF','ACTIVE_SENTINEL','TRIGGER_P0_PROBE','TRIGGER_P0_NO_PROBE','P0_PROBE')

@dataclass(frozen=True)
class Scenario:
    name: str
    mu0: float
    delta: float
    drift: bool = False
    flip: bool = False
    delay0: int = 1
    delay1: int = 1
    censor: str = 'none'
    hysteresis: float = 0.0
    capacity: float = 0.0

SCENARIOS = [
    Scenario('benefit5', .55, .05),
    Scenario('harm25', .70, -.25),
    Scenario('null_drift', .05, 0., drift=True),
    Scenario('benefit5_delay3', .55, .05, delay0=3, delay1=3),
    Scenario('harm25_delay3', .70, -.25, delay0=3, delay1=3),
    Scenario('harm25_diffdelay', .70, -.25, delay0=1, delay1=3),
    Scenario('harm25_MCAR20', .70, -.25, censor='mcar'),
    Scenario('harm25_MNAR', .70, -.25, censor='mnar'),
    Scenario('benefit5_hysteresis', .55, .05, hysteresis=-.10),
    Scenario('benefit5_capacity', .55, .05, capacity=.10),
    Scenario('sign_flip', .60, .05, flip=True),
]

def scenario_params(s:Scenario,t:int,e:np.ndarray,memory:np.ndarray):
    mu0 = (0.05 if t < 10 else 0.95) if s.drift else s.mu0
    delta = (-.25 if t >= 8 else .05) if s.flip else s.delta
    p0 = np.clip(mu0 + s.hysteresis*memory - s.capacity*e,0.,1.)
    p1 = np.clip(p0+delta,0.,1.)
    return p0,p1,p1-p0

def cp_interval(n, y, alpha=ALPHA_ARM):
    """Exact binomial (two-sided, conservative) interval, including empty arm.

    Inputs may be arrays. Coverage only under the specified binomial model.
    """
    n=np.asarray(n,dtype=int); y=np.asarray(y,dtype=int)
    lo=np.zeros(n.shape,float);hi=np.ones(n.shape,float)
    mlo=(n>0)&(y>0)
    mhi=(n>0)&(y<n)
    if np.any(mlo):lo[mlo]=beta.ppf(alpha/2,y[mlo],n[mlo]-y[mlo]+1)
    if np.any(mhi):hi[mhi]=beta.ppf(1-alpha/2,y[mhi]+1,n[mhi]-y[mhi])
    return lo,hi

def effect_ci(n0, obs0, good0, n1, obs1, good1, robust=False):
    """For robust=True, interval valid under arbitrary outcome-dependent attrition
    if each randomized arm is conditionally iid within a block. Uses Bernoulli
    proxies A=observed success, B=observed success+missing, with union control.
    """
    if robust:
        # Separate lower/upper Bernoulli events; exact CP uses alpha/2 in each tail.
        lo0,_=cp_interval(n0,good0,ALPHA_ARM)
        _,hi0=cp_interval(n0,good0+n0-obs0,ALPHA_ARM)
        lo1,_=cp_interval(n1,good1,ALPHA_ARM)
        _,hi1=cp_interval(n1,good1+n1-obs1,ALPHA_ARM)
    else:
        lo0,hi0=cp_interval(obs0,good0,ALPHA_ARM)
        lo1,hi1=cp_interval(obs1,good1,ALPHA_ARM)
    return lo1-hi0,hi1-lo0

def censor_probs(s:Scenario):
    if s.censor=='none': return (0.,0.),(0.,0.)
    if s.censor=='mcar': return (.20,.20),(.20,.20)
    # Z=0 favorable more likely missing; Z=1 adverse more likely missing:
    # an intentionally adversarial informative observation mechanism.
    if s.censor=='mnar': return (.50,.05),(.05,.80)
    raise ValueError(s.censor)

def fixed_policy_value(s:Scenario, n:int) -> tuple[float,str]:
    values=[]
    for e in [0.,1.]:
        memory=0.
        total=0.
        for t in range(B):
            p0,p1,_=scenario_params(s,t,np.array(e),np.array(memory))
            total += n*M*float(p0+e*(p1-p0))
            memory=.80*memory+.20*e
        values.append(total)
    if values[1]>=values[0]: return values[1], 'ALWAYS_ON'
    return values[0],'ALWAYS_OFF'

def _seed(seed:int, scenario:str, q:float, policy:str):
    val=f'{seed}|{scenario}|{q:.4f}|{policy}'.encode()
    return int.from_bytes(hashlib.sha256(val).digest()[:8],'big')

def sim_one(s:Scenario,q:float,policy:str,reps:int,n:int,seed:int,robust:bool=False):
    rng=np.random.default_rng(_seed(seed,s.name,q,policy))
    sh=(reps,M)
    memory=np.zeros(sh)
    if policy=='ALWAYS_OFF':state=np.full(sh,STATE_P0,dtype=np.int8)
    elif policy=='P0_PROBE':state=np.full(sh,STATE_PROBE,dtype=np.int8)
    else:state=np.full(sh,STATE_ACTIVE,dtype=np.int8)
    cum=np.zeros(sh,float)
    clinical_maint=np.zeros(sh,float)
    clinical_susp=np.zeros(sh,float)
    probe_patients=np.zeros(sh,float)
    probe_cohorts=np.zeros(sh,int)
    first_probe_t=np.full(sh,-1,int)
    first_reentry_t=np.full(sh,-1,int)
    p0_months_benefit=np.zeros(sh,int)
    time_p0=np.zeros(sh,int)
    evidence_harm=np.zeros(sh,int)
    evidence_benefit=np.zeros(sh,int)
    empirical_harm_switches=np.zeros(sh,int)
    empirical_false_switches=np.zeros(sh,int)
    first_true_harm_switch_t=np.full(sh,-1,int)
    active_months_harm=np.zeros(sh,int)
    exog_suspensions=np.zeros(sh,int)
    reentries=np.zeros(sh,int)
    intervals_tested=np.zeros(sh,int)
    intervals_conclusive=np.zeros(sh,int)
    ci_cover=np.zeros(sh,int)
    # each cohort is analyzed once at its predetermined maturity
    cohorts=[]
    c0,c1=censor_probs(s)
    for t in range(B):
        # Maturity and evaluation only BEFORE this period's exposure decision.
        for cohort in cohorts:
            if cohort['mature']!=t: continue
            lo,hi=effect_ci(cohort['n0'],cohort['o0'],cohort['g0'],cohort['n1'],cohort['o1'],cohort['g1'],robust)
            both=cohort['eligible']
            intervals_tested += both
            intervals_conclusive += both & ((lo>0)|(hi<0))
            ci_cover += both & ((lo<=cohort['delta'])&(cohort['delta']<=hi))
            active_origin=(cohort['state']==STATE_ACTIVE)|(cohort['state']==STATE_REENTRY)
            probe_origin=cohort['state']==STATE_PROBE
            current_active=(state==STATE_ACTIVE)|(state==STATE_REENTRY)
            # Observed harmful evidence under current active authority.
            switch = active_origin & current_active & (hi<0) & (policy in ('ACTIVE_SENTINEL','TRIGGER_P0_PROBE','TRIGGER_P0_NO_PROBE'))
            evidence_harm += switch
            empirical_harm_switches += switch
            empirical_false_switches += switch & (cohort['delta']>=0)
            first_true_harm_switch_t=np.where(switch & (cohort['delta']<0)&(first_true_harm_switch_t<0), t, first_true_harm_switch_t)
            if policy!='TRIGGER_P0_NO_PROBE':state=np.where(switch,STATE_PROBE,state)
            else:state=np.where(switch,STATE_P0,state)
            # Only cohorts randomized WHILE P0 probing qualify for reentry.
            reentry = probe_origin & (state==STATE_PROBE) & (lo>0) & (policy in ('P0_PROBE','TRIGGER_P0_PROBE','ACTIVE_SENTINEL'))
            evidence_benefit += reentry
            reentries += reentry
            first_reentry_t=np.where(reentry & (first_reentry_t<0),t,first_reentry_t)
            state=np.where(reentry,STATE_REENTRY,state)
        # Externally determined precautionary intervention (not evidence of harm).
        if t==6 and policy in ('TRIGGER_P0_PROBE','TRIGGER_P0_NO_PROBE'):
            trigger=(state==STATE_ACTIVE)|(state==STATE_REENTRY)
            exog_suspensions += trigger
            state=np.where(trigger,STATE_PROBE if policy=='TRIGGER_P0_PROBE' else STATE_P0,state)
        st=state.copy()
        if policy=='ALWAYS_ON': e=np.ones(sh)
        elif policy=='ALWAYS_OFF':e=np.zeros(sh)
        else:e=np.where((st==STATE_ACTIVE)|(st==STATE_REENTRY),1.-q,
                          np.where(st==STATE_PROBE,q,0.))
        n1=rng.binomial(n,e)
        n0=n-n1
        e_real=n1/n
        p0,p1,d=scenario_params(s,t,e_real,memory)
        # Outcome potential mean under actual exposure allocation; full truth
        # is simulator-only and never supplied to state machine.
        cum += n0*p0+n1*p1
        no_feedback=(s.hysteresis==0 and s.capacity==0)
        if no_feedback:
            clinical_maint += n1*np.maximum(-d,0)
            clinical_susp += n0*np.maximum(d,0)
        probe_patients+=np.where(st==STATE_PROBE,n1,0)
        probe_cohorts+=(st==STATE_PROBE)
        first_probe_t=np.where((st==STATE_PROBE)&(first_probe_t<0),t,first_probe_t)
        time_p0 += (st==STATE_PROBE)|(st==STATE_P0)
        p0_months_benefit += ((st==STATE_PROBE)|(st==STATE_P0))&(d>0)
        active_months_harm += ((st==STATE_ACTIVE)|(st==STATE_REENTRY))&(d<0)
        true_good0=rng.binomial(n0,p0)
        true_good1=rng.binomial(n1,p1)
        o_good0=rng.binomial(true_good0,1-c0[0]);o_bad0=rng.binomial(n0-true_good0,1-c0[1])
        o_good1=rng.binomial(true_good1,1-c1[0]);o_bad1=rng.binomial(n1-true_good1,1-c1[1])
        obs0=o_good0+o_bad0;obs1=o_good1+o_bad1
        # Delay cohort until BOTH arms have the prespecified endpoint matured.
        mature=t+max(s.delay0,s.delay1)
        cohorts.append(dict(mature=mature,n0=n0,o0=obs0,g0=o_good0,n1=n1,o1=obs1,g1=o_good1,
                            state=st,delta=d,eligible=np.ones(sh,dtype=int)))
        memory=.8*memory+.2*e_real
    bench,bench_name=fixed_policy_value(s,n)
    # Best static benchmark can be beaten by a dynamic policy; signed difference.
    gap=bench-cum.sum(axis=1)
    m_loss=clinical_maint.sum(axis=1)
    s_loss=clinical_susp.sum(axis=1)
    def avg_per_k(x): return float(np.mean(x)/(B*M*n)*1000)
    def se_per_k(x): return float(np.std(x,ddof=1)/np.sqrt(reps)/(B*M*n)*1000) if reps>1 else 0.
    res=dict(scenario=s.name,q=q,policy=policy,reps=reps,n_per_stratum_month=n,
       benchmark=bench_name,
       gap_best_static_per_1000=round(avg_per_k(gap),4),
       gap_mc_se_per_1000=round(se_per_k(gap),4),
       clinical_maint_per_1000=round(avg_per_k(m_loss),4) if s.hysteresis==0 and s.capacity==0 else None,
       clinical_susp_per_1000=round(avg_per_k(s_loss),4) if s.hysteresis==0 and s.capacity==0 else None,
       probe_exposure_per_1000=round(avg_per_k(probe_patients.sum(axis=1)),4),
       probe_cohorts_per_stratum=round(float(np.mean(probe_cohorts)),3),
       first_reentry_latency_months=round(float(np.mean((first_reentry_t-first_probe_t)[first_reentry_t>=0])),3) if np.any(first_reentry_t>=0) else None,
       probe_operational_cost_if_unit_0_001_per_1000=round(avg_per_k(probe_patients.sum(axis=1))*.001,5),
       p0_months_with_true_benefit_per_stratum=round(float(np.mean(p0_months_benefit)),3),
       active_months_with_true_harm_per_stratum=round(float(np.mean(active_months_harm)),3),
       false_empirical_switches_per_path=round(float(np.mean(empirical_false_switches.sum(axis=1))),5),
       first_harm_detection_delay_months=(round(float(np.mean((first_true_harm_switch_t-(8 if s.flip else 0))[first_true_harm_switch_t>=0])),3) if np.any(first_true_harm_switch_t>=0) else None),
       months_P0_or_PROBE_per_stratum=round(float(np.mean(time_p0)),3),
       fraction_paths_with_reentry=round(float(np.mean(np.any(reentries>0,axis=1))),5),
       mean_reentries_per_path=round(float(np.mean(reentries.sum(axis=1))),5),
       mean_empirical_harm_suspensions_per_path=round(float(np.mean(empirical_harm_switches.sum(axis=1))),5),
       mean_exogenous_suspensions_per_path=round(float(np.mean(exog_suspensions.sum(axis=1))),5),
       mature_fraction=round(float(np.sum(intervals_tested)/(B*M*reps)),4),
       conclusive_fraction_matured=round(float(np.sum(intervals_conclusive)/max(np.sum(intervals_tested),1)),6),
       interval_coverage_matured=round(float(np.sum(ci_cover)/max(np.sum(intervals_tested),1)),6),
       inferential_status='INVALID_COMPLETE_CASE_IF_MNAR' if s.censor=='mnar' and not robust else (
          'DIRECT_EFFECT_NOT_POLICY_VALUE_WITH_INTERFERENCE' if s.capacity else 'EXPLORATORY_CONDITIONAL_BLOCK'),
       robust_attrition=robust)
    return res

def attrition_diagnostic(reps=4000,n=2500,seed=20261110):
    """Separately tests a case where complete-case causal inference reverses sign.
    NOT clinical data. At high sample sizes for purpose of a diagnostic stress test.
    """
    rng=np.random.default_rng(seed+78)
    true_delta=-.25
    n1=rng.binomial(n,.5,size=reps)
    n0=n-n1
    g0=rng.binomial(n0,.70)
    g1=rng.binomial(n1,.45)
    # Z0: many favorable missing; Z1: many adverse missing.
    o0g=rng.binomial(g0,.50); o0b=rng.binomial(n0-g0,.95)
    o1g=rng.binomial(g1,.95); o1b=rng.binomial(n1-g1,.20)
    o0=o0g+o0b; o1=o1g+o1b
    ci0,ci1=effect_ci(n0,o0,o0g,n1,o1,o1g,False)
    mr0,mr1=effect_ci(n0,o0,o0g,n1,o1,o1g,True)
    delta_cc=np.divide(o1g,o1,out=np.zeros(reps),where=o1>0)-np.divide(o0g,o0,out=np.zeros(reps),where=o0>0)
    return dict(n=n,reps=reps,true_delta=true_delta,complete_case_mean_delta=round(float(delta_cc.mean()),4),
         complete_case_coverage=round(float(np.mean((ci0<=true_delta)&(true_delta<=ci1))),5),
         complete_case_false_evidence_benefit=round(float(np.mean(ci0>0)),5),
         missing_robust_coverage=round(float(np.mean((mr0<=true_delta)&(true_delta<=mr1))),5),
         missing_robust_benefit_claim=round(float(np.mean(mr0>0)),5),
         missing_robust_median_width=round(float(np.median(mr1-mr0)),4),
         assumption='iid subjects; independent randomized Z, outcome-dependent missingness; no interference')

def test_invariants():
    n=np.array([0,10,20]);y=np.array([0,0,20])
    lo,hi=cp_interval(n,y)
    assert np.all((lo>=0)&(hi<=1)&(lo<=hi))
    assert lo[0]==0 and hi[0]==1
    l,u=effect_ci(np.array([0]),np.array([0]),np.array([0]),np.array([125]),np.array([125]),np.array([100]))
    assert l[0]<=0<=u[0]  # zero control cannot prove sign
    # no missing => robust CP equals ordinary CP
    rng=np.random.default_rng(42)
    for _ in range(10):
        na=np.array([125]); nb=np.array([125]);ya=np.array([rng.integers(0,126)]); yb=np.array([rng.integers(0,126)])
        a=effect_ci(na,na,ya,nb,nb,yb,False)
        b=effect_ci(na,na,ya,nb,nb,yb,True)
        assert np.allclose(a,b)
    # signed dynamic benchmark may be beaten; do not call gap nonnegative regret
    assert fixed_policy_value(Scenario('x',.55,.05),125)[1]=='ALWAYS_ON'
    assert fixed_policy_value(Scenario('x',.70,-.25),125)[1]=='ALWAYS_OFF'
    # If policy is always off/on, gap to best static must be >= 0 to floating tolerance
    for policy in ['ALWAYS_ON','ALWAYS_OFF']:
        t=sim_one(Scenario('x',.55,.05),.02,policy,10,125,31)
        assert t['gap_best_static_per_1000']>=-1e-3
        if policy=='ALWAYS_ON': assert abs(t['gap_best_static_per_1000']) < 1e-3
    # MCAR can be assessed via observed binomial; MNAR CC cannot be trusted.

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reps',type=int,default=1000)
    ap.add_argument('--seed',type=int,default=20261110)
    ap.add_argument('--out',default=str(Path(__file__).parent))
    ap.add_argument('--highvolume',action='store_true',help='Separate mechanistic test of delayed reentry under huge artificial sample')
    args=ap.parse_args()
    test_invariants()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for s in SCENARIOS:
        for q in [.01,.02,.05]:
            for pol in POLICIES:
                rows.append(sim_one(s,q,pol,args.reps,N_BASE,args.seed))
        print(s.name,'done',flush=True)
    if args.highvolume:
        for delay in [1,3]:
            for direction, mu0, delta in [('benefit',.20,.60),('harm',.80,-.60)]:
                s=Scenario(f'artificial_highvolume_{direction}60_delay{delay}',mu0,delta,delay0=delay,delay1=delay)
                for pol in ['P0_PROBE','TRIGGER_P0_PROBE','ACTIVE_SENTINEL']:
                    rows.append(sim_one(s,.05,pol,300,2000,args.seed))
        print('highvolume done',flush=True)
    with (out/'decision_summary_v0_4.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    diag=attrition_diagnostic()
    (out/'attrition_stress_v0_4.json').write_text(json.dumps(diag,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    config={'version':'v0.4 exploratory','replications':args.reps,'seed':args.seed,
       'scenario_count':len(SCENARIOS),'policies':POLICIES,'rates':[.01,.02,.05],
       'block_count':B,'strata_count':M,'n_per_stratum_month':N_BASE,
       'alpha_family':ALPHA_FAMILY,'alpha_arm_monthly':ALPHA_ARM,
       'external_trigger_month_index':6,
       'reentry_criterion':'L>0 with clinical authorization only presumed in synthetic world',
       'suspension_inferential_criterion':'U<0 on mature cohort; no pooled data',
       'delays':'cohorts evaluated only after max of two arm delays; all patients counted once',
       'operational_unit_cost_illustration':.001,
       'benchmark':'best of ALWAYS_ON and ALWAYS_OFF fixed policy with its own history',
       'loss':'expected difference vs best fixed benchmark; maintenance/suspension only additive under no hysteresis and no interference',
       'ci':'two-sided Clopper-Pearson per arm, Bonferroni across 4 strata x 20 months x 2 arms; 2.5% reserved for unused family',
       'no_clinical_safety_or_confirmation_claim':True}
    (out/'configuration_v0_4.json').write_text(json.dumps(config,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(diag,indent=2))
    print('saved',len(rows),'rows in',out)

if __name__=='__main__':main()
