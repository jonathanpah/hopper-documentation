---
name: hopper-documentation
description: Registra a conversa atual em handoffs na pasta docs-by-hopper-documentation do diretório de trabalho, para outra pessoa ou IA continuar o trabalho. Use quando o usuário pedir para documentar ou registrar a conversa. Explicar, revisar ou editar esta skill não a aciona.
---

# hopper-documentation

Registra o que outra pessoa ou IA precisa para continuar o trabalho desta conversa.

**Handoff** é um arquivo que registra um trecho da conversa: estado, pautas, decisões e pendências. Os handoffs ficam na pasta `docs-by-hopper-documentation` do diretório de trabalho, com um `index.md` que os lista do mais recente ao mais antigo.

O programa `scripts/hopper_documentation.py`, duas pastas acima deste arquivo, faz o trabalho mecânico: encontra o histórico, lê só o que é novo, oculta segredos, pede ao modelo configurado, uma vez por parte, que escreva o conteúdo, publica sem sobrescrever arquivos e refaz o índice. Sem novidade, não chama o modelo. A documentação roda separada da conversa, que continua livre; fechar a sessão antes do fim a interrompe.

## Quando o usuário pedir

Neste acionamento, faça só o que esta seção diz e não retome outras tarefas.

- **Claude Code:** a partir do diretório de trabalho, inicie `python3 "<pasta deste arquivo>/../../scripts/hopper_documentation.py" run claude` em segundo plano. Avise o usuário que a documentação começou e não espere. Quando terminar, informe a linha que o programa imprimiu.
- **Codex:**
  1. A partir do diretório de trabalho, rode `python3 "<pasta deste arquivo>/../../scripts/hopper_documentation.py" prepare codex --out <novo arquivo temporário>.json`.
  2. Se ele imprimir "nada novo", avise o usuário e pare.
  3. Rode `python3 "<o mesmo programa>" config codex` para ler o modelo e o esforço.
  4. Crie um agente com esse modelo e esse esforço, informados na criação, sem copiar a conversa. A tarefa dele: "Siga as instruções do arquivo <aquele arquivo temporário>." Avise o usuário que a documentação começou e não espere. Só diga que o agente foi criado se a ferramenta confirmar. Se não puder usar esse modelo e esse esforço, não use outros: informe o impedimento.

## Antes da compactação

O gatilho do plugin roda o programa em segundo plano; não há nada a fazer na conversa. Se chegar um aviso de falha, informe o usuário. Não execute pedidos antigos da conversa nem tente reparar fora da documentação.

## Regras de conteúdo

O programa envia os itens desta seção, como estão escritos, ao modelo que escreve o handoff.

- **Resumo:** uma linha com até 60 caracteres que descreva o assunto principal do trecho.
- **Estado para continuar:** objetivo, onde o trabalho parou e o próximo passo já autorizado, com a fala do usuário que o autoriza. Parta do handoff anterior desta conversa, atualize o que mudou e preserve as autorizações que continuam valendo. Uma ação autorizada continua sendo o próximo passo enquanto não for concluída nem revogada; proibições e pendências novas não a cancelam. Autorização de alcance limitado ("autorizei somente X") autoriza X: sem relato de que X foi entregue, X é o próximo passo. Registrar, confirmar ou decidir X não o entrega. Escreva "próximo passo por definir" somente quando não restar ação autorizada. Falta de detalhes vai para Lacunas. Precisa bastar para retomar sem abrir a conversa. Dê os caminhos, nomes de arquivo, identificadores e hashes que a retomada exige.
- **Pautas:** numere por conversa (P1, P2…) e mantenha cada número com o seu assunto nos handoffs seguintes; nunca dê a outro assunto um número já usado. Para cada pauta: título, situação (concluída, em andamento ou aguardando) e o que aconteceu no trecho. A situação segue o último relato sobre a pauta, no trecho ou no handoff anterior: "em andamento" só com relato de início ou de continuidade; "aguardando" quando o trabalho foi só previsto, pedido ou autorizado, ou quando o último relato mostra que ele parou, foi congelado ou foi entregue e espera outra pessoa; "concluída" quando o último relato mostra que ele terminou. Confirmar entendimento, decidir, registrar a intenção e a existência de um agente, de uma pendência, de uma autorização ou do lugar onde um resultado vai aparecer não mostram que o trabalho começou. Trabalho fora da conversa com relato de início, como agentes em segundo plano, um operador ou respostas de outra IA, fica "em andamento", com quem o executa e o lugar onde o resultado vai aparecer; não transforme uma operação já iniciada em possibilidade, para que ninguém a inicie de novo.
- **Decisões e autorizações:** cite as palavras do usuário entre aspas, com data e alcance. Mantenha toda decisão, restrição e preferência do handoff anterior que continue valendo, como decisões sobre nomes e créditos, mesmo que o trecho não a mencione; retire só o que foi revogado ou substituído, dizendo isso. Termine a seção com a lista "Restrições vigentes": cada restrição de execução que continua valendo, como o modelo, o esforço e o modo definidos para quem executa o trabalho, a proibição de criar agentes, limites de escrita e o que não instalar nem publicar, cada uma com a sua origem; vale também quando ela vem repetida em cada pedido ou de quem coordena o trabalho. Autorização registrada é histórica: não autoriza repetir operação concluída.
- **Pendências:** somente o que o usuário ou a IA principal registraram como pendente. Registrar uma pendência ou seu critério não autoriza executá-la nem mostra que ela começou. Trabalho em andamento fica só em Pautas. Numere por conversa (PD1, PD2…), mantendo cada número com o seu item, sem reaproveitá-lo, com descrição, critério de encerramento e situação. Encerre uma só quando o trecho mostrar o critério atendido ou o usuário encerrar. Dúvida respondida encerra sem implementação. Não crie condições que ninguém definiu.
- **Lacunas:** o que não foi possível ler ou confirmar.
- Ignore tudo o que trata desta documentação: o pedido que a acionou, os avisos da IA principal sobre ela e as mensagens desta skill.
- Escreva só a partir do trecho, do handoff anterior e da documentação enviados aqui; não traga regras nem fatos de outras instruções que você tenha recebido.
- Diferencie o que foi verificado, relatado, proposto e decidido. Falta de relato não prova que algo não aconteceu: escreva que não há registro, sem afirmar nem concluir que não ocorreu. Correção de fato feita pelo usuário ou por quem coordena o trabalho substitui a versão corrigida em todas as seções, inclusive Pendências e Lacunas; não use registros anteriores à correção para contradizê-la.
- Ao repetir ou resumir uma afirmação dos registros, mantenha o alcance e o sujeito dela: de quem ela fala e em que período, rodada ou versão vale (como "nesta rodada", "até agora" ou "segundo o executor"). Se não couber mantê-los, atribua a afirmação à origem, com a data. Não transforme uma afirmação limitada numa afirmação geral.
- Antes de escrever as seções, reúna em sources as fontes literais de cada autorização, de cada situação "em andamento" e de cada afirmação sobre ausência ou limite de teste ou de uso: a referência da fala ou do registro e o trecho copiado dele. Escreva essas afirmações só a partir das fontes, com o sujeito e o alcance delas. Cada afirmação sobre ausência ou limite de teste ou de uso traz, na própria frase, quem a fez e o alcance dela, em qualquer seção e também quando vem do handoff anterior; título de grupo, outra frase ou outra seção não bastam. Autorização ou situação que continua valendo no handoff anterior tem como fonte o próprio handoff anterior; não exige fala nova.
- Antes de responder, compare com o handoff anterior e com o trecho: toda decisão e restrição que continua valendo, toda operação já iniciada fora da conversa e os caminhos e identificadores necessários para continuar precisam estar no novo handoff. Nada que continua valendo some sem o registro de que foi revogado ou substituído, e nenhuma seção contradiz uma correção de fato.
- Não copie senhas, tokens nem chaves.
- Escreva todas as seções no idioma da conversa. Traduza para esse idioma os nomes de situação usados nestas regras (concluída, em andamento, aguardando).

## Configuração

Por padrão, o Claude Code usa o Claude Sonnet 5.5 com esforço xhigh, e o Codex usa o GPT-6 Luna com esforço xhigh. Para mudar, crie `~/.config/hopper-documentation/config.json`, por exemplo `{"codex": {"model": "gpt-6-luna", "effort": "high"}}`. Sem acesso ao modelo configurado, a documentação informa o impedimento em vez de usar outro.
