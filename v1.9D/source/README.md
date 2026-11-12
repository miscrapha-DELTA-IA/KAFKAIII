# KAFKA III — Pacote de continuação v1.9D

Pacote independente e reproduzível para o desafio metodológico do v1.9C. É uma **nova bateria v1.9D**, NÃO reconstrução completa ou rerun dos 192 casos v1.9C.

## Conteúdo

- `RELATORIO_KAFKA_III_V1_9D.md` — relatório completo em português, definição do objetivo, perdas, resultados, provas condicionais, falsificadores e decisão editorial.
- `experiment_v1_9d.py` — enumerador determinístico de árvore de crenças, planejadores e máquina de auditoria.
- `test_independent.py` — verificação numérica em 201 pontos por cenário, propriedade de malha e autorização externa.
- `results_model.csv` — 12 cenários do modelo assumido.
- `results_misspecification.csv` — 27 testes adversos (3 cenários × 3 priors verdadeiros × 3 precisões verdadeiras).
- `audit_discretization.csv` — viabilidade contínua versus malha regular.
- `governance_audit.csv` — evolução do estado de revisão/contingência.
- `PROTOCOLO_CANDIDATO_V1_9E.md` — próximo protocolo, ainda não preregistrado.
- `metadata.json` — escopo, premissas e proveniência.
- `TESTS_OK.txt`, `independent_tests_log.txt` — verificações.
- `run_log.json` — resultados completos exportados no último run.

## Reproduzir

```bash
cd kafka_iii_v1_9d
python experiment_v1_9d.py > run_log.json
python test_independent.py > independent_tests_log.txt
```

Requer Python 3.10+ padrão. Não há dados de pacientes, acesso à rede, dependências externas, aleatoriedade nem execução assíncrona.

## Leitura essencial

O ótimo do modelo teve perda menor que a regra míope no modelo corretamente especificado em alguns cenários, e perda maior após especificação incorreta em **15 de 27** células adversas. **Isso não demonstra originalidade, eficácia clínica ou superioridade de KAFKA sobre um benchmark Bayes.**
