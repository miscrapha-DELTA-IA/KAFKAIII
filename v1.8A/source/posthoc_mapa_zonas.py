"""Exploratory post-run diagnostic; not part of the preregistered v1.8A core."""
import numpy as np
import pandas as pd
from kafka_v18a_map import SEED,SCENARIOS,make_history

def main():
    rng=np.random.default_rng(SEED)
    rows=[]
    for name,(past,future,mnar) in SCENARIOS.items():
        l,h,*_=make_history(rng,400,np.array(past),mnar)
        frac_green=float(np.mean(l>0))
        frac_red=float(np.mean(h<0))
        frac_gray=float(np.mean((l<=0)&(h>=0)))
        rows.append([name,frac_green,frac_red,frac_gray,float(np.mean(np.all((l<=np.asarray(past))&(np.asarray(past)<=h),axis=1)))])
    d=pd.DataFrame(rows,columns=['cenario','fracao_estratos_verde','fracao_estratos_vermelho','fracao_estratos_cinzento','cobertura_historica_4_estratos'])
    d.to_csv('outputs/mapa_zonas_posthoc.csv',index=False)
    print(d.to_string(index=False))
if __name__=='__main__':main()
