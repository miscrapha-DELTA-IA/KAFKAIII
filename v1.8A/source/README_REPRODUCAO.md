# KAFKA III v1.8A — Reprodução

Esta é uma subetapa exploratória de síntese conceitual e benchmark reduzido, **não um ensaio clínico nem um teste confirmatório independente**.

## Requisitos
Python 3.10+, numpy, scipy, pandas.

## Reproduzir os testes
`python -m unittest -q test_v18a.py`

## Reproduzir bateria principal
`python kafka_v18a_map.py --reps 400 --seed 18082026 --output outputs_recheck`

## Reproduzir conferência adicional (exploratória)
`python kafka_v18a_map.py --reps 400 --seed 18182026 --output outputs_replication_recheck`

## Mapa descritivo de evidência
`python posthoc_mapa_zonas.py` (requer executar da pasta atual)

## Arquivos
- `PROTOCOL_PRE_SIMULACAO.md`: protocolo fixado ANTES da bateria.
- `FREEZE_SHA256_BEFORE_RUN.txt`: hashes dos três arquivos principais antes da bateria.
- `kafka_v18a_map.py`: módulo de geração e políticas.
- `test_v18a.py`: testes de unidade.
- `RELATORIO_KAFKA_III_V1_8A.md`: síntese científica.
- `outputs/replicacoes.csv`: trajetórias por política (108 mil linhas).
- `outputs/resumo.csv`: agregação das políticas por família e b.
- `outputs/diferencas_pareadas.csv`: diferenças pareadas, intervalos Monte Carlo DESCRITIVOS.
- `outputs/diagnostico_amostras.csv`: médias de amostragem e observação.
- `outputs/mapa_zonas_posthoc.csv`: análises de zona cinzenta feitas após a bateria.
- `outputs_replication`: nova semente, após a primeira análise, ainda exploratória.

Observação: `kafka_v18a_map.py` não é substituto do SCM clínico v0.5B/v1.6. O experimento é sobre fronteiras de decisão e observabilidade. Os cenários têm pesos iguais por convenção ilustrativa, não por prevalência clínica.
