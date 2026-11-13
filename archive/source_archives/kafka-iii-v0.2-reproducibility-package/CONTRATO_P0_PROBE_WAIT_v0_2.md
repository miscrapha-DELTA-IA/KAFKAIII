# KAFKA III — Contrato de inferência e sondagem v0.2
**Natureza:** especificação e teste sintético exploratório, NÃO validação clínica; preparado em 09/11/2026. **Status:** pré-especificação inicial para crítica, não protocolo confirmatório congelado.

## 1. Escopo, estimando e orientação de sinais
Unidade: pessoa elegível para receber recomendação, pertencente ao estrato fixo m e mês de exposição b. Y=1 é desfecho clínico favorável. Z=1 indica recomendação exibida. Z=0 indica não exibida. Estimando de bloco Δ_{mb}=E[Y(1)-Y(0)|m,b,H_{b-1}], sob intervenções bem definidas e sem interferência entre unidades. Δ<0 significa dano médio por exibir; Δ>0 significa benefício médio por exibir. Efeito de exibição NÃO é efeito do tratamento biológico nem efeito de implantação integral.

## 2. Contrato formal de estados (proposta normativa)
| Estado | Exposição do alerta | Inferência permitida | Transições e exigências |
|---|---|---|---|
| `P0` — autoridade suspensa | Z=0 fora de sondagem | Desfechos sob Z=0 não identificam Δ sem informação complementar | Iniciar sondagem somente com autorização clínica/ética e plano de erro ainda disponível; se impossível, manter revisão explícita de risco de continuar suspenso |
| `PROBE_WAIT` — experimento em andamento ou aguardando maturação | Reexpor Z=1 com q_expose em unidades elegíveis e Z=0 nas demais; randomização exógena fixada antes do bloco | Nenhum resultado com follow-up incompleto; avaliações repetidas não são novas sondagens | Após maturação completa, avaliar uma única vez conforme plano; não reiniciar α |
| `PROBE_ASSESS` — evento lógico, não estado clínico durável | Nenhuma intervenção adicional | Calcular [L,U] somente com dados maduros e as mesmas definições de intervenção | U<−h: continuar P0; L>−h E autorização clínica: REENTRY_RESTRICTED; caso contrário: decisão inconclusiva e revisão, sem presumir segurança de P0 |
| `REENTRY_RESTRICTED` — recuperação condicionada | Exibição limitada conforme protocolo clínico | Inferências novas dependem de dados e orçamento previamente autorizados | Reavaliação após maturação; sem promoção automática a GREEN |

**Invariantes:** `n_probes` aumenta somente ao iniciar nova coorte randomizada; análises de seguimento não incrementam esse contador. Proibido usar desfechos parciais ou condicionados em maturação informativa. Sem recomeço implícito do orçamento de 5%. Em cenário de acompanhamento incompleto, requer ajuste explícito de identificação e limites de censura, não apenas exclusão. Mudança de equipe, leitos, modelo θ, outras políticas ou interferência potencial exige análise separada.

A fração `q_expose` em P0 é **reexposição**. A fração `q_withhold=π_W` em estado ativo é **retenção**. São comparáveis estatisticamente, mas não do ponto de vista ético/clínico. A opção de manter P0 na indeterminação NÃO foi demonstrada como a melhor política: requer prazo máximo, revisão e custo de suspensão explicitado.

## 3. Política de decisão a partir dos intervalos
Seja `h=0,05` margem **ilustrativa** de dano importante, sem validação clínica neste estudo. Diante de [L,U], onde intervalos são simultâneos sob os pressupostos:
- `U < −h`: evidência estatística de dano superior à margem; continuar sem autoridade, sujeita à governança.
- `L > −h`: evidência de não inferioridade à margem; **considerar** reentrada restrita apenas após autorização clínica e análise de custos.
- `L ≤ −h ≤ U`: inconclusão. Não inferir segurança nem dano; registrar risco de permanecer P0, e deliberar nova sondagem ou estratégia alternativa sob orçamento e justificativa clínica.
- `L > 0`: critério mais forte de benefício causal, ainda não garantia de segurança futura. A escolha entre esse critério e não inferioridade é **normativa**.

## 4. Validade estatística, alvo e prova condicional
Assuma dentro de cada bloco/estrato: (i) n=125 pacientes elegíveis independentes e Y(z)∈{0,1}; (ii) efeitos potenciais i.i.d. condicionais ao histórico disponível antes do bloco; (iii) randomização Bernoulli independente dos potenciais resultados, com probabilidade decidida antes da entrada da coorte e constante naquele bloco; (iv) desfechos finais completos no horizonte predefinido; (v) nenhuma interferência entre pacientes; (vi) indicador de elegibilidade fixado antes da randomização.

Para cada braço z, se n_z>0: r_z = sqrt[log(2/α_z)/(2 n_z)]. IC_z=[max(0, μhat_z−r_z),min(1, μhat_z+r_z)]. Quando n_z=0, IC_z=[0,1]. O intervalo do efeito é **[L_1−U_0, U_1−L_0]**. A truncagem por [0,1] é legítima pois médias Bernoulli estão nesse domínio. A desigualdade de Hoeffding aplicada condicionalmente à atribuição aleatória e ao histórico do bloco fornece cobertura do IC de cada braço de pelo menos 1−α_z. Pela desigualdade da união, os M×B×2 ICs de braços, e portanto todos os intervalos de efeito mensais, cobrem simultaneamente com probabilidade ≥ 1−α_mensal. Não se exige independência entre os ICs para a união. Isso NÃO prova validade sob variabilidade não controlada de atribuições dentro dos blocos nem sob desfechos faltantes ou interferência.

Orçamento total α=0,05 dividido **antes** de observar dados: mensal α=0,025 e análise final agrupada α=0,025. Para 4 estratos, 20 meses, 2 braços: α_por_braço_mensal=0,025/(4×20×2)=0,00015625. Para UMA análise final por estrato e braço: α_por_braço_final=0,025/(4×2)=0,003125. A família final só é válida para o efeito homogêneo sob **estacionariedade** dos desfechos potenciais e atribuição não responsiva dentro do desenho; caso contrário, a utilização de Hoeffding na diferença bruta de médias agrupadas pode ser inválida. O orçamento é único e NÃO se renova em P0, PROBE_WAIT, novas tentativas ou reentrada. O horizonte B=20 é finito: monitoramento adicional exigiria plano prévio de α para novas análises.

Se os efeitos mudarem ao longo dos meses, uma alternativa conservadora para o efeito médio dos blocos com pesos fixados antes dos dados é usar [Σ w_b L_b, Σ w_b U_b], aproveitando a cobertura simultânea. A precisão pode ser muito ruim. Isso NÃO equivale a uma sequência de confiança ótima ou a inferência de janelas móveis.

## 5. Experimento reprodutível
- Código: `kafka_probe_validation_v0_2.py` com **10,000 replicações** por combinação, seed `20261109`; simulação vetorizada de dados binários.
- 4 estratos × 20 blocos × 125 elegíveis = 10.000 pessoas por execução, 2.500 por estrato em vinte meses. Todos os elegíveis são assumidos expostos à decisão, o que é OTIMISTA para incidência de alertas reais.
- Proporções raras q=1%, 2%, 5% em dois modos: reter Z=0 durante exibição ativa; reexpor Z=1 em P0 durante sondagem.
- Cenários com μ0,μ1: nulo (0,55;0,55), benefício de 5 pp (0,55;0,60), dano de 5 pp (0,60;0,55), dano de 25 pp (0,70;0,45) e dano de 60 pp (0,80;0,20). Nenhuma dessas probabilidades é estimativa clínica; são configurações sintéticas ilustrativas.
- Resultado primário deste teste: cobertura, largura, inferência conclusiva e frequência de braço vazio. Não simula ainda a máquina completa com decisões que alteram a população e o tratamento.

### 5.1. Braço de retenção raro, efeito nulo (Δ=0): análise mensal
| Retenção q | Braço raro vazio | Cobertura marginal | Largura mediana | Decisões inconclusivas |
|---:|---:|---:|---:|---:|
| 1% | 28,51% | 100,00% | 1,39 | 100,00% |
| 2% | 7,98% | 100,00% | 1,39 | 100,00% |
| 5% | 0,17% | 100,00% | 1,40 | 100,00% |

A cobertura marginal de 100% é **conservadorismo observado**, não prova empírica de uma garantia exata nem sinal de bom poder. Com n=125 e q pequeno, alguns intervalos praticamente não identificam o sinal, mesmo quando ambos os braços têm observações.

### 5.2. Agrupamento estacionário de 20 meses, por estrato: dano de 25 pp
| q (retenção Z=0 ativa) | Cobertura marginal | Largura mediana | Evidência de dano U<−0,05 | Inconclusão |
|---:|---:|---:|---:|---:|
| 1% | 100,00% | 0,72 | 1,34% | 98,66% |
| 2% | 100,00% | 0,57 | 8,40% | 91,59% |
| 5% | 100,00% | 0,40 | 52,12% | 47,88% |

### 5.3. P0: sondagem com reexposição rara de 1/2/5%, sistema realmente benéfico (+5 pp)
| Reexposição q | Critério `L>−0,05` atingido | Inconclusão | Benefício provado `L>0` |
|---:|---:|---:|---:|
| 1% | 0,09% | 99,91% | 0,00% |
| 2% | 0,26% | 99,74% | 0,01% |
| 5% | 1,36% | 98,64% | 0,04% |

Essas frequências são médias por estrato, em avaliação final após vinte meses sob estacionariedade. Mesmo quando a recomendação ajuda (+5 pp), a regra quase nunca produz informação para reentrada com q≤5%. Não é uma simulação de decisões clínicas dinâmicas.

### 5.4. Cobertura simultânea
| Experimento | q | Cobertura simultânea (80 mensais + 4 finais) |
|---|---:|---:|
| Δ=0, retenção ativa | 1% | 99,98% |
| Δ=0, retenção ativa | 2% | 99,99% |
| Δ=0, retenção ativa | 5% | 100,00% |

Cobertura simultânea foi ≥99,98% nesses três desenhos nulos, consistente com uma construção conservadora. Não demonstra calibração para a malha clínica real nem validade para dados dependentes e decisões adaptativas não modeladas.

## 6. Contraexemplo adversarial obrigatório: pooling inválido
Considere Δ_b=0 em TODOS os meses. Nos primeiros 10 meses, μ0=μ1=0,05 e q_withhold=1%; nos 10 seguintes, μ0=μ1=0,95 e q_withhold=5%. As taxas de exibição foram predefinidas, mas se correlacionam com mudanças no prognóstico basal. Quando o analista ignora os blocos, compara grupos com misturas temporais diferentes, produzindo falso sinal causal.
- Média observada de Δ do estimador agregado ingênuo: **-0,31** (verdade em cada bloco: zero).
- Cobertura empírica do IC agrupado ingênuo: **9,81%**, muito abaixo do nominal.
- Falsa evidência de dano `U<−0,05`: **62,56%** das análises por estrato.
- Cobertura por intervalos mensais simultâneos: **100,00%**; agregação das suas margens com pesos fixos: **100,00%** mas largura mediana **1,20**.
**Conclusão:** o aparente ganho de poder mediante pooling não é gratuito; sem alinhamento temporal, pode produzir exatamente a suspensão incorreta que o KAFKA III pretende evitar. Os resultados de cobertura 9,815% NÃO refutam Hoeffding: eles demonstram sua aplicação sob hipóteses falsas.

## 7. Custo bilateral do conhecimento: cálculo de referência, não dado clínico
Oráculo simplificado: escolhe Z=1 quando Δ>0 e Z=0 quando Δ<0, sem custo de carga de alertas. Em 1.000 elegíveis, o prejuízo esperado da política versus oráculo é `1000 × (Y_oráculo − Y_política)`. É uma diferença esperada no desfecho favorável SIMULADO, não mortes clínicas estimadas.
| Verdade causal | Retenção ativa q=1% | Retenção ativa q=5% | Sondagem em P0 q=1% | Sondagem em P0 q=5% |
|---|---:|---:|---:|---:|
| Benefício de exibir +5 pp | 0,50 | 2,50 | 49,50 | 47,50 |
| Dano de exibir −25 pp | 247,50 | 237,50 | 2,50 | 12,50 |
A política que protege bem no cenário nocivo pode causar perda grande quando suspende benefício. A sondagem que aprende mais pode expor mais pacientes ao dano. Falta incorporar atraso, decisões subsequentes, carga de alertas, qualidade de vida e condições de irreversibilidade.

## 8. Conclusões e pendências bloqueantes
**[RESULTADO DO SIMULADOR]** Retenção/reexposição de 1–5% com n=125 por estrato/mês produziu quase sempre decisões inconclusivas no teste conservador. A agregação estacionária melhora sensibilidade, mas continua frequentemente inconclusiva para dano de 25 pp, e quase nunca confirma reentrada para +5 pp. A agregação temporal ingênua sob mudança em q e no prognóstico basal criou falso dano. Os dados não estabelecem vantagem ou segurança da máquina de estados.

**[LACUNAS]** (a) defasagem de resultados e censura dependente; (b) reentrada e suspensão realmente adaptativas; (c) efeito de mudanças na população/adesão e interferência; (d) avaliação por clusters quando há spillovers; (e) intervalos mais eficientes e válidos sob a política escolhida; (f) identificação de custos normativos por tipo de decisão; (g) reconstruir resultados brutos da Fase 12; (h) regra ética que autorize sondagem em casos concretos; (i) validação da margem h=5 pp. A robustez a confundimento não observado NÃO é adquirida por acompanhar somente resultados sob Z=0.

**[PRÓXIMA ETAPA]** A versão v0.3 deve testar inferência por blocos com melhor eficiência, sem pooling inválido, e a máquina causal completa com decisão adaptativa e prejuízo acumulado, preservando os cenários que resultarem inconclusivos. Antes de reivindicar resultados de monitoramento em tempo real, incluir resultados atrasados e uma regra operacional de reentrada com custos clínicos definidos.

## 9. Fontes metodológicas complementares
- Howard, Ramdas, McAuliffe, Sekhon (2021), *Time-uniform, nonparametric, nonasymptotic confidence sequences* — garantia time-uniform em cenário próprio; NÃO transferida automaticamente para este desenho.
- Cook, Mishler, Ramdas (2024), *Semiparametric Efficient Inference in Adaptive Experiments* — intervalos e sequências para experimentos adaptativos sob pressupostos específicos; NÃO aplicada como prova para nosso pooling.
- Os intervalos deste relatório usam Hoeffding elementar + desigualdade da união, com condições explícitas neste relatório, e não reivindicam método novo.
