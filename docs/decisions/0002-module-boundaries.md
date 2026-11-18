# 0002 — Fronteiras entre módulos

Estado: aceita (fase 1).

## Contexto

O roadmap pede um aplicativo modular em que a interface não calcula física, o domínio não conhece bibliotecas e o verificador não reaproveita a saída interna do solver. A fase 1 precisa provar essa separação com um único problema, sem criar pastas vazias para as fases seguintes.

## Decisão

As dependências apontam para dentro: interfaces chamam casos de uso, casos de uso dependem de contratos do domínio, adaptadores e solvers implementam esses contratos.

| Pacote | Responsabilidade | Pode importar |
| --- | --- | --- |
| `domain` | Dimensões, grandezas exatas, fichas, contratos de problema e de resultado, diagnósticos, arredondamento | Biblioteca padrão |
| `catalog` | Fichas homologadas | `domain` |
| `application` | Validação guiada pela ficha, plano e coordenação da execução | `domain`, `catalog` |
| `solvers/symbolic` | Solução fechada com SymPy | `domain`, SymPy |
| `verification` | Verificadores por família de problema | `domain`, SymPy |
| `adapters/units` | Registro de unidades e edição das constantes | `domain` |
| `adapters/execution` | Manifesto do ambiente de execução | `domain` |
| `interfaces/serialization` | Leitura do documento de entrada, documentos de saída e esquemas JSON | `domain` |
| `interfaces/cli` | Comandos, formatos de saída e códigos de saída | Os demais, pela composição |

`composition.py` é o único lugar que monta adaptadores, solvers e casos de uso.

Regras cobradas por teste:

- `domain` só importa a biblioteca padrão. Objetos do SymPy não cruzam a fronteira do solver: o relatório carrega frações exatas e texto.
- SymPy só aparece em `solvers` e `verification`.
- A validação não tem ramificação por problema. Ela lê da ficha as entradas, as hipóteses e as saídas. Uma área nova entra com ficha, método, verificador e caso de referência.
- O verificador do poço recebe o problema validado e a energia relatada e substitui a autofunção na equação de Schrödinger. Ele não chama a fórmula fechada do solver.
- O texto do usuário nunca chega a `eval`, `exec`, `sympify` ou `parse_expr`. Os números entram por uma gramática de literais e viram `Fraction`; os nós do SymPy são criados pelo código.
- CLI e futura API compartilham `interfaces/serialization`, então o JSON de saída tem um único codificador.

## O que ficou de fora

`notation`, `adapters/storage`, o controle de processos em `adapters/execution`, `interfaces/api` e `web` não existem ainda. Serão criados quando houver comportamento real para eles, como o roadmap determina.

## Quando rever

Se uma segunda ficha exigir regra de entrada que a ficha atual não expressa, ou quando a API local precisar de contratos que o codificador atual não cobre.
