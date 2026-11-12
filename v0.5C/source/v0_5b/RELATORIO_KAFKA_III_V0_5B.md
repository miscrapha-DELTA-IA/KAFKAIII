# KAFKA III — Relatório metodológico exploratório v0.5B

**Data:** 2026-11-10  
**Situação:** implementação exploratória do SCM clínico e testes adversariais; **não autoriza** ensaio real, claims de detecção/eficácia ou manuscrito confirmatório.

## 1. Pergunta da rodada e relação com a v0.4

Esta versão testa se conseguimos construir uma cadeia causal explícita entre exposição a alerta, decisão clínica, suporte efetivo, desfecho favorável em 90 dias, disponibilidade do desfecho e registro, **sem** permitir que o controlador veja contrafactuais ou conheça o efeito verdadeiro. A v0.4 usava um caminho reduzido Z→Y; a v0.5B modela Z→R→W/D→T→Y. A equivalência de classe foi comprovada apenas por ponte mediadora degenerada em teste unitário, não por reprodução numérica de todos os cenários v0.4.

## 2. Definições e mecanismos

- **S e A:** S=0,63+0,32X, com X uniforme; A=1{S≥0,60} para todos os participantes pré-selecionados. É um escore sintético, **não calibrado ou treinado em pacientes**.
- **U:** reserva prognóstica binária não revelada ao controlador; pode influenciar decisões e prognóstico.
- **Z e R:** randomização Bernoulli com probabilidade determinada pela política; R fica ausente sob Z=0.
- **W, B_req, Q, T:** WLST documentada, suporte indicado/solicitado, negativa por capacidade e suporte recebido, respectivamente. Em todo registro, W e Q são disjuntos e T não coexiste com W/Q.
- **Y:** resultado binário em 90 dias. Para sintéticos com reserva U, a probabilidade de Y=1 sem suporte é 0,08+0,06U−0,025X (com um deslocamento de drift no cenário específico), e o suporte aumenta essa probabilidade em 0,55 se U=1 e 0,17 se U=0. São escolhas ilustrativas, não parametrização clínica.
- **H:** memória comportamental dependente das proporções de exposição *já observadas*, com atualização após cada mês.
- **O, C_obs:** desfecho medido ou não; rótulo observado sujeito a perturbação independente num cenário específico. Atraso até a disponibilização vai de 3 a 5 meses após exposição; o monitor usa os resultados somente no quinto mês, sem selecionar os precocemente disponíveis.

## 3. Desenho de simulação e validade

Foram executadas **25 replicações por combinação**, **9 cenários × 7 políticas = 63 configurações** na taxa q=5%, totalizando **1.575 trajetórias**; cada trajetória possui 20 meses, 4 estratos e 500 elegíveis mensais (10.000 episódios sintéticos). A sensibilidade q=1% e 2% tem 2 cenários × 7 políticas × 25 replicações × 2 valores de q = **700 trajetórias adicionais**. A semente principal é `20261110`.

O orçamento para a família mensal permanece 0,025, com α por braço/estrato/bloco igual a 0,025/(20×4×2) = 0,00015625; a parcela restante do orçamento global de 0,05 **não foi utilizada**. Os 80 pares de braços estrato×mês de cada trajetória são avaliados uma única vez após seguimento completo previsto (o que não resolve perdas de seguimento). O procedimento CP tem interpretação binomial somente no núcleo sem interferência e com rótulos observados adequadamente; a versão de pior caso para dados ausentes só elimina a suposição de ausência independente se o rótulo dos observados realmente corresponde a Y.

## 4. Resultados primários — exposição total versus suspensão total

Todos os valores abaixo representam **probabilidade observada média de desfecho favorável no simulador**, não estimativas de pacientes reais. Contrastes são pareados pelos mesmos ruídos exógenos.

| Cenário | ALWAYS_ON | ALWAYS_OFF | V(ON) − V(OFF) por 1.000 | Interpretação |
|---|---:|---:|---:|---|
| neutral | 40.30% | 40.30% | +0.00 | Sem efeito da exposição |
| beneficial_alert | 43.38% | 40.36% | +30.12 | Alerta reduz WLST e melhora Y |
| harmful_wlst | 24.68% | 37.98% | -132.94 | Alerta aumenta WLST e piora Y |
| harmful_hidden_U | 29.52% | 40.23% | -107.09 | O mesmo mecanismo com U clínico latente |
| harmful_MNAR | 29.37% | 40.19% | -108.16 | Dano real com observação informativa |
| benefit_with_hysteresis | 41.52% | 40.31% | +12.13 | Benefício com carga comportamental histórica |
| capacity_interference | 25.84% | 33.49% | -76.47 | Comparação de políticas sob leitos limitados |
| harmful_record_bias | 29.45% | 40.41% | -109.57 | Dano real e rótulo parcialmente incorreto |
| neutral_drift | 45.87% | 45.87% | +0.00 | Risco basal muda, efeito Z nulo |

**Não é um contraste identificado por randomização entre hospitais** no cenário com capacidade compartilhada. Nesse caso, o valor é obtido diretamente de dois mundos sintéticos com políticas distintas, não do intervalo individual por braço.

## 5. Custo bilateral de manutenção, suspensão e sondagem

| Política (q=5%) | Alerta benéfico: favoráveis/1.000 | Alerta nocivo: favoráveis/1.000 |
|---|---:|---:|
| Sempre exibir | 433.76 | 246.84 |
| Sempre ocultar | 403.64 | 379.78 |
| Ativo, retenção 5% | 432.36 | 253.48 |
| Suspensão exógena | 412.40 | 341.21 |
| Suspensão exógena + 1 sondagem | 412.47 | 340.98 |
| P0 + 1 sondagem | 403.70 | 379.47 |
| Gatilho por evidência | 432.36 | 253.48 |

A diferença entre `TRIGGER_P0_*` e `ALWAYS_ON` decorre de uma **suspensão exógena programada no mês 6**, não de identificação de dano pelo monitor. A sondagem é uma única coorte (mês 8 para `TRIGGER_P0_WITH_PROBE`, mês 7 para `P0_PROBE_ONCE`) com e=q quando autorizada; os custos clínicos surgem das consequências da exposição, sem dupla contabilização de uma rubrica “dano da sondagem”.

No cenário `beneficial_alert`, ALWAYS_ON supera ALWAYS_OFF em cerca de **30,12 desfechos favoráveis por 1.000**. No cenário `harmful_wlst`, ALWAYS_ON fica **132,94 por 1.000 abaixo** de ALWAYS_OFF. Em capacidade limitada, a perda de ALWAYS_ON é de **76,47 por 1.000** frente a ALWAYS_OFF. Esses contrastes são condicionais ao gerador construído.

## 6. Sensibilidade a retenção/sondagem de 1%, 2% e 5%

| q | Perda da sentinela com alerta benéfico vs ALWAYS_ON (por 1.000) | Perda da sentinela com alerta nocivo vs ALWAYS_OFF (por 1.000) |
|---:|---:|---:|
| 1% | 0.280 | 131.580 |
| 2% | 0.556 | 130.232 |
| 5% | 1.396 | 126.296 |

Os desfechos de referência mantêm os mesmos valores de políticas fixas ao variar q, pois as sementes de base não dependem do nome da política nem da taxa. Isso não é uma estimativa populacional externa.

## 7. O resultado negativo de informatividade foi preservado

Nas 25 replicações por política e cenário da grade principal, **todas as 80 avaliações estrato×mês permaneceram inconclusivas**, inclusive com dano verdadeiro no gerador. Consequentemente, `EVIDENCE_GATED` não suspendeu ninguém e reproduziu a trajetória de exposição de `ACTIVE_SENTINEL`. **O funcionamento lógico do controlador foi testado, mas sua capacidade decisória NÃO foi demonstrada.**

O baixo poder decorre, em boa parte, de 125 elegíveis por estrato/mês e 1–5% de controle raro, além do alfa altamente repartido. Clopper–Pearson não elimina esse problema. Os resultados não são uma medição de cobertura nominal geral; a família experimental ainda precisa de uma calibração inferencial dedicada.

## 8. Diagnóstico adversarial de censura informativa e rótulos

Em uma amostra sintética independente de 80.000 pacientes com 50% de exibição: o efeito comparando **todos** os desfechos Y gerados foi **-11.32 pp**; a diferença entre apenas os casos com registro foi **+42.44 pp**; a construção conservadora baseada em desfechos ausentes retornou **[-0.191, 0.714]**. Essa faixa inclui o efeito gerado, mas não determina o sinal. É um teste ilustrativo único, **não** um estudo de cobertura empírica.

O cenário `harmful_record_bias` adiciona erro no rótulo C_obs mesmo quando O=1. A inferência sobre Y não é automaticamente válida após erro de classificação do rótulo. Estudar sensibilidade e adjudicação do rótulo permanece necessário.

## 9. Garantias e seus limites

- **Testes automatizados:** 15 testes de contrato causal executados com sucesso; não equivalem a verificação matemática de todos os modelos.
- **Firewalls:** o monitor só recebe `ObservedCohort` quando `ready_month <= current_month`. Coortes futuras são seladas fora do controlador. A classe observável não contém U, Y contrafactual ou efeito verdadeiro.
- **Atribuição:** Bernoulli previsível por período; todos os pacientes incluídos já têm A=1. O simulador não modela treinamento nem modificação de θ.
- **Randomização:** em cenário sem interferência, a atribuição individual cria variação exógena; isso NÃO identifica automaticamente o efeito biológico do tratamento T.
- **Informação perdida:** o mecanismo MNAR quebra o procedimento por casos completos, mas o monitor utiliza limites conservadores. O modelo com rótulo errado permanece sem correção.
- **Interferência:** recursos são distribuídos entre todos os 500 pacientes da mesma unidade/mês, não estratos isolados. Clopper–Pearson por braço não é garantia para o valor de política sob essa dependência.
- **Histerese:** o histórico utiliza a proporção efetivamente exposta em meses anteriores; a v0.5B apresenta um cenário de mudança de comportamento, não demonstra a generalidade do mecanismo.
- **Ponte com a v0.4:** foi testada a possibilidade matemática de representar um efeito reduzido Δ_Z no caminho mediado Z→D=T→Y com probabilidades μ0,μ1. Não ocorreu replicação bit a bit dos cenários históricos; a maioria dos parâmetros da v0.5B é nova.

## 10. As diferenças entre políticas não provam superioridade do KAFKA III

`TRIGGER_P0_*` **recebe informação exógena** sobre o momento da suspensão. Uma simulação que dá ao controlador uma intervenção programada não pode ser citada como prova de que detectaria dano sozinho. `EVIDENCE_GATED` não encontrou evidência suficiente no regime testado. `ALWAYS_ON`, `ALWAYS_OFF` e a retenção sentinela seguem sendo comparadores sintéticos mínimos; AEGIS, Kim AWM/SWM e Feng **não foram implementados aqui**. A Fase 12 negativa permanece inalterada.

## 11. Pendências antes de uma v0.5C ou experimento confirmatório

**Bloqueantes para comparação decisória conclusiva:** (1) política de reentrada completa, com autorização ética separada e vigilância após reentrada; (2) valor de política formal sob interferência com múltiplos clusters e desenho identificado; (3) calibração de cobertura e poder fora do núcleo binomial i.i.d.; (4) censura informativa e rótulo incorreto com análise de sensibilidade; (5) seleção/admissão endógena e possíveis efeitos de transporte; (6) critérios normativos de suspensão/reentrada e irreversibilidade clínica.

**Etapas seguintes recomendadas:** fechar a v0.5B por auditoria de código independente; introduzir a política de reentrada como módulo decisório separado; escolher métricas de perdas por trajetória hospitalar e contrafactuais pertinentes; validar o método estatístico onde há adaptação, censura ou interferência; implementar comparadores fiéis. **Não escrever ainda o artigo confirmatório.**

## 12. Reproduzir

Com Python 3.10+, NumPy e SciPy: `python -m unittest -v test_kafka_v05b.py`, depois `python run_all.py`. Resultados detalhados estão em `results_patient_policy_v0_5b.csv`, `paired_policy_comparisons.csv`, e arquivos JSON. A precisão numérica pode variar levemente entre versões do NumPy/SciPy.
