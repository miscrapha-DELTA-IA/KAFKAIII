# KAFKA III v0.5C — Reprodução

**Pesquisa sintética exploratória; não é software clínico.**

## Estrutura

O módulo `v0_5c/kafka_v05c_decision.py` importa o SCM **sem modificá-lo** de `v0_5b/kafka_v05b_scm.py`. Ambas as pastas precisam existir lado a lado após extrair o pacote.

## Requisitos

Python 3.10+, NumPy e SciPy.

## Comandos

Entre na pasta `v0_5c`:

```bash
python -m pip install numpy scipy
python reproduce_all_v05c.py --full
```

O comando acima recria tanto a bateria principal de q=5% quanto as sensibilidades de q=1% e 2%, e gera todas as tabelas descritivas. Para teste rápido (2 replicações), execute `python reproduce_all_v05c.py` sem `--full`. Isso substitui as saídas anteriores na pasta extraída.

## Arquivos

- `RELATORIO_KAFKA_III_V0_5C.md`: interpretação científica, limitações e tabelas principais.
- `kafka_v05c_decision.py`: controlador, SCM importado e perda por política.
- `test_kafka_v05c.py`: 16 testes de regras/invariantes.
- `analyze_v05c.py`: gera `analysis_summary_v0_5c.json` e tabelas descritivas.
- `main`: resultados 9 × 7 × 25, `q=0.05`.
- `q01`, `q02`: sensibilidade para dois cenários e `q=0.01,0.02`.
- `stress_*_reachability.json`: verificações não confirmatórias de transições com exposição e tamanhos amostrais artificialmente elevados.

## Prevenção de extrapolações

O sinal do efeito individual não identifica o valor da política hospitalar quando há interferência. A certificação do desenho é fornecida pelo pesquisador no simulador; não é um detector de confundimento ou erro de rótulo. Intervalos muito largos e decisões inconclusivas são resultados válidos. O gatilho de suspensão externa é **programado**, e não descoberto pelo algoritmo.
