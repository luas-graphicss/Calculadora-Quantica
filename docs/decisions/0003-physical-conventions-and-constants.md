# 0003 — Convenções físicas, unidades e constantes

Estado: aceita (fase 1).

## Unidades e dimensões

- O domínio representa a dimensão de uma grandeza pelos expoentes de massa, comprimento e tempo. Energia é derivada (M L^2 T^-2). Carga elétrica ainda não é dimensão: o elétron-volt entra pelo seu equivalente exato em joules.
- Toda grandeza é convertida uma vez, na fronteira, para unidades coerentes do SI e guardada como fração exata. O solver só recebe valores coerentes. A unidade de exibição é aplicada na saída.
- A entrada original fica preservada no registro da execução, junto com o SHA-256 do documento.
- O registro de unidades é próprio, versionado (`1.0.0`) e fica em `adapters/units`. Ele cobre kg, g e mg; m, mm, μm, nm, Å e pm; s, ms, μs, ns, ps e fs; J, eV, meV, keV e MeV, todos com fator racional exato.
- O roadmap cita o Pint como exemplo de registro. Ele não foi adotado nesta fase porque seu registro padrão traz constantes próprias e aritmética em ponto flutuante, o que quebraria a regra de preservar racionais. Rever na fase 2, quando a notação precisar de unidades compostas.
- Símbolos de unidade passam por normalização Unicode NFKC. `angstrom`, `um` e `us` são aceitos como grafias ASCII de Å, μm e μs.

## Constantes

Edição: CODATA 2022.

| Identificador | Símbolo | Valor | Natureza | Fonte |
| --- | --- | --- | --- | --- |
| `planck_constant` | h | `6.62607015e-34` J s | exata, definição do SI | https://physics.nist.gov/cgi-bin/cuu/Value?h |
| `electron_volt` | eV | `1.602176634e-19` J | exata, definição do SI | https://physics.nist.gov/cgi-bin/cuu/Value?evj |
| `electron_mass` | m_e | `9.1093837139e-31` kg | medida, u = `2.8e-40` kg | https://physics.nist.gov/cgi-bin/cuu/Value?me |

- Constantes do catálogo, parâmetros do usuário e unidade de exibição são campos separados da entrada e do registro. Uma constante só é usada quando o método a exige ou quando a entrada a cita pelo identificador.
- O registro da execução guarda a edição e o valor de cada constante usada. Trocar de edição é uma mudança de versão do pacote, não uma atualização silenciosa.
- A incerteza-padrão de uma constante medida fica registrada, mas não é propagada por conta própria.

## Modelo e hipóteses

- O programa não escolhe hipótese. A ficha do poço exige a confirmação explícita de paredes infinitas, potencial interno nulo e função de onda nula nas extremidades. Hipótese ausente é entrada inválida; hipótese com outro valor é problema não suportado.
- A massa é sempre explícita: um valor com unidade ou a referência a `electron_mass`. Não existe massa padrão.
- Massa e largura devem ser estritamente positivas e o nível deve ser um inteiro positivo.

## Incerteza

- Sem incerteza declarada, o resultado traz "incerteza não avaliada". Nunca zero.
- Com incerteza, a entrada declara a hipótese de covariância. Só `independent` está homologada. Todas as grandezas de entrada precisam de incerteza-padrão; zero declara que o valor é tratado como exato.
- A propagação é linear, de primeira ordem: u(E)^2 é a soma de (dE/dx_i)^2 u(x_i)^2, com as derivadas calculadas simbolicamente e avaliadas nos valores nominais.
- Os algarismos do resultado nominal não declaram precisão experimental.

## Quando rever

Ao adicionar a primeira grandeza com carga, temperatura ou quantidade de matéria; ao adotar unidades compostas; quando sair uma nova edição CODATA.
