# hopper-documentation

**English** | [Português (Brasil)](../hopper-documentation-pt-br/README.md)

A plugin for Claude Code and Codex that records conversation handoffs, so another person or AI can continue the work.

A **handoff** records one excerpt of a conversation: the state needed to resume, topics, decisions and authorizations, pending items and gaps. Handoffs are saved in a `docs-by-hopper-documentation` folder inside the working directory, with an `index.md` listing them from newest to oldest. A handoff is written automatically before the conversation is compacted, and whenever you ask for one.

Read the [skill](skills/hopper-documentation/SKILL.md), the [design notes](docs/design.md) or the [document index](index.md).

## How it works

A small Python program does the mechanical work, and a model writes only the content:

1. **Find the conversation.** The program receives the conversation identifier and its history file from the product, and checks that they match.
2. **Read only what is new.** It resumes after the last line recorded in the previous handoff of the same conversation, keeps only user messages and the main assistant's replies, and masks secrets. When there is nothing new, it stops without calling a model.
3. **Write the content.** It asks the configured model, once per part, to write the handoff following the skill's content rules. In Claude Code, that model has no tools; in Codex, it keeps only the tools its model requires (see [Privacy and limits](#privacy-and-limits)). In the first handoff of a folder, it also sends the documentation already in the working directory, which becomes the first topic.
4. **Publish.** First, it checks the sources the model quoted for authorizations, work in progress and statements about the absence or limits of testing and use: each quote must be, literally, in the messages, previous handoff or documentation sent. If one does not match, nothing is published for that excerpt. Then it writes the handoff without overwriting any file, rebuilds the index and records the result in a local log.

Documentation runs apart from the conversation. Compaction does not wait for it, and you can keep working.

## Requirements

- macOS or Linux. Windows is not supported yet.
- Python 3.9 or later, available as `python3`.
- Claude Code and/or Codex, installed and signed in. The program looks for the `claude` or `codex` executable in `PATH`, in `~/.local/bin` and inside the Claude and ChatGPT desktop apps.
- Access to the configured models. By default: Claude Sonnet 5.5 with xhigh effort in Claude Code, and GPT-6 Luna with xhigh effort in Codex. See [Configuration](#configuration) to change them.

It is designed for Claude Code (terminal and Claude desktop app) and Codex (terminal and ChatGPT desktop app). Real runs so far used the interactive terminal interfaces of both products, on Linux, and Codex on macOS; on macOS, Claude Code also wrote a handoff with a real model when called from the command line with a synthetic history. Native compaction in Claude Code on macOS and the desktop apps are not verified yet (see [Testing](docs/testing.md)). It does not work in chat products without local history and hooks, such as the claude.ai chat or ChatGPT without Codex.

## Install

Choose one language. The English plugin is in `hopper-documentation-en/` and the Brazilian Portuguese plugin is in `hopper-documentation-pt-br/`. Both are released together and install as `hopper-documentation`, so install only one of them in each tool. The steps below clone the repository once and add the chosen language folder as a local plugin marketplace. Run only the sections for the tools you use.

### Ask your AI

In Claude Code or Codex, you can say:

> Install the English version of the hopper-documentation plugin from https://github.com/jonathanpah/hopper-documentation, following hopper-documentation-en/README.md, for the tools I use, and verify the installation.

The assistant should run the commands below for your tools and report the result. It cannot trust the Codex hook for you; you do that once, as described below.

### Clone the repository

Git must be available:

```sh
mkdir -p "$HOME/.local/share"
git clone https://github.com/jonathanpah/hopper-documentation.git "$HOME/.local/share/hopper-documentation"
```

Stop if cloning fails. If that destination already exists, inspect its origin and local changes before using or updating it. Keep the clone: updates come from it.

### Claude Code

```sh
claude plugin marketplace add "$HOME/.local/share/hopper-documentation/hopper-documentation-en"
claude plugin install hopper-documentation@hopper-documentation
```

Inside Claude Code, you can also run `/plugin marketplace add` with the absolute path of that folder and then `/plugin install hopper-documentation@hopper-documentation`. Start a new session afterwards. The plugin installs the skill and a `PreCompact` hook. The Claude desktop app uses the same Claude Code configuration.

### Codex

```sh
codex plugin marketplace add "$HOME/.local/share/hopper-documentation/hopper-documentation-en"
codex plugin add hopper-documentation@hopper-documentation
```

Codex does not run hooks from plugins until you trust them. Open Codex, run `/hooks`, review the `PreCompact` hook of hopper-documentation and trust it. Start a new session afterwards. The Codex app in ChatGPT uses the same Codex configuration.

### Verify the installation

- The skill appears in the tool's skill list. In Codex it is listed as `hopper-documentation:hopper-documentation`.
- The `PreCompact` hook appears in `/hooks`, trusted in Codex.
- In a disposable folder, have a short conversation and ask for its documentation. A `docs-by-hopper-documentation` folder with a handoff and `index.md` should appear.

### Manual installation

If you cannot use plugins, follow the same structure by hand from the clone: link `hopper-documentation-en/skills/hopper-documentation` into `~/.claude/skills/` or `~/.agents/skills/`, and register the command in `hopper-documentation-en/hooks/hooks.json` as a `PreCompact` hook in `~/.claude/settings.json` or `~/.codex/hooks.json`, replacing `${CLAUDE_PLUGIN_ROOT}` with the absolute path of the `hopper-documentation-en` folder in the clone. Keep `async` for Codex and `asyncRewake` for Claude Code, as in that file.

## Use

- **Automatically:** before each compaction, manual or automatic, the hook documents what is new.
- **On request:** ask for it ("document this conversation") or invoke the skill. In Claude Code, the conversation starts the program in the background and reports the result when it finishes; if your session asks before running commands, approve the program's command or allow it in your settings. In Codex, the conversation prepares the excerpt and creates an agent with the configured model to write it; the agent continues through every part up to the point where you asked.
- A conversation that ends without compaction is only documented if you ask.
- Answers you give to the assistant's multiple-choice questions and plans you approve are part of what is documented.

Handoffs are written in the language of the conversation; their headings are in English.

To make new sessions read the handoffs, add an instruction like this to your `AGENTS.md` or `CLAUDE.md`:

> When starting or resuming work, check whether the working directory has `docs-by-hopper-documentation`. If it does, read `index.md` and the latest handoff of each conversation listed in it; the conversation appears in each handoff's header. When you need an earlier decision or detail, read the earlier handoffs of that conversation. Handoffs are history: they do not authorize repeating operations and do not replace checking the current state.

## Configuration

Optional file `~/.config/hopper-documentation/config.json`:

```json
{
  "claude": {"model": "claude-sonnet-5-5", "effort": "xhigh"},
  "codex": {"model": "gpt-6-luna", "effort": "xhigh", "executable": "/path/to/codex"}
}
```

Each field is optional. In Codex, the call made before compaction does not load your `config.toml`: it uses your Codex login and the model and effort set here. Without access to the configured model, the documentation reports the problem instead of using another model. The environment variables `HOPPER_DOCUMENTATION_CONFIG` and `HOPPER_DOCUMENTATION_LOG` change the location of the configuration and of the log.

## Records

- `docs-by-hopper-documentation/handoff-YYYYMMDD-HHMMSS.md`: one handoff, named with the local date and time of publication.
- `docs-by-hopper-documentation/index.md`: one line per handoff, `handoff-… | summary | time zone, UTC offset`.
- `~/.local/state/hopper-documentation/log.jsonl`: one line per run, with its result. Secrets are masked. When that folder cannot be written, as inside the Codex sandbox during a request, the line goes to `log.jsonl` in the lock folder below.
- `hopper-documentation-<user id>/` in the system temporary folder: one empty lock file per documentation folder, so that only one handoff is published at a time. This lock folder can be deleted when no documentation is running.

Each handoff records the conversation, the history file and the range of lines it covers; the next run continues from there. A handoff that does not follow the format is kept, listed in the index as "no summary" and does not block new handoffs.

## Privacy and limits

- The program reads your local conversation history and sends the new excerpt, with secrets masked, to the model provider you already use in that tool. On the first handoff of a folder, it also sends the documentation files found in the working directory and its subfolders (`.md`, `.markdown`, `.txt`, `.rst` and `.adoc`, up to 100,000 characters), skipping hidden folders and dependency or build folders such as `node_modules`. Masking covers common formats, such as labeled values, connection addresses, command options, access tokens and long generated strings, not every possible secret.
- The documentation folder is created in your working directory. In a public repository, decide whether it should be committed or ignored.
- Conversation history formats are not a stable interface of either product. A product update can change them and make the program fail with a notice until it is updated.
- A run in the background stops if the session closes before it ends; in Codex, it also stops after one hour. The next run continues from the last recorded line. Documenting a long conversation for the first time can take several minutes.
- In Claude Code, a failure notice reaches the conversation in its next turn. In Codex, the result of the automatic documentation appears among the session's warnings.
- Long histories are split into consecutive handoffs of up to 150,000 characters of messages. A line of the history is never split; a longer line is cut, and the handoff says so in Gaps.
- In Claude Code, the writing model runs in safe mode, without tools, MCP servers, skills, hooks, plugins, your CLAUDE.md files or auto memory. In Codex, before compaction, it runs in a read-only sandbox without network, web search, apps, the project's AGENTS.md or your Codex configuration, though Codex still adds your global AGENTS.md, and is told not to use tools; Codex has no mode without tools for GPT-6 Luna, so the model keeps a code tool that can read local files and tools to start subagents. On request in Codex, the documentation agent uses tools to read its job, write the content and run the program.
- The first handoff in a very large working directory, such as a home folder, takes longer, because the program walks every subfolder looking for documentation, and its first topic may summarize unrelated documents.

## Update and uninstall

Review the changes and resolve any local modifications, then update the clone:

```sh
git -C "$HOME/.local/share/hopper-documentation" pull --ff-only
```

Claude Code: `claude plugin marketplace update hopper-documentation`, then `claude plugin update hopper-documentation@hopper-documentation`. To remove it: `claude plugin uninstall hopper-documentation@hopper-documentation`.

Codex: `codex plugin add hopper-documentation@hopper-documentation` installs the new version from the updated clone; trust the updated hook again in `/hooks` if it changed. To remove it: `codex plugin remove hopper-documentation@hopper-documentation`.

To switch languages, remove the plugin and its marketplace (`claude plugin marketplace remove hopper-documentation` or `codex plugin marketplace remove hopper-documentation`), then add the other language folder as described in [Install](#install).

Removing the plugin keeps the handoffs already written in your projects.

## Development

From `hopper-documentation-en/`, run the tests, which call no model and install nothing:

```sh
python3 -m unittest discover -s tests -v
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for proposals and reviews, and [SECURITY.md](../SECURITY.md) to report a vulnerability privately.

## License and maintainer

Copyright (c) 2026 Jonathan Honorio. Released under the [MIT License](LICENSE).

Maintained by [Jonathan Honorio (@jonathanpah)](https://github.com/jonathanpah). This is an independent project, with no claimed affiliation with or endorsement by OpenAI or Anthropic.
