# Testes

## Testes unitários

```sh
python3 -m unittest discover -s tests -v
```

Os testes não chamam nenhum modelo e não instalam nada. Eles usam executáveis falsos de `claude` e `codex` e pastas temporárias. Eles cobrem:

- extração das mensagens do usuário e das respostas do assistente nos dois formatos de histórico, incluindo as respostas do usuário a perguntas estruturadas, os planos aprovados e as mensagens enviadas enquanto o assistente trabalhava, contando uma vez os registros gravados de novo depois de uma retomada, e excluindo raciocínio, chamadas e resultados de ferramentas, comandos, resumos de compactação, cadeias laterais (side chains), lembretes do sistema, contexto injetado e textos internos;
- identidade da conversa, inclusive de uma bifurcação cujo histórico começa com registros de outra sessão e de um histórico de outra sessão renomeado para o id pedido, limite de leitura e ponto de retomada, incluindo uma linha que mudou de lugar e uma linha ausente;
- divisão em partes sem dividir uma linha do histórico, e corte de uma linha grande demais com nota em Lacunas;
- texto que o UTF-8 não grava, como metade de um emoji no histórico ou um nome de arquivo com bytes inválidos, substituído em vez de interromper a documentação;
- leitura da documentação existente: pastas ignoradas, arquivos vazios, handoffs em subpastas, a ordem de leitura, o limite de leitura, a lista de arquivos lidos em parte ou não lidos, e arquivos e pastas que não podem ser lidos;
- ocultação de segredos: valores com rótulo, com os nomes lidos palavra por palavra, para que contadores como `max_tokens` continuem visíveis, incluindo valores entre aspas com espaços, JSON escapado de uma a quatro vezes e nomes logo depois de um escape; endereços de conexão; opções de comando e valores ditos em prosa, com ou sem aspas; tokens de acesso, incluindo JWTs inteiros, com JSON compacto ou espaçado; sequências longas geradas, preservando hashes (mesmo depois de letras como SHA), impressões digitais de chaves, UUIDs e identificadores técnicos; e o tempo dela em textos longos sem separadores;
- publicação sem sobrescrever, oito conversas publicando ao mesmo tempo, seis execuções da mesma conversa ao mesmo tempo, um handoff malformado, um resumo longo, um resumo ocultado no handoff e no índice, a recuperação do índice depois de uma falha, um sistema de arquivos sem links, uma gravação que falha e deixa o trecho para a próxima execução, um título de seção repetido e um campo que o modelo devolveu escapado de novo;
- conferência das fontes citadas pelo modelo: referência inexistente, trecho inventado ou fora da fonte, trecho que junta duas mensagens, cortes marcados com reticências, formatação Markdown omitida ou cortada (negrito, código na linha, blocos de código e reticências dentro de código), mudança em identificadores, globs, operadores e código entre crases, caracteres reservados do comparador na fonte ou na citação, `\n` literal na fonte, número da linha gravado como número ou rotulado ("linha 9"), referência ambígua ou inexistente, fonte no handoff anterior, segredo ocultado citado de volta e falha sem publicar nem avançar o ponto de retomada, também no fluxo manual do Codex;
- códigos de saída e mensagens do gatilho (hook) em cada produto, reentrada, eventos inválidos, sessões sem arquivo de histórico, detecção do produto e mensagens de falha que trazem o erro do executor;
- os comandos `prepare`, `publish`, `run` e `config`, incluindo os horários locais no prompt, o fluxo do agente do Codex por todas as partes até o limite de leitura, e o resultado parcial quando a parte seguinte não pode ser gravada;
- as opções que desligam ferramentas, ganchos, plugins e os arquivos de instruções do usuário nas duas chamadas ao modelo, e o prompt de sistema do Claude.

## Execuções reais

As execuções reais usaram o Claude Code e o Codex no Linux, e o Codex no macOS. No macOS, o Claude Code também escreveu um handoff com um modelo real, chamado pela linha de comando com um histórico sintético. Elas cobriram:

- conversas reais dos dois produtos, inclusive longas, documentadas em duas rodadas para conferir a continuação, com cada handoff conferido contra a sua conversa;
- sessões novas dos dois produtos retomando o trabalho só a partir dos handoffs;
- compactação nativa nas interfaces interativas de terminal, manual e automática nos dois produtos (no Claude Code, com uma janela de compactação menor definida para o teste), com a conversa continuando enquanto a documentação rodava, e avisos de falha;
- documentação a pedido nos dois produtos, incluindo um agente do Codex percorrendo as partes de uma conversa longa;
- casos-limite: execuções simultâneas da mesma conversa, os dois produtos na mesma pasta, uma conversa em inglês, segredos plantados, um conjunto grande de documentação existente e uma pasta pessoal inteira;
- instalação, atualização e remoção em configurações temporárias, a partir de uma pasta local e de um repositório git servido por HTTP, com o gatilho instalado executado como o produto o executa;
- execuções sobre todos os históricos locais dos dois produtos, sem modelo: identidade, partes, uma documentação simulada de todas as partes, ocultação e tempo;
- injeção de falhas sem modelo: resposta do modelo inválida ou ausente, interrupções em momentos aleatórios, erros de sistema de arquivos e de permissão, e históricos danificados.

O comportamento do modelo pode variar entre execuções e versões dos produtos. Por isso, uma mudança que afete chamadas ao modelo, gatilhos ou regras de conteúdo precisa de uma nova execução real no produto afetado.

## Ainda não verificado

- Execuções dentro dos aplicativos de desktop do Claude e do ChatGPT; os testes usaram as interfaces interativas de terminal dos mesmos produtos.
- O Claude Code no macOS pela compactação nativa ou dentro do aplicativo de desktop; no macOS, só a chamada pela linha de comando com um histórico sintético foi exercitada.
- Instalação e atualização a partir do repositório no GitHub; os testes usaram um repositório git servido por HTTP.
- A compactação automática no Claude Code com a janela padrão; os testes definiram uma janela menor para provocá-la.
