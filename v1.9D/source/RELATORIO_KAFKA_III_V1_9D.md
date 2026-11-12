# KAFKA III — Relatório técnico v1.9D

**Título de trabalho:** *When Should a Biomedical Prediction Lose Its Authority to Guide Care?*  
**Data:** 11 de novembro de 2026  
**Estado:** RESULTADO EXPLORATÓRIO REPRODUZÍVEL; **não confirmatório, não clínico**.  
**Natureza da etapa:** desafio mecanístico de decisão sob informação dependente da exposição, falha de especificação e admissibilidade regulatória.

## 0. Continuidade e proveniência

O checkpoint conversacional da v1.9C relatou (i) 192 casos em que ótimo exato, rollout e regra míope foram iguais, (ii) 1.947 combinações sem ação regular admissível, das quais (iii) 30 apresentaram inviabilidade **apenas** na grade discreta embora houvesse ação contínua admissível. A v1.9D **não reexecuta, não verifica independentemente e não substitui** esses números, porque o código e a matriz originais da v1.9C não foram recuperados neste pacote. A nova bateria é inteiramente identificada abaixo e contém apenas 12 cenários estruturais e 27 combinações de teste externo de especificação.

## 1. Pergunta científica delimitada

Existe uma classe simples e transparente de processos nos quais a aquisição prospectiva de informação tem valor não míope, mantendo equivalência de ações, observações e custos entre planejadores? A vantagem persiste se a precisão da evidência, o prior ou as restrições de governança estiverem incorretos? Como impedir que conflito de regras, revisão e discretização sejam interpretados como autorização de exposição?

**Resposta obtida:** sim, o planejamento prospectivo pode superar a regra míope *dentro do seu próprio modelo*. Porém, a vantagem não é robusta a todas as classes de erro de especificação, e não há evidência de originalidade ou superioridade do controlador KAFKA como arquitetura clínica.

## 2. Modelo reproduzível

### 2.1 Estado, exposição e objetivo

O estado latente estático é `theta ∈ {+d, -d}`, com `d = 0.10`, e `p = Pr(theta=+d)` representa crença do planejador; não é o verdadeiro estado revelado ao controlador. `e∈[0,1]` é a fração de exposição. Por período:

`ell(e,p) = d [p(1-e) + (1-p)e]`.

`theta=+d` significa que não expor gera perda; `theta=-d` significa que expor gera perda. A perda total incorpora custo por oportunidade de sinal `c_q q(e)`, e custo fixo de revisão somente quando se abre conflito. Esse é um objetivo *único* de perda esperada acumulada; não se somam arbitrariamente outras métricas como se fossem compatíveis.

### 2.2 Informação e positividade

Assume-se que uma observação comparativa (evidência informativa de dois braços) chega ao fim do período com probabilidade

`q(e) = q0 + 4(qmax-q0)e(1-e)`.

A chance de obter comparação é máxima com alguma presença de ambos os grupos; nos extremos, o canal rotineiro pequeno `q0` oferece a única comparação externa. No cenário-base, `q0=0.02`, `qmax=0.82`. O canal rotineiro é hipotético, igual para todas as políticas e **não** é criado pela revisão. Sua legitimidade causal não foi demonstrada. Na presença de sinal, a sensibilidade e a especificidade simétricas assumidas são `a`; sinal positivo satisfaz `Pr(+|theta=+d)=a`, `Pr(+|theta=-d)=1-a`. Sinal ausente não atualiza a crença.

`p_plus = p a/[p a+(1-p)(1-a)]`; `p_minus = p(1-a)/[p(1-a)+(1-p)a]`.

Para `a=0.5`, a observação não informa sobre o estado e não pode gerar valor informacional prospectivo. A avaliação sob precisão verdadeira diferente da assumida **não** permite que o planejador enxergue a verdadeira precisão ou o verdadeiro estado.

### 2.3 Horizonte, Bellman e comparadores

Horizonte de 6 períodos, sem desconto, estado estático, observação gerada após a decisão. Para os intervalos regulares não vazios, a recursão exata é:

`V_h(p)=min_{e∈[L,U]} {ell(e,p)+c_q q(e)+(1-q(e))V_{h-1}(p)+q(e)[r(p)V_{h-1}(p_plus)+(1-r(p))V_{h-1}(p_minus)]}`,

onde `r(p)=pa+(1-p)(1-a)` e `V_0=0`. A otimização em `e` é global para essa função quadrática, testando extremos e ponto estacionário, não usando uma grade grosseira. São três comparadores com **a mesma informação e autorização**:

- **Míope:** minimiza custo e perda corrente sem contabilizar observações futuras.
- **Rollout:** a cada período, minimiza custo corrente mais a perda futura exata se a política míope fosse seguida daí em diante; reavalia após receber sinais.
- **Ótimo exato:** usa Bellman em toda a árvore de crenças até o fim do horizonte.

A comparação possui sentido de *valor Bayes esperado dentro do gerador*. Não representa identificação causal clínica.

### 2.4 Conflito e revisão

Se `L>U`, não existe ação **regular** admissível. O motor executa a exposição de contingência **pré-especificada** `e_fb=0.10`, registra o conflito e cobra `0.02` pelo acionamento inicial da revisão, com prazo ilustrativo de 2 períodos. Essa contingência **não é classificada como ação regular autorizada**; sua própria legalidade e aceitabilidade clínica dependeriam de validação externa. A revisão não altera o prior nem fornece dados ou permissões privilegiadas. Após o prazo, o estado torna-se `UNRESOLVED`; mesmo se as cotas voltarem a ser compatíveis, a saída só ocorre mediante atualização externa válida e assinada. O custo de revisão é único por incidente, não repetido automaticamente enquanto a mesma revisão permanece irresolvida.

A máquina de auditoria é um teste isolado de governança; o Bellman aplica os limites fixos do cenário e o custo inicial comum, **sem** modelar uma futura mudança política provocada pela revisão.

## 3. Cenários escolhidos e resultados internos

Doze cenários (`results_model.csv`): `balanced`, `near_harm`, `harm_skew`, `benefit_skew`, `weak_signal`, `uninformative`, `expensive_signal`, `slow_signal`, `upper_restricted`, `narrow_grid_gap`, `high_floor`, `conflict`.

| Cenário | Míope | Rollout | Ótimo exato | Exposição inicial: míope / exato |
|---|---:|---:|---:|---|
| balanced | 0.289895 | 0.132938 | **0.132891** | 0.000 / 0.500 |
| near_harm | 0.244216 | 0.132551 | **0.130000** | 0.000 / 0.445 |
| harm_skew | 0.118600 | 0.108060 | **0.100653** | 0.000 / 0.272 |
| benefit_skew | 0.118600 | 0.108060 | **0.100653** | 1.000 / 0.728 |
| weak_signal | 0.252112 | 0.252035 | **0.252034** | 0.000 / 0.000 |
| uninformative | **0.252120** | **0.252120** | **0.252120** | 0.000 / 0.000 |
| expensive_signal | 0.249496 | 0.180999 | **0.180857** | 0.000 / 0.439 |
| slow_signal | 0.244216 | 0.220050 | **0.220034** | 0.000 / 0.384 |
| upper_restricted | 0.248894 | 0.206307 | **0.206303** | 0.000 / 0.396 |
| narrow_grid_gap | **0.283174** | **0.283174** | **0.283174** | 0.370 / 0.370 |
| high_floor | **0.258091** | **0.258091** | **0.258091** | 0.600 / 0.600 |
| conflict | **0.283448** | **0.283448** | **0.283448** | 0.100 / 0.100 (contingência) |

**Leitura:** existem situações ilustrativas nas quais explorar custa perda imediata, porém reduz perda esperada futura; nisso o planejador Bayes é superior à política míope. Não há evidência de que a política KAFKA seja melhor do que o próprio planejador Bayes que conhece o modelo. Empates e restrições também persistem. O cenário `conflict` contém custo inicial de revisão igual para os três métodos.

## 4. Teste de especificação adversa

Sem reotimizar a política, os cenários `near_harm`, `weak_signal` e `upper_restricted` foram submetidos a 9 ambientes cada: prior verdadeiro `0.20/0.42/0.70`, acurácia verdadeira `0.25/0.50/0.85`, totalizando **27 células**. O controlador continua usando o prior e a acurácia que havia assumido; somente o avaliador conhece o ambiente verdadeiro. `a_true=0.25` representa sinal **invertido/adversarial**, não uma estimativa realista de precisão clínica.

- Em **15 das 27 células**, o ótimo segundo o modelo assumido sofreu perda verdadeira maior que a regra míope (diferença maior que `1e-7`).
- Para `near_harm`, `p_true=0.42`, `a_true=0.85`, perdas: míope `0.244216`, exato `0.130000`.
- Mantendo `p_true=0.42`, porém com `a_true=0.50`, perdas: míope `0.254426`, exato `0.293972`; **inversão**.
- Com `p_true=0.20` e `a_true=0.25`, perdas: míope `0.136102`, exato `0.398680`; falha grave sob sinal invertido.

**Interpretação negativa obrigatória:** a superioridade Bayes em gerador próprio não garante ganho robusto; pode estimular exposição desnecessária quando o canal de informação é mal especificado. O conjunto adverso é pequeno, sintético e intencionalmente estressado: `15/27` não é uma estimativa epidemiológica de falha e não deve ser generalizado.

## 5. Inviabilidade regulatória versus artefato de grade

É necessário separar formalmente:

- `L>U`: **conflito real**, conjunto regular vazio; somente contingência com auditoria, jamais autorização tácita.
- `L<=U` mas `G∩[L,U]=∅`: **falso conflito numérico** introduzido pela grade `G`.
- `G∩[L,U]≠∅`: ao menos uma alternativa regular da grade.

Com grade `G={0,0.25,0.50,0.75,1}`, o intervalo `[0.37,0.43]` é continuamente viável mas não contém ponto da grade. Para uma grade uniforme de passo `h`, todo intervalo fechado dentro de `[0,1]` de largura **pelo menos `h`** contém pelo menos um ponto da grade. Inversamente, intervalos de largura menor que `h` podem ficar vazios na grade, sem haver conflito governamental. Esta afirmação foi checada na malha de teste e decorre da geometria elementar; não é teorema novo KAFKA III.

**Correção de desenho:** checar admissibilidade contínua **antes** da discretização; se `L<=U`, otimizar no intervalo e refinar a grade se necessário. Nunca emitir `NO_ADMISSIBLE_ACTION` apenas porque uma grade arbitrária não tocou o intervalo permitido.

## 6. Auditorias executadas

- O modelo produziu CSVs com 12 cenários estruturais, 27 condições adversas e mapa de discretização para cada cenário.
- Validação de ordenação: em todos os cenários **no gerador assumido**, `V_exact <= V_rollout <= V_greedy` dentro da tolerância numérica; essa ordem não é postulada fora do modelo.
- Caso `a=0.5`: ótimo exato e regra míope têm a mesma perda, sem falsificar valor informacional.
- Para cada cenário viável, a primeira ação foi conferida contra otimização exaustiva independente de **201** exposições uniformemente espaçadas entre as cotas.
- A garantia de intervalo versus grade foi verificada sobre uma malha de combinações de cotas.
- Em teste de auditoria com conflito por três períodos e depois cotas viáveis, a revisão permaneceu irresolvida até uma atualização **externa e assinada**; nenhuma permissão apareceu automaticamente.
- `test_independent.py`: **5.140 verificações numéricas, geométricas e de governança passaram**. `experiment_v1_9d.py`: as asserções principais também passaram.

Esses testes verificam consistência implementacional. **Não** fornecem cobertura frequentista, segurança em pacientes, prova de boa especificação causal, nem auditoria por equipe externa.

## 7. Proposições e falsificadores

**Proposição elementar P1 (igualdade em ausência de influência da ação sobre a informação).** Se (i) a observação posterior e sua probabilidade são independentes da exposição `e`, (ii) as ações futuras permitidas são independentes da escolha atual e (iii) a função objetivo é separável por período e não há dinâmica física controlada adicional, então o valor de continuação no Bellman não depende de `e`. Minimizar a perda total do período é então suficiente. A política míope e a ótima têm o mesmo valor. **Prova:** por indução retroativa a partir de `V_0=0`, o termo de continuação é constante relativamente à decisão presente; resta minimizar o termo corrente. Essa é uma condição suficiente, não uma explicação verificada para os 192 empates históricos da v1.9C.

**Falsificador F1:** diferença exato versus míope deve desaparecer se os sinais forem não informativos (`a=0.5`) ou se todo termo de continuação for independente da ação. **Passou no caso sem informação.**

**Falsificador F2:** vantagem do modelo não pode ser descrita como robusta se houver qualquer reversão sob erro de especificação relevante. **Falhou para robustez: 15/27 reversões.**

**Falsificador F3:** uma ação não pode surgir automaticamente de revisão, nem um conjunto regulatório vazio pode virar admissível pela malha. **Passou nos testes implementados.**

**Falsificador F4:** todo sucesso da política deve ser comparado com o ótimo exato com iguais oportunidades. **Não foi demonstrada vantagem própria de KAFKA sobre o ótimo Bayes.**

## 8. Limitações bloqueantes e decisão editorial

O estado latente é binário e estático; o sinal é simétrico, sem atraso, com mecanismo hipotético de comparação entre grupos; probabilidades, perdas, prazo, custos e governança foram arbitrados para ensaio de mecanismo. Não há MNAR, interferência hospitalar, heterogeneidade realista, efeitos dinâmicos sobre população futura, desfechos individualmente atrasados, garantia de inferência *anytime*, calibração com especialistas nem validação externa independente. A modelagem de revisão é uma máquina de auditoria simples, não um sistema jurídico ou clínico. As restrições são ilustrativas e não normas legais.

**Decisão da v1.9D:**

1. **Demonstrado apenas dentro do modelo ilustrativo:** planejamento informado pode superar uma regra míope ao internalizar o valor das observações futuras.
2. **Demonstrado como contraexemplo de robustez ilustrativo:** erros de precisão e de prior podem reverter a vantagem.
3. **Corrigido em contrato técnico:** distingue-se conflito de restrições de falha da grade e a revisão não atribui automaticamente exposição.
4. **Não demonstrado:** originalidade, superioridade incremental própria de KAFKA, segurança clínica, dominância sob gerador externo ou critério para autorizar implantação.

**Porta editorial:** manter estudo como *exploratory methods / counterexample*, sem alegação de eficácia ou recomendação clínica. A etapa seguinte é **v1.9E — protocolo externo adversarial e controle de erro de modelo**, detalhada no arquivo homônimo. Não promover publicação confirmatória nem implantação.

## 9. Execução e arquivos

Executar na pasta do pacote:

```bash
python experiment_v1_9d.py
python test_independent.py
```

Não são usados pacotes Python de terceiros nem números pseudoaleatórios: os resultados são **expectativas enumeradas exatamente no espaço de observações finito**, com otimização analítica em exposição contínua. As saídas são `results_model.csv`, `results_misspecification.csv`, `audit_discretization.csv`, `governance_audit.csv`, `metadata.json` e arquivos de verificação. Não há erro Monte Carlo a estimar; há, sim, risco de erro de modelagem e numérico.
