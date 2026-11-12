# KAFKA III — Subetapa v1.7-L: auditoria matemática de L1, L2, L3

**Data:** 10/11/2026. **Tipo:** auditoria computacional interna exploratória; **não** é experimento confirmatório. Nenhum paciente real. Esta subetapa **não** modifica a política KAFKA III v1.6 nem demonstra eficácia clínica.

## 1. Materiais examinados

Foram examinados os dois documentos da segunda revisão bibliográfica do Claude fornecidos nesta conversa, bem como o resumo de sua verificação numérica L1–L3. O usuário forneceu apenas os caminhos originais dos três arquivos de cálculo do Claude (`/mnt/user-data/outputs/...`), não o código-fonte ou os bytes desses arquivos; logo, **não auditamos o programa original**. A implementação anexa é uma **reprodução independente**, não validação linha a linha de código externo. Foram confrontados também `PROTOCOLO_V1_7_CANDIDATO.md` e `RELATORIO_KAFKA_III_V1_6.md` do projeto anterior.

## 2. Condições estatísticas desta reprodução

- Efeito alvo: Δ = P(Y=1|do(Z=1)) − P(Y=1|do(Z=0)), com desenho individual randomizado, sem interferência e dados totalmente observados.
- Por cenário, N pacientes i.i.d. com alocação Bernoulli independente e conhecida; cada braço tem seu próprio parâmetro Bernoulli estacionário p0 ou p1.
- ACTIVE: ocultação Z=0 rara, n0~Binomial(N,q); PROBE: exibição Z=1 rara, n1~Binomial(N,q).
- q ∈ {0.01, 0.02, 0.05}, N ∈ {125,500,2500,10000} e dois modelos: (p0,p1)=(.50,.55) e (.05,.10), sempre Δ=.05.
- 5.000 replicações por uma das 48 combinações, semente 1172026. Total de 240.000 replicações estatísticas simples (não políticas dinâmicas ou trajetórias clínicas).
- Diferença por união de dois CP bilaterais, com α=0,025 por braço. Pelo limite da união, cobertura conjunta de pelo menos 95% no desenho i.i.d. fixado. É uma análise **única ao final**, não um intervalo válido em qualquer parada nem uma família de 4 estratos e 20 meses com múltiplas decisões.

## 3. L1 — Cramér–Rao não é uma impossibilidade uniforme

Para n observações independentes Bernoulli(p), um estimador não viesado regular da média obedece Var(p̂) ≥ p(1−p)/n, com igualdade para a média amostral. Multiplicar o desvio-padrão por 1,95996 fornece uma **semilargura normal aproximada**, não uma cota universal sobre a largura de qualquer intervalo de confiança.

No pior caso p=.5:

| n do braço raro (fixado) | Semilargura Wald 95% | CP 95% no x≈np |
|---:|---:|---:|
| 25 | .196 | .204 |
| 50 | .139 | .145 |
| 125 | .088 | .091 |
| 500 | .044 | .045 |
| 385 | .0499 | .0511 |

Logo, **385 é um valor aproximado de planejamento normal**; em uma realização central n=385, CP ainda excede .05. Numa realização central com n=402, CP bilateral chega abaixo de .05 (isso também não garante a mesma largura para todas as realizações). Sob p=.05 e n=500, CP em uma realização típica tem semilargura ≈.020, não .044.

**Conclusão corrigida:** neste desenho, baixa probabilidade do braço raro costuma implicar grande imprecisão, mas não há teorema universal de que nenhum método possa atingir semilargura de cinco pontos dentro de um estrato. Dependem da distribuição, do estimando, do nível simultâneo, dos pressupostos e dos auxiliares externos. Abandonar a alegação absoluta do Claude.

## 4. L2 — Precisão de um braço ≠ potência para Δ>0

Para a diferença de dois braços independentes sob modelo superpopulacional, a aproximação normal usa:

Var(Δ̂ | n0,n1) ≈ p1(1−p1)/n1 + p0(1−p0)/n0.

A cota de .044 do Claude em quatro estratos e q=.05 conta somente um braço raro com 500 observações **esperadas**. A diferença envolve também o braço comum e um limite conjunto; no nosso benchmark CP-Bonferroni de 95%, a mediana da semilargura foi maior.

**Resultado novo reproduzido independentemente, com Δ=.05:**

| Desenho | Modelo | Semilargura mediana da diferença | Probabilidade empírica de L>0 |
|---|---|---:|---:|
| 20 meses, 1 estrato, ACTIVE q=5% | .50→.55 | .126 | 4,18% |
| 20 meses, 4 estratos, ACTIVE q=5% | .50→.55 | .062 | 28,76% |
| 20 meses, 4 estratos, PROBE q=5% | .50→.55 | .062 | 28,78% |
| 20 meses, 4 estratos, PROBE q=5% | .05→.10 | .036 | 92,52% |
| 1 mês, 1 estrato, PROBE q=5% | .50→.55 | .491 | 0,10% |
| 1 mês, 4 estratos, PROBE q=5% | .50→.55 | .277 | 0,68% |

A cobertura observada nas diversas configurações varia, como se espera com CP-Bonferroni conservador, e é descrita no CSV; o desempenho depende fortemente da taxa basal. Nenhum valor é prova de eficácia clínica.

**A falha conceitual mais importante:** os números n=25,50,125 do Claude se referem a **20 meses inteiros** de exposição sentinela por estrato. A sondagem v1.6 só abre **um mês** de novas exposições e depois aguarda o resultado. Com N=125 pacientes por estrato, q=.05, o número esperado de exibidos em PROBE é **6,25**, e não 125; com quatro estratos, 25. A chance de nenhum exibido em um estrato é (1−q)^125: aproximadamente **28,47%** para q=1%, **8,00%** para q=2% e **0,164%** para q=5%.

O compartilhamento de quatro estratos exige muito mais que um efeito comum: combinar diretamente contagens em CP binomial pressupõe uma distribuição Bernoulli comparável e estável por braço, ou um desenho de mistura que a justifique. Se os riscos basais variam por estrato ou mês, mesmo com Δ idêntico, o total fixado por estrato/bloco não é automaticamente binomial i.i.d. É necessária inferência estratificada/design-based ou pressupostos mais fortes.

Outras saídas conceituais, condicionais a pressupostos e custos, incluem amostras maiores, mais locais, modelos prognósticos anteriores, desfechos mais informativos e aquisição autorizada prolongada. Portanto, *pooling por homogeneidade* não é a única saída.

## 5. L3 — prova simples, alcance e restrição de ações

Considere mundos W+ e W− com **a mesma lei para o histórico disponível**, mas efeitos futuros +δ e −δ. Para uma regra que, antes de obter informação futura, escolhe uma fração de exposição esperada e, com δ>0, os arrependimentos em relação ao oráculo são:

- R+(e)=(1−e)δ;
- R−(e)=eδ.

Assim, inf_{e∈[0,1]} max{R+(e),R−(e)}=δ/2, em e=.5. Para δ=.05, regret minimax=.025, isto é, 25 desfechos favoráveis por 1.000 elegíveis, **na comparação de um único período sem interferência nem custos de transição**.

Se e estiver limitado ao conjunto operacional {0,.05,.25,.95}, minimax **determinístico** no mesmo exemplo é e=.25 com regret=.0375; se a política puder randomizar livremente entre esses estados, o conjunto convexo de exposições esperadas muda. Essa mistura não é automaticamente ética ou autorizada. Sob mundos assimétricos Δ+=.05 e Δ−=−.25, e*=1/6, regret=1/24≈.041667. Não afirmar δ/2 nesse caso.

**Atenção ao teste de falsificação proposto por Claude:** L3 é uma cota de perda **esperada no pior mundo**, não um limite inferior realizado em cada réplica. Uma regra pode ter perda realizada abaixo de δ/2 em muitos sorteios, sem contradizer o teorema. A checagem correta requer avaliar as expectativas em ambos os mundos e tomar o máximo, com a mesma lei para o histórico.

**O que a prova não demonstra:** não estabelece impossibilidade de aprender com novas sondagens; demonstra incapacidade de escolher corretamente em ambos os futuros **com o histórico idêntico e antes de novos resultados relevantes**. Não implica que todos os hospitais devam randomizar pacientes nem que a identidade linear se aplique sob interferência ou histerese.

## 6. Auditoria bibliográfica das duas partes do Claude

As contribuições de decisão robusta e safe-policy-improvement já têm antecedentes próximos. A fonte primária de Ben-Michael et al. (JASA 2025) descreve garantia de melhora relativa à política existente **sob hipóteses estruturais**, não garantia clínica universal: https://doi.org/10.1080/01621459.2025.2489135. O artigo de Jiang et al. (AOAS 2026) define efeitos de elegibilidade seletiva dependentes do histórico e utiliza hipóteses de ignorabilidade sequencial: https://imai.sites.fas.harvard.edu/research/eligibility/. Lindon e Kallus (ICML 2026) tratam efeitos sob resultados atrasados com estimando de recompensa contrafactual acumulada em tempo de calendário, não fornecem automaticamente intervalos para o efeito futuro do KAFKA III: https://proceedings.mlr.press/v306/lindon26a.html.

O Claude examinou sobretudo resumos/trechos. Não tratamos as indicações de teoremas não lidos como provas verificadas, nem reivindicamos originalidade do minimax, da identificação parcial, da alocação de Neyman ou da DUAL_KEY por simples composição.

## 7. Decisão metodológica para a v1.7

**Aceitar:** L3 como proposição condicional, com especificação de decisões e horizonte; L1 como cálculo local de precisão da média; L2 como possibilidade sob hipóteses fortes (e com demonstração do estimando causal).

**Corrigir:** trocar a frase “nenhum método identifica benefício +5pp” por “o procedimento e o desenho estudados têm potência inadequada para certas taxas basais e escalas”; não equiparar o sinal de Δ à semilargura da média de um braço; não reutilizar o poder de 20 meses como poder de sondagem de um mês.

**Não autorizar:** alegação de eficácia clínica, superioridade geral, garantia de reentrada com q≤5%, nem que o ganho do benchmark estacionário se transfira a um controlador dinâmico com censura, deriva e alfa fracionado.

**Próxima hipótese falsificável:** em estudo prospectivo, comparar aquisição de uma coorte/mês versus duas ou mais coortes sob o mesmo orçamento de exposição total e o mesmo prazo de maturação; variar p0, p1, deriva, heterogeneidade, censura e capacidade. Comparar poder de reentrada e **perda acumulada**, não só largura do intervalo. Congelar antes da nova bateria tanto o teste quanto o alvo e a perda normativa.

## 8. Reprodutibilidade e status

`auditar_L1_L3.py` gera os CSVs determinísticos e Monte Carlo e `test_limites.py` testa propriedades essenciais. Os números são reprodutíveis com a semente explicitada. Esta auditoria é interna e exploratória. Não examinou o script original do Claude nem realizou experimento de política KAFKA III v1.7 completo. A alegação de superioridade metodológica permanece não demonstrada.
