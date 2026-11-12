# KAFKA III — Protocolo candidato v1.9E (ainda não registrado)

**Objetivo:** demonstrar, refutar ou limitar valor incremental de um mecanismo explícito de autoridade sob erro de modelo, custo de informação e restrições de governança, sem a vantagem de escolher geradores após observar resultados.

## Requisitos para congelamento pré-avaliação

1. Fixar estimando de perda acumulada em unidades justificadas clinicamente, com componentes de exposição incorreta, suspensão incorreta, custo de sondagem e atraso, evitando dupla contagem.
2. Contratar desenho e geradores com avaliador **independente** que mantenha sementes/dados finais sob sigilo. Definir famílias antes do acesso, sem reparametrizar depois de conhecer os desfechos.
3. Incluir famílias: sempre benefício, sempre dano, efeito nulo, reversão de ambos os sinais e após reentrada, diferenças por estrato, observabilidade e positividade variáveis, sinais fracamente informativos/invertidos, acurácia e prior errados, MNAR, atraso de desfechos e interferência hospitalar em análise de clusters separada.
4. Comparar com ótimo Bayes com mesmo prior quando esse for conhecido, Bayes sob mistura robusta, minimax protegido, safe policy learning estático equivalente, sentinela, regra histórica, sondagem fixa com orçamento igual e regra míope.
5. Definir *admissibilidade contínua*, exposições de contingência, custo/duração de revisão e gatilhos externos de autorização antes de executar. Não confundir `NO_GRID_ACTION` com `NO_REGULAR_ACTION`.
6. Estabelecer um envelope robusto para parâmetros `a`, `q(e)`, prior e drift, sem usar a verdade sintética no controlador. Comparar uma política de não adquirir informação quando robustez falhar.
7. Selecionar, antes de dados finais, margens normativas de ganho mínimo e dano excessivo máximo. Relatar separadamente falha de cobertura, violação de restrição, falsas suspensões, reentrada incorreta, tempo até decisão e fração inconclusiva.
8. Versionar código, parâmetros, permissões, sementes, hashes e auditoria. Exigir revisão matemática independente e inspeção crítica de originalidade, incluindo confusão com controle Bayes/POMDP e safe policy learning.

## Gates exigidos

- **Gate de fidelidade:** quatro políticas recebem a mesma evidência, acesso, custos e permissões; caso contrário, comparação inválida.
- **Gate de segurança:** nenhuma decisão automática é tomada em conjunto vazio; revisão não fornece privilégio nem atualiza crença sem dado válido.
- **Gate de robustez:** falhas em ambientes adversos precisam ser explicitamente relatadas; nenhuma alegação de superioridade irrestrita.
- **Gate confirmatório:** só depois de protocolo registrado, validação externa, revisão de prova e margens justificadas clinicamente.

Este arquivo é um **candidato** para pré-registro, não um registro prévio real. Não reclassificar ensaios internos como confirmação.
