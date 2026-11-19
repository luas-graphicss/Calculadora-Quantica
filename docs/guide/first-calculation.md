# Primeiro cálculo

Ao fim deste guia você terá a energia do nível fundamental de um elétron em um poço infinito de 1 nm, com a verificação aprovada, e terá repetido o cálculo com 2 nm para comparar as duas respostas. Nenhum passo pede programação.

Os comandos supõem que `qcalc` está no `PATH`. Se não estiver, use o caminho da instalação, como `~/quantum-calculator/bin/qcalc`.

## Pela bancada

    qcalc serve

O comando imprime o endereço da bancada e o caminho do arquivo de acesso, e abre esse arquivo no navegador:

    Bancada em http://127.0.0.1:40701
    Arquivo de acesso: /home/ana/.local/share/quantum-calculator/abrir-calculadora.html
    Abra o arquivo de acesso no navegador para entrar. Ctrl+C encerra a bancada.

Se o navegador não abrir sozinho, abra você o arquivo indicado. Uma aba aberta direto no endereço mostra "Sessão não aberta": é o arquivo de acesso que entrega à página o segredo daquela execução da bancada.

1. Em **Problemas**, escolha "Qual é a energia de uma partícula confinada em um poço infinito?". As fichas aparecem pela pergunta física, não pelo nome do método.
2. Em "Hipóteses do modelo", confirme as três: paredes infinitas, potencial interno nulo e função de onda nula nas extremidades. Em "Grandezas", informe a massa do elétron, a largura de 1 nm e o nível 1. Em "Resposta pedida", escolha eV. Nenhum desses campos tem valor padrão.
3. **Conferir interpretação** mostra como a entrada foi lida e o plano de cálculo, sem calcular. Confira a largura convertida, `L = 1E-9 m`, e a massa, `m = 9.1093837139E-31 kg`. Uma entrada com defeito é recusada aqui, com cada problema apontado no campo em que está.
4. **Confirmar e calcular** cria a execução. A resposta vem primeiro:

       E = 0.3760301621 eV

   Abaixo ficam "Problema e hipóteses", "Método", "Precisão", as verificações, "Limitações" e "Reprodução e comparação". Leia o estado da verificação antes de usar o número: "verificação aprovada" é o único que autoriza a resposta sem ressalva.
5. **Alterar e recalcular**, com a largura em 2 nm, cria uma segunda execução ligada à primeira: `E = 0.09400754053 eV`.
6. Em **Histórico**, marque as duas execuções e compare. A comparação lista a largura, de 1 para 2, e a razão 0.25 entre as respostas, que é o que a expressão `E = h^2 n^2 / (8 m L^2)` prevê quando a largura dobra.

Trocar a unidade de exibição para meV ou J converte o valor guardado; nenhum cálculo é refeito.

## Pelo terminal

Os mesmos dois passos, a partir da pasta que contém `reference_cases/`:

    qcalc validate reference_cases/quantum/electron_box_1nm.json
    qcalc solve reference_cases/quantum/electron_box_1nm.json

`validate` mostra a leitura e o plano. `solve` responde nas duas primeiras linhas:

    E = 0.3760301621 eV
    resultado exact; 10 algarismos significativos, arredondamento half_even; verificação: passed

Depois vêm o problema, as hipóteses, os parâmetros em unidades do SI, as constantes com edição e fonte, a memória de cálculo, a incerteza, a verificação, as limitações e o ambiente. Com `--format json` o mesmo conteúdo sai como um registro versionado.

A entrada é este arquivo. Para o poço de 2 nm, copie-o e troque `"value": 1` por `"value": 2`:

    {
      "schema_version": "1.0",
      "problem": "quantum.infinite_square_well.energy_level",
      "hypotheses": {
        "walls": "infinite",
        "interior_potential": "zero",
        "boundary_wavefunction": "zero"
      },
      "parameters": {
        "mass": {"constant": "electron_mass"},
        "width": {"value": 1, "unit": "nm"},
        "level": 1
      },
      "requested": {"quantity": "energy", "unit": "eV", "significant_digits": 10}
    }

## Como conferir sem a calculadora

A memória de cálculo mostra cada passo com até 34 algarismos, para a conta poder ser refeita à mão ou em outra ferramenta:

    1. Expressão fechada dos níveis de energia: E_n = h**2*n**2/(8*L**2*m)
    2. Numerador em unidades coerentes do SI: h**2*n**2 = 4.39048056327210225E-67 J^2 s^2
    3. Denominador em unidades coerentes do SI: 8*L**2*m = 7.28750697112E-48 kg m^2
    4. Energia em unidades coerentes do SI: h**2*n**2/(8*L**2*m) = 6.024667394036591229315698043602203E-20 J (arredondado)
    5. Conversão para eV: divisão por 1.602176634E-19 J/eV

`reference_cases/quantum/electron_box_1nm.derivation.md` traz a mesma conta feita de forma independente, com as constantes CODATA 2022 e a tolerância usada na homologação.

## Quando a resposta não é aprovada

Peça os três primeiros níveis do mesmo poço por diferenças finitas, com uma malha grossa demais:

    qcalc solve reference_cases/numerical/electron_box_1nm_coarse.json

O comando calcula, mas termina com código 5 e diz por quê:

    inconclusive [numerical_evidence] mesh_refinement
      observado: ordem observada entre 1.746 e 1.972 com 4, 8 e 16 subintervalos: a malha não está no regime assintótico e não é declarada convergida

Um número acompanhado de `inconclusive`, `conditional` ou `failed` não é uma resposta aprovada. `diagnostics.md` explica cada estado.
