#!/usr/bin/env python3
"""KAFKA III v1.9E: internally specified exploratory adversarial falsification.

Standard library only; no patients; no clinical calibration; not externally blinded.
Run: python experiment_v1_9e.py
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from statistics import mean, stdev
import csv, hashlib, json, math, random

ROOT = Path(__file__).resolve().parent
VERSION = "1.9E"
N = 800
H = 6
PRIOR = 0.42
EFFECT = 0.10
ACQ_COST = 0.001
REVIEW_COST = 0.02
PROBE_BUDGET = 2
GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
POLICIES = ('kafka_gate', 'nominal_bayes', 'robust_bayes_mix',
            'minimax_one_step', 'greedy', 'safe_static_proxy',
            'historical_on', 'sentinel', 'fixed_probe')

@dataclass(frozen=True)
class Environment:
    name: str
    theta_mode: str = 'random'
    true_prior: float = PRIOR
    accuracy: float = 0.85
    drop_plus: float = 0.0
    drop_minus: float = 0.0
    delay: int = 0
    q0: float = 0.02
    qmax: float = 0.82
    kappa: float = 0.0
    rule: str = 'normal'

FAMILIES = (
    Environment('nominal_static'),
    Environment('always_benefit', theta_mode='plus'),
    Environment('always_harm', theta_mode='minus'),
    Environment('null_effect', theta_mode='null'),
    Environment('harm_to_benefit', theta_mode='harm_to_benefit'),
    Environment('benefit_to_harm', theta_mode='benefit_to_harm'),
    Environment('reverse_after_reentry_window', theta_mode='reverse_twice'),
    Environment('heterogeneity_two_strata', theta_mode='strata'),
    Environment('inverted_signal', accuracy=.25),
    Environment('weak_signal', accuracy=.55),
    Environment('prior_shift', true_prior=.85),
    Environment('informative_missingness', drop_plus=.05, drop_minus=.70),
    Environment('delayed_outcomes', delay=2),
    Environment('weak_positivity', q0=.001, qmax=.06),
    Environment('cluster_congestion_proxy', kappa=.04),
    Environment('governance_conflict', rule='conflict'),
    Environment('grid_only_gap', rule='gap'),
    Environment('drifting_accuracy', rule='drifting_accuracy'),
)


def q_of(e: float, q0: float, qmax: float) -> float:
    return q0 + 4 * (qmax - q0) * e * (1-e)


def is_probe(e: float) -> bool:
    return 1e-10 < e < 1.0 - 1e-10


def clinical_loss(theta: int, e: float) -> float:
    return EFFECT * (1-e if theta == 1 else e if theta == -1 else 0.0)


def r10(w):
    return tuple(round(float(x), 10) for x in w)


class BeliefModel:
    """Hidden theta ± and static unknown accuracy mixture; DP only on model posterior.

    No true generator or outcomes are passed to this class.
    """
    def __init__(self, accuracies, mixing):
        self.a = tuple(accuracies)
        self.w0 = r10(v for pa in mixing for v in (pa*PRIOR, pa*(1-PRIOR)))

    def posterior_p(self, w):
        return sum(w[::2]) / sum(w)

    def positive_prob(self, w):
        return sum(w[2*i]*a + w[2*i+1]*(1-a)
                   for i, a in enumerate(self.a)) / sum(w)

    def signal(self, w, positive):
        raw = []
        for i, a in enumerate(self.a):
            raw += [w[2*i] * (a if positive else 1-a),
                    w[2*i+1] * (1-a if positive else a)]
        z = sum(raw)
        if z <= 0: return w
        return r10(x/z for x in raw)

    def immediate(self, w, e):
        p = self.posterior_p(w)
        return EFFECT*(p*(1-e)+(1-p)*e) + ACQ_COST*q_of(e, .02, .82)

    @lru_cache(maxsize=180000)
    def value(self, h, w, b):
        if h == 0: return 0.0
        return min(self.action_value(h, w, b, e) for e in GRID
                   if not is_probe(e) or b > 0)

    def action_value(self, h, w, b, e):
        if is_probe(e) and b <= 0: return math.inf
        v = self.immediate(w, e)
        if h <= 1: return v
        bnext = b - int(is_probe(e))
        q = q_of(e, .02, .82)
        pos = self.positive_prob(w)
        return v + (1-q)*self.value(h-1, w, bnext) + q*(
            pos*self.value(h-1, self.signal(w, True), bnext)
            +(1-pos)*self.value(h-1, self.signal(w, False), bnext))

    def decide(self, h, w, b, allowed):
        assert allowed, 'caller must handle conflict before selection'
        return min(allowed, key=lambda e: (round(self.action_value(h,w,b,e), 11), e))


NOMINAL = BeliefModel((.85,), (1.0,))
ROBUST = BeliefModel((.55,.85), (.5,.5))


@dataclass
class Gov:
    state: str = 'NORMAL'
    remaining: int = 0
    incidents: int = 0

    def force_review(self):
        if self.state == 'NORMAL':
            self.state = 'PENDING_REVIEW'
            self.remaining = 2
            self.incidents += 1
            return REVIEW_COST
        return 0.0

    def check(self, lo, hi, release_signed):
        """Signed external update releases only with fresh feasible bounds.
        No statistical observations or new privileges originate in this state machine.
        """
        new_charge = 0.0
        if self.state == 'NORMAL' and lo > hi:
            self.state = 'PENDING_REVIEW'
            self.remaining = 2
            self.incidents += 1
            new_charge = REVIEW_COST
        if self.state != 'NORMAL':
            if release_signed and lo <= hi:
                self.state = 'NORMAL'
                self.remaining = 0
                return False, new_charge, 'SIGNED_EXTERNAL_RELEASE'
            if self.state == 'PENDING_REVIEW':
                self.remaining -= 1
                if self.remaining <= 0: self.state = 'UNRESOLVED'
            return True, new_charge, 'NO_REGULAR_ACTION_REVIEW'
        return False, new_charge, 'NORMAL'


def bounds_for(env, t):
    if env.rule == 'conflict' and t in (2,3): return (.70,.30)
    if env.rule == 'gap' and t == 1: return (.37,.43)
    return (0.0,1.0)


def reentry_authorized(env, t):
    # Standing simulated external permission issued by an exogenous schedule;
    # NOT derived from the signal, truth, posterior, review or clinician.
    return t >= 1 and (env.rule != 'conflict' or t in (1, 5))


def signed_release(env, t):
    # Precommitted exogenous hypothetical signature: not evidence and not
    # automatically generated by an internal review process.
    return env.rule == 'conflict' and t == 5


def theta_for(env, latent, t, rep):
    mode = env.theta_mode
    if mode == 'plus': return 1
    if mode == 'minus': return -1
    if mode == 'null': return 0
    if mode == 'harm_to_benefit': return -1 if t < 3 else 1
    if mode == 'benefit_to_harm': return 1 if t < 3 else -1
    if mode == 'reverse_twice': return -1 if t < 2 or t >= 4 else 1
    if mode == 'strata': return 1 if rep % 2 == 0 else -1
    return latent


def accuracy_for(env, t):
    return (.90 if t < 3 else .30) if env.rule == 'drifting_accuracy' else env.accuracy


def allowed_regular(lo, hi, budget):
    """Never conflate continuous feasibility, grid absence and budget absence."""
    if lo > hi: return (), 'NO_REGULAR_ACTION'
    on_grid = [e for e in GRID if lo-1e-12 <= e <= hi+1e-12]
    if not on_grid:
        mid = round((lo+hi)/2, 10)
        if is_probe(mid) and budget <= 0: return (), 'NO_BUDGET_ACTION'
        return (mid,), 'NO_GRID_ACTION_CONTINUOUS_RESCUE'
    valid = tuple(e for e in on_grid if not is_probe(e) or budget > 0)
    if not valid: return (), 'NO_BUDGET_ACTION'
    return valid, 'REGULAR'


def select_policy(policy, t, h, budget, w, last_sig_t, count_received, allowed,
                  authorized_reentry=False):
    if policy == 'nominal_bayes': return NOMINAL.decide(h, w, budget, allowed)
    if policy == 'robust_bayes_mix': return ROBUST.decide(h, w, budget, allowed)
    if policy == 'greedy':
        return min(allowed, key=lambda e: (round(NOMINAL.immediate(w, e), 11), e))
    if policy == 'minimax_one_step':
        p = NOMINAL.posterior_p(w)
        low, high = max(0.0,p-.35), min(1.0,p+.35)
        worst = lambda e: max(EFFECT*(low*(1-e)+(1-low)*e),
                              EFFECT*(high*(1-e)+(1-high)*e)) + ACQ_COST*q_of(e,.02,.82)
        return min(allowed, key=lambda e: (round(worst(e), 11), e))
    if policy == 'kafka_gate':
        p = NOMINAL.posterior_p(w)
        fresh = last_sig_t is not None and (t - last_sig_t) <= 2
        # Signed reentry whitelist is an exogenous time-invariant permission
        # available to all policies, not an observation; all other safety bounds
        # still apply to all policies.
        target = 1.0 if p >= .80 and count_received >= 1 and fresh and authorized_reentry else (
                 .50 if t in (0,3) and budget > 0 and p > .20 else 0.0)
    elif policy == 'safe_static_proxy': target = 0.0
    elif policy == 'historical_on': target = 1.0
    elif policy == 'sentinel': target = .5 if t in (0,3) and budget > 0 else 0.0
    elif policy == 'fixed_probe': target = .5 if t in (0,1) and budget > 0 else 0.0
    else: raise ValueError(policy)
    return min(allowed, key=lambda e: (abs(e-target),e))


def exogenous(env, rep, rng):
    # Fixed common random numbers for all policy trajectories within episode.
    latent = 1 if rng.random() < env.true_prior else -1
    returns = []
    for t in range(H):
        returns.append((rng.random(), rng.random(), rng.random()))
    return latent, returns


def simulate_one(env, policy, latent, exog, rep, audit_trace=False):
    model = ROBUST if policy == 'robust_bayes_mix' else NOMINAL
    w = model.w0
    gov = Gov()
    queue = []
    budget = PROBE_BUDGET
    last_sig_t = None
    count_received = 0
    values = dict(total=0., biological=0., acquisition=0., congestion=0., review=0.,
                  regular_probes=0, received=0, false_suspends=0,
                  false_reentries=0, reentries=0, inconclusive=0,
                  contingencies=0, grid_rescues=0, no_budget_action=0,
                  authorization_violations=0, late_signals=0)
    trace = []
    for t in range(H):
        # Delivery happens only when an earlier observation becomes mature.
        due = [(src_t,sgn) for due_t,src_t,sgn in queue if due_t <= t]
        queue = [(due_t,src_t,sgn) for due_t,src_t,sgn in queue if due_t > t]
        for source_t,sgn in due:
            w = model.signal(w, sgn)
            last_sig_t=source_t
            count_received+=1
            values['received']+=1
        lo, hi = bounds_for(env,t)
        blocked, review_fee, gov_reason = gov.check(lo,hi,signed_release(env,t))
        values['review'] += review_fee
        if blocked:
            e = .10 # A hypothetical contingency, never a regular authorization
            values['contingencies'] += 1
            reason='CONTINGENCY_NO_REGULAR_AUTHORITY'
        else:
            legal, reason = allowed_regular(lo,hi,budget)
            if reason=='NO_GRID_ACTION_CONTINUOUS_RESCUE': values['grid_rescues'] += 1
            if not legal:
                values['no_budget_action'] += int(reason=='NO_BUDGET_ACTION')
                values['contingencies'] += 1
                values['review'] += gov.force_review()
                e = .10
                reason='CONTINGENCY_'+reason
            else:
                e=select_policy(policy,t,H-t,budget,w,last_sig_t,count_received,legal,
                                authorized_reentry=reentry_authorized(env,t))
                assert any(abs(e-c)<1e-10 for c in legal)
                assert lo-1e-12 <= e <= hi+1e-12
                if is_probe(e):
                    assert budget > 0
                    budget-=1
                    values['regular_probes']+=1
        # The policies never see true theta, q_true, a_true or these latent uniforms.
        theta=theta_for(env,latent,t,rep)
        # Contingency may cause biological loss, but cannot harvest a free
        # comparison signal or circumvent the two regular-probe budget.
        q_true=0.0 if reason.startswith('CONTINGENCY_') else q_of(e,env.q0,env.qmax)
        bio=clinical_loss(theta,e)
        acq=ACQ_COST*q_true
        cong=env.kappa*e*e
        values['biological']+=bio
        values['acquisition']+=acq
        values['congestion']+=cong
        if theta == 1 and e <= .25+1e-9: values['false_suspends']+=1
        if theta == -1 and e >= .75-1e-9: values['false_reentries']+=1
        if e >= .75-1e-9: values['reentries']+=1
        if policy == 'kafka_gate' and e >= .75-1e-9:
            # An evaluator-side assertion, computed from the *available*
            # posterior, signed permission and source cohort timestamps.
            gate_eligible=(NOMINAL.posterior_p(w) >= .80 and count_received >= 1
                and last_sig_t is not None and t-last_sig_t <= 2
                and reentry_authorized(env,t) and not reason.startswith('CONTINGENCY_'))
            if not gate_eligible: values['authorization_violations']+=1
        if policy == 'kafka_gate' and e < .75 and .20 < NOMINAL.posterior_p(w) < .80:
            values['inconclusive']+=1
        u_acq,u_miss,u_sig = exog[t]
        if u_acq < q_true:
            dropout=env.drop_plus if theta==1 else env.drop_minus if theta==-1 else .50
            if u_miss >= dropout:
                a_true=accuracy_for(env,t) if theta else .50
                positive=u_sig < (a_true if theta==1 else 1-a_true if theta==-1 else .50)
                arrival=t+1+env.delay
                queue.append((arrival, t, positive))
                if arrival>=H: values['late_signals']+=1
        if audit_trace:
            trace.append(dict(period=t,theta_evaluator_only=theta,exposure=e,
                  authority_state=gov.state,governance_reason=gov_reason,decision_reason=reason,
                  belief_before_action=round(model.posterior_p(w),6),
                  observation_count=count_received,last_evidence_cohort=last_sig_t,remaining_probe_budget=budget,
                  acquired_probability=round(q_true,6),signed_external_release=signed_release(env,t),
                  simulated_reentry_permission=reentry_authorized(env,t)))
    values['total']=sum(values[x] for x in ('biological','acquisition','congestion','review'))
    values['remaining_probe_budget']=budget
    values['reviews_opened']=gov.incidents
    assert values['regular_probes']<=PROBE_BUDGET
    assert values['authorization_violations']==0
    return values, trace


def mean_se(values):
    return mean(values), stdev(values)/math.sqrt(len(values)) if len(values)>1 else 0.


def csv_out(name, rows):
    assert rows
    with (ROOT/name).open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)


def main():
    summaries, differences, traces, family_summaries = [],[],[],[]
    all_results=[]
    for idx, env in enumerate(FAMILIES):
        rng=random.Random(20261111 + 1009*idx)
        samples={p:[] for p in POLICIES}
        for rep in range(N):
            latent, uniforms = exogenous(env,rep,rng)
            for policy in POLICIES:
                val,tr=simulate_one(env,policy,latent,uniforms,rep,
                                    audit_trace=(rep==0 and policy in ('kafka_gate','nominal_bayes')))
                samples[policy].append(val)
                if tr: traces.extend(dict(family=env.name,policy=policy,**row) for row in tr)
        for policy in POLICIES:
            losses=[row['total'] for row in samples[policy]]
            avg,se=mean_se(losses)
            metric=('biological','acquisition','congestion','review','regular_probes',
                    'received','false_suspends','false_reentries','reentries',
                    'inconclusive','contingencies','grid_rescues','no_budget_action',
                    'reviews_opened','late_signals')
            row=dict(family=env.name,policy=policy,episodes=N,
                     mean_loss=round(avg,8),se_loss=round(se,8),
                     ci95_lower=round(avg-1.96*se,8),ci95_upper=round(avg+1.96*se,8))
            row.update({f'mean_{k}':round(mean(r[k] for r in samples[policy]),6) for k in metric})
            summaries.append(row)
        k=samples['kafka_gate']
        for policy in POLICIES:
            if policy=='kafka_gate':continue
            contrasts=[samples[policy][i]['total']-k[i]['total'] for i in range(N)]
            gain,se=mean_se(contrasts)
            differences.append(dict(family=env.name,comparator=policy,
                n=N,comparator_minus_kafka=round(gain,8),paired_se=round(se,8),
                ci95_low=round(gain-1.96*se,8),ci95_high=round(gain+1.96*se,8),
                interpretation='positive favors Kafka; negative favors comparator',
                multiplicity='not adjusted; exploratory'))
        pidx={p:mean(row['total'] for row in samples[p]) for p in POLICIES}
        family_summaries.append(dict(family=env.name,
            best_by_sample=min(pidx,key=pidx.get),
            kafka_loss=pidx['kafka_gate'],
            nominal_loss=pidx['nominal_bayes'],
            robust_loss=pidx['robust_bayes_mix'],
            static_loss=pidx['safe_static_proxy'],
            kafka_minus_nominal=pidx['kafka_gate']-pidx['nominal_bayes'],
            kafka_minus_static=pidx['kafka_gate']-pidx['safe_static_proxy']))
    csv_out('results_policy_metrics.csv',summaries)
    csv_out('results_paired_differences.csv',differences)
    csv_out('audit_example_paths.csv',traces)
    meta=dict(version=VERSION, nature='exploratory internal synthetic simulation',
        preregistration='NONE',independent_evaluator=False,clinical_calibration=False,
        horizon=H,replicates_per_family=N,number_families=len(FAMILIES),
        total_trajectories=N*len(FAMILIES)*len(POLICIES),
        seed_rule='20261111 + 1009*family_index',
        software='Python >=3.10 standard library',common_random_numbers=True,
        policies=POLICIES,families=[asdict(env) for env in FAMILIES],
        losses='cumulative synthetic regret + acquisition attempt cost + cluster-only congestion + review incident',
        frequency_coverage='NOT ESTIMATED; no confidence sequence or valid interval implemented',
        caveats=['not the original safe policy learning implementation',
            'candidate kafka_gate is a toy rule rather than full Kafka architecture',
            'cluster congestion is not causal interference identification',
            'Monte Carlo confidence intervals are unadjusted and nonconfirmatory',
            'no externally held-out test seeds or independent auditor'])
    (ROOT/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (ROOT/'family_summary.json').write_text(json.dumps(family_summaries,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(families=len(FAMILIES),episodes=N,policies=len(POLICIES),
        trajectories=meta['total_trajectories'],
        kafka_worse_than_static=[r['family'] for r in family_summaries if r['kafka_minus_static']>1e-6],
        kafka_worse_than_nominal=[r['family'] for r in family_summaries if r['kafka_minus_nominal']>1e-6],
        summary=family_summaries),ensure_ascii=False,indent=2))


if __name__=='__main__': main()
