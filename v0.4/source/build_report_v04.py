from pathlib import Path
import csv, json, hashlib, zipfile
import pandas as pd
P=Path(__file__).resolve().parent
D=pd.read_csv(P/'decision_summary_v0_4.csv')
A=json.loads((P/'attrition_stress_v0_4.json').read_text())
C=json.loads((P/'configuration_v0_4.json').read_text())
ALPHA_ARM=C["alpha_arm_monthly"]

def f(s,q,p,col='gap_best_static_per_1000'):
    qrow=D[(D.scenario==s)&(D.q==q)&(D.policy==p)]
    if len(qrow)!=1:raise ValueError((s,q,p,len(qrow)))
    return qrow.iloc[0][col]
def vf(x, decimals=2):
    return f'{x:.{decimals}f}'

def md_table_scenario():
    lines=['| Política | Benefício +5 pp | Dano −25 pp |', '|---|---:|---:|']
    for p,nam in [('ALWAYS_ON','Sempre exibir'),('ALWAYS_OFF','Sempre suspender'),('ACTIVE_SENTINEL','Ativo com sentinela de 5%'),('TRIGGER_P0_NO_PROBE','Suspensão exógena sem sondagem'),('TRIGGER_P0_PROBE','Suspensão exógena com sondagem 5%'),('P0_PROBE','P0 e sondagem desde o início')]:
        lines.append(f'| {nam} | {vf(f("benefit5",.05,p))} | {vf(f("harm25",.05,p))} |')
    return '\n'.join(lines)

def md_q():
    lines=['| q (retenção ou sondagem) | Sentinela: perda com alerta benéfico | Sentinela: perda com alerta nocivo | P0+sondagem: perda com alerta benéfico | P0+sondagem: perda com alerta nocivo |','|---:|---:|---:|---:|---:|']
    for q in [.01,.02,.05]:
        lines.append('| '+f'{int(q*100)}% | '+ ' | '.join(vf(f(s,q,p)) for s,p in [('benefit5','ACTIVE_SENTINEL'),('harm25','ACTIVE_SENTINEL'),('benefit5','P0_PROBE'),('harm25','P0_PROBE')])+' |')
    return '\n'.join(lines)

def md_delay():
    lines=['| Mecanismo | Atraso de 1 mês | Atraso de 3 meses | Diferença |', '|---|---:|---:|---:|']
    for title,tag,pol in [('Suspensão diante de dano −60 pp','harm','ACTIVE_SENTINEL'),('Reentrada com benefício +60 pp','benefit','P0_PROBE')]:
        a=f(f'artificial_highvolume_{tag}60_delay1',.05,pol)
        b=f(f'artificial_highvolume_{tag}60_delay3',.05,pol)
        lines.append(f'| {title} | {vf(a)} | {vf(b)} | {vf(b-a)} |')
    return '\n'.join(lines)

report=f'''# KAFKA III — Contrato decisório e testes adversariais v0.4
**Data:** 2026-11-10  
**Status:** exploração sintética reproduzível; NÃO confirmatória; SEM validação clínica; NÃO autoriza escrever o manuscrito.

## 1. Objetivo e proveniência

Esta versão avança a v0.3 para um simulador que acumula perdas ao longo de 20 meses. Emprega os 4 estratos × 125 elegíveis/mês, as taxas de 1%, 2% e 5% e o orçamento de erro já definidos na v0.2. As tabelas da v0.3 com Hoeffding versus Clopper–Pearson foram tomadas como antecedentes; esta versão **não recalcula Sandoval nem Cook**, e não utiliza o código do Claude que não foi entregue nesta conversa.

A pergunta operacional é bilateral: quanto custa (i) manter uma recomendação nociva, (ii) suspender uma benéfica, (iii) sondar e (iv) atrasar uma mudança de autoridade? Os componentes de prejuízo só são aditivos quando a ausência de interferência e efeitos históricos permite um único efeito de exibição por bloco. O benefício da sondagem não é presumido.

## 2. Contrato executado e pressupostos

- `ACTIVE`: alerta exibido em `1−q` dos pacientes; `q` é retenção sentinela aleatória.
- `P0`: recomendação suspensa, `e=0`.
- `PROBE_WAIT`: sondagem autorizada apenas **no universo sintético**: alerta reexibido a `q` dos elegíveis; cada mês em sondagem inicia **nova coorte** e consome sua alocação de α pré-planejada; não há reinício de α.
- `REENTRY_RESTRICTED`: recupera `e=1−q` se, e somente se, uma coorte de sondagem *já madura* obtiver `L>0`. A autorização clínica foi suposta **somente** para testar a lógica, não dada como real.
- `U<0` em uma coorte madura iniciada com o sistema ativo leva ao estado de sondagem/suspensão em políticas monitoradas. Conclusões inconclusivas não justificam reentrada. Nenhuma margem clínica arbitrária de 5 pp foi aplicada.
- `TRIGGER_P0_*`: suspensão **exógena hipotética** no mês de índice 6, NÃO uma inferência de dano. Serve somente para testar custos de suspensão e recuperação.

Todas as avaliações ocorrem **no início do mês**, antes de escolher a exposição da nova coorte, usando apenas desfechos cujo atraso predefinido terminou. Coortes são contabilizadas uma única vez, identificadas por mês e estado de origem. Atrasos distintos nos dois braços levam à espera pelo maior deles; nenhum desfecho parcial influencia o estado.

### 2.1. Modelo de inferência

Com randomização Bernoulli definida antes de cada bloco, desfechos binários i.i.d. condicionais ao histórico e ausência de interferência, há um efeito condicional por estrato/mês, Δ_{{mb}}(H) = E[Y(1)-Y(0) | H_{{m,b-1}}]. As contagens por braço são analisadas por Clopper–Pearson bilateral com α_braço={ALPHA_ARM:.8f}, alocado *antes* dos dados: α_família=0,025 para 20 meses × 4 estratos × 2 braços. Pela desigualdade da união, a família de intervalos cobre simultaneamente com probabilidade ≥0,975 sob esses pressupostos. A outra metade do erro total de 0,05 permanece **não utilizada e não reciclada**. Há uma análise por coorte, não um pooling ingênuo.

Os estados futuros dependem das análises passadas, mas a probabilidade do bloco corrente é conhecida e previsível. Isso **não** autoriza inferência conjunta de valor de política, janelas móveis ou censura informativa. Amostras n_z=0 retornam braço [0,1] e a inferência de diferença permanece inconclusiva.

### 2.2. Perda e benchmark

Sem histórico/interferência, em cada bloco com efeito Δ e exposição realizada e:

    L_manutencao = N·e·max(-Δ,0)
    L_suspensao = N·(1-e)·max(Δ,0)
    L_clinica = L_manutencao + L_suspensao

O prejuízo clínico da sondagem JÁ pertence ao primeiro ou segundo termo; NÃO existe uma terceira perda clínica independente chamada "sondagem". Número de reexposições na sondagem e custo operacional **ilustrativo** de 0,001 unidade por reexposição são reportados à parte. Atraso é perda clínica acumulada enquanto o estado não muda, NÃO um segundo dano no mesmo paciente.

Para histerese ou interferência, a decomposição acima não é transferida. O simulador calcula o valor esperado sob cada trajetória e o compara com a melhor **política fixa entre ALWAYS_ON e ALWAYS_OFF**, cada qual com sua própria história. A diferença pode ser NEGATIVA: portanto, chamamos `gap_best_static_per_1000`, não "regret" garantidamente não negativo. O benchmark é estático e não é um oráculo dinâmico global.

## 3. Experimentos e modelos sintéticos

**Configuração base:** 20 meses × 4 estratos × 125 elegíveis, 1.000 réplicas para cada uma de 11 configurações × 3 taxas × 6 políticas (198 combinações), mais 12 combinações mecânicas de alto volume; total **210 linhas** no CSV. As probabilidades são parâmetros artificiais escolhidos para estressar mecanismos; não são efeitos hospitalares estimados.

Cenários: benefício +5 pp; dano −25 pp; drift basal de 0,05 para 0,95 com Δ=0; desfechos com 1 versus 3 meses de atraso; atraso de braço diferencial (o braço mais lento governa maturação); 20% de censura completamente aleatória; censura dependente de desfecho/braço; histerese de comportamento (memória 0,8 e carga −0,10); interferência por saturação de recursos (−0,10e na probabilidade basal); mudança de efeito de +5 pp nos 8 meses iniciais para −25 pp nos 12 finais.

## 4. Resultados de perdas acumuladas no desenho original

**Perdas médias esperadas por 1.000 pacientes versus melhor política fixa, taxa q=5%:**

{md_table_scenario()}

**Trade-off ao variar q** (unidades: perda esperada de desfechos favoráveis por 1.000 elegíveis):

{md_q()}

No desenho de 125 elegíveis/estrato/mês, os intervalos mensais ficaram essencialmente inconclusivos. Não houve reentrada estatisticamente sustentada nas políticas correspondentes, nem uma vantagem adquirida por detecção causal de dano no cenário de −25 pp. As alterações observadas nos braços `TRIGGER_*` são fruto da suspensão **exógena**, não do desempenho de um detector KAFKA III.

### 4.1. Atrasos — teste mecânico separado de alta informação

Para verificar que o simulador realmente respeita maturação e atraso, aumentamos artificialmente para **2.000 pacientes por estrato/mês** e um efeito muito grande de **±60 pp**, q=5%, com 300 replicações por configuração. Isso equivale a até 160 mil elegíveis em 20 meses, e **não representa uma coorte usual de UTI**.

{md_delay()}

Nesse teste, os intervalos reconhecem o sinal e a primeira transição ocorre depois de 1 ou 3 meses, respectivamente. Dois meses adicionais de espera custam aproximadamente 54 desfechos favoráveis esperados por 1.000 elegíveis na média dos 20 meses, seja por manter por mais tempo um alerta prejudicial, seja por prolongar a ausência de um alerta benéfico. No regime original de q≤5% com 125 pacientes/estrato/mês, as decisões permanecem inconclusivas: mudar o atraso não melhora a inferência.

### 4.2. Censura informativa — inversão de sinal

Um experimento **separado**, com 4.000 replicações, 2.500 elegíveis por replicação, atribuição 50/50, Δ verdadeiro = −0,25, e censura dependente de Y e Z produziu:

- Média estimada por casos completos: **{vf(A['complete_case_mean_delta'],4)}**, invertendo o sinal verdadeiro;
- Cobertura empírica do intervalo de casos completos: **{vf(A['complete_case_coverage']*100,2)}%**;
- Declaração falsa de benefício com casos completos: **{vf(A['complete_case_false_evidence_benefit']*100,2)}%**;
- Cobertura de limite conservador para ausências: **{vf(A['missing_robust_coverage']*100,2)}%**;
- Largura mediana desse último: **{vf(A['missing_robust_median_width'],3)}**.

O limite robusto usa, em cada braço, A=O·Y e B=O·Y+(1−O), com O indicando desfecho observado. Como A≤Y≤B, construímos um limite inferior de E[A] e superior de E[B] por CP (com α repartido), e depois subtraímos os intervalos dos braços. Sob randomização, independência **entre pessoas** e desfecho binário, a cobertura das médias é válida ainda que O dependa de Y. Isso é uma implementação conservadora de **identificação parcial por pior caso**, não uma solução estreita para censura MNAR. Não preserva validade se os resultados dos pacientes forem correlacionados sem ajuste por clusters.

As análises da política que usam **casos completos** no cenário MNAR são deliberadamente **mal especificadas**. Os números de perda verdadeira continuam computáveis pelo simulador porque nele se conhece Y latente, mas seus intervalos observacionais não são válidos para a decisão. A implementação robusta está disponível como função e foi testada em diagnósticos, mas ainda não foi usada como procedimento principal de todas as políticas MNAR.

### 4.3. Histerese e capacidade

Sob histerese, a memória M se atualiza como M_(t+1)=0,8·M_t+0,2·e_t; resultados potenciais condicionais dependem de M_t. Com benefício direto de +5 pp e carga histórica de −10 pp, a política sempre ativa perdeu cerca de **{vf(f('benefit5_hysteresis',.05,'ALWAYS_ON'))}** desfechos favoráveis por 1.000 versus sempre suspender no horizonte de 20 meses. Um efeito individual condicionado positivo não garante valor positivo da trajetória histórica.

Sob capacidade compartilhada, especifique E[Y(z;e)]=0,55−0,10e+0,05z. Para saturação e mantida, a diferença direta entre os braços é +5 pp; para política de exibição em proporção e, a média é V(e)=0,55−0,05e. Assim, ALWAYS_ON apresenta perda populacional **{vf(f('benefit5_capacity',.05,'ALWAYS_ON'))} por 1.000** frente a ALWAYS_OFF. A regra baseada em Δ direto não identifica o valor de saturar o hospital. O exemplo usa um único agregado artificial; **não** estima efeitos de spillover real nem substitui randomização entre hospitais.

### 4.4. Mudança do sinal do efeito e gatilho exógeno

No cenário de mudança (+5 pp até o mês 8, −25 pp depois), `TRIGGER_P0_NO_PROBE` alcançou diferença **{vf(f('sign_flip',.05,'TRIGGER_P0_NO_PROBE'))} por 1.000** comparada à melhor política FIXA, negativa porque a política dinâmica artificialmente troca de estado num momento favorável. A troca foi **programada no mês 7 sem inferência causal** e não demonstra capacidade antecipatória do KAFKA III. O benchmark é a melhor política fixa, não o melhor oráculo dinâmico. Esse resultado não deve ser incluído como evidência de superioridade do sistema.

## 5. Auditoria de invariantes e garantias

1. A rotina de intervalos retorna [0,1] com braço vazio, e nunca declara sinal com controle inexistente no teste unitário.
2. Um paciente pertence a uma coorte, que é analisada uma vez quando madura; não se reaproveitam desfechos parciais.
3. O alfa é reservado para cada braço/estrato/mês; sondar repetidamente não renova o orçamento.
4. As políticas não recebem o efeito verdadeiro, que é usado somente para avaliação de perdas.
5. Sem censura, o limite robusto coincide com o CP convencional, verificado computacionalmente.
6. Sempre ativo com efeito benéfico e sempre suspenso com efeito nocivo atingem perda zero vs melhor política fixa nos mundos sem feedback.
7. Atraso de 3 meses, em vez de 1, mudou **de fato** a data de transição no teste de alta informação.
8. Censura informativa foi incluída como **violação** dos pressupostos do procedimento por casos completos, não como comprovação de robustez desse procedimento.

**Advertência:** cobertura empírica próxima de 100% resulta em grande parte de intervalos largos. Não constitui evidência de poder adequado nem uma garantia para censura informativa ou interferência.

## 6. Pendências bloqueantes após v0.4

| Pendente | Por que impede experimento confirmatório | Próxima decisão verificável |
|---|---|---|
| Modelo causal D→T→Y e desfecho registrado | A simulação atual colapsa alerta diretamente em Y | Inserir SCM para adesão, tratamento, WLST, registro e confusão |
| Política dinâmica causal com interferência | Δ direto pode ter sinal inverso ao valor da política | Estabelecer estimando de política e unidades de randomização por clusters |
| Censura informativa e eventos concorrentes | CP por casos completos pode inverter sinais | Comparar pior caso, IPCW sob hipóteses explícitas e análise de sensibilidade MNAR |
| Inferência eficiente sob adaptação | CP mensal é válido em cenário restrito, porém vacuoso | Contrastar A2IPW, inferência design-based e métodos não assintóticos dentro do desenho efetivo |
| Atrasos estocásticos e dependentes do estado | Atualmente atraso fixo, tempo máximo por bloco | Modelar atraso relacionado a Y, tratamento e estado sem vazamento temporal |
| Plano ético de sondagem e reentrada | Exposição experimental não é autorização clínica | Definir admissibilidade, revisão, limite de coortes e justificativa de risco |
| Regra de perdas normativas | Custo operacional 0,001 é hipotético; prognósticos não têm utilidade única | Pré-especificar análise de sensibilidade de pesos e gravidade, não margens arbitrárias |
| Registro de Fase 12 e comparadores fiéis | Não foi reexecutado AEGIS, SWM, Feng nem simulação antiga | Incorporar comparadores completos e repetir os resultados negativos históricos |

**NÃO AUTORIZADO:** experimento confirmatório, reivindicação de detecção de dano oculto, estudo clínico, declaração de superioridade ou manuscrito final.

## 7. Fontes primárias e escopo da leitura

Consultados registros, resumos e páginas de artigos; as provas completas destes trabalhos NÃO foram reconstituídas aqui:

- Cook, Mishler e Ramdas (2024), *Semiparametric Efficient Inference in Adaptive Experiments*: https://proceedings.mlr.press/v236/cook24a.html — alocação sequencial adaptativa, A2IPW, CS; NÃO implementados nesta versão.
- Sandoval et al. (2026), *On Nonasymptotic Confidence Intervals for Treatment Effects in Randomized Experiments*: https://arxiv.org/abs/2601.11744 — limites de amostra finita; não implica poder suficiente em grupos raros.
- Group sequential methods for interim monitoring of randomized clinical trials with time-lagged outcome (2022): https://pubmed.ncbi.nlm.nih.gov/36117235/ — inferência com resultados atrasados.
- Manski (2005), *Partial identification with missing data: concepts and findings*: https://doi.org/10.1016/j.ijar.2004.10.006 — identificação parcial de médias com dados ausentes.
- *Spillover effects in epidemiology: parameters, study designs and methodological considerations* (2018): https://academic.oup.com/ije/article/47/1/332/4583505 — distinção entre efeitos diretos e indiretos sob interferência.
- *Causal inference with interfering units for cluster and population level treatment allocation programs* (2019): https://pubmed.ncbi.nlm.nih.gov/30859545/ — estimandos de política sob interferência.

## 8. Reproduzir

Requer Python 3 com numpy, scipy e pandas (pandas é usado somente para construir este relatório).

    python kafka_v04_decision_sim.py --reps 1000 --highvolume --out .
    python build_report_v04.py

A rotina `test_invariants()` é chamada automaticamente. Os resultados são determinísticos com seed 20261110, salvo divergências numéricas de versões/bibliotecas. O CSV contém 210 linhas para auditoria de todos os cenários, inclusive os casos não decisivos.
'''
(P/'RELATORIO_KAFKA_III_V0_4.md').write_text(report,encoding='utf-8')
readme='''# KAFKA III v0.4 — pacote reprodutível\n\nConteúdo:\n- `RELATORIO_KAFKA_III_V0_4.md`: resultados, fórmulas, critérios e lacunas.\n- `kafka_v04_decision_sim.py`: motor de simulação e testes de invariantes.\n- `decision_summary_v0_4.csv`: 210 linhas de resultados por cenário, q e política.\n- `attrition_stress_v0_4.json`: diagnóstico de censura informativa.\n- `configuration_v0_4.json`: parâmetros, alocação alfa, flags de ausência de validação clínica.\n- `build_report_v04.py`: gerador do relatório.\n- `SHA256SUMS.txt`: resumos de integridade.\n\nReprodução: `python kafka_v04_decision_sim.py --reps 1000 --highvolume --out .` e depois `python build_report_v04.py`.\n\nEsta é uma simulação sintética metodológica: não é software médico nem autorização de exposição em pacientes.\n'''
(P/'README.md').write_text(readme,encoding='utf-8')
files=['README.md','kafka_v04_decision_sim.py','build_report_v04.py','decision_summary_v0_4.csv','attrition_stress_v0_4.json','configuration_v0_4.json','RELATORIO_KAFKA_III_V0_4.md']
manifest='\n'.join(f"{hashlib.sha256((P/p).read_bytes()).hexdigest()}  {p}" for p in files)+'\n'
(P/'SHA256SUMS.txt').write_text(manifest,encoding='utf-8')
files.append('SHA256SUMS.txt')
zpath=P.parent/'PACOTE_KAFKA_III_V0_4_PERDAS_E_ATRASOS.zip'
with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(P/p,arcname=f'kafka_iii_v0_4/{p}')
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
print('report size',len(report),'zip',zpath,zpath.stat().st_size)
