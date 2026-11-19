# Diagnóstico

O que cada recusa, código de saída e falha quer dizer, e o que fazer. A regra geral: quando a calculadora não consegue defender um número, ela diz o motivo no lugar do número.

## Códigos de saída do `qcalc`

| Código | Significado | O que fazer |
| --- | --- | --- |
| 0 | Concluído; em `solve`, verificação `passed` | usar o resultado |
| 1 | O arquivo de entrada não pôde ser lido | conferir o caminho e a permissão |
| 2 | Uso incorreto da linha de comando | `qcalc COMANDO --help` |
| 3 | `invalid_input`: a entrada tem defeito | corrigir o campo apontado |
| 4 | `unsupported_problem`: o problema é outro, fora do catálogo | ver `qcalc catalog` e `methods.md` |
| 5 | Resultado calculado, mas a verificação não passou | ler a checagem que não passou; ver abaixo |
| 6 | `ambiguous_input`: o enunciado ou a ficha admite mais de uma leitura | fixar a leitura com parênteses ou com o campo `problem` |
| 7 | `budget_exceeded`: o enunciado, o pedido ou o cálculo passou de um limite | reduzir o pedido ou aumentar `--time-limit`; ver `operational-limits.md` |
| 8 | O processo de cálculo terminou sem devolver resultado | repetir; se persistir, relatar com a entrada |
| 9 | `non_convergent`: o método não convergiu ou deu valor não finito | rever o problema; nenhuma iteração parcial é resposta |
| 10 | A bancada não foi iniciada | ler o motivo impresso: a porta não pôde ser aberta ou a pasta de dados não pôde ser usada |
| 11 | A cópia ou a restauração do histórico foi recusada | ler o motivo impresso; nada foi sobrescrito |
| 130 | Cálculo cancelado | nenhum resultado parcial ficou |

Em uma recusa, nada é escrito na saída padrão. O diagnóstico vai para a saída de erro, em texto ou, com `--format json`, como documento `rejection`.

## Como ler uma recusa

    Entrada recusada (invalid_input)
      /parameters/width/unit [dimension_mismatch]
        A unidade "s" mede tempo, mas o parâmetro width (largura do poço) exige comprimento.
        esperado: unidade de comprimento: m, mm, μm, nm, Å, pm

A primeira linha traz a categoria. Cada diagnóstico traz o campo, como ponteiro JSON, o código entre colchetes, a frase e o que era esperado. Na bancada, o mesmo diagnóstico aparece no campo do formulário. Um enunciado ambíguo vem com o trecho marcado:

    Entrada recusada (ambiguous_input)
      /statement [ambiguous_division]
        Depois de uma divisão, outro fator na mesma sequência admite duas leituras.
        esperado: parênteses que fixem a leitura, como (a/b)*c ou a/(b*c)
        trecho: diff(1/2x, x)
                     ^^^^

Nada é corrigido em silêncio: `1/2x` não vira `(1/2)*x` nem `1/(2*x)`.

## Quando a verificação não passa

O código 5 quer dizer que há um número, mas ele não foi aprovado. O estado diz o tamanho do problema.

`failed`: uma checagem reprovou. Em uma revisão de candidata, é a resposta esperada para uma candidata errada, e a checagem reprovada diz se o defeito está na equação (`equation_residual`) ou na condição inicial (`initial_condition`). Em um espectro, `domain_truncation` reprovado quer dizer que o domínio corta os estados: aumente `half_width`.

`inconclusive`: a checagem não chegou a uma decisão. O caso mais comum é `mesh_refinement` com a malha fora do regime assintótico: aumente `subintervals` e calcule de novo. Uma identidade simbólica que a simplificação não demonstra também fica assim; concordância em pontos amostrados é relatada como evidência numérica, não como prova.

`conditional`: a resposta vale sob uma condição que a entrada não fixa. A condição vem escrita; declare o domínio do símbolo, por exemplo `positive`, se ela for verdadeira no seu problema.

## Bancada

"Sessão não aberta", ou 401 com `session_required`: a página não veio do arquivo de acesso. Abra o arquivo `abrir-calculadora.html` indicado no terminal em que o `qcalc serve` está rodando. Cada execução do `qcalc serve` tem um segredo novo, então uma aba antiga deixa de valer quando a bancada reinicia.

403 com `origin_not_allowed` ou 421 com `host_not_allowed`: a requisição veio de outra página ou por outro nome de máquina. A bancada só atende a própria interface, em `127.0.0.1` ou `localhost`, na porta em que foi iniciada.

"O cálculo terminou sem resultado": o processo de cálculo foi encerrado, pelo sistema ou por falta de memória, ou o disco não aceitou o registro do resultado. A execução fica como falha, sem valor, e as execuções anteriores continuam intactas. Libere espaço em disco e calcule de novo.

"Cálculo interrompido": a bancada foi encerrada no meio do cálculo. A execução volta como interrompida, sem valor e sem verificação. Use "Calcular de novo".

"O pacote não foi importado", ou 422 com `package_refused`: um arquivo do pacote não confere com o hash do manifesto, o manifesto está em formato desconhecido ou o pacote passa dos limites de tamanho. Nada foi importado nem calculado. Peça o pacote de novo a quem o exportou.

409 em `POST /api/v1/runs`: a mesma chave de idempotência foi enviada com outra entrada. Gere uma chave nova.

## Histórico, cópia e restauração

`qcalc backup` e `qcalc restore` terminam com código 11 quando recusam, e dizem o motivo:

    qcalc: A pasta /home/ana/vazio não tem histórico; não há o que copiar.
    qcalc: O arquivo /home/ana/copia.zip já existe; a cópia não sobrescreve outro arquivo.
    qcalc: A pasta /home/ana/restaurado já tem conteúdo; a restauração só grava em pasta nova ou vazia, para não sobrescrever uma pesquisa.

A cópia confere cada artefato com o próprio hash antes de gravá-lo: um artefato corrompido interrompe a cópia em vez de entrar nela. A restauração confere o tamanho e o hash de cada arquivo antes de materializar qualquer coisa.

Um histórico escrito por uma versão mais nova da calculadora é recusado ao abrir. Instale a versão que o escreveu ou restaure uma cópia anterior.

## Como relatar um problema

Junte a saída de `qcalc --version`, a entrada, o comando e a saída completa com `--format json`. O bloco `environment` do registro traz o sistema, o Python, as dependências e a biblioteca de álgebra linear. Não inclua dados que você não possa divulgar: a entrada vai inteira no registro.
