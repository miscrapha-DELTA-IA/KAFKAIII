# KAFKA III v1.8A — Protocolo exploratório: ganhos, perdas e zonas cinzentas

Status: EXPLORATÓRIO, não confirmatório, não clínico. Preparado antes da execução.

## Objetivo
Retomar a pesquisa integrada: mapear ganho, dano e indeterminação no efeito causal de exibição, e testar se uma política **parcial e limitada pelo risco de suspender benefício** oferece trade-offs melhores do que sentinela, histórico, Bayes posterior e minimax estático, sempre com dados iguais.

## Estimando e hipóteses
Para cada estrato m, Δ_m,t=E[Y_m(Z=1)-Y_m(Z=0)], Y=1 favorável; sem interferência nem censura, a perda por paciente relativa ao oráculo é (1-e)[Δ]+ + e[-Δ]+; sob MNAR, bounds de Clopper-Pearson conservadores por braço. As políticas agem sobre o período futuro de 12 meses usando apenas resultados de histórico de 20 meses; nunca veem Δ verdadeiro. Sem pressuposto de transporte temporal válido, o alargamento [L-b,U+b] é apenas sensibilidade.

## Simulação
4 estratos; 125 pacientes por estrato/mês e 20 meses => n=2.500 por estrato; probabilidade histórica de exibição rara q=0.05 (regime P0 com sonda/ativo invertido não está aqui sendo modelado; o dado foi gerado de dois braços randomizados). N raro médio=125 por estrato. 400 replicações por família com mesmas realizações históricas entre políticas. Taxa basal p0=(0.30,0.40,0.50,0.60). 

8 famílias (histórico → futuro): BENEFICIO_5, BENEFICIO_FORTE, DANO_5, DANO_FORTE, MISTO, NULO, RECUPERACAO, DANO_NOVO, mais MISTO_MNAR (9 famílias). Não seleção por resultados. MNAR de observação depende de Y e Z; bounds consideram todos os dados ausentes.

Sensibilidade transportabilidade b={0, 0.10, 0.30} (efeito em proporções; nunca tratado como verdade clínica); tolerância normativa eta={0.005,0.02,0.05}. Comparadores: ALWAYS_ON, ALWAYS_OFF, SENTINEL=0.95, HIST_SIGN (suspende se U_hist<0), TEMP_SIGN (suspende se U_hist+b<0), BAYES_POST (Beta(.5,.5), escolhe sinal esperado, ignora MNAR), MINIMAX_STATIC (usa conjunto histórico alargado), KAFKA_MAP_GUARD (minimax sujeito à restrição de perda adicional frente à sentinela). Grade de exposição hipotética {0,.05,.25,.5,.75,.95}, ALWAYS_ON=1, ALWAYS_OFF=0; permissões clínicas para exposições parciais são assumidas no experimento, não concedidas na prática.

## Medidas
Regret verdadeiro médio por 1000 sob os 4 estratos; ganho pareado vs sentinela, ganho pareado vs Bayes e vs minimax; máximo arrependimento por família; fração de decisões parciais; cobertura empírica do efeito histórico; validade da hipótese b e cobertura futura. O pior caso sobre cenários e valores normativos não é uma garantia geral. Estatística de Monte Carlo com IC normal descritivo para diferença pareada (não inferência clínica).

## Restrições de interpretação
Resultados são exploração sintética reduzida; não incluem tratamento D/W/T, pressão hospitalar, dinâmica durante futuro, chegada de resultados ou efeitos de políticas na observabilidade. Critérios para artigo e teste independente serão congelados apenas depois de confrontar esta exploração com fortes comparadores sob gerador clínico. Não reivindicar novidade de minimax nem eficácia clínica.

Semente global: 18082026. Pacote exige Python, NumPy, SciPy, pandas.
