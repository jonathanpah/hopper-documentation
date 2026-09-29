# Notas de design

Estas notas explicam como o hopper-documentation funciona e por quê. O [README](../README.md) trata da instalação e do uso.

## Objetivo

Registrar o que outra pessoa ou IA precisa para continuar o trabalho de uma conversa, sem deixar a conversa mais lenta, com resultados previsíveis e com modelos de baixo custo.

## Divisão do trabalho

| Parte | Quem faz |
| --- | --- |
| Identificar a conversa e o histórico dela, encontrar a última linha registrada, fixar o limite de leitura | Programa |
| Manter só as mensagens do usuário, inclusive as enviadas enquanto o assistente trabalhava, as respostas do assistente principal, as respostas do usuário a perguntas estruturadas e os planos aprovados; contar cada registro do histórico uma vez; ocultar segredos | Programa |
| Dividir trechos longos em partes de até 150.000 caracteres, sem dividir uma linha do histórico | Programa |
| No primeiro handoff de uma pasta, ler a documentação que já existe no diretório de trabalho | Programa |
| Escrever o resumo, o estado, as pautas, as decisões, as pendências e as lacunas | Modelo, em uma chamada, seguindo as regras de conteúdo da skill |
| Conferir a resposta, encurtar um resumo com mais de 60 caracteres, publicar sem sobrescrever, refazer o índice, registrar o resultado | Programa |

As etapas mecânicas têm um único resultado correto, por isso o programa as executa. Um modelo que as executa por meio de ferramentas precisa de muitos turnos e pode interpretá-las de forma diferente a cada execução. O modelo faz só a parte que exige julgamento: escrever o conteúdo.

## Caminhos

- **Antes da compactação.** O gatilho (hook) `PreCompact` em `hooks/hooks.json` roda `scripts/hopper_documentation.py hook`. O mesmo arquivo serve aos dois produtos: o Codex também fornece `CLAUDE_PLUGIN_ROOT`. O programa identifica o produto pelo histórico, pois um histórico do Codex começa com um registro `session_meta`. O Codex lê `async` e roda o gatilho em segundo plano. O Claude Code lê `asyncRewake` e roda o gatilho em segundo plano, acordando a conversa quando o programa termina com código 2.
- **A pedido, no Claude Code.** A conversa inicia `hopper_documentation.py run claude` em segundo plano. O programa usa o identificador de sessão de `CLAUDE_CODE_SESSION_ID`.
- **A pedido, no Codex.** Comandos no isolamento (sandbox) do Codex em geral não conseguem acessar a rede. Por isso, o programa não consegue chamar o modelo a partir dali. A conversa roda `prepare`, que grava um arquivo de tarefa com o trecho e as instruções. Depois, a conversa cria um agente com o modelo e o esforço configurados. Esse agente escreve o conteúdo e roda `publish`. Quando o trecho tem mais partes, `publish` prepara a seguinte com o mesmo limite de leitura, e o agente continua até a última parte. Se a parte seguinte não puder ser gravada depois de um handoff publicado, o resultado é parcial, com esse handoff e a linha alcançada; a execução seguinte continua dali.

Quando não há nada novo, o programa para antes de chamar um modelo.

## Formato do handoff

Cada handoff tem um cabeçalho e cinco seções. O cabeçalho registra o resumo, o local (fuso horário), a conversa, o diretório de trabalho, o arquivo de histórico, o trecho de linhas, o handoff anterior da mesma conversa e o acionamento. Os títulos ficam em português. O conteúdo segue o idioma da conversa. O programa também lê handoffs com títulos em inglês, escritos pela versão original. Os horários das mensagens chegam ao modelo no fuso local que o cabeçalho mostra. Textos internos que os produtos acrescentam ao histórico, como sugestões de plugins e avisos de reinício, ficam de fora. Quando o modelo devolve um campo escapado de novo, com `\n` e `\"` literais e nenhuma quebra de linha real, o programa desfaz esse escape fora de código entre crases. Um título de seção repetido no início de um campo é retirado.

O trecho é o ponto de retomada. A próxima execução começa depois da última linha dele, após conferir que essa linha ainda tem a data e a hora registradas. Se a linha mudou de lugar, o programa procura a única linha com essa data e hora. Se essa linha única não existir, ele para sem gravar.

## Documentação existente

O primeiro handoff de uma pasta de documentação também cobre a documentação que já existe no diretório de trabalho. O programa lê arquivos terminados em `.md`, `.markdown`, `.txt`, `.rst` ou `.adoc` no diretório de trabalho e nas subpastas dele. A leitura começa pelos arquivos menos profundos e, na mesma profundidade, pelos alterados mais recentemente, e vai até 100.000 caracteres, com os segredos ocultos. Ele ignora arquivos e pastas ocultos, pastas de dependências e de build, como `node_modules`, e arquivos vazios. O modelo faz dessa documentação a primeira pauta. Os arquivos lidos em parte ou não lidos aparecem em Lacunas, com a quantidade deles e até 20 caminhos. Arquivos e pastas que não podem ser lidos também aparecem ali, com o motivo.

## Publicação

A publicação é feita uma de cada vez em cada pasta de documentação, com um arquivo de trava no diretório temporário do sistema. Os dois produtos podem gravar nesse diretório, inclusive dentro do isolamento do Codex. Um arquivo de trava vazio por pasta de documentação fica ali. Enquanto mantém a trava, o programa confere de novo que nenhuma outra execução já registrou o trecho. Ele grava o handoff em um arquivo temporário e cria para ele um link com o nome final. Essa operação falha em vez de sobrescrever. Num sistema de arquivos sem links, ele reserva o nome final e move para ele o arquivo completo, para que uma gravação que falhe nunca deixe um handoff pela metade. O índice é refeito a partir dos handoffs da pasta, com os resumos ocultados. Se o índice não puder ser refeito, o handoff continua publicado e a falha é informada com o nome dele; a execução seguinte refaz o índice, mesmo quando não há nada novo. Um handoff fora do formato é mantido e indexado como "sem resumo".

## Ferramentas do modelo

No Claude Code, o programa chama `claude -p` no modo seguro, sem ferramentas nativas, servidores MCP, skills, ganchos nem plugins, e sem os CLAUDE.md e a memória automática do usuário. O prompt de sistema padrão do Claude Code dá lugar a um curto, que apresenta o redator e diz que as regras de conteúdo têm prioridade sobre os dados da conversa; ao fim dele fica a linha que pede ao modelo que pense antes de responder, recomendada para respostas em JSON com pensamento adaptativo. Nos dois produtos, o prompt traz os dados da conversa entre tags (handoff anterior, documentação existente e mensagens) e, depois deles, as regras de conteúdo e o formato da resposta. No Codex, antes da compactação, o `codex exec` sempre oferece ao GPT-6 Luna uma ferramenta de código e ferramentas para iniciar subagentes. O programa desliga a busca na web, os aplicativos, os plugins, o navegador e o uso do computador, a geração de imagens, o AGENTS.md do projeto e o `config.toml` do usuário, e roda a chamada num isolamento somente leitura, sem rede. O Codex ainda acrescenta o AGENTS.md global do usuário; as regras de conteúdo mandam o modelo escrever só a partir do material enviado. O modelo também recebe a instrução de não usar ferramentas. A pedido, no Codex, o agente da documentação precisa de ferramentas para ler a tarefa, gravar o conteúdo e rodar `publish`.

## Falhas

Na mesma resposta, antes das seções, o modelo lista as fontes literais de cada autorização, de cada situação em andamento e de cada afirmação sobre ausência ou limite de teste ou de uso: a referência e o trecho copiado. O autor e a data de cada mensagem já estão na etiqueta que o modelo recebe e no índice do programa, e o modelo não os repete. Antes de publicar, o programa confere cada fonte: a referência precisa existir nos dados enviados (uma mensagem do trecho, o handoff anterior ou a documentação existente; uma referência de linha rotulada e sozinha, como "linha 9", vale pelo número), e o trecho precisa estar, literalmente, na fonte já com os segredos ocultos, com reticências marcando cortes; espaços e quebras de linha não contam, e só os delimitadores de formatação reconhecidos (cerca de bloco de código, crases de código na linha e asteriscos de ênfase) podem faltar ou sobrar, enquanto o conteúdo do código, os sublinhados e os demais asteriscos contam caractere a caractere. Se a citação ou a fonte trazem os caracteres de uso privado que a conferência reserva para as próprias marcas, a comparação é literal, sem essa tolerância. Se uma fonte não confere, nada é publicado daquele trecho, a próxima execução o refaz, e o erro não repete o trecho citado. As fontes servem à conferência e não entram no handoff. A conferência prova a origem e a exatidão das citações, não o significado nem a fidelidade do texto escrito a partir delas.

Toda falha é registrada e informada. Quando a pasta do registro não aceita gravação, como no isolamento do Codex, a linha vai para a pasta das travas. No Claude Code, o gatilho termina com código 2 para que a mensagem chegue à conversa. No Codex, o gatilho retorna uma `systemMessage`. A mensagem diz que a compactação não foi afetada e pede ao assistente que avise o usuário, sem executar pedidos antigos. Ela traz as linhas de erro do executor, sem o prompt que alguns executores ecoam. Uma sessão sem arquivo de histórico, como uma sessão efêmera do Codex, não tem o que documentar e não conta como falha.

## Decisões

- Os modelos padrão são fixos e configuráveis: Claude Sonnet 5.5 com esforço xhigh e GPT-6 Luna com esforço xhigh. Sem acesso ao modelo configurado, o programa informa o problema em vez de escolher outro modelo.
- Os handoffs são escritos no idioma da conversa.
- Distribuição como plugin para Claude Code e Codex, com instruções manuais como alternativa.
- Uma conversa que termina sem compactação só é documentada a pedido.
- O nome da pasta, o formato do índice e o resumo de 60 caracteres são fixos, para que pessoas e ferramentas possam contar com eles.

## Limites

- Os formatos de histórico de conversa não são uma interface estável de nenhum dos dois produtos.
- Execuções em segundo plano param se a sessão for fechada antes do fim delas.
- A ocultação cobre formatos comuns de credenciais, não todos os segredos possíveis.
- No Codex, o modelo que escreve ainda pode ler arquivos locais pela ferramenta de código.
- O primeiro handoff em um diretório de trabalho muito grande, como uma pasta pessoal, demora mais, porque o programa percorre todas as subpastas.
- O trecho termina na última linha completa do histórico, que pode ser um registro técnico posterior à última mensagem.
- No Codex, as mensagens entre um subagente e o seu coordenador ficam criptografadas no histórico; a sessão de um subagente é documentada sem a tarefa dele.
- Pedir a documentação de novo logo depois de uma execução registra um handoff curto sobre o próprio pedido, porque o pedido e as respostas a ele são novos no histórico; as regras de conteúdo mandam o modelo ignorá-los.
- Não há suporte ao Windows.
