#!/usr/bin/env python3
"""Reproducible invariants for KAFKA III v0.5B. Run python -m unittest -v."""
import math, unittest
from dataclasses import fields
import numpy as np
from kafka_v05b_scm import (
 Scenario, ObservedCohort, ObservedMonitor, SCENARIOS, ALPHA_ARM,
 exposure, exogenous, patient_process, effect_interval, exact_binom_ci,
 simulate_policy, HORIZON_MONTHS, FULL_MATURITY_LAG,
)

class TestCausalContract(unittest.TestCase):
    def setUp(self):
        self.sc=Scenario('unit_harm', alert_wlst_shift=1.8)
        self.ex=exogenous(12345,self.sc,0,1,500)

    def test_states_semantics(self):
        q=.02
        self.assertEqual(exposure('ALWAYS_ON',q,0,'ACTIVE',False)[0],1)
        self.assertEqual(exposure('ALWAYS_OFF',q,0,'ACTIVE',False)[0],0)
        self.assertEqual(exposure('ACTIVE_SENTINEL',q,0,'ACTIVE',False)[0],.98)
        self.assertEqual(exposure('P0_PROBE_ONCE',q,7,'P0',True)[0],.02)
        self.assertEqual(exposure('P0_PROBE_ONCE',q,7,'P0',False)[0],0)
        self.assertEqual(exposure('P0_PROBE_ONCE',q,8,'P0',True)[0],0)
        self.assertEqual(exposure('TRIGGER_P0_WITH_PROBE',q,8,'P0',True)[0],.02)
        self.assertEqual(exposure('TRIGGER_P0_WITH_PROBE',q,9,'P0',True)[0],0)

    def test_wlst_and_capacity_are_distinct(self):
        p=patient_process(self.ex,self.ex['z_uniform']<.95,self.sc,0,.4,0)
        self.assertGreater(p['Q'].sum(),0)
        self.assertGreater(p['W'].sum(),0)
        self.assertFalse(np.any(p['Q'] & p['W']))
        self.assertFalse(np.any(p['T'] & p['Q']))
        self.assertFalse(np.any(p['T'] & p['W']))
        self.assertEqual(p['T'].sum(),200)
        self.assertTrue(np.all(p['S']>=.60))
        self.assertTrue(np.all(np.isnan(p['R'][~p['Z']])))

    def test_policy_no_effect_when_treatment_path_blocked(self):
        sc=Scenario('blocked',alert_wlst_shift=3.)
        e={k:v.copy() for k,v in self.ex.items()}
        e['indicated_uniform'][:]=1. # No patient is indicated for support
        p0=patient_process(e,np.zeros(500,dtype=bool),sc,0,1.,0)
        p1=patient_process(e,np.ones(500,dtype=bool),sc,0,1.,0)
        self.assertTrue(np.array_equal(p0['Y'],p1['Y']))
        self.assertTrue(np.array_equal(p0['T'],p1['T']))
        self.assertTrue(np.all(p1['T']==0))

    def test_benefit_and_harm_mediated_by_treatment(self):
        e=self.ex
        p0=patient_process(e,np.zeros(500,dtype=bool),Scenario('a'),0,1.,0)
        pb=patient_process(e,np.ones(500,dtype=bool),Scenario('b',alert_wlst_shift=-3.),0,1.,0)
        ph=patient_process(e,np.ones(500,dtype=bool),Scenario('c',alert_wlst_shift=3.),0,1.,0)
        self.assertGreater(pb['T'].sum(),p0['T'].sum())
        self.assertLess(ph['T'].sum(),p0['T'].sum())
        self.assertGreater(pb['Y'].sum(),p0['Y'].sum())
        self.assertLess(ph['Y'].sum(),p0['Y'].sum())

    def test_delays_and_maturity_no_early_release(self):
        sc=Scenario('d',delay_differential=True)
        p=patient_process(self.ex,self.ex['z_uniform']<.5,sc,0,1.,0)
        self.assertGreaterEqual(int(np.min(p['report_lag'])),0)
        self.assertLessEqual(int(np.max(p['report_lag'])),2)
        self.assertEqual(HORIZON_MONTHS,3)
        c=ObservedCohort('cohort',0,0,FULL_MATURITY_LAG,10,10,10,10,5,5)
        mon=ObservedMonitor()
        with self.assertRaises(ValueError):mon.receive(c,current_month=4)
        self.assertEqual(mon.evaluate_ready(4),[])
        mon.receive(c,current_month=5)
        self.assertEqual(len(mon.evaluate_ready(5)),1)
        self.assertEqual(len(mon.evaluate_ready(6)),0)
        with self.assertRaises(ValueError):mon.receive(c,current_month=6)

    def test_observed_data_cannot_reveal_truth(self):
        names={f.name for f in fields(ObservedCohort)}
        self.assertTrue({'n0','n1','o0','o1','g0','g1'}<=names)
        self.assertFalse({'U','Y0','Y1','truth','counterfactual','delta','p_y'}&names)

    def test_CP_empty_arm_and_missing(self):
        self.assertEqual(exact_binom_ci(0,0,ALPHA_ARM),(0.,1.))
        c=ObservedCohort('c',0,0,5,100,0,100,0,50,0)
        ev=effect_interval(c)
        self.assertLessEqual(ev.lower,0)
        self.assertGreaterEqual(ev.upper,0)
        self.assertEqual(ev.mode,'CP_full')
        d=ObservedCohort('d',0,0,5,100,100,20,20,10,10)
        ev2=effect_interval(d)
        self.assertEqual(ev2.mode,'Manski_CP_worstcase')
        self.assertLessEqual(ev2.lower,0)
        self.assertGreaterEqual(ev2.upper,0)

    def test_mnar_missing_is_not_censoring_independent(self):
        sc=Scenario('mnar',alert_wlst_shift=2.,mnar=True)
        e=exogenous(1,sc,0,0,30000)
        z=e['z_uniform']<.5
        p=patient_process(e,z,sc,0,1.,0)
        # Observed case-only effect differs materially from actual effect.
        true=float(p['Y'][z].mean()-p['Y'][~z].mean())
        obs=float(np.nanmean(p['C_obs'][z])-np.nanmean(p['C_obs'][~z]))
        self.assertLess(true,-.05)
        self.assertGreater(obs,0.)
        self.assertGreater(obs-true,.10)

    def test_model_label_misclassification_not_hidden(self):
        sc=Scenario('mislabel',mislabel=True)
        p=patient_process(self.ex,self.ex['z_uniform']<.5,sc,0,1.,0)
        self.assertGreater(np.sum(p['O'] & (p['C_obs']!=p['Y'])),0)

    def test_common_random_numbers(self):
        a=exogenous(22,self.sc,0,0,500)
        b=exogenous(22,self.sc,0,0,500)
        self.assertTrue(all(np.array_equal(a[k],b[k]) for k in a))

    def test_no_probe_without_authorization(self):
        r=simulate_policy(Scenario('probe'), 'P0_PROBE_ONCE',0,123,q=.05,
                          months=10,n_stratum=20,authorize_probe=False)
        self.assertEqual(r['probe_exposures'],0)
        self.assertEqual(r['alerts_shown'],0)

    def test_one_cohort_once_and_run_deterministic(self):
        a=simulate_policy(self.sc,'EVIDENCE_GATED',0,321,n_stratum=25,months=10)
        b=simulate_policy(self.sc,'EVIDENCE_GATED',0,321,n_stratum=25,months=10)
        self.assertEqual(a,b)
        self.assertEqual(a['monitoring_evaluated'],10*4)

    def test_capacity_works_across_whole_hospital(self):
        sc=Scenario('capacity',capacity_fraction=.44)
        r=simulate_policy(sc,'ALWAYS_OFF',0,120,n_stratum=125,months=5)
        self.assertEqual(r['treated'],5*220)
        self.assertGreater(r['capacity_denials'],0)

    def test_reduced_v04_bridge_mediation(self):
        # A constructive restricted SCM showing that Z->D=T->Y can implement
        # v0.4's reduced Bernoulli model without a direct Z->Y arrow.
        rng=np.random.default_rng(9876)
        u=rng.random(150000)
        mu0,mu1=.55,.60
        z=np.ones(len(u),dtype=bool)
        D=z.copy();T=D.copy()
        Y=u<np.where(T,mu1,mu0)
        z[:]=False;D=z.copy();T=D.copy()
        Y0=u<np.where(T,mu1,mu0)
        self.assertLess(abs(Y.mean()-mu1),.005)
        self.assertLess(abs(Y0.mean()-mu0),.005)
        self.assertLess(abs((Y.mean()-Y0.mean())-(mu1-mu0)),.005)

    def test_proposition_2_two_worlds(self):
        # Z=1: P(U=1)=.5, P(D=1|U)=.5, P(Y=1|T=1,U=1)=.8
        mu1=.5*.5*.8
        mu0_plus=.5*.25*.8
        mu0_minus=.5*.75*.8
        self.assertAlmostEqual(mu1,.20)
        self.assertAlmostEqual(mu1-mu0_plus,.10)
        self.assertAlmostEqual(mu1-mu0_minus,-.10)

if __name__ == '__main__':unittest.main(verbosity=2)
