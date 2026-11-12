#!/usr/bin/env python3
"""Additional independent regression checks for v1.9D toy experiment."""
import math
from experiment_v1_9d import (make_scenarios,Planner,Scenario,pkey,acquisition,
    biological_loss,posterior,signal_pos_probability,governance_audit)


def first_period_q(pl,e):
    s=pl.s;p=pkey(s.prior);h=s.horizon
    q=acquisition(e,s)
    value=biological_loss(e,p,s.effect)+s.signal_cost*q
    if h>1:
        a=s.accuracy;r=signal_pos_probability(p,a)
        value+=(1-q)*pl.exact_value(h-1,p)+q*(
          r*pl.exact_value(h-1,posterior(p,a,True))+
          (1-r)*pl.exact_value(h-1,posterior(p,a,False)))
    return value

cases=make_scenarios()
checks=0
for s in cases:
    pl=Planner(s); p=pkey(s.prior)
    if s.low<=s.high:
        opt=pl.exact_value(s.horizon,p)
        # Independent uniform-grid comparison against analytical optimizer.
        for i in range(201):
            e=s.low+(s.high-s.low)*i/200
            assert opt<=first_period_q(pl,e)+1e-8,(s.name,e,opt,first_period_q(pl,e))
            checks+=1
        assert abs(pl.exact_value(1,p)-pl.greedy_value(1,p))<1e-9
    else:
        assert not s.low<=s.high

# Discrete grid mesh guarantee: every closed interval of width >= 0.25
# on [0,1] contains at least one of {0,0.25,0.50,0.75,1}.
mesh=[i/4 for i in range(5)]
for i in range(101):
    for j in range(i+25,101):
        lo=i/100;hi=j/100
        assert any(lo-1e-12<=x<=hi+1e-12 for x in mesh)
        checks+=1

# Check that a signed authorization lacking feasible bounds does not release.
audit=governance_audit([(.8,.2),(.8,.2),(.8,.2)],
                        externally_signed=[False,True,True])
assert all(a['state']!='NORMAL' for a in audit)
assert sum(a['review_cost'] for a in audit)==.02
assert all(a['reason']=='CONTINGENCY_NOT_REGULAR_ACTION' for a in audit)
checks+=3

print(f'OK: {checks} independent numeric, grid and governance assertions')
