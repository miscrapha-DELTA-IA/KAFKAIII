"""KAFKA III v1.7: auditoria INDEPENDENTE dos limites L1-L3 do Claude.

Amostras ficticias, sem dados de pacientes. Nao e avaliacao confirmatoria.
Desenho: atribuicao Bernoulli aleatoria ao Z=0 (braco raro) em prob q;
Y | Z=z iid Bernoulli(p_z). Delta=p1-p0, sem interferencia.
CI para diferenca: uniao Bonferroni de dois Clopper-Pearson bilaterais
cada qual com cobertura >= 1-alpha/2, simultanea ao nivel >= 1-alpha.
NAO e anytime-valid, nem cobre efeitos futuros com deriva.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import beta

OUT=Path(__file__).resolve().parent
SEED=1172026
REPS=5000
ALPHA=0.05


def cp_bounds(x,n,alpha):
    """CP bilateral para n heterogeneo, incluindo n=0 ([0,1])."""
    x=np.asarray(x,dtype=int)
    n=np.asarray(n,dtype=int)
    lo=np.zeros(x.shape,float)
    hi=np.ones(x.shape,float)
    m=(n>0)
    i=m & (x>0)
    j=m & (x<n)
    lo[i]=beta.ppf(alpha/2,x[i],n[i]-x[i]+1)
    hi[j]=beta.ppf(1-alpha/2,x[j]+1,n[j]-x[j])
    return lo,hi


def analytic_table():
    rows=[]
    for scope, N in [('estrato_20_meses',2500),('4_estratos_20_meses',10000),('estrato_1_probe_mes',125),('4_estratos_1_probe_mes',500)]:
        for q in [.01,.02,.05]:
            n=N*q
            rows.append(dict(escopo=scope,N=N,q=q,n_raro_esperado=n,
                prob_braco_raro_vazio=(1-q)**N,
                semi95_wald_media_p050=1.959963984540054*np.sqrt(.25/n),
                semi95_wald_media_p005=1.959963984540054*np.sqrt(.05*.95/n)))
    return pd.DataFrame(rows)


def ci_fixed_arm():
    rows=[]
    for n in [25,50,125,100,200,500,385]:
        for p in [.5,.05]:
            x=int(np.floor(n*p+0.5))
            lo,hi=cp_bounds(np.array([x]),np.array([n]),.05)
            rows.append(dict(n=n,p=p,x=x,cp95_inferior=float(lo[0]),cp95_superior=float(hi[0]),
              cp95_semi_largura=float((hi[0]-lo[0])/2),
              wald95_semi_largura=1.959963984540054*np.sqrt(p*(1-p)/n)))
    return pd.DataFrame(rows)


def mc_table():
    rng=np.random.default_rng(SEED)
    rows=[]
    for mode in ['ACTIVE_retencao_Z0_raro','PROBE_sondagem_Z1_raro']:
      for label,N in [('1_mes_estrato',125),('1_mes_4_estratos',500),('20_meses_estrato',2500),('20_meses_4_estratos',10000)]:
        for q in [.01,.02,.05]:
            nr=rng.binomial(N,q,size=REPS)
            nc=N-nr
            if mode.startswith('ACTIVE'):
                n0,n1=nr,nc
            else:
                n0,n1=nc,nr
            for label_p,p0,p1 in [('intermediario',.5,.55),('baixo_risco',.05,.10)]:
                y0=rng.binomial(n0,p0)
                y1=rng.binomial(n1,p1)
                # 97.5% CP por braco => 95% simultaneo dos dois bracos
                l0,u0=cp_bounds(y0,n0,ALPHA/2)
                l1,u1=cp_bounds(y1,n1,ALPHA/2)
                L=l1-u0
                U=u1-l0
                width=U-L
                # Um intervalo para a diferenca; nao afirmar validade de testes reiterados.
                rows.append(dict(politica=mode,escopo=label,N=N,q=q,cenario=label_p,p_oculto=p0,p_exibido=p1,
                    delta_verdade=p1-p0,replicacoes=REPS,
                    n_raro_medio=float(nr.mean()),frac_braco_vazio=float(np.mean(nr==0)),
                    cobertura_diferenca=float(np.mean((L<=p1-p0)&(p1-p0<=U))),
                    deteccao_beneficio_L_positivo=float(np.mean(L>0)),
                    deteccao_dano_U_negativo=float(np.mean(U<0)),
                    largura_mediana=float(np.median(width)),
                    semilargura_mediana=float(np.median(width)/2),
                    fracao_semilargura_ate_5pp=float(np.mean(width/2<=.05)),
                    limite_inferior_mediano=float(np.median(L)),
                    limite_superior_mediano=float(np.median(U))))
    return pd.DataFrame(rows)


def minimax_table():
    # Historico comum; futuro nao observado. p sao regras aleatorias de exposicao.
    rows=[]
    for delta_plus,delta_minus,label in [(0.05,-0.05,'simetrico_5pp'),(.05,-.25,'assimetrico_5pp_25pp')]:
        e_star=delta_plus/(delta_plus-delta_minus)
        for definition, feasible in [('continuo',None),('estados_clinicos',[0,.05,.25,.95]),('binario_ON_OFF',[0,1])]:
            if feasible is None:
                e=e_star
            else:
                e=min(feasible,key=lambda a:max((1-a)*delta_plus, a*(-delta_minus)))
            regret=max((1-e)*delta_plus,e*(-delta_minus))
            rows.append(dict(mundos=label,acoes=definition,e_minimax=e,regret_maximo=regret,
                             regret_por_1000=1000*regret))
    return pd.DataFrame(rows)


def assertions(a,b,c,d):
    assert np.isclose(a.query('escopo=="estrato_20_meses" and q==0.05')['n_raro_esperado'].iloc[0],125)
    assert np.isclose(a.query('escopo=="4_estratos_20_meses" and q==0.05')['n_raro_esperado'].iloc[0],500)
    assert np.isclose(a.query('escopo=="estrato_1_probe_mes" and q==0.05')['n_raro_esperado'].iloc[0],6.25)
    assert np.isclose(a.query('escopo=="4_estratos_1_probe_mes" and q==0.05')['n_raro_esperado'].iloc[0],25)
    assert np.isclose(d.query('mundos=="simetrico_5pp" and acoes=="continuo"')['regret_maximo'].iloc[0],.025)
    assert np.isclose(d.query('mundos=="assimetrico_5pp_25pp" and acoes=="continuo"')['e_minimax'].iloc[0],1/6)
    assert np.all((c['cobertura_diferenca']>=0)&(c['cobertura_diferenca']<=1))
    assert np.all(b['cp95_inferior']<=b['cp95_superior'])
    # Pooled result is NOT usable for heterogeneous cohorts without further assumptions.


def main():
    a=analytic_table();b=ci_fixed_arm();c=mc_table();d=minimax_table()
    assertions(a,b,c,d)
    for name,df in [('amostras_exposicao',a),('precisao_um_braco',b),('poder_e_efeito_causal',c),('minimax_L3',d)]:
        df.to_csv(OUT/(name+'.csv'),index=False,float_format='%.10f')
    config=dict(seed=SEED,replicacoes=REPS,alpha=ALPHA,
       metodos='Clopper Pearson individual bilateral alfa .025 por braço, Bonferroni para diferença',
       limites='Apenas dados completos iid estacionários sem interferência, análise uma vez ao final',
       caminhos=[str(x.name) for x in OUT.glob('*.csv')])
    (OUT/'configuracao.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
    print('ANALITICO:')
    print(a.to_string(index=False,formatters={'q':lambda x:f'{x:.0%}','prob_braco_raro_vazio':lambda x:f'{x:.3%}',
    'semi95_wald_media_p050':lambda x:f'{x:.3f}'}))
    print('\nMONTE CARLO:')
    print(c[['politica','escopo','q','cenario','frac_braco_vazio','semilargura_mediana','deteccao_beneficio_L_positivo','cobertura_diferenca']].to_string(index=False))
    print('\nMINIMAX:')
    print(d.to_string(index=False))

if __name__=='__main__':main()
