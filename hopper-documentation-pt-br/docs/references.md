# Referências

Documentação oficial consultada durante a construção deste plugin.

## Claude Code

- [Hooks](https://code.claude.com/docs/en/hooks): evento `PreCompact`, campos `async` e `asyncRewake`, campos de entrada e códigos de saída.
- [Skills](https://code.claude.com/docs/en/skills): formato de skill e frontmatter.
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference): manifesto de plugin, estrutura padrão, `hooks/hooks.json` e `${CLAUDE_PLUGIN_ROOT}`.
- [Data usage](https://code.claude.com/docs/en/data-usage): transcrições locais e a retenção delas.

## Codex

- [Hooks](https://learn.chatgpt.com/docs/hooks): evento `PreCompact`, campos de entrada, `async`, revisão para aprovação e `systemMessage`.
- [Build plugins](https://developers.openai.com/codex/plugins/build): estrutura de plugin, gatilhos (hooks), `PLUGIN_ROOT`, catálogos (marketplaces) e instalação.
- [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): modelo e esforço de raciocínio definidos na criação de um agente.

## Formatos

- [Agent Skills specification](https://agentskills.io/specification): formato portátil de skill.
- [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html): formato de data e hora usado nos trechos dos handoffs.
