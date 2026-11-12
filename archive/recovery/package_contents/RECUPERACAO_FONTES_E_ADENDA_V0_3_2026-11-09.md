# KAFKA III — Recuperação de fontes e adenda crítica para Claude (v0.3)
**Data:** 09/11/2026. **Escopo:** revisão independente da resposta entregue pelo Claude; não é validação clínica nem autorização de experimentos confirmatórios.

## 1. Resultado da recuperação documental
- Sandoval et al. **LOCALIZADO**: Ricardo J. Sandoval, Sivaraman Balakrishnan, Avi Feller, Michael I. Jordan, Ian Waudby-Smith (2026), *On Nonasymptotic Confidence Intervals for Treatment Effects in Randomized Experiments*. arXiv:2601.11744; texto integral HTML https://arxiv.org/html/2601.11744 ; versão consultada no site datada de outubro de 2026. Seções 2, 3 e Teorema 3.5 lidas. Sob randomização Bernoulli com probabilidade fixa π, o Teorema 3.5 fornece IC de amostra finita com escala de tamanho efetivo nπ (sem garantia automaticamente sequencial/para q adaptativo intra-bloco). A fonte também considera modelos i.i.d. e design-based, sempre sob requisitos explícitos. Importante: em amostras raríssimas a largura ainda pode ser praticamente não informativa.
- Shekhar & Ramdas (2023), *On the near-optimality of betting confidence sets for bounded means*. arXiv:2310.01547; https://arxiv.org/abs/2310.01547 . Localizados resumo e identificação; **provas não auditadas nesta rodada**. Fundamenta limites/ótimo aproximado de betting IC/CS para médias limitadas; não estabelece diretamente um IC causal sob atribuição clínica adaptativa.
- Turner, Ly & Grünwald (2024), *Generic E-variables for exact sequential k-sample tests that allow for optional stopping*. Journal of Statistical Planning and Inference 230, 106116. https://arxiv.org/abs/2106.02693 ; DOI: https://doi.org/10.1016/j.jspi.2023.106116 . Resumos primários verificados, provas não auditadas; e-values e parada opcional em testes k-amostras, sem transferência automática ao KAFKA.
- Feng et al. (2024a), *Designing monitoring strategies for deployed machine learning algorithms: navigating performativity through a causal lens*. CLeaR / PMLR 236:587–608. https://proceedings.mlr.press/v236/feng24a.html . Resumo primário: seis procedimentos = 3 critérios x 2 fontes de dados, voltados ao monitoramento sob performatividade; não são seis estimadores do efeito Z de exibir alerta.
- Feng et al. (2024b), *Monitoring machine learning-based risk prediction algorithms in the presence of performativity*. AISTATS / PMLR 238:919–927. https://proceedings.mlr.press/v238/feng24b.html . Resumo primário: monitoramento de desempenho condicional; CUSUM com limites dinâmicos sob pressupostos de exchangeability ou selection bias constante; **não garante** a identificação de Δ_Z.
- Waudby-Smith & Ramdas (2024), *Estimating means of bounded random variables by betting*. JRSS B 86(1):1–27, DOI https://doi.org/10.1093/jrsssb/qkad009 ; texto integral https://arxiv.org/html/2010.09686 . Teorema 2 consultado: CS empirical Bernstein em média limitada sob hipóteses de observações apropriadas e stakes previsíveis. Métodos incluem CIs em amostra fixa; não é um teorema pronto de comparação de duas políticas clínicas com q adaptativo.
- Cook, Mishler & Ramdas (2024), *Semiparametric Efficient Inference in Adaptive Experiments*. PMLR 236; https://arxiv.org/html/2311.18274 . Teorema 1: inferência **assintótica** para A2IPW com truncagem. Teorema 2: Hedged-CS **não assintótica** para efeitos causais em desenho adaptativo de desfechos limitados, com atribuições limitadas por [1/k_t, 1-1/k_t], dentre outras condições. Em particular, truncar a POLÍTICA de atribuição para garantir explorabilidade não é igual a truncar pesos analíticos depois da randomização.
- Lindon & Kallus (2026), *Design-Based Anytime-Valid Inference for Randomized Experiments with Delayed Outcomes and Staggered Entry*. arXiv:2603.25971v2, https://arxiv.org/html/2603.25971 . Seções introdutórias e 3 consultadas. O alvo primário é recompensa contrafactual acumulada até data calendário, contando tempo potencial do evento; esse alvo **não é automaticamente** desfecho binário fixado em 90 dias por mês de entrada. Hipóteses de interferência e mecanismos de observação precisam ser alinhadas.
- Howard et al. (2021), *Time-uniform, nonparametric, nonasymptotic confidence sequences*. Annals of Statistics, DOI https://doi.org/10.1214/20-AOS1991 ; https://arxiv.org/abs/1810.08240 . Fundamento para sequências anytime-valid, não prova validade sob filtros de dados censurados e estados adaptativos particulares.
- Hudgens & Halloran (2008), *Toward causal inference with interference*. JASA, DOI https://doi.org/10.1198/016214508000000292 ; texto gratuito https://pmc.ncbi.nlm.nih.gov/articles/PMC2600548/ . Base para especificar efeitos diretos/indiretos e estimandos sob interferência parcial; apenas indicação bibliográfica nesta rodada.

## 2. Correções à recomendação do Claude
**C1 — Sandoval é central, não inexistente.** O método do Teorema 3.5 merece entrar entre os candidatos principais para q=1/2/5% em blocos com randomização Bernoulli fixa. Não há transferibilidade automática para q_t adaptativo no interior de bloco, desfechos atrasados, censura e interferência.

**C2 — Seleção pós-hoc do IC mais estreito é estatisticamente perigosa.** Se método A e método B são válidos separadamente em nível α, não está garantido que selecionar, após ver os desfechos, o intervalo mais estreito mantenha nível α. Pré-registrar método primário; para combinação/interseção de ICs, repartir α entre métodos ou demonstrar outra garantia conjunta.

**C3 — Não chamar média histórica ponderada de efeito contemporâneo.** Com pesos w_b fixados previamente, [Σ w_b L_b, Σ w_b U_b] cobre Σw_b Δ_b quando todos os ICs por bloco cobrem. Isso não identifica Δ do bloco seguinte nem o efeito atual sem hipótese de transporte/estabilidade.

**C4 — A2IPW de Cook apresenta resultados com garantias distintas.** Sua inferência fixed-time é assintótica nas hipóteses do Teorema 1, e sua Hedged-CS é não assintótica nas hipóteses do Teorema 2. Não confundir nenhuma delas com a validade exata do pooling original. Conhecer q=1% não torna os pesos pequenos: o limite inferior de exploração importa.

**C5 — Censura e atraso são mecanismos distintos.** Aguardar o horizonte de desfecho definido para uma coorte completa, com informação eventual para todos os elegíveis, não é equivalente a eliminar pacientes perdidos no seguimento. Se censura se relaciona a desfechos, não basta maturação administrativa. Definir endpoint: por exemplo, status favorável aos 90 dias, com ausência de informação modelada explicitamente.

**C6 — Reentrada é decisão normativa, não teorema.** O teste L > -h admite efeitos causais ainda negativos. O h=0,05 da v0.2 é exploratório e não deve autorizar reexposição humana. Sob inconclusão, permanecer P0 também pode causar dano; registrar custo e revisão humana, sem automatismo de reentrada ou suspensão.

**C7 — Definir alvo principal para v0.3 antes da comparação:** recomendação provisória = efeito médio superpopulacional em bloco (m,b), com Y(1), Y(0) i.i.d. condicionais ao histórico pré-bloco, q_b fixo ex ante, sem interferência e endpoint completo. Comparação de sensibilidade = efeito design-based da coorte finita com IC específico válido, não reutilizar automaticamente IC de superpopulação. Os dois não são sinônimos.

**C8 — Documento e arquivos recuperados:** O pacote zip antigo foi validado (teste CRC sem erros). O arquivo `results_raw_v0_2.json`, existente na pasta, NÃO integra o ZIP v0.2. O novo ZIP de transferência o inclui. O acesso ao ZIP não era impossível, apenas não estava disponível no ambiente do Claude.

## 3. Checagem aritmética
- 4 estratos × 20 meses × 2 braços: α braço mês = 0,025/160 = 0,00015625. Hoeffding requer n ≥ log(2/α)/(2×0,05²) ≈ 1.891 observações por braço para semilargura ≤5 pp em cada IC do braço. Esses valores não representam semilargura de Δ, que soma raios dos dois braços.
- 4 estratos × 2 braços, α braço final = 0,025/8 = 0,003125. Para semilargura ≤5 pp por braço: n ≥ log(2/0,003125)/(2×0,05²) ≈ 1.292.
- CIs exatos de Clopper–Pearson por braço para Y binário são um **comparador adicional útil** sob modelo i.i.d. Bernoulli e análise fixa; usar a mesma partição α por braço e unir limites de braços. Isto não substitui Sandoval e não é automaticamente design-based ou anytime-valid.

## 4. Matriz recomendada para próxima implementação exploratória
A. **Baseline:** Hoeffding por braço e bloco (v0.2).
B. **Comparador binário simples:** Clopper–Pearson exato por braço e bloco, com a mesma alocação α, modelo i.i.d. e suporte de q fixo.
C. **Candidato causal:** IC sub-Bernoulli de Sandoval (Teorema 3.5) em blocos compatíveis com o desenho do teorema. Validar reprodução das fórmulas antes de decidir uso.
D. **Candidato adaptativo separado:** Cook Hedged-CS/A2IPW nas condições completas do artigo, para q_t previsível e desenho que efetivamente corresponda às hipóteses. Não misturar com os testes A-C sem plano de α.
E. **Modelo de atrasos:** fixar coorte por data de exposição e análise após maturação de Y em horizonte clínico definido; planejar cenários com perdas seletivas e sem selecionar somente resultados conhecidos.
F. **Interferência:** começar com efeito individual sem interferência como módulo demonstrativo; estudo de sensibilidade com recurso compartilhado exige redefinir desfecho potencial Y_i(z_i, z_{-i}) ou estimando de política por cluster/hospital.

Metas: cobertura nominal simultânea; largura; erro direcional; inconclusão; custo de sondagem; perda de manutenção; perda de suspensão; atraso de reentrada; cenários de deriva e censura. Não aceitar estimador apenas porque estreita IC. Usar replicações pareadas por números aleatórios comuns e publicar os cenários inconclusivos.

## 5. Impedimentos ainda reais
- Reentrada clínica não possui limiar de não inferioridade justificado nem aprovação ética (o h ilustrativo de 5pp deve permanecer apenas como sensibilidade).
- O alvo para interferência entre pacientes não foi formalizado.
- A inferência Sandoval/Cook não foi adaptada, implementada ou calibrada no KAFKA III nesta rodada.
- Não se verificaram integralmente as provas da teoria de atrasos de Lindon–Kallus nem sua adequação ao endpoint de 90 dias.
- Não foram modelados mecanismos causais para censura informativa e mudança de adesão/histerese.
- Não há evidência atual de superioridade da máquina de estados, nem autorização dos experimentos confirmatórios ou manuscrito.

**Decisão de versão:** tratar este documento como adenda de recuperação e proposta de pesquisa, não como substituto do contrato v0.2 nem como v0.3 validada.
