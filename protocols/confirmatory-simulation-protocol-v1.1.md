# KAFKA III: protocolo confirmatório de simulação (v1.1, pré-execução)

**Versão:** 1.1 (corrige a contagem de comparadores da v1.0; ver seção 11).  
**Status:** protocolo escrito antes de qualquer execução confirmatória. Estudo de simulação; não é avaliação clínica. Resultados negativos serão reportados integralmente.

**Autor:** Raphael Di Giorgio (pesquisador independente, sem afiliação institucional nesta pesquisa).  
**Data de registro:** 12/11/2026.

## 1. Pergunta confirmatória

Uma política de autoridade KAFKA III, nas condições pré-especificadas abaixo, obtém perda acumulada menor que cada comparador forte em todas as famílias de cenários listadas na seção 3?

**Direção:** menor perda.  
**Métrica primária:** perda acumulada por 1.000 elegíveis.

## 2. Estimando e comparadores

**Estimando de decisão:** efeito de exibição por bloco de exposição, como em `manuscript_v0_3.md`. Não se misturam estimandos.

**Comparadores obrigatórios (8, contados individualmente),** com a mesma informação, ações, restrições e custos do KAFKA III:

1. Política sempre ativa.
2. Política sempre suspensa.
3. Sentinela fixa com retenção de 1%.
4. Sentinela fixa com retenção de 2%.
5. Sentinela fixa com retenção de 5%.
6. Regra de suspensão por evidência histórica.
7. Regra estática segura (mesma formulação e informação do KAFKA III).
8. Planejador Bayes multietapas com o mesmo modelo, ações, custos e restrições.

**Oráculo:** usado apenas para calcular arrependimento, nunca como comparador de decisão.

## 3. Famílias de cenários (fixadas)

1. Nulo.
2. Benefício moderado.
3. Benefício severo.
4. Dano moderado.
5. Dano severo.
6. Reversão de dano para benefício.
7. Reversão de benefício para dano.
8. Reversão após sondagem positiva.
9. Atraso e censura informativa.
10. Violação do limite temporal assumido.
11. Ausência de positividade.
12. Interferência em desenho independente.

**Y = 12 famílias.** Nenhuma família será adicionada ou removida depois do registro.

## 4. Decisões normativas (decisão do autor, 12/11/2026)

- **Razão de perdas, caso principal:** 1:1 (dano por manter alerta nocivo = dano por suspender alerta benéfico). Motivo: não há base para assumir que um tipo de erro é mais grave; 1:1 não favorece nenhum dos lados.
- **Sensibilidade:** 2:1 e 5:1, com dano por manter como o erro mais caro.
- **Margens de não inferioridade (h):** 2, 5 e 10 pontos percentuais. A margem de 5 pp é o caso principal apenas por já ter sido usada no manuscrito. É uma convenção, não um limiar clínico validado.

Estas decisões são do autor. Não foram derivadas dos resultados exploratórios.

## 5. Critério de sucesso e de falsificação (escrito antes)

- **Sucesso naquela família:** o KAFKA III tem perda menor que todos os oito comparadores em todas as três margens h e nas duas razões principais (1:1 e 2:1), com intervalo de Monte Carlo corrigido para as comparações feitas excluindo zero.
- **Sucesso global:** sucesso em X = 12 de Y = 12 famílias. Uma única falha invalida a alegação de superioridade geral.
- **Falsificação:** se o KAFKA III perder de qualquer comparador em qualquer família, com intervalo excluindo zero, a alegação de superioridade naquela família é rejeitada.
- **Resultado negativo:** se houver falsificação, o manuscrito reporta o resultado negativo, sem reinterpretação.

## 6. Métricas

- Perda acumulada por 1.000 elegíveis;
- arrependimento em relação ao oráculo;
- probabilidade de dano excessivo;
- tempo para suspensão correta;
- tempo para reentrada correta;
- custo de sondagem;
- frequência de decisões erradas.

## 7. Sementes e reprodutibilidade

- **Sementes confirmatórias** (novas; não usadas em nenhuma exploração anterior): `20261201`, `20261202`, `20261203`, `20261204`, `20261205`.
- Números aleatórios comuns entre todos os comparadores dentro de cada semente.
- **Sementes já usadas na exploração e proibidas neste teste:** `20261109`, `20261110`, `18082026`, `18182026`.
- Réplicas por semente e por família: a definir no código, mas fixas antes da execução e declaradas no README.
- Este protocolo é gravado com SHA-256 antes de qualquer execução.

## 8. Análise estatística

- Comparações pareadas, com intervalos de Monte Carlo corrigidos para o número total de comparações declarado (**8 comparadores × 12 famílias × 3 margens × 2 razões = 576 contrastes**).
- Todas as famílias são relatadas, inclusive as adversas.
- Não há ajuste de cenários nem de parâmetros depois do registro.

## 9. Declarações obrigatórias

As seguintes declarações deverão constar dos materiais do estudo e de sua divulgação:

- “Estudo confirmatório de simulação; não é avaliação clínica.”
- “Resultados negativos serão reportados integralmente.”
- “Nenhuma alegação de superioridade será feita fora das famílias pré-especificadas.”
- “A exploração anterior (v1.8A, v1.9E, v1.9G) não é usada como evidência confirmatória.”

## 10. Pendências declaradas

- **Código do simulador confirmatório:** a ser escrito e testado contra este protocolo antes da execução.
- **Número de réplicas por semente e por família:** a ser fixado no código e registrado no README antes da execução.

## 11. Registro de emenda (v1.0 para v1.1)

- **Motivo:** a v1.0 dizia “seis comparadores” mas listava oito estratégias distintas (a sentinela de 1%, 2% e 5% contava como três). Os 432 contrastes eram consistentes com seis, não com a lista.
- **Correção:** oito comparadores, enumerados individualmente. Total de contrastes: **8 × 12 × 3 × 2 = 576**.
- **Momento:** emenda feita antes de qualquer código confirmatório e antes de qualquer execução. Nenhum resultado foi produzido.
- **O que não mudou:** as doze famílias, as cinco sementes, as margens de 2, 5 e 10 pp, a razão 1:1 principal e a regra de sucesso e falsificação.
- **Hash da v1.0 (`fa5a3c97...`):** preservado como registro histórico. O protocolo vigente é a v1.1.
