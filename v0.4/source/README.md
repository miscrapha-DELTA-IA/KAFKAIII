# KAFKA III v0.4 — pacote reprodutível

Conteúdo:
- `RELATORIO_KAFKA_III_V0_4.md`: resultados, fórmulas, critérios e lacunas.
- `kafka_v04_decision_sim.py`: motor de simulação e testes de invariantes.
- `decision_summary_v0_4.csv`: 210 linhas de resultados por cenário, q e política.
- `attrition_stress_v0_4.json`: diagnóstico de censura informativa.
- `configuration_v0_4.json`: parâmetros, alocação alfa, flags de ausência de validação clínica.
- `build_report_v04.py`: gerador do relatório.
- `SHA256SUMS.txt`: resumos de integridade.

Reprodução: `python kafka_v04_decision_sim.py --reps 1000 --highvolume --out .` e depois `python build_report_v04.py`.

Esta é uma simulação sintética metodológica: não é software médico nem autorização de exposição em pacientes.
