# hopper-documentation

[English](../hopper-documentation-en/README.md) | **Português (Brasil)**

Um plugin para Claude Code e Codex que registra handoffs de conversas, para que outra pessoa ou IA possa continuar o trabalho.

Esta é a versão em português brasileiro, publicada junto com a versão em inglês. O código e o comportamento são os mesmos; mudam os textos e os títulos dos handoffs.

Um **handoff** registra um trecho de uma conversa: o estado necessário para retomar, as pautas, as decisões e autorizações, as pendências e as lacunas. Os handoffs são salvos em uma pasta `docs-by-hopper-documentation` dentro do diretório de trabalho, com um `index.md` que os lista do mais recente ao mais antigo. Um handoff é escrito automaticamente antes de a conversa ser compactada e sempre que você pedir.

Leia a [skill](skills/hopper-documentation/SKILL.md), as [notas de design](docs/design.md) ou o [índice de documentos](index.md).

## Como funciona

Um pequeno programa em Python faz o trabalho mecânico, e um modelo escreve só o conteúdo:

1. **Encontrar a conversa.** O programa recebe do produto o identificador da conversa e o arquivo de histórico dela. Ele confere se os dois correspondem.
2. **Ler só o que é novo.** Ele retoma a leitura depois da última linha registrada no handoff anterior da mesma conversa. Mantém só as mensagens do usuário e as respostas do assistente principal, e oculta segredos. Quando não há nada novo, ele para sem chamar um modelo.
3. **Escrever o conteúdo.** Ele pede ao modelo configurado, uma vez por parte, que escreva o handoff seguindo as regras de conteúdo da skill. No Claude Code, esse modelo não tem ferramentas; no Codex, fica só com as ferramentas que o modelo exige (veja [Privacidade e limites](#privacidade-e-limites)). No primeiro handoff de uma pasta, ele também envia a documentação que já existe no diretório de trabalho. Essa documentação vira a primeira pauta.
4. **Publicar.** Antes, ele confere as fontes que o modelo citou para as autorizações, as situações em andamento e as afirmações sobre ausência ou limite de testes e de uso: cada citação precisa estar, literalmente, nas mensagens, no handoff anterior ou na documentação enviados. Se uma não confere, nada é publicado daquele trecho. Depois, grava o handoff sem sobrescrever nenhum arquivo, refaz o índice e anota o resultado em um registro local.

A documentação roda separada da conversa. A compactação não espera por ela, e você pode continuar trabalhando.

## Requisitos

- macOS ou Linux. Ainda não há suporte ao Windows.
- Python 3.9 ou posterior, disponível como `python3`.
- Claude Code e/ou Codex, instalados e com login feito. O programa procura o executável `claude` ou `codex` no `PATH`, em `~/.local/bin` e dentro dos aplicativos de desktop do Claude e do ChatGPT.
- Acesso aos modelos configurados. Por padrão: Claude Sonnet 5.5 com esforço xhigh no Claude Code e GPT-6 Luna com esforço xhigh no Codex. Para trocá-los, veja [Configuração](#configuração).

O plugin foi feito para o Claude Code (terminal e aplicativo de desktop do Claude) e para o Codex (terminal e aplicativo de desktop do ChatGPT). Até agora, as execuções reais usaram as interfaces interativas de terminal dos dois produtos, no Linux, e o Codex no macOS; no macOS, o Claude Code também escreveu um handoff com um modelo real, chamado pela linha de comando com um histórico sintético. A compactação nativa do Claude Code no macOS e os aplicativos de desktop ainda não foram verificados (veja [Testes](docs/testing.md)). Ele não funciona em produtos de chat sem histórico local e sem gatilhos (hooks), como o chat do claude.ai ou o ChatGPT sem o Codex.

## Instalação

Escolha um idioma. O plugin em inglês fica em `hopper-documentation-en/` e o plugin em português brasileiro, em `hopper-documentation-pt-br/`. Os dois são publicados juntos e se instalam como `hopper-documentation`; por isso, instale só um deles em cada ferramenta. Os passos abaixo clonam o repositório uma vez e adicionam a pasta do idioma escolhido como catálogo (marketplace) local de plugins. Execute só as seções das ferramentas que você usa.

### Peça à sua IA

No Claude Code ou no Codex, você pode dizer:

> Instale a versão em português do plugin hopper-documentation a partir de https://github.com/jonathanpah/hopper-documentation, seguindo o hopper-documentation-pt-br/README.md, nas ferramentas que eu uso, e verifique a instalação.

O assistente deve executar os comandos abaixo para as suas ferramentas e informar o resultado. Ele não pode aprovar o gatilho do Codex por você. Você faz isso uma vez, como descrito abaixo.

### Clone o repositório

O Git precisa estar disponível:

```sh
mkdir -p "$HOME/.local/share"
git clone https://github.com/jonathanpah/hopper-documentation.git "$HOME/.local/share/hopper-documentation"
```

Pare se a clonagem falhar. Se o destino já existir, confira a origem e as alterações locais dele antes de usá-lo ou atualizá-lo. Mantenha o clone: as atualizações vêm dele.

### Claude Code

```sh
claude plugin marketplace add "$HOME/.local/share/hopper-documentation/hopper-documentation-pt-br"
claude plugin install hopper-documentation@hopper-documentation
```

Dentro do Claude Code, você também pode rodar `/plugin marketplace add` com o caminho absoluto dessa pasta e depois `/plugin install hopper-documentation@hopper-documentation`. Depois, inicie uma nova sessão. O plugin instala a skill e um gatilho `PreCompact`. O aplicativo de desktop do Claude usa a mesma configuração do Claude Code.

### Codex

```sh
codex plugin marketplace add "$HOME/.local/share/hopper-documentation/hopper-documentation-pt-br"
codex plugin add hopper-documentation@hopper-documentation
```

O Codex não executa gatilhos de plugins até que você os aprove. Abra o Codex, rode `/hooks`, revise o gatilho `PreCompact` do hopper-documentation e aprove-o. Depois, inicie uma nova sessão. O aplicativo do Codex no ChatGPT usa a mesma configuração do Codex.

### Verifique a instalação

- A skill aparece na lista de skills da ferramenta. No Codex, ela aparece como `hopper-documentation:hopper-documentation`.
- O gatilho `PreCompact` aparece em `/hooks`. No Codex, ele aparece como aprovado.
- Em uma pasta descartável, tenha uma conversa curta e peça a documentação dela. Deve aparecer uma pasta `docs-by-hopper-documentation` com um handoff e um `index.md`.

### Instalação manual

Se você não puder usar plugins, reproduza a mesma estrutura à mão a partir do clone. Crie um link de `hopper-documentation-pt-br/skills/hopper-documentation` em `~/.claude/skills/` ou em `~/.agents/skills/`. Registre o comando de `hopper-documentation-pt-br/hooks/hooks.json` como gatilho `PreCompact` em `~/.claude/settings.json` ou em `~/.codex/hooks.json`. No comando, troque `${CLAUDE_PLUGIN_ROOT}` pelo caminho absoluto da pasta `hopper-documentation-pt-br` no clone. Mantenha `async` para o Codex e `asyncRewake` para o Claude Code, como nesse arquivo.

## Uso

- **Automaticamente:** antes de cada compactação, manual ou automática, o gatilho documenta o que é novo.
- **A pedido:** peça ("documente esta conversa") ou acione a skill. No Claude Code, a conversa inicia o programa em segundo plano e informa o resultado quando ele termina; se a sua sessão pede aprovação antes de rodar comandos, aprove o comando do programa ou libere-o nas suas configurações. No Codex, a conversa prepara o trecho e cria um agente com o modelo configurado para escrevê-lo; o agente continua por todas as partes, até o ponto em que você pediu.
- Uma conversa que termina sem compactação só é documentada se você pedir.
- As respostas que você dá às perguntas de múltipla escolha da IA e os planos que você aprova entram na documentação.

Os handoffs são escritos no idioma da conversa; os títulos ficam em português.

Para que novas sessões leiam os handoffs, adicione ao seu `AGENTS.md` ou `CLAUDE.md` uma instrução como esta:

> Ao iniciar ou retomar um trabalho, verifique se o diretório de trabalho tem `docs-by-hopper-documentation`. Se tiver, leia o `index.md` e, entre os handoffs listados nele, o mais recente de cada conversa. A conversa aparece no cabeçalho de cada handoff. Quando precisar de uma decisão ou de um detalhe anterior, leia os handoffs anteriores dessa conversa. Handoffs são histórico: não autorizam repetir operações e não substituem a verificação do estado atual.

## Configuração

Arquivo opcional `~/.config/hopper-documentation/config.json`:

```json
{
  "claude": {"model": "claude-sonnet-5-5", "effort": "xhigh"},
  "codex": {"model": "gpt-6-luna", "effort": "xhigh", "executable": "/path/to/codex"}
}
```

Cada campo é opcional. No Codex, a chamada feita antes da compactação não carrega o seu `config.toml`: ela usa o seu login do Codex e o modelo e o esforço definidos aqui. Sem acesso ao modelo configurado, a documentação informa o problema em vez de usar outro modelo. As variáveis de ambiente `HOPPER_DOCUMENTATION_CONFIG` e `HOPPER_DOCUMENTATION_LOG` mudam o local da configuração e do registro.

## Registros

- `docs-by-hopper-documentation/handoff-YYYYMMDD-HHMMSS.md`: um handoff, nomeado com a data e a hora locais da publicação.
- `docs-by-hopper-documentation/index.md`: uma linha por handoff, `handoff-… | resumo | fuso, deslocamento UTC`.
- `~/.local/state/hopper-documentation/log.jsonl`: uma linha por execução, com o resultado dela. Os segredos ficam ocultos. Quando essa pasta não aceita gravação, como no isolamento do Codex durante um pedido, a linha vai para `log.jsonl` na pasta de travas abaixo.
- `hopper-documentation-<id do usuário>/` na pasta temporária do sistema: um arquivo de trava vazio por pasta de documentação, para que só um handoff seja publicado por vez. Essa pasta de travas pode ser apagada quando nenhuma documentação estiver rodando.

Cada handoff registra a conversa, o arquivo de histórico e o trecho de linhas que ele cobre. A próxima execução continua a partir dali. Um handoff que não segue o formato é mantido e aparece no índice como "sem resumo". Ele não bloqueia novos handoffs.

## Privacidade e limites

- O programa lê o seu histórico local de conversas e envia o trecho novo, com os segredos ocultos, ao provedor de modelo que você já usa nessa ferramenta. No primeiro handoff de uma pasta, ele também envia os arquivos de documentação encontrados no diretório de trabalho e nas subpastas dele (`.md`, `.markdown`, `.txt`, `.rst` e `.adoc`, até 100.000 caracteres). Ele ignora pastas ocultas e pastas de dependências ou de build, como `node_modules`. A ocultação cobre formatos comuns, como valores com rótulo, endereços de conexão, opções de comando, tokens de acesso e sequências longas geradas, não todos os segredos possíveis.
- A pasta de documentação é criada no seu diretório de trabalho. Em um repositório público, decida se ela deve ser versionada ou ignorada.
- Os formatos de histórico de conversa não são uma interface estável de nenhum dos dois produtos. Uma atualização do produto pode mudá-los e fazer o programa falhar, com um aviso, até que ele seja atualizado.
- Uma execução em segundo plano para se a sessão for fechada antes do fim; no Codex, também para depois de uma hora. A próxima execução continua a partir da última linha registrada. Documentar uma conversa longa pela primeira vez pode levar vários minutos.
- No Claude Code, um aviso de falha chega à conversa no turno seguinte. No Codex, o resultado da documentação automática aparece entre os avisos da sessão.
- Históricos longos são divididos em handoffs consecutivos de até 150.000 caracteres de mensagens. Uma linha do histórico nunca é dividida; uma linha maior é cortada, e o handoff informa isso em Lacunas.
- No Claude Code, o modelo que escreve roda no modo seguro, sem ferramentas, servidores MCP, skills, ganchos, plugins, os seus CLAUDE.md nem a memória automática. No Codex, antes da compactação, ele roda num isolamento (sandbox) somente leitura, sem rede, busca na web, aplicativos, o AGENTS.md do projeto nem a sua configuração do Codex, embora o Codex ainda acrescente o seu AGENTS.md global, e recebe a instrução de não usar ferramentas; o Codex não tem modo sem ferramentas para o GPT-6 Luna, então o modelo mantém uma ferramenta de código que pode ler arquivos locais e ferramentas para iniciar subagentes. A pedido, no Codex, o agente da documentação usa ferramentas para ler a tarefa, gravar o conteúdo e rodar o programa.
- O primeiro handoff em um diretório de trabalho muito grande, como uma pasta pessoal, demora mais, porque o programa percorre todas as subpastas procurando documentação, e a primeira pauta pode resumir documentos sem relação com o trabalho.

## Atualização e remoção

Revise as mudanças e resolva as alterações locais; depois, atualize o clone:

```sh
git -C "$HOME/.local/share/hopper-documentation" pull --ff-only
```

Claude Code: `claude plugin marketplace update hopper-documentation` e depois `claude plugin update hopper-documentation@hopper-documentation`. Para remover: `claude plugin uninstall hopper-documentation@hopper-documentation`.

Codex: `codex plugin add hopper-documentation@hopper-documentation` instala a nova versão a partir do clone atualizado; aprove de novo, em `/hooks`, o gatilho atualizado, se ele tiver mudado. Para remover: `codex plugin remove hopper-documentation@hopper-documentation`.

Para trocar de idioma, remova o plugin e o catálogo dele (`claude plugin marketplace remove hopper-documentation` ou `codex plugin marketplace remove hopper-documentation`) e adicione a pasta do outro idioma, como em [Instalação](#instalação).

Remover o plugin mantém os handoffs já gravados nos seus projetos.

## Desenvolvimento

Na pasta `hopper-documentation-pt-br/`, rode os testes, que não chamam nenhum modelo e não instalam nada:

```sh
python3 -m unittest discover -s tests -v
```

Veja o [CONTRIBUTING.md](CONTRIBUTING.md) para propostas e revisões, e o [SECURITY.md](SECURITY.md) para relatar uma vulnerabilidade de forma privada.

## Licença e mantenedor

Copyright (c) 2026 Jonathan Honorio. Distribuído sob a [Licença MIT](LICENSE).

Mantido por [Jonathan Honorio (@jonathanpah)](https://github.com/jonathanpah). Este é um projeto independente. Não alega afiliação com a OpenAI ou a Anthropic, nem endosso delas.
