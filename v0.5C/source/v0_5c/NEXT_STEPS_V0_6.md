# KAFKA III — Ordem de implementação v0.6

**Não executar como ensaio confirmatório nem iniciar o manuscrito de resultados.**

1. **Auditar v0.5C de forma independente.** Reproduzir a grade, os 16 testes, verificar os casos em que a inferência é desligada e reconciliar decisões com maturação de coortes.
2. **Definir estimando para variação temporal.** Escolher separadamente: efeito no bloco, média histórica pré-especificada, valor de política por hospital. Não utilizar uma média pooled ingênua como estimativa do efeito corrente.
3. **Plano inferencial v0.6.** Comparar intervalos binários exatos, estimadores de efeito estratificados e AIPW/CS adequadamente justificados; gastar alfa de modo pré-especificado. Estimar o tamanho necessário para detectar danos menores e para autorizar reentrada.
4. **Analisar imputação/censura.** Adicionar chegadas assíncronas observáveis, mecanismos de perda de seguimento, limites de identificação parcial e análises de sensibilidade sob MNAR/erro de rótulo.
5. **Separar interferência.** Implementar múltiplos hospitais com randomização de política por cluster (ou estudo de validade do estimando com desenho mais apropriado), não usar CP individual para inferir valor hospitalar.
6. **Módulo normativo.** Implementar, como comparador e não como decisão clínica automática, a escolha entre manter/suspender/sondar com custos explícitos e análise de valor da informação; declarar condições de permissão ética.
7. **Comparadores fiéis.** Mapear os respectivos estimandos de Kim, Feng, AEGIS e SWM; usar rótulos que não insinuem equivalência entre modelos diferentes.
8. **Congelar protocolo confirmatório.** Definir sementes independentes, comparadores, desfechos e critérios que possam refutar superioridade ou identificar danos da própria proteção.
