"""KAFKA III v1.8A. Exploratory, non-confirmatory, synthetic.
Map gains, losses, and gray area; identical observed history for all policies.
"""
import argparse
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import beta

SEED=18082026
P0=np.array([.30,.40,.50,.60])
N=2500
Q=.05
E0=.95
GRID=np.array([0.,.05,.25,.50,.75,.95])
ALPHA=.05
BGRID=(0.,.10,.30)
ETAGRID=(.005,.02,.05)
SCENARIOS={
  'BENEFICIO_5':((.05,.05,.05,.05),(.05,.05,.05,.05),False),
  'BENEFICIO_FORTE':((.20,.15,.15,.20),(.20,.15,.15,.20),False),
  'DANO_5':((-.05,-.05,-.05,-.05),(-.05,-.05,-.05,-.05),False),
  'DANO_FORTE':((-.25,-.25,-.25,-.25),(-.25,-.25,-.25,-.25),False),
  'MISTO':((-.25,-.10,.05,.20),(-.25,-.10,.05,.20),False),
  'NULO':((0,0,0,0),(0,0,0,0),False),
  'RECUPERACAO':((-.25,-.10,-.20,-.10),(.05,.05,.10,.15),False),
  'DANO_NOVO':((.10,.05,.15,.20),(-.25,-.15,-.10,-.25),False),
  'MISTO_MNAR':((-.25,-.10,.05,.20),(-.25,-.10,.05,.20),True)
}

def validate_scenarios():
    for name,(past,future,_) in SCENARIOS.items():
        past=np.asarray(past); future=np.asarray(future)
        assert past.shape==(4,) and future.shape==(4,)
        assert np.all((P0+past>=0)&(P0+past<=1)),name
        assert np.all((P0+future>=0)&(P0+future<=1)),name
validate_scenarios()

def lower(k,n,a):
    k=np.asarray(k);n=np.asarray(n)
    out=np.zeros(np.broadcast_shapes(k.shape,n.shape))
    k,n=np.broadcast_arrays(k,n)
    mask=k>0
    out[mask]=beta.ppf(a,k[mask],n[mask]-k[mask]+1)
    return out

def upper(k,n,a):
    k=np.asarray(k);n=np.asarray(n)
    out=np.ones(np.broadcast_shapes(k.shape,n.shape))
    k,n=np.broadcast_arrays(k,n)
    mask=(n>0)&(k<n)
    out[mask]=beta.ppf(1-a,k[mask]+1,n[mask]-k[mask])
    return out

def make_history(rng, reps, past, mnar):
    n1=rng.binomial(N,Q,size=(reps,4)); n0=N-n1
    p1=P0+np.asarray(past)
    # Binomial responses, independent across arms and strata, known assignment probabilities.
    y1=rng.binomial(n1,p1); y0=rng.binomial(n0,P0)
    if mnar:
        # Exact splitting of successes and failures into observed and missing,
        # with observation probability depending on the unseen Y and treatment arm.
        k1=rng.binomial(y1,.60); f1=rng.binomial(n1-y1,.95)
        k0=rng.binomial(y0,.90); f0=rng.binomial(n0-y0,.60)
        obs1=k1+f1;obs0=k0+f0
    else:
        k1=y1;k0=y0;obs1=n1;obs0=n0
    # 0.05 family-wise across 4 strata × 2 arms × 2 tails.
    tail=ALPHA/(4*2*2)
    l1=lower(k1,n1,tail); u1=upper(k1+n1-obs1,n1,tail)
    l0=lower(k0,n0,tail); u0=upper(k0+n0-obs0,n0,tail)
    lo=np.maximum(-1,l1-u0); hi=np.minimum(1,u1-l0)
    # Exploratory Bayes benchmark, not valid under MNAR: complete cases only.
    post1=(k1+.5)/(obs1+1.);post0=(k0+.5)/(obs0+1.)
    return lo,hi,post1-post0, n1, obs1,obs0

def regret(e,true_effect):
    return (1-e)*np.maximum(true_effect,0)+e*np.maximum(-true_effect,0)

def pick_minimax(lo,hi,grid=GRID):
    # True max over Δ∈[lo,hi] is achieved at endpoints for convex regret.
    worst=np.maximum(regret(grid[None,:],lo[:,None]),regret(grid[None,:],hi[:,None]))
    # prefer baseline on ties
    idx=np.argmin(worst + 1e-11*np.abs(grid-E0),axis=1)
    return grid[idx]

def pick_guard(lo,hi,eta):
    # Exact identity: loss(e,Δ)-loss(e0,Δ)=(e0-e)*Δ.
    # For e<=e0, worst-case additional loss is (e0-e)*max(hi,0).
    permissible=(E0-GRID[None,:])*np.maximum(hi[:,None],0)<=eta+1e-12
    worst=np.maximum(regret(GRID[None,:],lo[:,None]),regret(GRID[None,:],hi[:,None]))
    worst=np.where(permissible,worst,np.inf)
    idx=np.argmin(worst+1e-11*np.abs(GRID-E0),axis=1)
    return GRID[idx]

def check_identity():
    e=np.array([0.,.2,.9,1.]); d=np.array([-.25,-.1,.05,.35]);
    assert np.allclose(regret(e,d)-regret(np.full_like(e,E0),d),(E0-e)*d)
    a=np.array([-.3,-.08,.01]);b=np.array([.05,.05,.1]);e=pick_guard(a,b,.005)
    assert np.all((E0-e)*np.maximum(b,0)<=.005+1e-10)
check_identity()

def simulate(reps=400,seed=SEED):
    rng=np.random.default_rng(seed)
    rows=[]; diag=[]
    for sname,(past_,future_,mnar) in SCENARIOS.items():
        past=np.array(past_);future=np.array(future_)
        l,h,post,nrare,obs1,obs0=make_history(rng,reps,past,mnar)
        # Diagnostics per replicate: all 4 historical effects covered
        histcovered=np.all((l<=past)&(past<=h),axis=1)
        for b in BGRID:
            lo=np.maximum(-1,l-b);hi=np.minimum(1,h+b)
            futcovered=np.all((lo<=future)&(future<=hi),axis=1)
            assumption=np.all(np.abs(future-past)<=b+1e-12)
            policies={
                'ALWAYS_ON':np.ones_like(l),
                'ALWAYS_OFF':np.zeros_like(l),
                'SENTINEL':np.full_like(l,E0),
                'HIST_SIGN':np.where(h<0,0,E0),
                'TEMP_SIGN':np.where(hi<0,0,E0),
                'BAYES_POST':np.where(post<0,0,E0),
                'MINIMAX_STATIC':pick_minimax(lo.reshape(-1),hi.reshape(-1)).reshape(l.shape),
            }
            for eta in ETAGRID:
                policies[f'KAFKA_MAP_eta{eta:g}']=pick_guard(lo.reshape(-1),hi.reshape(-1),eta).reshape(l.shape)
            for policy,e in policies.items():
                losses=regret(e,future[None,:]).mean(axis=1)*1000.
                for i in range(reps):
                    rows.append((sname,i,b,policy,float(losses[i]),float(np.mean(e[i])),
                                 int(np.any((e[i]>0)&(e[i]<E0))),int(histcovered[i]),
                                 int(futcovered[i]),int(assumption),int(mnar)))
        diag.append((sname,float(nrare.mean()),float((obs1/nrare.clip(1)).mean()),float((obs0/(N-nrare).clip(1)).mean())))
    columns=['cenario','rep','b','politica','regret_1000','exposicao_media','alguma_exposicao_parcial',
             'cobertura_historica','cobertura_futura','deriva_respeita_b','mnar']
    return pd.DataFrame.from_records(rows,columns=columns),pd.DataFrame(diag,columns=['cenario','n_raro_medio','observabilidade_braco_raro','observabilidade_braco_comum'])

def summarize(df):
    s=df.groupby(['cenario','b','politica'],as_index=False).agg(regret_medio=('regret_1000','mean'),
              regret_dp=('regret_1000','std'),exposicao_media=('exposicao_media','mean'),
              parcial=('alguma_exposicao_parcial','mean'),cob_hist=('cobertura_historica','mean'),
              cob_fut=('cobertura_futura','mean'),deriva_valida=('deriva_respeita_b','first'))
    pivot=df.pivot_table(index=['cenario','rep','b'],columns='politica',values='regret_1000')
    pairs=[]
    for pol in pivot.columns:
        if pol=='SENTINEL':continue
        for comp in ('SENTINEL','BAYES_POST','MINIMAX_STATIC','HIST_SIGN'):
            if pol==comp:continue
            d=(pivot[comp]-pivot[pol]).dropna()
            if len(d)<2:continue
            # By scenario, b; paired standard error
            for (sc,b),grp in d.groupby(level=[0,2]):
                arr=grp.values
                se=arr.std(ddof=1)/np.sqrt(len(arr))
                pairs.append((sc,float(b),pol,comp,len(arr),float(arr.mean()),float(arr.mean()-1.96*se),float(arr.mean()+1.96*se)))
    p=pd.DataFrame(pairs,columns=['cenario','b','politica','comparador','reps','ganho_1000','ic_mc_inf','ic_mc_sup'])
    return s,p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reps',type=int,default=400);ap.add_argument('--seed',type=int,default=SEED)
    ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'outputs');args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    df,diag=simulate(args.reps,args.seed);sm,paired=summarize(df)
    df.to_csv(args.output/'replicacoes.csv',index=False)
    sm.to_csv(args.output/'resumo.csv',index=False)
    paired.to_csv(args.output/'diferencas_pareadas.csv',index=False)
    diag.to_csv(args.output/'diagnostico_amostras.csv',index=False)
    print('done',len(df),'rows',df.cenario.nunique(),'families',df.politica.nunique(),'policies')
    print(sm[(sm.b==.10)&(sm.politica.isin(['SENTINEL','HIST_SIGN','MINIMAX_STATIC','KAFKA_MAP_eta0.02','BAYES_POST']))][['cenario','politica','regret_medio','parcial']].to_string(index=False))

if __name__=='__main__':main()
