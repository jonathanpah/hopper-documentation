# References

Official documentation consulted while building this plugin.

## Claude Code

- [Hooks](https://code.claude.com/docs/en/hooks): `PreCompact` event, `async` and `asyncRewake` fields, input fields and exit codes.
- [Skills](https://code.claude.com/docs/en/skills): skill format and frontmatter.
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference): plugin manifest, standard layout, `hooks/hooks.json` and `${CLAUDE_PLUGIN_ROOT}`.
- [Data usage](https://code.claude.com/docs/en/data-usage): local transcripts and their retention.

## Codex

- [Hooks](https://learn.chatgpt.com/docs/hooks): `PreCompact` event, input fields, `async`, trust review and `systemMessage`.
- [Build plugins](https://developers.openai.com/codex/plugins/build): plugin layout, hooks, `PLUGIN_ROOT`, marketplaces and installation.
- [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): model and reasoning effort set when an agent is created.

## Formats

- [Agent Skills specification](https://agentskills.io/specification): portable skill format.
- [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html): date and time format used in handoff ranges.
