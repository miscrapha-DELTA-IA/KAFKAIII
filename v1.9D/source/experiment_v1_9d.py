#!/usr/bin/env python3
"""KAFKA III v1.9D: reproducible, exploratory toy decision benchmark.

No clinical calibration, no simulated patient data, no causal identification claims.
Dependencies: Python >= 3.10 standard library only.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from functools import lru_cache
import csv, json, math, pathlib
from typing import Callable

BASE = pathlib.Path(__file__).resolve().parent
TOL = 1e-11

@dataclass(frozen=True)
class Scenario:
    name: str
    prior: float
    horizon: int
    effect: float
    accuracy: float
    q0: float
    qmax: float
    signal_cost: float
    low: float
    high: float
    fallback: float = 0.10
    review_cost: float = 0.02
    review_duration: int = 2

    def validate(self):
        assert 0.0 <= self.prior <= 1.0
        assert 1 <= self.horizon <= 12
        assert 0 < self.effect <= 1
        assert 0.5 <= self.accuracy <= 1
        assert 0 <= self.q0 <= self.qmax <= 1
        assert self.signal_cost >= 0
        assert 0 <= self.low <= 1 and 0 <= self.high <= 1
        assert 0 <= self.fallback <= 1
        assert self.review_cost >= 0 and self.review_duration >= 1


def pkey(p: float) -> float:
    return round(min(1.0, max(0.0, p)), 12)


def acquisition(e: float, s: Scenario) -> float:
    # An informative TWO-ARM signal is easiest with overlap/positivity.
    # q0 is a small, independent routine comparison channel with cost shared
    # by all policies; it is not an extra channel granted to review.
    return s.q0 + 4*(s.qmax-s.q0)*e*(1-e)


def acquisition_prime(e: float, s: Scenario) -> float:
    return 4*(s.qmax-s.q0)*(1-2*e)


def posterior(p: float, a: float, signal_positive: bool) -> float:
    wplus = a if signal_positive else 1-a
    wminus = 1-a if signal_positive else a
    den = p*wplus+(1-p)*wminus
    return pkey(p*wplus/den) if den > 0 else pkey(p)


def signal_pos_probability(p: float, a: float) -> float:
    return p*a+(1-p)*(1-a)


def biological_loss(e: float, p: float, effect: float) -> float:
    # θ+ means exposure helps: loss (1-e)*effect; θ- means it harms: loss e*effect
    return effect*(p*(1-e)+(1-p)*e)


def argmin_exposure(s: Scenario, p: float, info_coefficient: float) -> float:
    """Global minimum of affine biological loss plus a quadratic info term.

    The quadratic has at most one stationary point. Check endpoints and it.
    """
    if s.low > s.high:
        return s.fallback # governance contingency: NOT an admissible regular action
    L, U = s.low, s.high
    slope = s.effect*(1-2*p)
    def fn(e): return slope*e + info_coefficient*acquisition(e,s)
    def der(e): return slope+info_coefficient*acquisition_prime(e,s)
    candidates = [L,U]
    coefficient = -8*info_coefficient*(s.qmax-s.q0)
    if abs(coefficient) > 1e-14:
        stationary = -der(0.0)/coefficient
        if L < stationary < U: candidates.append(stationary)
    # deterministic less-exposure tie-break when values equal
    return min(candidates, key=lambda e: (round(fn(e),13),e))


class Planner:
    def __init__(self,s:Scenario):
        s.validate()
        self.s=s

    def parts(self,p:float,h:int,nextV: Callable[[int,float],float]):
        if h<=1:
            return 0.0,0.0
        a=self.s.accuracy
        prob=signal_pos_probability(p,a)
        updated = prob*nextV(h-1, posterior(p,a,True))+(1-prob)*nextV(h-1, posterior(p,a,False))
        same=nextV(h-1,p)
        return same, updated-same

    @lru_cache(None)
    def greedy_action(self,h:int,p:float) -> float:
        return argmin_exposure(self.s,p,self.s.signal_cost)

    @lru_cache(None)
    def greedy_value(self,h:int,p:float) -> float:
        return self.policy_value(h,p,'greedy')

    @lru_cache(None)
    def exact_action(self,h:int,p:float) -> float:
        _, di=self.parts(p,h,self.exact_value)
        return argmin_exposure(self.s,p,di+self.s.signal_cost)

    @lru_cache(None)
    def exact_value(self,h:int,p:float) -> float:
        return self.policy_value(h,p,'exact')

    @lru_cache(None)
    def rollout_action(self,h:int,p:float) -> float:
        _, di=self.parts(p,h,self.greedy_value)
        return argmin_exposure(self.s,p,di+self.s.signal_cost)

    @lru_cache(None)
    def rollout_value(self,h:int,p:float) -> float:
        return self.policy_value(h,p,'rollout')

    def action(self,mode:str,h:int,p:float) -> float:
        return {'exact':self.exact_action,'rollout':self.rollout_action,
                'greedy':self.greedy_action}[mode](h,p)

    def policy_value(self,h:int,p:float,mode:str) -> float:
        if h==0: return 0.0
        e=self.action(mode,h,p)
        s=self.s
        q=acquisition(e,s)
        cost=biological_loss(e,p,s.effect)+s.signal_cost*q
        if h==1: return cost
        posprob=signal_pos_probability(p,s.accuracy)
        cont=(1-q)*self._value(mode,h-1,p)
        cont+=q*(posprob*self._value(mode,h-1,posterior(p,s.accuracy,True))
            +(1-posprob)*self._value(mode,h-1,posterior(p,s.accuracy,False)))
        return cost+cont

    def _value(self,mode:str,h:int,p:float):
        return {'exact':self.exact_value,'rollout':self.rollout_value,
                'greedy':self.greedy_value}[mode](h,p)

    @lru_cache(None)
    def true_conditional_value(self,mode:str,h:int,p:float,truth:int,true_accuracy:float) -> float:
        """Evaluate fixed learned policy conditional on θ without revealing θ to it.

        true_accuracy modifies the signal generator ONLY.  Belief updates still
        use the assumed accuracy s.accuracy (intentional misspecification test).
        """
        if h<=0: return 0.0
        e=self.action(mode,h,p)
        s=self.s
        q=acquisition(e,s)
        clinical=s.effect*((1-e) if truth==1 else e)
        immediate=clinical+s.signal_cost*q
        if h==1: return immediate
        prob_positive=(true_accuracy if truth==1 else 1-true_accuracy)
        return immediate+(1-q)*self.true_conditional_value(mode,h-1,p,truth,true_accuracy)+q*(
            prob_positive*self.true_conditional_value(mode,h-1,posterior(p,s.accuracy,True),truth,true_accuracy)
            +(1-prob_positive)*self.true_conditional_value(mode,h-1,posterior(p,s.accuracy,False),truth,true_accuracy))

    def external_value(self,mode:str,true_prior:float,true_accuracy:float) -> float:
        s=self.s
        return true_prior*self.true_conditional_value(mode,s.horizon,pkey(s.prior),1,true_accuracy) + \
          (1-true_prior)*self.true_conditional_value(mode,s.horizon,pkey(s.prior),-1,true_accuracy)


def make_scenarios() -> list[Scenario]:
    base=dict(horizon=6,effect=.10,accuracy=.85,q0=.02,qmax=.82,
              signal_cost=.001,low=0.,high=1.)
    defs=[
        ('balanced',.50,{}),
        ('near_harm',.42,{}),
        ('harm_skew',.20,{}),
        ('benefit_skew',.80,{}),
        ('weak_signal',.42,dict(accuracy=.55)),
        ('uninformative',.42,dict(accuracy=.50)),
        ('expensive_signal',.42,dict(signal_cost=.045)),
        ('slow_signal',.42,dict(qmax=.17)),
        ('upper_restricted',.42,dict(high=.40)),
        ('narrow_grid_gap',.42,dict(low=.37,high=.43)),
        ('high_floor',.42,dict(low=.60)),
        ('conflict',.42,dict(low=.70,high=.30)),
    ]
    return [Scenario(name=n,prior=p,**(base|overrides)) for n,p,overrides in defs]


def governance_audit(bounds:list[tuple[float,float]],fallback=.10,delay=2,cost=.02,
                     externally_signed: list[bool] | None=None) -> list[dict]:
    """Fixed external governance inputs. Review provides no new signal or permission.

    A signed external authorization can release review only with feasible new
    bounds; this is supplied externally, never generated by review.
    """
    if externally_signed is None: externally_signed=[False]*len(bounds)
    assert len(externally_signed)==len(bounds)
    state='NORMAL'
    remaining=0
    cost_charged=False
    audit=[]
    for t,((low,high),signed) in enumerate(zip(bounds,externally_signed),1):
        feasible=low<=high
        if state=='NORMAL' and not feasible:
            state='PENDING_REVIEW'
            remaining=delay
            cost_charged=True
            new_cost=cost
        else: new_cost=0.
        if state in ('PENDING_REVIEW','UNRESOLVED'):
            # authorization requires independent, signed fresh bounds
            if feasible and signed:
                state='NORMAL'; remaining=0
                exposure=None; reason='AUTHORIZED_EXTERNAL_UPDATE'
            else:
                exposure=fallback; reason='CONTINGENCY_NOT_REGULAR_ACTION'
                if state=='PENDING_REVIEW':
                    remaining-=1
                    if remaining<=0: state='UNRESOLVED'
        else:
            exposure=None; reason='REGULAR_ADMISSIBILITY'
        audit.append(dict(period=t,low=low,high=high,feasible_regular=feasible,
                          state=state,review_cost=new_cost,review_duration=delay,
                          contingency_exposure=exposure,reason=reason,
                          authorized_external_update=bool(signed)))
    assert cost_charged == any(lo>hi for lo,hi in bounds)
    return audit


def csv_write(path:pathlib.Path,rows:list[dict]):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)


def main():
    scenarios=make_scenarios()
    rows=[]
    for s in scenarios:
        pl=Planner(s);p=pkey(s.prior);h=s.horizon
        vals={m:pl._value(m,h,p) for m in ('greedy','rollout','exact')}
        actions={m:pl.action(m,h,p) for m in ('greedy','rollout','exact')}
        # Mandatory conflict review cost is identical for all policies; a
        # pending review cannot create extra evidence or permissions.
        conflict=s.low>s.high
        surcharge=s.review_cost if conflict else 0.
        rows.append(dict(scenario=s.name,regular_feasible=not conflict,horizon=h,
          prior=s.prior,accuracy=s.accuracy,q0=s.q0,qmax=s.qmax,
          signal_cost=s.signal_cost,lower=s.low,upper=s.high,
          greedy_exposure=round(actions['greedy'],8),
          rollout_exposure=round(actions['rollout'],8),
          exact_exposure=round(actions['exact'],8),
          greedy_loss=round(vals['greedy']+surcharge,10),
          rollout_loss=round(vals['rollout']+surcharge,10),
          exact_loss=round(vals['exact']+surcharge,10),
          exact_minus_greedy=round(vals['exact']-vals['greedy'],10),
          exact_minus_rollout=round(vals['exact']-vals['rollout'],10),
          clinical_calibration='NONE_SYNTHETIC'))
    csv_write(BASE/'results_model.csv',rows)

    # Strict frozen misspecification grid (not optimized after inspecting outcome)
    stress=[]
    for name in ('near_harm','weak_signal','upper_restricted'):
        s=next(x for x in scenarios if x.name==name)
        pl=Planner(s)
        for true_prior in (.20,.42,.70):
            for true_accuracy in (.25,.50,.85):
                vals={m:pl.external_value(m,true_prior,true_accuracy)
                      for m in ('greedy','rollout','exact')}
                stress.append(dict(scenario=name,assumed_prior=s.prior,
                    true_prior=true_prior,assumed_accuracy=s.accuracy,
                    true_accuracy=true_accuracy,
                    greedy_loss=round(vals['greedy'],10),
                    rollout_loss=round(vals['rollout'],10),
                    exact_loss=round(vals['exact'],10),
                    exact_minus_greedy=round(vals['exact']-vals['greedy'],10),
                    exact_minus_rollout=round(vals['exact']-vals['rollout'],10)))
    csv_write(BASE/'results_misspecification.csv',stress)

    grid=[0.,.25,.5,.75,1.]
    feasibility=[]
    for s in scenarios:
        eligible=[e for e in grid if s.low <=e<=s.high]
        feasibility.append(dict(scenario=s.name,continuous_feasible=s.low<=s.high,
          coarse_grid_feasible=bool(eligible),regular_grid_options=';'.join(map(str,eligible)),
          fallback_is_regular=(s.low<=s.fallback<=s.high)))
    csv_write(BASE/'audit_discretization.csv',feasibility)
    audit=governance_audit([(.70,.30),(.70,.30),(.70,.30),(.20,.80),(.20,.80)],
                           externally_signed=[False,False,False,False,True])
    csv_write(BASE/'governance_audit.csv',audit)
    metadata=dict(version='1.9D',status='exploratory',date='2026-11-11',
      description='Deterministic exact finite-horizon belief-tree enumeration',
      scenario_count=len(scenarios),misspecification_count=len(stress),
      seed='not_applicable_exact_enumeration',
      disclaimer='Toy model; neither clinical validation nor independent confirmation',
      prior_stage_reference='v1.9C: 192 equal cases, 1,947 infeasible combinations, 30 grid-only failures (not reproduced here)',
      policy_definitions={'greedy':'one-period biological risk + signal cost',
        'rollout':'receding one-step policy improvement over exact greedy continuation value',
        'exact':'Bellman optimum over same actions, observations and costs'},
      objective='expected cumulative biological regret plus signal-acquisition costs and mandatory conflict review cost',
      code='experiment_v1_9d.py')
    (BASE/'metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False),encoding='utf8')
    tests(scenarios,rows,stress,feasibility,audit)
    print(json.dumps({'scenarios':len(scenarios),'stress_cases':len(stress),
        'dynamic_advantage_scenarios':[r['scenario'] for r in rows if r['exact_minus_greedy']< -1e-7],
        'misspecification_reversals':[r for r in stress if r['exact_minus_greedy']>1e-7][:5],
        'model_results':rows},indent=2))


def tests(scenarios,rows,stress,feasibility,audit):
    # All planners have exactly the same data, cost and admissible action set.
    assert len(rows)==12 and len(stress)==27
    for r in rows:
        assert r['exact_loss'] <= r['rollout_loss']+1e-8, r
        assert r['rollout_loss'] <= r['greedy_loss']+1e-8, r
    for r in rows:
        s=next(s for s in scenarios if s.name==r['scenario'])
        if s.low<=s.high:
            for mode in ['greedy','rollout','exact']:
                assert s.low-1e-8<=r[mode+'_exposure']<=s.high+1e-8
        else:
            assert all(abs(r[m+'_exposure']-s.fallback)<1e-8 for m in ['greedy','rollout','exact'])
            assert r['greedy_loss']==r['exact_loss']==r['rollout_loss']
    # Informativeness-free evidence should not produce a nonmyopic improvement.
    nul=next(r for r in rows if r['scenario']=='uninformative')
    assert abs(nul['exact_minus_greedy']) < 1e-8
    # Continuous feasible but coarse grid contains no admissible action.
    gap=next(r for r in feasibility if r['scenario']=='narrow_grid_gap')
    assert gap['continuous_feasible'] and not gap['coarse_grid_feasible']
    # Review duration and cost do not grant any action or update.
    assert audit[0]['review_cost']==.02
    assert audit[1]['state']=='UNRESOLVED'
    assert audit[3]['state']=='UNRESOLVED' and audit[3]['reason']=='CONTINGENCY_NOT_REGULAR_ACTION'
    assert audit[4]['state']=='NORMAL' and audit[4]['authorized_external_update']
    # Bayes-risk decomposition under correctly specified generator
    s=next(s for s in scenarios if s.name=='near_harm')
    p=Planner(s)
    for m in ('exact','greedy','rollout'):
        assert abs(p.external_value(m,s.prior,s.accuracy)-p._value(m,s.horizon,pkey(s.prior))) < 1e-8
    (BASE/'TESTS_OK.txt').write_text('8 groups of reproducible assertions passed.\n',encoding='utf8')

if __name__=='__main__':main()
