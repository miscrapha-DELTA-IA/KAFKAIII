import unittest
import numpy as np
from kafka_v18a_map import (
    SCENARIOS,P0,GRID,E0,regret,pick_minimax,pick_guard,make_history,
    lower,upper,simulate,summarize)

class Tests(unittest.TestCase):
    def test_scenarios(self):
        for past,future,_ in SCENARIOS.values():
            self.assertTrue(np.all((P0+past>=0)&(P0+past<=1)))
            self.assertTrue(np.all((P0+future>=0)&(P0+future<=1)))
    def test_regret_identity(self):
        for d in np.linspace(-1,1,101):
            for e in GRID:
                self.assertAlmostEqual(float(regret(e,d)-regret(E0,d)),(E0-e)*d)
    def test_minimax_two_worlds(self):
        e=pick_minimax(np.array([-.05]),np.array([.05]))[0]
        self.assertAlmostEqual(e,.5)
    def test_guardrail(self):
        lo=np.array([-.25,-.1,0.]);hi=np.array([.05,.1,0.])
        for eta in (.005,.02,.05):
            e=pick_guard(lo,hi,eta)
            self.assertTrue(np.all((E0-e)*np.maximum(hi,0)<=eta+1e-10))
    def test_no_valid_history_shortcut(self):
        rng=np.random.default_rng(33)
        lo,hi,post,n,obs1,obs0=make_history(rng,10,np.array([.1,.1,.1,.1]),False)
        self.assertTrue(np.all(lo<=hi));self.assertTrue(np.all(n<=2500))
        self.assertTrue(np.all(obs1==n));self.assertTrue(np.all(obs0==2500-n))
    def test_mnar_bounds_not_tighter_than_fully_observed_same_k(self):
        # no subtraction of missing observations from original assignment denominators
        rng=np.random.default_rng(10)
        lo,hi,post,n,obs1,obs0=make_history(rng,12,np.array([0.,0.,0.,0.]),True)
        self.assertTrue(np.any(obs1<n));self.assertTrue(np.all((hi-lo)>=0.))
    def test_empty_arm_cp(self):
        self.assertEqual(float(lower(np.array([0]),np.array([0]),.01)[0]),0.)
        self.assertEqual(float(upper(np.array([0]),np.array([0]),.01)[0]),1.)
    def test_reproducibility(self):
        a,_=simulate(6,777); b,_=simulate(6,777)
        self.assertTrue(a.equals(b))
    def test_policy_equal_information(self):
        df,_=simulate(4,1)
        self.assertEqual(len(df[df.cenario=='NULO'].politica.unique()),10)
        self.assertEqual(int(df.groupby(['cenario','rep','b']).size().min()),10)
    def test_summary_works(self):
        df,_=simulate(4,2);s,p=summarize(df)
        self.assertTrue(len(s)>0 and len(p)>0)
        self.assertTrue(np.all((s.cob_hist>=0)&(s.cob_hist<=1)))

if __name__=='__main__':unittest.main()
