# 0001 — Plataforma de referência e dependências

Estado: aceita (fase 1).

## Contexto

O roadmap fixa Linux x86-64, Ubuntu 24.04 LTS e CPython 3.12 como plataforma de referência e pede versões de pacotes fixadas. A fase 1 só tem cálculo simbólico exato; nenhum caminho numérico em dupla precisão existe ainda.

## Decisão

- O pacote declara `requires-python = "==3.12.*"`. Outra versão do Python não instala, porque não foi homologada.
- `uv` gerencia o projeto. As dependências diretas ficam fixadas com `==` em `pyproject.toml`; o fechamento completo, com hashes, fica em `uv.lock`. A CI e a reprodução usam `uv sync --locked`, que falha se o lock divergir do manifesto.
- Dependência de execução: SymPy 1.14.0, que traz o mpmath. NumPy, SciPy e Pint não entram agora: nenhum código desta fase usa álgebra linear, integração numérica ou unidades compostas.
- Ferramentas de desenvolvimento: ruff 0.17.5 para lint e formatação, mypy 2.4.1 em modo estrito, pytest 9.2.0 e jsonschema 4.26.0 para os testes de contrato.
- Build com hatchling 1.33.0, também fixado.
- A CI roda em `ubuntu-24.04`. As actions são fixadas por SHA de commit: `actions/checkout` v7.0.1, `astral-sh/setup-uv` v10.3.3 com uv 0.13.5 e `actions/upload-artifact` v7.0.2.

## Licença

O arquivo `LICENSE` (GNU GPL versão 3) permanece como estava. Os metadados do pacote apontam para ele com `license-files` e usam o classificador GPLv3. A escolha entre "somente a versão 3" e "versão 3 ou posterior" cabe ao autor e não foi feita aqui.

## Consequências

Uma instalação limpa resolve os mesmos pacotes, nas mesmas versões. Atualizar uma dependência exige mudar `pyproject.toml` e `uv.lock` no mesmo commit e repetir a suíte. O registro da BLAS efetiva fica para a fase que introduzir o NumPy.

## Quando rever

Ao homologar outra plataforma, ao introduzir o caminho numérico (fase 3) ou quando uma dependência fixada receber correção de segurança.
