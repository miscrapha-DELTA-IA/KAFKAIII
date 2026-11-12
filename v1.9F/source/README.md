# KAFKA III v1.9F — Etapa 1

Este pacote contém a auditoria metodológica, os dois módulos de código originais usados como dependência e a reimplementação independente da regra segura v1.8A. Não substitui os pacotes originais completos.

Requisitos: Python 3.10+, numpy, pandas, scipy.

Na pasta do pacote:

```bash
python audit_baseline_v1_9f.py
```

Resultado esperado: 129600 decisões idênticas; 112690 divergências em relação a e=0; 111570 violações do limite de risco v1.8A caso e=0 fosse imposto.

Atenção: software exploratório, sem validação clínica ou confirmação independente.
