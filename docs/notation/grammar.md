# Referência da notação

O enunciado de um problema simbólico é um texto em uma de duas notações: texto simples (`"notation": "text"`) ou um subconjunto de LaTeX (`"notation": "latex"`). As duas produzem a mesma árvore tipada. O que a calculadora entendeu é sempre mostrado de volta, com o agrupamento e os produtos explícitos.

Um enunciado que admite duas leituras é recusado com o trecho apontado. Nada é corrigido em silêncio.

## Notação de texto

    enunciado  = expressão [ "=" expressão ]
    expressão  = termo { ("+" | "-") termo }
    termo      = "-" termo | produto
    produto    = potência { ("*" | "/" | justaposição) potência }
    potência   = primário [ "^" expoente ]
    expoente   = [ "-" ] primário
    primário   = número | "pi" | símbolo
               | "(" expressão ")"
               | função "(" expressão ")"
               | "diff" "(" expressão "," variável [ "," ordem ] ")"
               | "partial" "(" expressão "," variável [ "," ordem ] ")"
               | "integral" "(" expressão "," variável [ "," expressão "," expressão ] ")"
               | incógnita { "'" } [ "(" expressão ")" ]

| Construção | Exemplo | Leitura |
| --- | --- | --- |
| Soma e subtração | `x + y - a` | `(x + y) - a` |
| Sinal | `-x^2` | `-(x^2)` |
| Produto explícito ou por justaposição | `2 a x`, `a*x`, `(x + 1)(x - 1)` | produto, associado à esquerda |
| Divisão | `a*x/b` | `(a*x)/b` |
| Potência | `x^2`, `x^-2`, `x^(y + 1)` | o expoente é um primário, com sinal opcional |
| Função | `sin(x)`, `sqrt(x^2)` | argumento sempre entre parênteses |
| Derivada ordinária | `diff(x^2*sin(x), x)`, `diff(f, x, 2)` | derivada em relação a `x`, de ordem 1 ou a informada |
| Derivada parcial | `partial(x^2*y, x)` | os outros símbolos ficam fixos |
| Primitiva | `integral(1/x, x)` | integral indefinida em `x` |
| Integral definida | `integral(x^2, x, 0, 1)` | de 0 a 1 |
| Função incógnita | `y(t)`, `y'(t)`, `y'`, `y(0)` | sem argumento, vale no argumento declarado |
| Equação | `y' = -k y` | um único `=` |

## Subconjunto de LaTeX

| Construção | Exemplo |
| --- | --- |
| Fração | `\frac{a}{b}` |
| Potência | `x^{2}`, `x^2`, `x^{-2}` |
| Função | `\sin(x)`, `\cos\left(x\right)`, `\tan(x)`, `\exp(-x)`, `\ln(x)` |
| Raiz e módulo | `\sqrt{x}`, `\left\|x\right\|` |
| Produto | `a x`, `a \cdot x` |
| Letras gregas e pi | `\lambda`, `\omega_{0}`, `\pi` |
| Subscrito | `y_0`, `y_{0}`, `y_{in}` |
| Nome com mais de uma letra | `\mathrm{mass}` |
| Derivada | `\frac{d}{dx}\left(x^{2}\right)`, `\frac{d^{2}}{dx^{2}}(x^{3})` |
| Derivada parcial | `\frac{\partial}{\partial x}(x^{2} y)` |
| Derivada de função incógnita | `\frac{dy}{dt}`, `y'(t)` |
| Primitiva | `\int x^{2} \, dx` |
| Integral definida | `\int_{0}^{1} x^{2} \, dx` |
| Agrupamento | `( )`, `\left( \right)`, `{ }` |

Em LaTeX cada letra é um símbolo: `kt` é o produto de `k` por `t`. Os comandos de espaço `\,`, `\;`, `\:`, `\!`, `\quad` e `\qquad` são ignorados. Qualquer outro comando é recusado com `unsupported_operation`. LaTeX de exibição não é linguagem de execução: os comandos aceitos são só os desta tabela.

## Precedência

Da menor para a maior: igualdade, soma e subtração, sinal, produto e divisão, potência, primário. Soma e produto associam à esquerda. O sinal vale para o produto inteiro que o segue: `-a*b` é `-(a*b)`. Depois de `*` ou `/` um sinal precisa de parênteses: `a*(-b)`.

## Leituras recusadas por ambiguidade

| Entrada | Código | Como escrever |
| --- | --- | --- |
| `1/2x`, `a/b*c`, `a/b/c` | `ambiguous_division` | `(1/2)*x` ou `1/(2*x)` |
| `x^y^z` | `ambiguous_power` | `(x^y)^z` ou `x^(y^z)` |
| `k(t + 1)` com `k` símbolo comum | `ambiguous_application` | `k*(t + 1)`, ou declarar `k` como função |
| `sin x`, `\sin x`, `\frac{d}{dx} x^2 + 1` | `ambiguous_argument` | `sin(x)`, `\frac{d}{dx}\left(x^2 + 1\right)` |
| `x 2`, `2 3`, `y0` em LaTeX | `ambiguous_juxtaposition` | `x*2`, `x^2` ou `x_2` |

Em uma fração LaTeX não há ambiguidade: `\frac{1}{2} x` é `(1/2)*x`.

## Nomes

Símbolos, funções e unidades vivem em espaços separados.

- Um símbolo é declarado em `symbols` com papel (`variable`, `parameter` ou `function`), domínio e unidade. Um nome que aparece no enunciado sem declaração é recusado com `undeclared_symbol`.
- O nome tem letras, dígitos opcionais e um subscrito opcional: `x`, `x1`, `y_0`, `omega_0`. Em texto um nome pode ter várias letras; `kt` é um símbolo só, diferente de `k t`.
- As funções registradas são `sin`, `cos`, `tan`, `exp`, `ln`, `sqrt` e `abs`. `log` não é aceito, porque não diz a base.
- São reservados e não podem ser declarados: os nomes das funções, `pi`, `d`, `diff`, `partial` e `integral`. Não existe `e` reservado: a exponencial é `exp(x)`.
- Unidades só aparecem no campo `unit` de cada símbolo, nunca no enunciado. Um símbolo `m` não se confunde com o metro.

## Números

Ponto decimal, com dígitos dos dois lados: `1.5`, `0.25`. Em texto, notação científica com `e`: `1.5e3`, `2e-3`. Todo número vira uma fração exata. A vírgula separa argumentos; `1,5` é recusado. O literal tem até 64 caracteres e expoente de módulo até 99.

## Unicode e equivalentes textuais

| Unicode | Equivalente |
| --- | --- |
| `π` | `pi` |
| `λ`, `ω`, demais letras gregas | `lambda`, `omega`, ... |
| `·`, `⋅` | `*` |
| `−` | `-` |
| `√` | `sqrt` |
| `²`, `³`, demais dígitos sobrescritos | `^2`, `^3`, ... |
| `′` | `'` |

`lambda`, `λ` e `\lambda` são o mesmo símbolo.

## Limites

Enunciado de até 512 caracteres, 32 níveis de aninhamento, 200 nós na árvore e derivadas até a ordem 8. Passar de um deles é `budget_exceeded`, não um travamento.

## A árvore

A estrutura lida aparece na saída em três formas: texto canônico, LaTeX e uma forma estrutural entre parênteses. Para `diff(x^2*sin(x), x)`:

    diff(x^2*sin(x), x)
    \frac{d}{dx}\left(x^{2} \cdot \sin\left(x\right)\right)
    (derivative ordinary x 1 (multiply (power (symbol x) (number 2)) (sin (symbol x))))

Os nós são `number`, `pi`, `symbol`, `negate`, `add`, `subtract`, `multiply`, `divide`, `power`, as funções registradas, `unknown` (função incógnita, com ordem de derivação e argumento), `derivative`, `integral` e `equation`. O texto canônico e o LaTeX gerados são aceitos de volta como entrada e dão a mesma árvore.
