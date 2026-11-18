# Elétron em um poço infinito de 1 nm: derivação independente

Pergunta: qual é a energia do nível fundamental de um elétron de massa livre confinado em um poço unidimensional de largura 1 nm?

O oráculo vale para este modelo: paredes infinitas, potencial nulo dentro do poço e função de onda nula nas extremidades. Um poço finito, uma massa efetiva ou outro zero de energia são problemas diferentes.

## Derivação

Dentro do poço, 0 < x < L, a equação de Schrödinger independente do tempo é

$$-\frac{\hbar^2}{2m}\,\psi''(x) = E\,\psi(x), \qquad \psi(0)=\psi(L)=0.$$

Para E > 0 a solução geral é $\psi(x) = A\sin(kx) + B\cos(kx)$, com $k = \sqrt{2mE}/\hbar$. A condição em x = 0 dá B = 0. A condição em x = L exige $\sin(kL) = 0$, isto é, $kL = n\pi$ com n = 1, 2, 3, ... O valor n = 0 anula a função de onda e os negativos repetem os mesmos estados. E ≤ 0 só admite a solução nula.

Logo

$$E_n = \frac{\hbar^2 k^2}{2m} = \frac{n^2\pi^2\hbar^2}{2mL^2} = \frac{n^2 h^2}{8 m L^2}, \qquad \psi_n(x) = \sqrt{\tfrac{2}{L}}\,\sin\left(\frac{n\pi x}{L}\right).$$

A energia cresce com n² e cai com L². Dobrar a largura divide a energia por quatro; passar do primeiro para o segundo nível multiplica por quatro.

## Aritmética

| Grandeza | Valor | Origem |
| --- | --- | --- |
| h | `6.62607015e-34` J s | exata, definição do SI |
| m_e | `9.1093837139e-31` kg | CODATA 2022, u = `2.8e-40` kg |
| 1 eV | `1.602176634e-19` J | exata, definição do SI |
| L | `1e-9` m | 1 nm, valor nominal da pergunta |
| h² | `4.39048056327210225e-67` J² s² | exato |
| 8 m_e L² | `7.28750697112e-48` kg m² | exato |
| E_1 = h² / (8 m_e L²) | `6.024667394036591e-20` J | 16 algarismos |
| E_1 em eV | `0.3760301621048726` eV | 16 algarismos |

Com 10 algarismos significativos, **E_1 = 0.3760301621 eV**.

As contas foram feitas com frações exatas da biblioteca padrão do Python, sem importar `quantum_calculator`:

```python
from fractions import Fraction

h = Fraction("6.62607015e-34")
m_e = Fraction("9.1093837139e-31")
eV = Fraction("1.602176634e-19")
L = Fraction("1e-9")

energy_eV = h**2 / (8 * m_e * L**2) / eV
print(float(energy_eV))
```

A saída é `0.3760301621048726`.

## Segunda rota

A mesma energia sai de $E_1 = (hc)^2 / (8\, m_e c^2\, L^2)$ com valores tabelados em outras unidades: hc = `1239.841984332` eV nm, que decorre das constantes exatas h, c e e, e m_e c² = `510998.95069` eV (CODATA 2022). O quociente `1537208.146112311 / 4087991.60552` dá `0.37603016210616` eV. A diferença para a primeira rota é de 1,3 × 10⁻¹² eV, compatível com os 11 algarismos de m_e c².

## Tolerância

O teste compara com `0.3760301621` eV e aceita diferença absoluta de até `0.000000001` eV. O valor de referência está arredondado na décima casa, com erro de até 5 × 10⁻¹¹ eV, e a calculadora arredonda a fração exata uma única vez, na exibição, com outros 5 × 10⁻¹¹ eV no pior caso. A tolerância cobre a soma com margem de dez vezes.

Esse limite pega erro de fórmula, constante trocada e conversão de unidade errada. Ele não separa a edição CODATA 2018 da 2022: a massa do elétron de 2018 muda a energia em 5,1 × 10⁻¹⁰ eV. Por isso a edição das constantes é conferida à parte, por igualdade exata com os valores de `electron_box_1nm.expected.json`.

## Valores derivados

| Caso | Energia |
| --- | --- |
| n = 2, L = 1 nm | `1.504120648` eV |
| n = 1, L = 2 nm | `0.09400754053` eV |
| n = 1, L = 10 Å | igual ao caso de 1 nm, exatamente |

## Incerteza

Com massa e largura independentes, a propagação linear dá

$$\left(\frac{u(E)}{E}\right)^2 = \left(\frac{u(m)}{m}\right)^2 + \left(\frac{2\,u(L)}{L}\right)^2,$$

porque $\partial E/\partial m = -E/m$ e $\partial E/\partial L = -2E/L$. Para u(m) = `2.8e-40` kg e u(L) = `0.01` nm, a parcela da massa é `3.07e-10`, a da largura é `0.02` e u(E) = `0.0075` eV. A incerteza da largura domina por mais de sete ordens de grandeza.

## Fontes

- CODATA 2022, valores recomendados das constantes físicas fundamentais, NIST: https://physics.nist.gov/cuu/Constants/
- BIPM, *The International System of Units (SI)*, 9ª edição, 2019: constantes definidoras h, e e c.
- D. J. Griffiths e D. F. Schroeter, *Introduction to Quantum Mechanics*, 3ª edição, Cambridge University Press, 2018, seção 2.2.
