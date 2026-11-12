# KAFKA III — v1.8A | Retomada do mapa de ganhos, perdas e espaço cinzento

**Status:** síntese teórica e experimento computacional **exploratórios**. Não é uma avaliação confirmatória; não valida eficácia clínica; não prova superioridade do KAFKA III em geral. Data: 10–11 nov. 2026.

## 0. Resumo executivo

A pergunta do projeto é mais abrangente que *quando suspender*: queremos caracterizar **quando a previsão melhora ou piora o cuidado, quanto custa manter/suspender/investigar e como governar autoridade sob incerteza**, incluindo a reversibilidade e os efeitos de política hospitalar. A pesquisa mantém o título *When Should a Biomedical Prediction Lose Its Authority to Guide Care?*

Nesta etapa: (i) formalizamos o mapa triplo de ganho, perda e zona cinzenta; (ii) derivamos a fronteira de exposição minimax com uma restrição de prejuízo frente à sentinela; (iii) testamos um benchmark contextual exploratório contra comparadores, inclusive Bayes posterior simples e minimax estático; (iv) identificamos **uma família positiva mas ainda não confirmatória**: heterogeneidade entre estratos + censura informativa + ausência de deriva; (v) demonstramos que fora dessa família há perdas relevantes e que a regra estática não constitui necessariamente contribuição original frente a *safe policy learning*.

## 1. Escopo científico restaurado

A autoridade é uma **decisão que muda o ambiente causal e a disponibilidade de dados**, e não um rótulo de desempenho. A matriz de avaliação deve relatar, separadamente:

- **Benefício realizado:** melhora de desfechos favoráveis atribuível à exposição quando Δ>0.
- **Dano por manutenção:** exposição a uma recomendação que piora desfechos quando Δ<0.
- **Dano por suspensão:** oportunidade de benefício perdida por ocultar uma recomendação favorável.
- **Custo informacional:** despesas organizacionais da sondagem e exposição experimental; o efeito clínico da exposição já integra as perdas anteriores, sem dupla contagem.
- **Custo do atraso:** perda acumulada enquanto a política aguarda evidência; não é parcela extra quando já avaliada mês a mês.
- **Espaço cinzento epistêmico:** dados compatíveis com Δ>0 e Δ<0; inclui violação de positividade, observação MNAR, pequenas amostras.
- **Espaço cinzento decisório:** alternativas com trade-offs e restrições normativas mesmo quando há dados; falta de dominância não é prova de que todas as escolhas sejam equivalentes.
- **Espaço cinzento temporal:** efeito passado identificado, efeito futuro não transportável sem hipótese de deriva.
- **Heterogeneidade e interferência:** efeito favorável agregado pode esconder grupos prejudicados; com leitos compartilhados, usar valor de política hospitalar em vez de ∆ individual.

Assim, três classificações superficiais `GREEN/AMBER/RED` não bastam. O KAFKA deve manter dois objetos separados: **conjunto de evidência** (sobre qual estimando/período/estrato) e **fronteira de decisões admissíveis** (quanto cada decisão pode ganhar/perder).

## 2. Modelo causal e contabilidade de perdas

Para um estrato m e mês t, na subclasse SEM interferência, seja Δ_{m,t}=E[Y(Z=1)-Y(Z=0)]. Uma política e_{m,t} em [0,1] produz bem-estar médio E[Y(0)] + e_{m,t}Δ_{m,t}. Comparada ao oráculo que escolhe a exibição ótima sabendo Δ:

    ℓ(e,Δ)=(1-e)max(Δ,0)+e max(-Δ,0).

Isto separa formalmente dano por **suspensão indevida** de dano por **manutenção indevida**. São exclusivas para um ∆ fixo, mas podem coexistir em estratos ou períodos diferentes. A diferença relativa à sentinela e0 é exatamente:

    ℓ(e,Δ)−ℓ(e0,Δ)=(e0−e)Δ.

**Não somar** de novo o dano clínico de sondagem, já contido em e; custos operacionais não clínicos podem ser somados separadamente. Sob interferência, essas identidades deixam de ser a medida adequada e devem ser substituídas por V(π) no hospital.

## 3. Fronteira analítica da zona cinzenta: derivação condicional, não reivindicação de novidade

Considere um conjunto de possíveis efeitos futuros Θ=[L,U], com L<0<U, uma exposição padrão e0 e permissão apenas para e∈[0,e0]. O arrependimento máximo é:

    R(e;Θ) = max{ (1−e)U, e(−L) }.

A decisão minimax estática irrestrita no intervalo [0,e0] é a projeção de e*=U/(U−L) nesse intervalo. Se adicionarmos a condição de que a suspensão não possa aumentar a perda em mais de η *em qualquer mundo de Θ*, teremos

    (e0−e)U ≤ η,
    e ≥ max{0, e0−η/U}.

Portanto, a solução contínua é

    e_safe = Proj_[max{0,e0−η/U},e0](U/(U−L)).

Em uma grade autorizada, escolher o elemento viável de menor R. Esta proposição é algébrica e pode ser conferida diretamente. Seu mérito aqui é organizar a **fronteira de ganhos e perdas sob incerteza**, não descobrir minimax-regret, que é conhecido.

Exemplo ilustrativo: Θ=[−0,25,+0,05], e0=0,95. Sem proteção, e*=1/6≈0,167. Com η=.005, ações da grade {0,.05,.25,.50,.75,.95} só permitem e=.95. Com η=.020, e=.75 já é viável, mas a perda máxima é grande (0,1875). Com η=.050, a grade escolhe e=.05; o arrependimento máximo cai para 0,0475, ante 0,2375 para a sentinela. Isto exige admitir perda adicional de até 0,045 caso o efeito seja positivo +0,05. **Não é uma recomendação clínica**: η, Θ, ações permitidas e validade temporal precisariam de validação externa.

A restrição é *condicional* à presença do efeito futuro real em Θ. Um intervalo estatístico para efeitos históricos não basta; Θ=[L_hist−b,U_hist+b] só é válido para o futuro se a hipótese substantiva de variação ≤b realmente se cumprir.

## 4. Desenho computacional v1.8A

O protocolo foi escrito e registrado por hash antes da bateria. Simulação de **um único instante decisório** com histórico observado, não a máquina clínica dinâmica completa. Quatro estratos, 2.500 episódios históricos/estrato, randomização rara de 5% **no braço de exibição Z=1**, 20 meses, efeitos futuros constantes ao longo do horizonte simplificado; nove famílias e 400 replicações por família; 108.000 registros de política (9×400×3 valores de b×10 políticas). **ATENÇÃO:** isso representa 20 meses de exposição rara Z=1, semelhante a várias sondagens autorizadas em P0; NÃO é o mesmo regime ACTIVE padrão da v0.5A, em que Z=1 ocorre com probabilidade 95%. Também NÃO é uma única sondagem mensal. Essa disponibilidade informacional deve ser tratada como hipótese deliberadamente favorável, cuja autorização e custo não foram modelados na v1.8A. Replicação adicional com outras 400 amostras/família para conferência interna da família positiva. Todas as políticas recebem os mesmos dados observados em cada réplica.

Intervalos Clopper–Pearson conservadores por braço, com alfa global 5% subdividido entre 4 estratos, 2 braços e 2 caudas. Para resultados MNAR, os dados não observados recebem limites extremos [0,1], sem imputar o desfecho desconhecido. O Bayes posterior Beta(0,5;0,5) usa apenas casos completos, sendo propositalmente vulnerável à censura informativa; não é o melhor método robusto possível.

A classe de futuras ações permitidas nesta exploração inclui exposição parcial de 0%, 5%, 25%, 50%, 75% e 95%. Essas frações **não receberam autorização clínica** e não são equivalentes aos estados atuais sem novas decisões normativas.

**Critério descritivo:** arrependimento relativo ao oráculo verdadeiro, medido em desfechos favoráveis perdidos por 1.000 elegíveis. Os resultados futuros contrafactuais são usados só para avaliação; nunca entram no cálculo dos intervalos ou das decisões. O futuro é representado apenas por Δ verdadeiro na avaliação: o arrependimento futuro é calculado como **valor esperado exato do gerador**, sem amostragem adicional de Y no futuro. Isso torna diferenças entre políticas menos ruidosas, mas não representa uma implantação clínica. Os ICs publicados das diferenças entre políticas medem incerteza de Monte Carlo, não validade clínica nem incerteza do estimador causal.

## 5. Mapa inferencial: quanto da evidência ficou cinzenta?

Classificações por estrato e réplica a partir do sinal do intervalo **histórico** (não do futuro). No arquivo `outputs/mapa_zonas_posthoc.csv`, calculado após a bateria sem mudança de regra:

| Família | Verde (L>0) | Vermelho (U<0) | Cinzento (L≤0≤U) |
|---|---:|---:|---:|
| BENEFICIO_5 | 1,38% | 0% | 98,62% |
| BENEFICIO_FORTE | 67,13% | 0% | 32,88% |
| DANO_5 | 0% | 1,31% | 98,69% |
| DANO_FORTE | 0% | 99,25% | 0,75% |
| MISTO | 23,13% | 27,50% | 49,38% |
| NULO | 0% | 0,06% | 99,94% |
| RECUPERACAO | 0% | 53,19% | 46,81% |
| DANO_NOVO | 38,50% | 0% | 61,50% |
| MISTO_MNAR | 0% | 24,00% | 76,00% |

**Interpretação:** um intervalo cinzento não prova que o efeito verdadeiro é pequeno; em MISTO_MNAR há efeitos materialmente positivos e negativos que frequentemente permanecem inconclusivos por observação incompleta. Em RECUPERACAO e DANO_NOVO, cores históricas podem induzir decisões inadequadas porque o sinal mudou.

## 6. Resultado exploratório candidato à tese — e seu falsificador

Família `MISTO_MNAR`: quatro estratos com efeitos estacionários Δ=(-0,25,-0,10,+0,05,+0,20), observação informativa dependente de Y e Z. Hipótese de b=0 (estacionariedade correta no gerador). Regra `KAFKA_MAP_eta0.05` (tolerância 5 pontos percentuais, apenas *ilustrativa*).

| Política | Arrependimento por 1.000 |
|---|---:|
| KAFKA_MAP_eta0.05 | **19,10** |
| BAYES_POST sem ajuste para MNAR | 29,61 |
| HIST_SIGN | 29,34 |
| MINIMAX_STATIC sem proteção de baseline | 37,14 |
| SENTINEL | 86,25 |

Diferença pareada exploratória contra BAYES_POST: +10,50/1.000 (IC de Monte Carlo descritivo +8,30 a +12,70). Contra HIST_SIGN: +10,23; contra MINIMAX_STATIC: +18,04; contra sentinela: +67,15. A semente adicional (também exploratória, não confirmatória) gerou perdas 19,96 versus 30,20 para Bayes, 37,10 minimax e 31,12 histórico.

**Há um contexto matematicamente significativo de potencial vantagem: heterogeneidade + MNAR + limite de prejuízo frente ao baseline.** Porém, a regra de *safe policy learning* que receba os mesmos intervalos, grade e η e minimize o mesmo regret **produzirá exatamente a mesma decisão**. Esse comparador de mesma classe ainda não foi avaliado como máquina própria porque é algebricamente equivalente à regra estática; a equivalência é um limite de novidade. Portanto não temos prova de superioridade própria do KAFKA III.

**Falsificador:** no cenário estacionário `MISTO` com observação completa, KAFKA_MAP_eta0.05 teve regret 11,07/1.000, contra 4,70 do Bayes posterior; e na família `RECUPERACAO` a mesma configuração teve 75,17, ante 4,38 da sentinela. A política falha seriamente quando transportabilidade temporal não se verifica. Essas falhas devem ser exibidas junto aos ganhos.

## 7. Fronteira multicontexto (mesmo gerador, família equal-weight ilustrativa)

Com b=0, ao atribuir **pesos iguais às nove famílias por conveniência matemática**, a perda média foi cerca de 72,36/1.000 sentinela, 37,24 histórica, 35,41 Bayes, 36,90 minimax e 35,45 KAFKA_MAP_eta0.05. Logo a política proposta NÃO superou o Bayes na média dessas famílias. O pior regret médio dentre as nove famílias foi aproximadamente 173,43 para Bayes, 163,74 para minimax e 167,41 para KAFKA_MAP_eta0.05. Esses agregados são totalmente dependentes dos pesos arbitrários das famílias e não devem ser interpretados como desempenho clínico generalizável.

Com b=0.10, a condição foi falsa nos cenários de recuperação e dano novo; o garantidor perde sua interpretação de proteção nesses cenários. Com b=0.30, a proteção frequentemente bloqueia alterações, sacrificando a capacidade de reduzir dano persistente. Isto reproduz o custo de proteção demasiado abrangente observado em v1.1–v1.6.

## 8. O que já fundamenta uma tese e o que ainda bloqueia alegações de eficácia

**Material consolidado a favor da parte teórica:** (i) contraexemplo de não identificação da exibição determinística, (ii) efeito individual favorável coexistindo com política hospitalar coletiva nociva, (iii) impossibilidade de transportar efeitos históricos sem hipótese temporal, (iv) mapa bidirecional ganho-perda e zona cinzenta, (v) limite de informação sob braço raro e atraso. Isso permite formular uma tese sobre *governança da autoridade algorítmica sob identificabilidade imperfeita*, mas os teoremas não devem ser apresentados como inéditos sem exame integral da literatura.

**Material novo desta etapa:** a possibilidade de construir *fronteiras de decisão auditáveis por estrato, por mundo causal e por estado de autoridade*, com proteção parametrizada contra suspender recomendações benéficas. O método estático é antecedido por safe policy learning e identificação parcial; a hipótese de novidade precisa deslocar-se para **o acoplamento dinâmico de observabilidade, validade temporal, aquisição de informação e restrições de governança**.

**Bloqueadores da parte de superioridade:** ainda não implementamos neste mapa um comparador dinâmico safe-policy de força equiparável; não avaliamos a consequência de novas exposições sobre a informação futura; não apresentamos prova de vantagem não trivial sobre a política ótima da mesma classe; e nosso simulador reduzido não implementa Z→D/W→T→Y nem o valor hospitalar com interferência. A família favorável e a configuração b=0, η=.05 foram escolhidas para destaque após inspecionar uma grade exploratória de hipóteses; não há correção da seleção/multiplicidade. A semente adicional não é confirmação independente e tampouco o conjunto de famílias foi obtido de distribuição clínica empiricamente validada. Exigirá novas famílias causais independentes e protocolo congelado antes da confirmação.

## 9. Plano mínimo para um manuscrito metodológico com alegações defensáveis

**Núcleo teórico:** seção de notação e estimandos; teorema/contraexemplos de identificabilidade; proposição do mapeamento de ganho/perda/cinza; relação entre incerteza histórica e futura; inferência por braço, censura e cluster interferência.

**Núcleo do método:** definição verificável de G_t=(I_t, Θ_t, E_t, s_t), com I_t informação observada, Θ_t conjunto de efeitos futuros sob hipóteses, E_t exposições eticamente autorizadas e s_t estado de autoridade. Política otimiza perda acumulada com monitoramento, aquisição e efeitos de mudança de estado. Não substituir inferência por priors pessimistas.

**Núcleo experimental:** estudo ADEMP com quatro famílias-a-priori: benefício persistente, dano persistente, efeitos heterogêneos simultâneos e mudanças temporais adversariais; testes MNAR e interferência separados, além de diversos riscos basais e atrasos. Comparar com `ALWAYS_ON`, `ALWAYS_OFF`, sentinela, regra histórica, Bayes multietapas, safe policy learning robusto e oráculo somente avaliativo. Conjunto de cenários desenhado por equipe clínica/estatística, sem selecionar apenas casos de vitória.

**Critério de alegação condicional:** uma família-alvo com relevância clínica/decisória justificada antes do teste independente; vantagem em perda ou arrependimento frente ao comparador mais forte, com IC Monte Carlo de diferenças pareadas e controle de multiplicidade; custos explícitos de observação e violação de pressupostos; relatório separado de cenários em que houve prejuízo. Não afirmar eficácia em pacientes reais.

**Porta de passagem:** até aqui, o projeto tem material para **desenho de tese/manuscrito**, não para defender superioridade metodológica da arquitetura dinâmica. A prioridade operacional seguinte é v1.8B: POMDP/planejador forte com valor de informação, validade temporal e restrição de risco, e revisão por terceiros. Uma réplica da regra estática safe-risk será baseline obrigatório para impedir alegação de originalidade vazia.

## 10. Literatura próxima, com potencial de invalidar novidade fraca

- Ben-Michael, Greiner, Imai e Jiang, *Safe Policy Learning through Extrapolation* (2025): https://imai.fas.harvard.edu/research/files/safe.pdf — estimandos parcialmente identificados, política segura frente à referência sob pressupostos.
- Joshi, Zhang e Bareinboim, *Towards Safe Policy Learning under Partial Identifiability* (AAAI 2024): https://ojs.aaai.org/index.php/AAAI/article/view/29198 — seguro sob identificação parcial.
- Li e Li, *Constrained Feedback Learning for Non-Stationary Multi-Armed Bandits* (NeurIPS 2025): https://proceedings.neurips.cc/paper_files/paper/2025/hash/741aab8b41a2987867acc9939ad50383-Abstract-Conference.html — orçamento de feedback e deriva.
- Bar-On e Mansour, *Non-stochastic Bandits With Evolving Observations* (ALT 2025): https://proceedings.mlr.press/v272/bar-on25a.html — feedback atrasado e alterado.

A existência desses trabalhos exige análise de teoremas, não apenas comparação por título. O problema clínico de exibição, retirada e reentrada pode diferir das hipóteses dos bandits, mas precisamos demonstrar formalmente a diferença.

**Conclusão:** recolocamos a pesquisa no eixo ganhos–perdas–cinza e identificamos um contexto exploratório com vantagem sob censura informativa, junto com falsificadores de magnitude comparável. A tese defensável dependerá de transformar esse mapeamento em uma **política dinâmica com valor causal demonstrado sobre alternativas de mesma classe**, ou de reformular honestamente a contribuição como teoria de governança e limites.
