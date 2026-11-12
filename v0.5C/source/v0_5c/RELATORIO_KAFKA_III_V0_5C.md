# KAFKA III — Relatório exploratório v0.5C

**Data:** 10 de novembro de 2026  
**Status:** integração dinâmica implementada e simulada; **não é estudo confirmatório** e **não é software clínico**.

## 1. Objetivo

Integrar `ACTIVE`, `P0`, `PROBE_WAIT` e `REENTRY_RESTRICTED` sobre o SCM v0.5B sem introduzir conhecimento contrafactual no controlador; contabilizar os custos de manter, suspender, sondar e atrasar decisões; confrontar com políticas fixas. As duas proposições v0.5A de não identificação sob `Z≡1` e de divergência entre efeito individual e valor de política hospitalar permanecem como contraexemplos conceituais, **não como diagnósticos causais observáveis**.

## 2. Contrato de autoridade

| Estado | Exibição no mês de exposição | Condição de entrada/saída |
|---|---:|---|
| `ACTIVE` | `1−q` | Sentinela; uma evidência de dano `U<0` de coorte *madura* pode suspender somente quando a certificação do desenho permite interpretar o efeito individual. |
| `P0` | 0 | Autoridade suspensa; não equivale a ausência de tratamento ou retorno do comportamento médico ao passado. |
| `PROBE_WAIT` durante a inscrição | `q` | **Reexibição** para uma única coorte, mediante autorização sintética separada. |
| `PROBE_WAIT` durante espera | 0 | Nenhuma inscrição adicional; aguardam-se desfechos de 90 dias mais até dois meses administrativos. |
| `REENTRY_RESTRICTED` | `ρ=0,25` | Somente se **todos os quatro estratos** da coorte sondada apresentarem `L>0` com inferência certificada. Sem evidência positiva nos controles de reentrada, não retorna automaticamente a `ACTIVE`. |
| `ALWAYS_ON` / `ALWAYS_OFF` | 1 / 0 | Comparadores fixos de valor de política. |

Retorno a `ACTIVE` exige uma **segunda coorte nova**, produzida já em `REENTRY_RESTRICTED`, madura e com `L>0` em todos os estratos. Evidência inconclusiva não significa que o alerta seja prejudicial. Permanecer em `P0` após sondagem inconclusiva é **uma política conservadora normativa**, cujos prejuízos são medidos, não uma conclusão estatística de dano.

A autorização de sondagem é representada por `probe_approval`, uma variável de **experimento sintético**. Não constitui aprovação ética ou regulatória. A inscrição de sondagem é limitada a uma coorte; a contagem não é reiniciada após suspensão.

## 3. Inferência e limites

O módulo de observação do v0.5B foi reutilizado. Ele recebe somente contagens agregadas de `C_obs` por braço em coortes com acompanhamento completo; o controlador não acessa `U`, desfechos contrafactuais, mecanismo estrutural ou efeito real. Clopper–Pearson por braço aplica-se ao núcleo binomial sob condições de randomização, independência/estrutura distributiva e rótulo íntegro; desfechos ausentes usam limites conservadores de identificação parcial.

- `α_arm=0,025/(20×4×2)=0,00015625`; os 160 intervalos de braço compartilham uma reserva de erro **de 0,025**. A outra metade do orçamento global de 0,05 não foi empregada.
- Cada uma das 80 coortes estrato×mês é avaliada uma vez após maturação. Somente as 60 coortes dos primeiros 15 meses podem influenciar decisões **dentro do horizonte de 20 meses**. Aquelas maturadas após esse horizonte são auditadas, mas não mudam decisões passadas.
- Não há agrupamento temporal ingênuo, reinício de alfa, janelas móveis de CS ou imputação do desfecho ainda não maduro.
- Para interferência de capacidade (`capacity_fraction<1`) ou corrupção de rótulo conhecida pelo desenho, a certificação para inferência individual é desligada. **Essa certificação é imposta pelo experimentador; em dados reais, não se pode supor que todo erro de rótulo latente seja conhecido.**
- Em caso de sondagem concluída sob desenho não certificado, retorna-se a `P0` sem interpretar o sinal do intervalo.

**Limitação importante:** o gerador v0.5B sorteia atrasos administrativos individuais, mas entrega as coortes de modo conservador apenas no atraso máximo fixo de cinco meses. Portanto, a v0.5C **não compara algoritmos de inferência com disponibilização assíncrona**; apenas impede uso prematuro de desfechos e selecionamento pelo atraso.

## 4. Desenho experimental

- **Principal:** 9 cenários × 7 políticas × 25 replicações = **1.575 trajetórias sintéticas**.
- **Por trajetória:** 20 meses, 4 estratos de 125 elegíveis/mês, **10.000 episódios**.
- **Sensibilidade:** `q=1%` e `2%` com 2 cenários × 7 políticas × 25 replicações = **350 trajetórias por taxa**. Principal: `q=5%`.
- Mesmos ruídos exógenos por paciente, cenário, réplica e mês entre políticas (common random numbers), com históricos comportamentais e alocações de recurso evoluindo conforme cada política.
- Desfecho: probabilidade **sintética** de resultado funcional favorável, parametrizada pela v0.5B, **não por observação clínica**.
- Comparadores: `ALWAYS_ON`, `ALWAYS_OFF`, `ACTIVE_SENTINEL`, `EVIDENCE_GATED`, suspensão exógena sem/com sondagem, e `P0` com sondagem única. **Não** foram implementados AEGIS, Feng, AWM/SWM ou um verdadeiro cluster RCT.

## 5. Resultado negativo principal

Em **todas as 1.575 trajetórias**, a política `EVIDENCE_GATED` realizou **zero transições justificadas pelos intervalos de evidência**. Durante os 20 meses, 60 coortes por trajetória podem afetar estados; todas as avaliações correspondentes permaneceram sem decisão de sinal (`U<0` ou `L>0`). O comportamento da política foi idêntico ao de `ACTIVE_SENTINEL` nas condições testadas.

Isso não significa segurança do alerta nem equivalência clínica entre métodos: é **falta de capacidade operacional para decidir no regime informacional simulado**. Não foi alcançado um episódio real de reentrada na grade principal.

## 6. Perdas bilaterais e políticas

Definimos para cada réplica um comparador fixo de retrospectiva: o melhor entre `ALWAYS_ON` e `ALWAYS_OFF` quanto à **soma das probabilidades esperadas de desfecho favorável** dos pacientes gerados nesse cenário. A perda registrada, por 1.000, é:

`L(π) = 1000·[max{E_good(ON),E_good(OFF)} − E_good(π)] / N`.

Esse oráculo é uma referência **offline** com informação que o controlador não possui, e a escolha ex post por réplica pode produzir otimismo de seleção. Valores negativos de diferença são matematicamente possíveis quando uma política mista supera ambas as políticas fixas; nenhuma conclusão de superioridade é feita por essa referência.

| Política (q=5%) | Alerta benéfico | Alerta prejudicial por WLST | Capacidade limitada |
|---|---:|---:|---:|
| `ALWAYS_ON` | 0,00 | 133,20 | 77,55 |
| `ALWAYS_OFF` | 30,03 | 0,00 | 0,00 |
| `ACTIVE_SENTINEL` | 1,40 | 126,61 | 73,51 |
| `EVIDENCE_GATED` | **1,40** | **126,61** | **73,51** |
| Suspensão **exógena** no mês de índice 6, sem sondagem | 21,33 | 38,25 | 21,87 |
| Suspensão **exógena** + sondagem de 5% | 21,25 | 38,55 | 21,95 |
| `P0` com uma sondagem | 29,96 | 0,31 | 0,08 |

Todos os valores são **perdas de desfechos favoráveis por 1.000 pacientes sintéticos** ao longo de 20 meses. A suspensão programada no mês 7 do calendário humano é informação exógena privilegiada e **não** deve ser apresentada como sucesso de detecção do KAFKA III.

### Custo marginal da sondagem após suspensão externa

Em comparação pareada com suspensão externa *sem* sondagem, uma sondagem de 5%:

- **Alerta benéfico:** reduziu a perda em média **0,071/1.000** (IC descritivo Monte Carlo aproximado entre −0,097 e −0,045 para diferença de perdas).
- **Alerta prejudicial:** aumentou a perda em média **0,309/1.000** (intervalo Monte Carlo aproximado +0,256 a +0,363).
- **Interferência de capacidade:** aumentou a perda em **0,078/1.000**; o intervalo de braço **não** identifica o valor hospitalar.

Essas faixas exprimem flutuação de replicações no *gerador sintético fixado*, não confiança em uma estimativa clínica nem inferência sobre outros cenários.

### Análise de sensibilidade de q

| q | Benefício: ganho líquido da sondagem vs. não sondar | Dano: perda adicional da sondagem vs. não sondar |
|---:|---:|---:|
| 1% | aproximadamente 0,012/1.000 | 0,054/1.000 |
| 2% | aproximadamente 0,029/1.000 | 0,106/1.000 |
| 5% | aproximadamente 0,071/1.000 | 0,309/1.000 |

Como a sondagem não conseguiu possibilitar reentrada em nenhuma dessas configurações, esses são efeitos da **exposição durante a investigação**, não de aprendizado causal aproveitado. Mais sondagem pode causar dano; pouca sondagem pode não fornecer informação utilizável.

## 7. Decomposição sem dupla contagem

A diferença mensal `E_good(oracle,t) − E_good(policy,t)` é atribuída a **exatamente uma categoria** do estado corrente. Na política de suspensão exógena + sondagem de 5%:

| Categoria mensal | Alerta benéfico | Alerta prejudicial |
|---|---:|---:|
| `ACTIVE` antes da suspensão | 0,40 | 38,25 |
| `P0` fora da sondagem | 13,50 | 0,00 |
| `PROBE_ENROLL` | 1,39 | 0,31 |
| `PROBE_WAIT` sem nova inscrição | 5,96 | 0,00 |
| **Total** | **21,25** | **38,55** |

As perdas são por 1.000 elegíveis ao longo do horizonte completo. A categoria `PROBE_ENROLL` é **parte** do estado `PROBE_WAIT`, mas foi destacada de modo exclusivo no cálculo. O custo de **atraso** aparece como permanência em `ACTIVE`, `P0` ou `PROBE_WAIT` enquanto a decisão necessária não foi obtida; não foi adicionado novamente como uma taxa separada. A decomposição vale para valores de políticas completos, inclusive sob interferência, enquanto a interpretação causal de componentes individuais continua dependente do SCM.

Um custo operacional adicional por alerta pode ser simulado, porém a métrica primária o fixa em zero. O código possui **oráculo separado de utilidade** que paga seu próprio custo de alertas, evitando somar custos apenas ao método candidato e deixar o comparador artificialmente gratuito.

## 8. Prova de alcançabilidade dos estados — fora do protocolo principal

Para testar caminhos que o desenho original não consegue exercitar, executamos **dois testes de estresse não confirmatórios**, cada um com `q=50%`, 20.000 pacientes por estrato/mês, efeito de alerta deliberadamente exagerado (deslocamento da log-odds WLST de magnitude 10) e uma única réplica.

1. **Dano extremo:** `EVIDENCE_GATED` suspendeu no mês de índice 5, abriu uma sondagem sintética no mês 6 e, após maturação, registrou `PROBE_INCONCLUSIVE_OR_NONPOSITIVE` no índice 11, retornando a `P0`.
2. **Benefício extremo:** uma coorte sondada em `P0` produziu evidência positiva em todos os estratos; a política entrou em `REENTRY_RESTRICTED` no mês de índice 12. **Não houve reentrada plena** até o fim do horizonte.

Esses testes são **testes de alcançabilidade/controle de fluxo**. Foram ajustados para produzir informação abundante e efeitos fortes. Não são evidência de eficácia, poder no regime de q=1–5%, generalização ou ética da exposição.

## 9. Validação de software

A suíte de v0.5C tem **16 testes aprovados**, incluindo: autorização sintética de sondagem; apenas uma inscrição; ausência de reexposição durante espera; reentrada restrita e plena condicionais a evidências fabricadas de teste; rollback por intervalo negativo; bloqueio de sinais em desenho não certificado; não duplicação de coortes; exclusão de verdades contrafactuais da interface do controlador; soma exata de perdas por estado; comparação de utilidade com custo também aplicado ao oráculo; replicação determinística. A suíte anterior da v0.5B pode ser executada em separado.

**Testes de software não substituem prova de cobertura causal, validação de parâmetros clínicos, aprovação ética ou generalização.**

## 10. Limitações bloqueantes e próxima rodada (v0.6)

1. **Precisão informacional:** com 125 elegíveis por estrato/mês e q=1–5%, não houve decisões inferenciais. Avaliar pooling estratificado **pré-definido**, desenho adaptativo e estudo de potência/custos com garantias estatísticas adequadas, sem voltar à agregação temporal ingênua.
2. **Desfechos e observação:** entrega conservadora no atraso máximo; censura MNAR tratada por limites largos. Trabalhar mecanismos de observação, sensibilidade e verificações de rótulo; não inferir ausência de viés sem pressupostos.
3. **Interferência/cluster:** o intervalo individual por braço não identifica automaticamente o valor de política hospitalar. Exige desenho multi-hospital ou avaliação identificada sob interferência.
4. **Mudanças organizacionais:** o SCM tem histerese, mas não seleção/admissão endógena, retreinamento efetivo ou efeitos cruzados entre hospitais.
5. **Normatividade e ética:** escolha de políticas durante incerteza permanece uma proposta, com autorização de sondagem sintética; não há margens clínicas adjudicadas nem validação prospectiva.
6. **Comparadores fiéis:** AEGIS, Feng, Kim AWM/SWM e política de valor da informação/minimax ainda não foram implementados de forma fiel. Fase 12 negativa preservada.
7. **Avaliação confirmatória:** sementes, critérios de decisão, plano de sensibilidade e comparadores devem ser congelados *antes* de experimentos confirmatórios; o conjunto atual é exploratório.

**Veredito:** o simulador v0.5C já contabiliza perdas bilaterais e modela reentrada de maneira verificável, mas o KAFKA III **não demonstrou vantagem** nem capacidade inferencial na escala original. Também não demonstrou equivalência. Sua contribuição potencial permanece descrever, com condições explícitas, o custo de manutenção, suspensão, investigação e **indeterminação causal**.
