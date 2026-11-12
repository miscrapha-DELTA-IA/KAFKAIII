#!/usr/bin/env python3
"""KAFKA III v0.5C state and information-boundary invariants."""
import unittest, tempfile
from pathlib import Path
from dataclasses import fields
from kafka_v05c_decision import (Controller, ControllerInput, Governance, Scenario,
                                 simulate_v05c,run_v05c, default_design_certificate)


def e(month, cohort_month, stratum, low, high, label=None):
    return ControllerInput(month,label or f'c{cohort_month}-{stratum}',cohort_month,stratum,
                           low,high,'CP_full',100,100)

class TestDynamicState(unittest.TestCase):
    def test_no_probe_without_authorization(self):
        c=Controller(Governance(q=.02,probe_approval=False),initial='P0')
        for t in range(10):
            p,state,pr=c.decide_exposure(t,'P0_PROBE_ONCE')
            self.assertEqual(p,0)
            self.assertFalse(pr)
        self.assertFalse(any('PROBE' in x['action'] for x in c.events))

    def test_probe_exposure_only_one_cohort(self):
        c=Controller(Governance(q=.02),initial='P0')
        for t in range(10):
            p,state,pr=c.decide_exposure(t,'P0_PROBE_ONCE')
            if t==7:self.assertEqual((p,state,pr),(.02,'PROBE_WAIT',True))
            if t==8:self.assertEqual((p,state,pr),(0.,'PROBE_WAIT',False))
        self.assertEqual(c.probe_count,1)

    def test_positive_probe_and_restricted_reentry(self):
        c=Controller(Governance(q=.05),initial='P0')
        _,_,probe=c.decide_exposure(7,'P0_PROBE_ONCE')
        self.assertTrue(probe)
        c.cohort_origin[7]='PROBE_WAIT'
        self.assertEqual(c.state,'PROBE_WAIT')
        c.consume(12,[e(12,7,m,.04,.3) for m in range(4)])
        self.assertEqual(c.state,'REENTRY_RESTRICTED')
        x=c.decide_exposure(12,'P0_PROBE_ONCE')
        self.assertEqual(x[0],.25)
        self.assertEqual(x[1],'REENTRY_RESTRICTED')
        c.cohort_origin[12]='REENTRY_RESTRICTED'
        c.consume(17,[e(17,12,m,.04,.3) for m in range(4)])
        self.assertEqual(c.state,'ACTIVE')
        self.assertTrue(any(v['action']=='FULL_REENTRY_ON_CERTIFIED_POSITIVE' for v in c.events))

    def test_inconclusive_probe_returns_to_p0(self):
        c=Controller(Governance(),initial='P0')
        c.decide_exposure(7,'P0_PROBE_ONCE')
        c.cohort_origin[7]='PROBE_WAIT'
        c.consume(12,[e(12,7,m,-.1,.2) for m in range(4)])
        self.assertEqual(c.state,'P0')
        self.assertEqual(c.decide_exposure(13,'P0_PROBE_ONCE')[0],0.)

    def test_negative_evidence_suspends_when_certified(self):
        c=Controller(Governance())
        c.decide_exposure(0,'EVIDENCE_GATED')
        c.cohort_origin[0]='ACTIVE'
        c.consume(5,[e(5,0,0,-.4,-.01)])
        self.assertEqual(c.state,'P0')
        self.assertEqual(c.valid_decisions,1)

    def test_uncertified_evidence_cannot_change_authority(self):
        c=Controller(Governance(certified_individual_inference=False))
        c.decide_exposure(0,'EVIDENCE_GATED')
        c.cohort_origin[0]='ACTIVE'
        c.consume(5,[e(5,0,0,-.4,-.01)])
        self.assertEqual(c.state,'ACTIVE')
        self.assertEqual(c.invalid_evidence_blocked,1)

    def test_no_duplicated_evidence(self):
        c=Controller(Governance())
        c.decide_exposure(0,'EVIDENCE_GATED')
        c.cohort_origin[0]='ACTIVE'
        obs=e(5,0,0,-.1,.1)
        c.consume(5,[obs])
        with self.assertRaises(AssertionError):c.consume(5,[obs])

    def test_controller_input_excludes_truth(self):
        names={f.name for f in fields(ControllerInput)}
        self.assertFalse(names & {'U','Y0','Y1','delta_true','oracle','counterfactual','scenario'})

    def test_scenario_certification(self):
        self.assertFalse(default_design_certificate(Scenario('cap',capacity_fraction=.4)))
        self.assertFalse(default_design_certificate(Scenario('badlabels',mislabel=True)))
        self.assertTrue(default_design_certificate(Scenario('basic')))

    def test_uncertified_probe_returns_without_claiming_benefit(self):
        c=Controller(Governance(certified_individual_inference=False),initial='P0')
        c.decide_exposure(7,'P0_PROBE_ONCE')
        c.cohort_origin[7]='PROBE_WAIT'
        c.consume(12,[e(12,7,m,.1,.4) for m in range(4)])
        self.assertEqual(c.state,'P0')
        self.assertFalse(any(x['action']=='REENTRY_ON_CERTIFIED_POSITIVE' for x in c.events))
        self.assertTrue(any(x['action']=='PROBE_NOT_DECISION_ELIGIBLE' for x in c.events))

    def test_no_new_probe_after_one(self):
        c=Controller(Governance(q=.05,max_probes=1),initial='P0')
        c.decide_exposure(7,'P0_PROBE_ONCE')
        c.cohort_origin[7]='PROBE_WAIT'
        c.consume(12,[e(12,7,m,-.3,.3) for m in range(4)])
        self.assertEqual(c.state,'P0')
        for t in range(13,20):
            rate, _, enrolled=c.decide_exposure(t,'P0_PROBE_ONCE')
            self.assertFalse(enrolled)
            self.assertEqual(rate,0.)
        self.assertEqual(c.probe_count,1)

    def test_alpha_budget_not_dynamic(self):
        from kafka_v05c_decision import ALPHA_ARM, M, B
        self.assertAlmostEqual(ALPHA_ARM*2*M*B, .025)

    def test_simulation_and_pair_loss_identity(self):
        x=simulate_v05c(Scenario('harm_unit',alert_wlst_shift=1.8),
                        'EXTERNAL_P0_PROBE',0,123,Governance(),months=10,n_stratum=10)
        self.assertEqual(x['cohorts_evaluated'],40)
        self.assertEqual(x['probe_enrollment_months'],1)
        self.assertEqual(x['probe_exposures'],sum(m['shown'] for m in x['monthly'] if m['probe_enrollment']))
        self.assertEqual(sum(x['state_months'].values()),10)
        self.assertTrue(any(e['action']=='SYNTHETIC_AUTHORIZED_PROBE_ENROLL' for e in x['decisions']))
        self.assertTrue(all(m['exposure_probability']==0 for m in x['monthly'] if m['state']=='PROBE_WAIT' and not m['probe_enrollment']))
        with tempfile.TemporaryDirectory() as d:
            rows,moms=run_v05c(Path(d),reps=1,months=10,n_stratum=10,
                               scenarios=[Scenario('harm_unit',alert_wlst_shift=1.8)])
            for row in rows:
                m=[r for r in moms if r['policy']==row['policy']]
                total=sum((r['loss_vs_oracle_month_per_1000']*r['n']/1000) for r in m)
                ref_loss=(row['fixed_oracle_expected_good']-row['expected_good'])
                self.assertAlmostEqual(total,ref_loss,places=9)

    def test_utility_comparator_counts_oracle_cost(self):
        with tempfile.TemporaryDirectory() as d:
            rows,_=run_v05c(Path(d),reps=1,months=8,n_stratum=15,
                            scenarios=[Scenario('benefit',alert_wlst_shift=-1.5)],
                            extra_operating_cost_per_alert=.02)
            on=next(x for x in rows if x['policy']=='ALWAYS_ON')
            off=next(x for x in rows if x['policy']=='ALWAYS_OFF')
            utility_on=on['expected_good']-.02*on['alerts_shown']
            utility_off=off['expected_good']-.02*off['alerts_shown']
            self.assertAlmostEqual(on['utility_loss_vs_fixed_oracle_per_1000'],
                    1000*(max(utility_on,utility_off)-utility_on)/on['n'])
            self.assertAlmostEqual(off['utility_loss_vs_fixed_oracle_per_1000'],
                    1000*(max(utility_on,utility_off)-utility_off)/off['n'])

    def test_simulation_same_seed_deterministic(self):
        sc=Scenario('beneficial',alert_wlst_shift=-1.5)
        gov=Governance()
        a=simulate_v05c(sc,'EVIDENCE_GATED',0,123,gov,months=8,n_stratum=15)
        b=simulate_v05c(sc,'EVIDENCE_GATED',0,123,gov,months=8,n_stratum=15)
        self.assertEqual(a,b)

    def test_withholding_q_is_not_probe_q(self):
        a=simulate_v05c(Scenario('a'),'ACTIVE_SENTINEL',0,19,Governance(q=.05),months=8,n_stratum=30)
        b=simulate_v05c(Scenario('a'),'P0_PROBE_ONCE',0,19,Governance(q=.05),months=8,n_stratum=30)
        self.assertGreater(a['alerts_shown'],b['alerts_shown'])

if __name__=='__main__':unittest.main(verbosity=2)
