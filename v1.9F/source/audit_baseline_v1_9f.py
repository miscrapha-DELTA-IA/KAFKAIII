#!/usr/bin/env python3
"""KAFKA III v1.9F / gate 1: reproduction and structural non-equivalence audit.

Uses the untouched v1.8A and v1.9E source modules on disk. This is
software verification, NOT an evaluation of policy safety or clinical effect.
"""
from __future__ import annotations
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLD = ROOT / 'v1_8a_mapas'
NEW = ROOT / 'kafka_iii_v1_9e'
sys.path.insert(0, str(OLD))
sys.path.insert(0, str(NEW))
import kafka_v18a_map as v18  # noqa: E402
import experiment_v1_9e as v19  # noqa: E402
import numpy as np  # noqa: E402


def robust_regret(e: float, delta: float) -> float:
    return (1.0 - e) * max(delta, 0.0) + e * max(-delta, 0.0)


def independent_safe_baseline(lo: float, hi: float, eta: float) -> float:
    """Independently coded grid-constrained safe static regret minimizer.

    Same information and loss used in v1.8A; distinct scalar implementation.
    Tiebreak mimics the original baseline preference.
    """
    if not (-1.000001 <= lo <= hi <= 1.000001):
        raise ValueError('invalid uncertainty interval')
    actions = [float(e) for e in v18.GRID]
    allowable = [e for e in actions if (v18.E0 - e) * max(hi, 0.0) <= eta + 1e-12]
    if not allowable:
        raise AssertionError('baseline must remain an available action')
    return min(allowable, key=lambda e: (
        max(robust_regret(e, lo), robust_regret(e, hi)) + 1e-11 * abs(e-v18.E0)))


def audit():
    assert float(v18.E0) == 0.95
    assert tuple(v18.GRID.tolist()) == (0.0, 0.05, 0.25, 0.5, 0.75, 0.95)
    assert v19.GRID == (0.0, 0.25, 0.5, 0.75, 1.0)

    # Direct counterexample from the v1.8A report.
    examples = []
    for eta, expected in ((.005,.95), (.020,.75), (.050,.05)):
        old = float(v18.pick_guard(np.array([-.25]), np.array([.05]), eta)[0])
        reconstructed = independent_safe_baseline(-.25, .05, eta)
        assert abs(old-expected)<1e-12 and abs(reconstructed-old)<1e-12
        examples.append(dict(L=-.25,U=.05,eta=eta,guard=old,constant_zero=0.,
            zero_violates_guard=(v18.E0*0.05>eta+1e-12)))

    # Reconstruct all v1.8A history draws and the interval-expansion choices.
    rng = np.random.default_rng(v18.SEED)
    total = 0
    exact_matches = 0
    zero_mismatches = 0
    zero_guard_violations = 0
    by_eta = {str(eta): dict(total=0,mismatch_zero=0,guard_violations_zero=0)
              for eta in v18.ETAGRID}
    for _, (past, future, mnar) in v18.SCENARIOS.items():
        l, h, post, nrare, obs1, obs0 = v18.make_history(rng, 400, past, mnar)
        for b in v18.BGRID:
            low = np.maximum(-1, l-b).reshape(-1)
            high = np.minimum(1, h+b).reshape(-1)
            for eta in v18.ETAGRID:
                actual = v18.pick_guard(low, high, eta)
                key = str(eta)
                for i, (L,U) in enumerate(zip(low,high)):
                    expected = independent_safe_baseline(float(L),float(U),eta)
                    got = float(actual[i])
                    total += 1
                    by_eta[key]['total'] += 1
                    match = abs(expected-got) < 1e-12
                    exact_matches += int(match)
                    zero_differs = abs(got-0.0)>1e-12
                    zero_mismatches += int(zero_differs)
                    by_eta[key]['mismatch_zero'] += int(zero_differs)
                    zero_violates = v18.E0*max(float(U),0.0) > eta+1e-12
                    zero_guard_violations += int(zero_violates)
                    by_eta[key]['guard_violations_zero'] += int(zero_violates)
    assert total==9*400*4*3*3
    assert exact_matches==total

    # Source-code direct check: v1.9E returns the action closest to zero on an
    # unconstrained regular grid. No assumptions about outcomes are used.
    proxy_action = v19.select_policy('safe_static_proxy',0,6,2,None,None,0,
                                     v19.GRID,authorized_reentry=True)
    assert proxy_action==0.0
    result = dict(stage='v1.9F gate 1 internal software audit',status='completed',
        kind='exploratory code/decision audit, not clinical evaluation',
        history='original v1.8A synthetic generator, 400 reps per family',
        scenarios=9,decision_checks=total,independent_static_exact_matches=exact_matches,
        independent_static_exact_match_fraction=round(exact_matches/total,6),
        proxy_zero_differs_from_v18_guard=zero_mismatches,
        proxy_zero_differs_fraction=round(zero_mismatches/total,6),
        proxy_zero_violates_v18_guard=zero_guard_violations,
        proxy_zero_guard_violation_fraction=round(zero_guard_violations/total,6),
        per_eta=by_eta,
        source_grids=dict(v18a=list(map(float,v18.GRID)),v19e=list(v19.GRID)),
        v18a_reference_exposure=v18.E0,
        v19e_proxy_target=proxy_action,
        examples=examples,
        warning='Same-history diagnostic only. Loss scales and dynamic inference differ; no performance comparison.'
    )
    out=ROOT/'audit_baseline_v1_9f_results.json'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':audit()
