# Casos de referência

Cada caso é uma entrada que o CLI resolve e um oráculo escrito sem chamar o código sob teste.

    reference_cases/quantum/
      electron_box_1nm.json                        entrada
      electron_box_1nm.expected.json               valor nominal, unidade, tolerância e fontes
      electron_box_1nm.derivation.md               derivação e aritmética independentes
      electron_box_1nm_uncertainty.json            mesma entrada com incertezas independentes
      electron_box_1nm_uncertainty.expected.json   incerteza esperada
      rejected/                                    entradas que devem ser recusadas
        expectations.json                          categoria, código e campo esperados

Contrato de reprodução da fase 1:

    qcalc validate reference_cases/quantum/electron_box_1nm.json
    qcalc solve reference_cases/quantum/electron_box_1nm.json --format json

Regras:

- O valor esperado vem de uma fonte ou de uma derivação registrada neste diretório. Nunca da saída do método que ele confere.
- A tolerância vem acompanhada do motivo. Ela testa a implementação, não a precisão de um experimento.
- Cada entrada em `rejected/` difere do caso aceito por um único defeito, para que o diagnóstico esperado seja inequívoco.
