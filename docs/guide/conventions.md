# Convenções

Como a calculadora trata unidades, constantes, números, incerteza e o vocabulário dos resultados. As decisões e os motivos estão em `docs/decisions/` no repositório; aqui fica o que você precisa saber para ler uma resposta.

## Nada é presumido

A calculadora não escolhe hipótese, massa, unidade nem resolução numérica. Uma hipótese ausente é entrada inválida; uma hipótese com outro valor é outro problema, fora do catálogo. A massa é um valor com unidade ou uma constante citada pelo nome, como `electron_mass`. Uma ficha numérica sem o bloco `numerics` é recusada.

## Unidades

Toda grandeza é convertida uma vez, na leitura, para unidades coerentes do SI. O cálculo só vê valores coerentes, e a unidade de exibição é aplicada na saída. A entrada original fica no registro, com o SHA-256 do documento.

Unidades aceitas: kg, g e mg; m, mm, μm, nm, Å e pm; s, ms, μs, ns, ps e fs; J, eV, meV, keV e MeV. `angstrom`, `um` e `us` valem como grafias ASCII de Å, μm e μs. Uma unidade com a dimensão errada é recusada com o campo apontado: uma largura em segundos não é convertida nem corrigida.

Os problemas de Schrödinger numéricos são resolvidos em unidades reduzidas de comprimento, energia e tempo. Essas escalas aparecem nos parâmetros efetivos do resultado, e as unidades voltam na saída.

## Constantes

Edição CODATA 2022.

| Constante | Símbolo | Valor | Natureza |
| --- | --- | --- | --- |
| `planck_constant` | h | 6.62607015e-34 J s | exata, definição do SI |
| `electron_volt` | eV | 1.602176634e-19 J | exata, definição do SI |
| `electron_mass` | m_e | 9.1093837139e-31 kg | medida, u = 2.8e-40 kg |

O registro de cada execução guarda a edição e o valor de cada constante usada. A incerteza de uma constante medida fica registrada, mas só é propagada quando você a declara como incerteza de entrada.

## Números

Nas fichas de expressão fechada e nos enunciados, inteiros e racionais ficam exatos até a exibição. `1e-9` vira uma fração exata, e `"1/3"` é aceito como texto. O valor exibido é a fração arredondada para N algarismos significativos, metade para o par (`half_even`). N vem de `requested.significant_digits`: o padrão é 10 e o máximo, 34.

Nas fichas numéricas a resposta é um número em dupla precisão, marcado `approximate`, com o erro estimado e a origem dele escritos ao lado.

Todo número usa ponto decimal e notação científica com `E`, para poder ser colado em outra ferramenta. No JSON, um valor exato sai como texto, com numerador e denominador, porque um leitor de JSON o converteria para binário.

Os algarismos exibidos não declaram precisão experimental. Dez algarismos em `E = 0.3760301621 eV` dizem que a conta foi feita com essa precisão no modelo, não que a largura do seu poço é conhecida com dez algarismos.

## Incerteza

Sem incerteza declarada, o resultado traz "incerteza não avaliada", nunca zero. Para propagar, declare a hipótese de covariância e a incerteza-padrão de cada grandeza:

    "uncertainty": {
      "covariance": "independent",
      "standard_uncertainties": {
        "mass": {"value": "2.8e-40", "unit": "kg"},
        "width": {"value": "0.01", "unit": "nm"}
      }
    }

Só `independent` está homologada. A propagação é linear, de primeira ordem, com as derivadas calculadas simbolicamente nos valores nominais. A incerteza sai com 2 algarismos significativos. Para o exemplo acima, `reference_cases/quantum/electron_box_1nm_uncertainty.json` dá u(E) = 0.0075 eV, 2,0% do valor.

As fichas numéricas não propagam incerteza experimental. O erro que elas relatam é o do método: malha, passo, corte do domínio ou tolerância do integrador.

## Vocabulário de um resultado

Natureza: `exact` quando a resposta vem de uma expressão fechada ou de uma manipulação simbólica; `approximate` quando vem de um método numérico.

Verificação:

| Estado | Significado | Código de saída de `solve` |
| --- | --- | --- |
| `passed` | todas as checagens aplicáveis passaram | 0 |
| `conditional` | a resposta vale sob uma condição que a entrada não fixa, e a condição é listada | 5 |
| `inconclusive` | uma checagem não chegou a uma decisão; há evidência numérica, não prova | 5 |
| `failed` | uma checagem reprovou a resposta ou a candidata | 5 |

O cálculo ter terminado não é aprovação científica. Cada checagem diz o tipo de evidência que oferece: `proof` é uma demonstração simbólica, `consistency_test` é uma conferência de dimensão ou de estrutura e `numerical_evidence` é uma comparação numérica com tolerância. Concordância em pontos amostrados nunca é relatada como prova.

Uma checagem que a ficha não faz aparece como "não realizada", com o motivo. A lista do que não foi conferido faz parte do resultado.
