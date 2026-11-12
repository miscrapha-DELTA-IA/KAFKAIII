# KAFKA III — Mapa de passagem para tese metodológica defensável

## Pergunta abrangente (preservada)
Quando uma previsão biomédica deveria **manter, restringir, perder, investigar e recuperar autoridade** para orientar cuidado, levando em conta ganhos, perdas, indeterminação causal, riscos assimétricos, feedback e recursos limitados?

## Estrutura das duas contribuições
**I. Teoria da autoridade causal:** (a) identificação parcial sob exibição determinística, (b) valores de políticas e efeitos individuais divergentes por interferência, (c) mapa de ganhos/perdas/zonas cinzentas, (d) limites de informação e de transporte temporal, (e) fronteiras de decisão sob restrições normativas.

**II. Eficácia metodológica condicional:** uma política que converta inferência + custos + atualidade + autorização em decisões dinâmicas e apresente desempenho superior, para alvos pré-definidos, frente a algoritmos robustos de mesma classe, com cenários adversariais e validação independente.

## O que está disponível agora
- Contrato causal v0.5A, SCM v0.5B, máquina v0.5C–v1.6, estudos sequenciais v0.6–v0.9 e limites v1.7.
- Experimento v1.8A: mapa exploratório comparativo; vantagem em família MISTO_MNAR contra métodos estáticos especificados, porém equivalência algébrica potencial com baseline safe policy learning de mesma restrição.
- Demonstrações condicionais de limitação de identificação e de divergência entre políticas e efeitos individuais.

## O que falta ANTES da alegação de superioridade do KAFKA como sistema
1. Definir contribuição incremental além de **safe policy learning**, bandits com feedback limitado e minimax conhecidos. O mapa estático sozinho não basta.
2. Construir **mesmo cenário/simulador clínico** e dois controladores dinâmicos fortes com o mesmo conjunto de informação: (i) baseline-constrained Bayesian/POMDP multietapas, (ii) robust safe-policy dinâmica com atualização e observabilidade.
3. Separar estimandos sem interferência e valor de política hospitalar sob interferência; validar cada um no desenho causal certo.
4. Delimitar 1–3 famílias-alvo com relevância científica substantiva e declarar **custos, perdas, faixas normativas, b e autorizações** antes do estudo independente. Incluir mundos de benefício persistente, dano persistente, mistura, reversões, MNAR e b falso como falsificadores.
5. Usar gerador externo distinto, código e sementes não utilizados na seleção da política; estudo ADEMP e intervalos pareados de erro Monte Carlo com multiplicidade.
6. Exigir vantagem sobre o melhor baseline **da mesma classe** em pelo menos uma família pré-registrada, sem prejuízo excessivo além da margem especificada em famílias adversariais. Se falhar, não declarar superioridade; preservar os achados como contribuição de governança e limites.
7. Revisão externa das provas e do código e revisão bibliográfica de novidade, inclusive Joshi et al. (AAAI 2024), Ben-Michael et al. (JASA 2025), Li & Li (NeurIPS 2025) e Jiang et al. (2026).

## Sequência operacional recomendada
**v1.8B** — atacar a lacuna original: observabilidade dependente do estado e janela temporal; otimização multietapas de autoridade restrita com valor da informação. Comparar com POMDP/Bayes e robust safe-policy forte sob mesmas restrições; experimentar sem seleção de 'vencedores'.

**v1.9** — congelar política e margens; novo gerador clínico SCM Z→D/W→T→Y, diversos riscos basais, tempos de maturação, MNAR e mudança de sinal após sondagem positiva; módulo hospitalar randomizado por clusters em avaliação independente.

**v2.0** — teste confirmatório externo com código fechado, contrato causal auditado, métricas e baselines pré-definidos, documentação de capacidade estatística e alegações aprovadas; somente então redação com resultados de eficácia metodológica **condicional**, se verdadeiramente presentes.

## Critérios de alegação
- **Teorema de limite:** prova exata + pressupostos + antecedente literário. Não tratar simples positividade como nova teoria.
- **Superioridade exploratória:** pode ser relatada com ressalvas, mas não é prova definitiva.
- **Superioridade confirmatória sintética:** requer protocolo prospectivo independente, forte baseline da mesma classe, ganho de desfechos/regret e tolerância a pior caso sob famílias pertinentes.
- **Eficácia clínica:** requer um desenho empírico apropriado e governança ética; nenhuma das simulações aqui autoriza alegação clínica.

## Princípio científico
Os resultados negativos não devem bloquear a busca de eficácia, nem a busca de eficácia deve apagar resultados negativos. A tese é a **fronteira entre informação, autoridade e consequências**; a política KAFKA III será defendida como eficaz apenas se ultrapassar a melhor alternativa comparável dentro da família-alvo declarada.
