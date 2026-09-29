# Changelog

## 0.1.1

Plugin display name fixed to `hopper-documentation`, matching the skill name and CLI identifier. No changes to the skill, program, or hooks.

## 0.1.0

First version.

- Handoffs in `docs-by-hopper-documentation`, with an index and one handoff per documented excerpt.
- Automatic documentation before compaction, through a `PreCompact` hook shared by Claude Code and Codex.
- Documentation on request: in the background in Claude Code, and through an agent with the configured model in Codex.
- Program for the mechanical work: history reading from the last recorded line, secret masking, one model call per part, checking of the sources quoted by the model, publication without overwriting and index rebuild.
- On the first handoff of a folder, the documentation already in the working directory becomes the first topic.
- The user's answers to the assistant's structured questions and approved plans are documented.
- Default models: Claude Sonnet 5.5 with xhigh effort and GPT-6 Luna with xhigh effort, configurable.
- The writing model runs without tools in Claude Code, and with only the tools its model requires in Codex.
