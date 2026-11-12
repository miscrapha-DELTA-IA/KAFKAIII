# KAFKA III — Contrato causal formal v0.5A
**Data de fechamento:** 2026-11-10  
**Situação:** especificação lógica pré-código, passível de implementação exploratória v0.5B; **não** é validação estatística/ética/clinicamente confirmatória.  
**Projeto:** *When Should a Biomedical Prediction Lose Its Authority to Guide Care?*  
**Autoria científica:** única, a cargo do pesquisador.  
**Evidência histórica:** Fase 12 não demonstrou superioridade; resultados negativos v0.2–v0.4 preservados.

## 0. Decisões normativas e epistêmicas de base
1. O KAFKA III não pode interpretar ausência de identificação como identificação de dano nem ausência de evidência de dano como segurança.
2. A avaliação deve ser bilateral: prejuízo por **manter**, **suspender**, **sondar** e **atrasar**. A exposição durante sondagem já integra o dano clínico relacionado ao desfecho; não somar novamente como rubrica independente.
3. A política de autoridade distingue evidências científicas, regras estatísticas, premissas de transportabilidade, decisão de governança e autorização ética de exposição.
4. Um efeito individual da exibição do alerta não é igual ao efeito de uma política hospitalar sob interferência, competição por recursos ou história comportamental.
5. Escores podem parecer bons enquanto recomendações alteram cuidados e desfechos; esse fenômeno é antecedente da literatura e **não** constitui uma novidade reivindicável por si só.
6. Não impor margem de não-inferioridade ou regra de suspensão por futilidade sem justificativa independente. A análise exploratória primária de sinal usa U<0, L>0 e L≤0≤U.

## 1. Unidade, calendário, população e ordem temporal
**Índices:** hospital/cluster c=1,…,C; mês de entrada t=1,…,B; paciente candidato j; paciente elegível i; estrato basal m=1,…,M. O horizonte do resultado primário é 90 dias após a elegibilidade, não “o mês t” como desfecho contemporâneo.

**Definição de população-alvo:** pacientes candidatos que satisfariam, em t, os critérios de elegibilidade clínica E=1, incluindo A=1, definidos *antes* do sorteio Z. No núcleo v0.5B, a população será condicionada à admissão e à elegibilidade. Isso **não** identifica automaticamente o valor de uma política sobre todos os candidatos se a política anterior modificar quem é admitido.

**Sequência dentro do mês:**
1. Definir a história disponível F⁻_{c,t}, capacidade K_{c,t}, protocolo, θ_t e estado de autoridade prévios à decisão; atualizar H_{c,t} apenas a partir do passado, sem resultados futuros.
2. Gerar/selecionar candidatos; definir admissão I_adm antes de S e Z. Determinar X, U e características da equipe. Registrar possível seleção dependente de política/ocupação.
3. Calcular S=f_{θ_t}(X) como **risco de desfecho desfavorável**; A=1{S≥τ₀} é **alerta gerado/elegibilidade do aviso**, não tratamento administrado nem desfecho favorável.
4. Para A=1, sortear Z∈{0,1} segundo a probabilidade e_{cmt} fixada a partir da história anterior; R=(S,A,texto do aviso) se Z=1; R=∅ se Z=0. Entre A=0, impor Z=0 por definição e excluir esses pacientes do estimando primário do alerta. Oculte todas as vias relevantes de apresentação do escore no braço Z=0 ou marque contaminação.
5. O profissional decide D, com possibilidade explícita de WLST W. Registra-se se houve solicitação/intenção de suporte B_req.
6. A unidade distribui recursos: Q=1 indica **negação por capacidade entre quem teria suporte solicitado**. T descreve suporte realmente recebido; outras modalidades de cuidado permanecem documentadas.
7. O desfecho biológico Y é definido no horizonte clínico fixo de 90 dias (Y=1 favorável). O processo de aferição determina o atraso administrativo L e o indicador O de Y observado, independentemente de Y existir biologicamente. O registro C_obs pode refletir Y, ausência de medida ou rótulo imperfeito; C_obs≠Y em geral.
8. No início de meses posteriores, apenas coortes cujo endpoint maturou e cujos dados já estavam disponíveis podem entrar no monitor. θ_{t+1}, H_{t+1} e estado de autoridade são atualizados somente com passado causalmente elegível.

Uma ordem mais fiel em forma de grafo inclui U→D, U→Y, H→D, Z/R→D/W, D/W→B_req, (B_req, D_{-i}, K)→Q→T, (T,R,U,X,K,ações de outros)→Y, (Y,T,W,O)→C_obs e história passada→H/θ/State do próximo bloco.

## 2. Variáveis, informação conhecida e SCM
- **X:** covariáveis clínicas observáveis antes do alerta.
- **U:** prognóstico e informação contextual não observados pelo controlador (podem influenciar médico, tratamentos e Y).
- **G:** indicadores de diretrizes/avaliação clínica; se exigirem adjudicação posterior, **não** estão disponíveis em tempo real. G=0 não implica automaticamente WLST inadequada.
- **S:** risco predito de **desfecho desfavorável** (0 a 1); **A:** indicador de alerta gerado/alta probabilidade de risco.
- **Z:** exibição/ocultação real entre elegíveis A=1; **R:** conteúdo visível, ou ∅ sob ocultação verificada.
- **D:** intenção clínica ou decisão terapêutica multicomponente, não apenas um 0/1 genérico.
- **W:** WLST documentada, decisão de limitar/retirar suporte por razões clínicas e de preferências.
- **B_req:** suporte solicitado/indicado; **Q:** indisponibilidade de recursos que impede suporte solicitado; **T:** vetor de cuidados efetivamente administrados, incluindo T_support.
- **K:** capacidade institucional e concorrência; **H:** hábito/adesão/competência do corpo clínico, potencialmente parcialmente latente; **θ:** versão do modelo preditivo.
- **Y:** desfecho biológico favorável em horizonte predefinido; **O:** presença de aferição suficiente no horizonte; **L:** atraso até disponibilização; **C_obs:** rótulo usado pelo sistema, possivelmente contaminado.
- **E:** elegibilidade basal; **I_adm:** admissão; **State:** estado administrativo da autoridade; **P:** autorização clínica/ética para sondagem.

**SCM modular proposto (funções ainda a especificar e testar):**

```text
I_adm[j,t] = f_adm(X,U,K,H,policy_previous,ε_adm)
(X,U,G)_it = f_baseline(t,c,I_adm,ε_baseline)
S_it = f_θt(X_it)                       ; A_it = 1{S_it ≥ τ₀}
Z_it ~ Bernoulli(e_cmt) se E_it=A_it=1 ; caso contrário Z_it=0
R_it = (S_it,A_it,mensagem) se Z_it=1 ; caso contrário R_it=∅
(D_it,W_it,B_req_it) = f_care(X_it,U_it,G_it,R_it,H_ct,ε_care)
Q_it = f_capacity(B_req_i, B_req_-i, K_ct, regras_de_triagem,ε_capacity)
T_it = f_treatment(D_it,W_it,B_req_it,Q_it,ε_treat)
Y_it(90d) = f_outcome(X_it,U_it,T_it,R_it,K_ct,T_-i,ε_Y)
(O_it,L_it) = f_ascertain(X_it,U_it,T_it,W_it,Y_it,ε_O)
Cobs_it = f_record(Y_it,O_it,T_it,W_it,R_it,ε_C), com Cobs=∅ se sem rótulo
H_c,t+1 = f_history(H_ct, {Z,D,W,T,O}_ct, ε_H)
θ_t+1 = f_retrain(θ_t, dados madurados permitidos pela versão do protocolo)
State_c,m,t+1 = f_governance(State_cmt, apenas dados maduros permitidos,
                             orçamento estatístico, P, avaliação normativa)
```

**Núcleo controlado v0.5B:** congelar θ, admissão/elegibilidade exógenas, H constante, K sem restrição, O=1, R sem caminho direto sobre Y além dos mediadores documentados; acrescentar separadamente WLST, U, censura, H e K por flags. É uma **restrição experimental**, não suposição universal sobre UTI.

### 2.1. Regra para não confundir WLST, falta de leito e não indicação
O evento `T_support=0` tem múltiplas origens mutuamente distinguíveis **na classificação de motivo principal**, embora decisões possam coexistir ao longo da trajetória:
- `W=1`: decisão clínica de limitação/retirada de suporte documentada.
- `B_req=1, Q=1`: suporte indicado e solicitado, mas indisponível por capacidade; isso **não** é WLST.
- `B_req=0, W=0`: suporte não solicitado por ausência de indicação, preferência ou outra decisão registrada.
- `T_support=0` por falha operacional ou recusa: categoria adicional codificada.
A variável `W_disc` só pode ser criada por critérios clínicos/adjudicação explícitos, com erro de avaliação modelado; nunca por (1−T)(1−G). Um óbito após WLST não permite inferir a recuperação que ocorreria sem WLST.

## 3. Estimandos distintos e seus limites
**A. Efeito de exibição, sem interferência** (alvo inicial simplificado):

Δ_Z(m,t | F⁻) = E[Y_it( Z=1 ) − Y_it( Z=0 ) | E=1, m, t, F⁻].

Inclui as consequências de exibir a recomendação via decisão do médico, terapêutica e possíveis caminhos diretos, sem exigir atribuir mecanicamente toda a mudança a T.

**B. Efeito biológico de tratamento:**

τ_T(x; r) = E[Y(do(T_support=1),do(R=r)) − Y(do(T_support=0),do(R=r)) | X=x].

É uma intervenção conceitual controlada em suporte, cujo significado depende de outros tratamentos mantidos, viabilidade e tempo. **Randomizar Z não randomiza T**; U confunde T e Y. Não confundir T=0 com a definição de Y^{T=0} usada em Kim et al.; alinhar cuidadosamente a versão de tratamento/ausência de tratamento.

**C. Efeito da recomendação sobre a decisão de WLST:**

Δ_W(m,t) = E[W_it(Z=1) − W_it(Z=0) | E=1,m,t].

Pode ser observado mais cedo que Y, se W for registrado sem diferenças de aferição entre braços e se Z for randomizado. NÃO é desfecho biológico, nem prova de que as WLST adicionais foram incorretas.

**D. Desempenho preditivo sob regime contrafactual:**

ℒ^{(T=0)}_t(θ)=E[ℓ_pred(f_θ(X),Y^{T=0})] sob um regime de tratamento precisamente definido; não equivale a Δ_Z nem ao valor do alerta. É estimando da literatura precedente, não reivindicação original.

**E. Efeito direto individual com interferência:**

DE_i(e,h)=E_{Z_-i~π_e}[Y_i(1,Z_-i;H=h)−Y_i(0,Z_-i;H=h)].

Depende da política e de como a exposição dos demais é distribuída; não igualar a um efeito institucional. Mesmo a interpretação ‘direta’ pode incluir caminhos mediadores via T próprio e rearranjo de capacidade.

**F. Valor de política hospitalar dinâmica:**

V(π)=E_{candidatos e história sob π}[Σ_{t,i} ω_it·Y_it^π / Σ_{t,i} ω_it],
ΔV(π₁,π₀)=V(π₁)−V(π₀),

onde π mapeia a história observável em regras de autoridade/exposição. Fixar denominador/população-alvo comum quando houver seleção endógena de admissão. Para desfecho principal, ω=1 e média por candidato elegível previamente definido é o padrão causal transparente; médias apenas entre admitidos sob cada política podem comparar populações diferentes. O comparador ALWAYS_ON é e=1 e ALWAYS_OFF é e=0; ambos induzem suas próprias trajetórias H, K e admissão.

**G. Perda de política:** no mundo sem história/interferência/custos de alerta, ℓ(e,Δ)=(1−e)[Δ]_+ + e[−Δ]_+. Essa identidade NÃO deve ser aplicada sob K ou H variáveis, quando se compara valores integrais V(π) de trajetórias.

## 4. Proposição 2 — equivalência observacional sob Z≡1
Com Y binário, consistência, exibição em 100% dos elegíveis e sem outras restrições contrafactuais, só μ₁=E[Y(1)] é identificado. Como μ₀=E[Y(0)]∈[0,1], o conjunto não paramétrico **sharp neste modelo irrestrito** é

Δ_Z∈[μ₁−1, μ₁].

Os dois mundos já auditados adotam P(U=1)=1/2, Y(T=0)=0, P(Y(T=1)=1|U)=0,8 U. Em ambos, P(D=1|U,Z=1)=1/2, dando P(D=1,Y=1)=0,20, P(D=1,Y=0)=0,30 e P(D=0,Y=0)=0,50. Sob Z=0, o mundo positivo tem P(D=1|U)=0,25U (μ₀=0,10, Δ=+0,10); o negativo tem P(D=1|U)=0,75U+0,25(1−U) (μ₀=0,30, Δ=−0,10). Portanto **os registros observáveis sob Z≡1 são idênticos**, incluindo D, T, W e Y; a diferença é contrafactual.

Não afirmar que qualquer distribuição permite efeitos ±δ independentemente de μ₁: é necessário δ≤μ₁≤1−δ. Positividade da exibição isoladamente tampouco basta: para identificar por Z é preciso intercambialidade (por ex. randomização), consistência, desenho de observação e ausência/abordagem explícita de interferência.

## 5. Proposição 1 — inversão de sinais sob capacidade
Construção formal corrigida: N=100, K=50, exatamente 50 pacientes com U=1. Um suporte concedido gera Y=U e sem suporte Y=0. Em ALWAYS_OFF, a triagem humana baseada em U aloca os 50 leitos aos 50 U=1 e V(0)=0,50. Em ALWAYS_ON, a priorização entre todos os 100 alertados é aleatória, alocando em média 25 leitos a U=1 e V(1)=0,25, logo ΔV=−0,25.

Mantidos os outros 99 pacientes alertados, se o paciente i isoladamente recebe Z_i=1, concorre aos 50 leitos aleatórios: P(T_i=1|Z_i=1,Z_-i=1)=0,5. Se Z_i=0, tem prioridade inferior e P(T_i=1|Z_i=0,Z_-i=1)=0. Portanto seu efeito direto é 0,5 se U_i=1, 0 caso contrário, e a média sobre os 100 é +0,25. **Efeito direto local positivo e efeito de mudar toda a política negativo são compatíveis.** No cenário real, essa contradição entre estimandos só é uma possibilidade, não prevalência clínica estimada.

O contraste de política requer evidência em políticas diferentes, idealmente entre múltiplos clusters ou desenhos de implementação que separem spillovers e histórias; variar somente Z dentro de uma UTI sob saturação única não identifica automaticamente V(1)−V(0). Referência externa: Hudgens & Halloran (2008), JASA, doi:10.1198/016214508000000292.

## 6. Estados e protocolo de exposição
Seja q∈{0,01,0,02,0,05}; sempre considerar **somente elegíveis A=1**:

| Estado | Exposição e=P(Z=1 | A=1,F⁻) | Significado | Condição para nova exposição |
|---|---|---|---|
| ALWAYS_ON (comparador) | 1 | exibição total | política sintética fixa |
| ALWAYS_OFF (comparador) | 0 | nenhum alerta | política sintética fixa |
| ACTIVE | 1−q | exibição predominante e sentinela ocultada | protocolo autorizado |
| P0 | 0 | suspensão | nenhuma exposição nova |
| PROBE_WAIT (inscrição autorizada) | q | reexibição rara randomizada | P=1, elegibilidade, orçamento e plano fixos |
| PROBE_WAIT (apenas espera; sem inscrição) | 0 | desfechos de sondagem prévia pendentes | novas exposições interrompidas |
| REENTRY_RESTRICTED | ρ predefinido (0<ρ≤1−q) | retorno limitado e monitorado | decisão normativa/ética separada, não automática |

A v0.4 efetivamente mantinha novas inscrições mensais em PROBE_WAIT. O contrato v0.5A distingue `probe_enrollment_authorized` de `waiting_for_maturity`: pode haver novas coortes enquanto a autorização existir; se cessar, é preciso esperar com e=0, mantendo pendências e registros. P0 não oferece observações sob Z=1; dado histórico válido não é necessariamente transportável à população atual. Uma transição P0→PROBE_WAIT **não** ocorre por inferência matemática de segurança: exige autorização externa em contexto admissível.

**Transições candidatas (não autorização clínica):**
- ACTIVE com evidência intervalar U_CI<0: candidato à restrição/suspensão, sujeito à governança e à avaliação do tipo de evidência (individual vs política). Não é prova de dano no hospital se houver interferência.
- ACTIVE com [L_CI,U_CI] contendo zero: indeterminação. Mantém vigilância e encaminha revisão; não aciona suspensão por ‘dano oculto detectado’.
- P0: sem sondagem autorizada, permanece sem exibição; rever periodicamente custo de oportunidade e necessidade de fontes independentes.
- PROBE_WAIT: coortes aguardam horizonte; só análises preespecificadas após maturação. Se L_CI>0 sob modelo válido, candidata à revisão de REENTRY_RESTRICTED. Caso contrário, mantém indeterminação ou evidência de dano.
- REENTRY_RESTRICTED: ρ limitado, nova avaliação e critérios explícitos de rollback; não equivale a ALWAYS_ON nem a ‘segurança provada’.
- Nenhuma reentrada automática se versão θ, população, intervenções, horizonte, condições de interferência ou suporte mudarem de modo a impedir transporte da evidência.

### 6.1. Contrato de dados e ausência de oráculo
O controlador observa somente registros disponíveis até a decisão: X,S,A,Z,R,D,W,B_req,Q,T, K monitorado, O, C_obs quando maduro e validado, logs de exposição, versões θ, IDs de coorte, histórico de estados e α gasto. O controlador NÃO observa U, ε, Y contrafactual, verdade causal Δ, valor de oracle, efeitos individuais, nem H latente se não mensurado. O simulador mantém dois canais separados: `world_truth` para avaliação **após** a decisão e `controller_observed` para decidir. O teste automatizado deve falhar se o controlador importar dados de `world_truth`.

## 7. Garantias inferenciais: onde valem e onde falham
Na v0.4, com 20 meses × 4 estratos × 2 braços, reserva-se α_família_mensal=0,025 e α_braço=0,025/(20·4·2)=0,00015625 para intervalos Clopper–Pearson binomiais por braço. A parcela α=0,025 não alocada à família mensal continua indisponível até um protocolo prévio de uso, sem reciclagem de α. A desigualdade da união dá cobertura simultânea ≥97,5% para as médias condicionais dentro de cada bloco **se** cada CI individual tiver sua cobertura declarada válida. A regra de decisão pode usar essas regiões cobertas, mas não as torna causalmente identificadas em situações de interferência.

**Condições para o CI por braço:** dentro do estrato e bloco, potenciais resultados independentes e com distribuição Bernoulli homogênea condicionalmente à história prealocação; randomização Bernoulli independente, p comum e conhecida; ausência de interferência; Y observado corretamente no horizonte; consistência; o histórico utilizado é prévio à decisão. Se há heterogeneidade fixa por paciente (finite-population/design-based), pesos variáveis por pessoa, censura informativa, dependência entre resultados, H mutável dentro do bloco ou competição por leitos, a cobertura ‘exata Clopper–Pearson’ não pode ser simplesmente afirmada para Δ_Z. Sob desenho aleatório conhecido, métodos design-based poderão ser empregados, mas precisam de prova própria e estimando próprio.

**Atrasos:** definir antes da atribuição endpoint (90 d), data de elegibilidade e data prevista de avaliação, com variações de disponibilização entre pacientes/brasos; `matured_i` e `observed_i` são estados diferentes. Somente usar resultados finais efetivamente aferidos, nunca tratar desfechos pendentes como desfecho desfavorável nem silêncio como sobrevida. Maturidade administrativa completa do bloco não garante observação completa se houve perda de seguimento. Morte antes do dia 90 pode determinar Y=0 quando o endpoint foi assim definido — não confundir com censura. Se as verificações dependem de quem retornou, evitar análise de casos completos sem pressupostos para O.

**Censura/ausência:** com Y binário e randomização válida, limites de pior caso por braço:

μ_z∈[E(OY|Z=z), E(OY+1−O|Z=z)],

logo Δ∈[lower_1−upper_0, upper_1−lower_0]. Para incerteza amostral, construir intervalos simultâneos dos eventos binários observáveis OY e OY+1−O, com α próprio e sem confundir identificação parcial com precisão. Sob ausência de suposições extras esses limites serão frequentemente largos. Mecanismos IPCW/MAR só poderão ser usados após definir e avaliar as suposições pertinentes; MNAR não é reparável só removendo pacientes.

**Atribuição adaptativa:** e_{cmt} pode mudar entre coortes como função previsível de F⁻, e a validade condicional do IC por coorte depende de o plano de atribuição e a lei de Y satisfazerem os pressupostos **dentro** da coorte. Não fazer pooling bruto quando o risco basal e e mudam juntos. Intervalos para médias históricas, efeitos correntes e efeitos de políticas são objetos diferentes. Parada opcional dentro da mesma coorte ou inspeções múltiplas não programadas precisam de CS ou ajuste próprio.

**Interferência/histerese:** quando a ação de um paciente altera a disponibilidade de cuidado de outro, o CI individual por braço pode medir outra quantidade — ou ter cobertura inválida por dependência. Tratar o valor da política da unidade como alvo separado. Randomizar pacientes dentro de um único hospital não basta, em geral, para identificar a diferença entre políticas de cobertura total e nula e seus efeitos históricos.

## 8. Perdas acumuladas, benchmarks e não duplicação
No núcleo sem interferência/história/custos fixos:

R_t(e,Δ)=N_t((1−e)[Δ]_+ + e[−Δ]_+).

- `mantencao`: N_t e[-Δ]_+.
- `suspensao`: N_t(1−e)[Δ]_+.
- `sondagem_clinica`: **não** adicionar como terceiro dano, pois as exposições q já entram em e; registrar sondagens como contagem e custos *não clínicos* específicos.
- `atraso`: a soma de R_t para os meses em que a ação desejada não ocorreu; não adicionar duas vezes uma parcela de desfecho já acumulada.

Sob interferência e H: comparar V(π) entre trajetórias completas geradas por cada π no **mesmo universo de candidatos exógenos quando esse alvo for escolhido**. Benchmark ‘melhor entre ALWAYS_ON e ALWAYS_OFF’ é distinto de um oráculo que conhece efeitos futuros, e a diferença de valor em relação ao melhor fixo pode ser negativa para uma política adaptativa que o supere. Guardar os dois comparadores separadamente, declarar estimando e sinais. Não transferir a decomposição estática para K/H variáveis.

## 9. Os três bloqueios priorizados para v0.5B
**B1 — Plano experimental de identificação (bloqueante antes da inferência):** separar experimento sem interferência (randomização Bernoulli individual, A=1) de experimentos com capacidade/H (estimando de política e, se houver pretensão inferencial, desenho com vários clusters ou hipóteses modeladas explicitamente). Congelar elegibilidade, θ e horizonte no primeiro núcleo para validar causalidade básica.

**B2 — Medição e missingness (bloqueante antes do monitor final):** especificar endpoint de 90 dias, data de elegibilidade, delays, captura de óbito, perda de seguimento, O e C_obs; pré-especificar fallback conservador sob MNAR. O CI por casos completos será intencionalmente um comparador mal especificado em cenários de MNAR, nunca a regra principal ‘válida’.

**B3 — Regras decisórias e ética (bloqueante antes de conclusões clínicas):** separar estatística de governança, representar autorização de sondagem e custo bilateral, e documentar que L>0/U<0 são condições candidatas, não decisões automaticamente seguras nem aprovação para pacientes reais. Nenhuma margem arbitrária entra no núcleo principal.

## 10. Critérios de aceitação da implementação v0.5B
1. **Fidelidade causal:** `Z` altera `R`, `D/W`, `T` e depois `Y`, com cenário negativo de nenhum efeito; não ler Y futuro ao decidir.
2. **Semântica correta de W/Q:** cenário de W sem Q, cenário Q sem W, cenário ambos ausentes e registros separados; `T=0` nunca implica automaticamente W=1.
3. **Reprodução do núcleo reduzido:** ao desligar U, interferência, H, censura, drift e permitir g_Y composto calibrado aos mesmos μ₀,μ₁, reproduzir **distribuições/estatísticas dentro de Monte Carlo**, não exigir trajetórias bit-a-bit idênticas às da v0.4.
4. **Inferência:** validação de cobertura sob modelo i.i.d. sem interferência, faltas e seleção de modo; quando falha um pressuposto, mostrar que não existe garantia e buscar métodos apropriados, sem ‘corrigir’ apenas a semente.
5. **Estados:** teste de e=1−q (ACTIVE), 0 (P0), q (sondagem autorizada), 0 (sondagem sem inscrição), ρ (reentrada), 1 (ALWAYS_ON), 0 (ALWAYS_OFF).
6. **Desfechos:** testes diferenciando 90 dias pendentes, aferição final válida, ausência informativa, registro errôneo e morte como Y=0.
7. **Ética:** P0→sondagem apenas no universo sintético com autorização de cenário; sem permissão a política não reexibe e apenas contabiliza perdas de oportunidade no oráculo.
8. **Interferência:** pelo menos duas unidades ou comparação de políticas completas com mundos acoplados para resultados sintéticos; nunca relatar como estimativa randomizada de efeito de política de um cluster único.
9. **Reprodutibilidade:** seeds e ruídos exógenos por candidato/coorte, códigos e logs de fontes, versões θ, IDs únicos e testes de invariantes; paralelizar mundos com números aleatórios comuns sem fingir pareamento individual quando admissão for endógena.
10. **Resultados adversariais:** preservar cenário de Z≡1 não identificável, inversão sob K, censura informativa que inverte sinal, atraso de reentrada, false suspensions e Fase 12 negativa.

## 11. Dicionário de decisões fechadas vs. abertas
**FECHADO PARA ESPECIFICAÇÃO:** S como risco desfavorável; A=1 se S≥τ₀; Z exibição real; estimando restrito a A=1; W≠Q; P0=0; sondagem autorizada e=q; separação de Y/O/Cobs; efeitos de tratamento, alerta e políticas distintos; sem prova de segurança por não identificação; α sem reinício; não tratar política da unidade como efeito individual; duas proposições numéricas condicionais; desfechos favoráveis codificados Y=1.

**ABERTO/DEPENDENTE DA FINALIDADE:** definição clínica operacional e adjudicação de WLST discordante; escolha do endpoint específico e protocolo de seguimento para mundo clínico; funções funcionais g_care, g_outcome, g_capacity e parâmetros; desenho e número de clusters e hipóteses de transportabilidade; margens de não inferioridade clinicamente aceitas; eventual política minimax; estimadores para dados com interferência/MNAR; validade de extrapolar dos experimentos sintéticos para uma instituição real.

## 12. Bibliografia contextual (não reivindicação de originalidade)
Hudgens MG, Halloran ME. Toward causal inference with interference. *JASA*. 2008;103(482):832–842. DOI:10.1198/016214508000000292. Texto aberto: https://pmc.ncbi.nlm.nih.gov/articles/PMC2600548/.

A literatura histórica do projeto (Kim, van Amsterdam, Boeken, Mertens, AEGIS, entre outros) permanece no inventário já validado pelo autor. Este contrato não supõe que suas demonstrações sejam substituídas por um resumo secundário.

**Conclusão:** há especificação causal suficiente para **iniciar uma implementação modular exploratória** do núcleo sem interferência, respeitadas as barreiras B1–B3; não há autorização para ensaio real, afirmação de superioridade, inferência hospitalar sob interferência ou manuscrito confirmatório.
