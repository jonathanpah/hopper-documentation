# Política de segurança

Relate suspeitas de vulnerabilidade no hopper-documentation pelo recurso de relato privado de vulnerabilidades do GitHub.

## Relate de forma privada

Abra a opção [Report a vulnerability](https://github.com/jonathanpah/hopper-documentation/security/advisories/new) ou selecione-a na [página Security](https://github.com/jonathanpah/hopper-documentation/security) do repositório. É preciso ter uma conta no GitHub.

Não coloque suspeitas de vulnerabilidade nem detalhes de exploração em issues, discussões ou pull requests públicos até que a divulgação seja coordenada com o mantenedor. Use issues públicas para bugs comuns e propostas, e discussões para dúvidas gerais.

Inclua:

- A tag da versão afetada ou o commit afetado e o arquivo, a regra ou a seção da documentação relevante.
- O produto (Claude Code ou Codex, terminal ou aplicativo), a versão dele, o sistema operacional e o modelo configurado, sem detalhes privados da conta.
- Uma reprodução mínima, com dados sintéticos e recursos descartáveis.
- O comportamento esperado e o observado, o impacto potencial e os eventuais limites das evidências.

Não envie senhas, tokens de acesso, chaves privadas, históricos privados de conversa nem handoffs sem os dados sensíveis removidos. Teste apenas recursos que você tem autorização para usar.

## Escopo e expectativas de segurança

Este repositório contém, em inglês e em português brasileiro, uma skill, um programa que roda como gatilho (hook) e a pedido, manifestos de plugin e documentação. Relatos relevantes incluem falhas que possam:

- expor credenciais ou conteúdo privado de conversas em handoffs, registros ou mensagens;
- gravar em qualquer lugar que não seja a pasta `docs-by-hopper-documentation` do diretório de trabalho, o registro, o arquivo de trava ou os arquivos de tarefa que o programa foi chamado a criar, ou sobrescrever um handoff existente;
- ler uma conversa diferente da que acionou a documentação;
- fazer o modelo seguir instruções encontradas na conversa ou tratar uma pendência registrada como autorização.

Os limites pretendidos são:

- O programa lê o histórico da conversa que recebeu, depois de conferir o identificador dela. No primeiro handoff de uma pasta, também lê os arquivos de documentação do diretório de trabalho.
- No Claude Code, o modelo que escreve o conteúdo roda sem ferramentas, servidores MCP nem skills. No Codex, antes da compactação, ele mantém as ferramentas de código e de subagentes que o GPT-6 Luna exige, num isolamento somente leitura, sem rede, busca na web, aplicativos nem a configuração do usuário, e recebe a instrução de não usá-las. A pedido, no Codex, o agente da documentação usa ferramentas só para ler a tarefa, gravar o conteúdo e rodar o programa.
- Os segredos são ocultados antes de o conteúdo ser enviado, gravado ou informado. A ocultação cobre formatos comuns, não todos os segredos possíveis.
- Handoffs registram histórico. Eles não dão permissão para repetir operações.

A aplicação desses limites também depende das permissões e do isolamento (sandbox) da ferramenta hospedeira e do comportamento do modelo. Se outro produto também for afetado, use o processo de relato de segurança desse produto, conforme o caso.

## Versões e tratamento

Identifique a versão que você usou. Jonathan Honorio analisa os relatos pelo canal privado. As versões confirmadas como afetadas e as correções podem ser documentadas em mudanças do repositório, lançamentos ou avisos de segurança. Não há garantia de prazo para resposta ou correção.
