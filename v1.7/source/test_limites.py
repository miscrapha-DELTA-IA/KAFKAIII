"""Testes determinísticos do módulo de auditoria v1.7."""
import unittest
import numpy as np
from auditar_L1_L3 import cp_bounds, analytic_table, ci_fixed_arm, minimax_table

class TestLimites(unittest.TestCase):
    def test_arm_zero(self):
        lo,hi=cp_bounds(np.array([0]),np.array([0]),.025)
        self.assertEqual((lo[0],hi[0]),(0,1))

    def test_extremo_zero(self):
        lo,hi=cp_bounds(np.array([0]),np.array([10]),.05)
        self.assertEqual(lo[0],0)
        self.assertTrue(0<hi[0]<1)

    def test_extremo_um(self):
        lo,hi=cp_bounds(np.array([10]),np.array([10]),.05)
        self.assertEqual(hi[0],1)
        self.assertTrue(0<lo[0]<1)

    def test_dentro(self):
        lo,hi=cp_bounds(np.array([5]),np.array([10]),.05)
        self.assertTrue(lo[0]<.5<hi[0])

    def test_esperado_20_meses_estrato(self):
        df=analytic_table().query('escopo=="estrato_20_meses" and q==0.05')
        self.assertEqual(df.iloc[0].n_raro_esperado,125)

    def test_esperado_probe_estrato(self):
        df=analytic_table().query('escopo=="estrato_1_probe_mes" and q==0.05')
        self.assertEqual(df.iloc[0].n_raro_esperado,6.25)

    def test_raro_pode_ser_vazio(self):
        df=analytic_table().query('escopo=="estrato_1_probe_mes" and q==0.01')
        self.assertAlmostEqual(df.iloc[0].prob_braco_raro_vazio,(1-.01)**125)

    def test_meia_largura_385_nao_e_CP(self):
        cp=ci_fixed_arm().query('n==385 and p==0.5').iloc[0]
        self.assertGreater(cp.cp95_semi_largura,.05)
        self.assertLess(cp.wald95_semi_largura,.05)

    def test_CP_p005_500(self):
        cp=ci_fixed_arm().query('n==500 and p==0.05').iloc[0]
        self.assertLess(cp.cp95_semi_largura,.03)

    def test_minimax_simetrico(self):
        d=minimax_table().query('mundos=="simetrico_5pp" and acoes=="continuo"').iloc[0]
        self.assertAlmostEqual(d.e_minimax,.5)
        self.assertAlmostEqual(d.regret_maximo,.025)

    def test_minimax_assimetrico(self):
        d=minimax_table().query('mundos=="assimetrico_5pp_25pp" and acoes=="continuo"').iloc[0]
        self.assertAlmostEqual(d.e_minimax,1/6)

    def test_restricao_operacional(self):
        a=minimax_table().query('mundos=="simetrico_5pp" and acoes=="estados_clinicos"').iloc[0]
        b=minimax_table().query('mundos=="simetrico_5pp" and acoes=="continuo"').iloc[0]
        self.assertGreater(a.regret_maximo,b.regret_maximo)

if __name__ == '__main__':
    unittest.main()
