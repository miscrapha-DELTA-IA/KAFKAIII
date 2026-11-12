# KAFKA III — Subetapa v1.7-L: checagem independente dos limites L1–L3

Arquivos: `RELATORIO_AUDITORIA_L1_L3.md` (relatório), `auditar_L1_L3.py` (reprodução), `test_limites.py` (12 testes), `amostras_exposicao.csv`, `precisao_um_braco.csv`, `poder_e_efeito_causal.csv`, `minimax_L3.csv`, `configuracao.json`, `resultado_execucao.txt`.

Execute com Python 3 e numpy/scipy/pandas:

```
python auditar_L1_L3.py
python -m unittest test_limites.py -v
```

O programa testa apenas um benchmark i.i.d. estacionário de uma análise por conjunto de dados; **não** é a validação confirmatória da política dinâmica v1.6 e **não** implementa desfechos atrasados ou censura informativa.
