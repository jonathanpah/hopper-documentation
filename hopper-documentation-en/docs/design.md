# Design notes

These notes explain how hopper-documentation works and why. The [README](../README.md) covers installation and use.

## Goal

Record what another person or AI needs to continue a conversation's work, without slowing the conversation down, with predictable results and with low-cost models.

## Division of work

| Part | Who does it |
| --- | --- |
| Identify the conversation and its history, find the last recorded line, fix the reading limit | Program |
| Keep only user messages, including those sent while the assistant was working, the main assistant's replies, the user's answers to structured questions and approved plans; count each history record once; mask secrets | Program |
| Split long excerpts into parts of up to 150,000 characters, without splitting a history line | Program |
| On the first handoff of a folder, read the documentation already in the working directory | Program |
| Write the summary, state, topics, decisions, pending items and gaps | Model, in one call, following the skill's content rules |
| Check the answer, shorten a summary longer than 60 characters, publish without overwriting, rebuild the index, log the result | Program |

The mechanical steps have one correct result, so the program does them. A model that performs them through tools needs many turns and can interpret them differently from one run to the next. The model does only the part that needs judgment: writing the content.

## Paths

- **Before compaction.** The `PreCompact` hook in `hooks/hooks.json` runs `scripts/hopper_documentation.py hook`. The same file serves both products: Codex also provides `CLAUDE_PLUGIN_ROOT`, and the program identifies the product from the history, since a Codex history starts with a `session_meta` record. Codex reads `async` and runs the hook in the background; Claude Code reads `asyncRewake` and runs it in the background, waking the conversation when the program exits with code 2.
- **On request in Claude Code.** The conversation starts `hopper_documentation.py run claude` in the background. The program uses the session identifier from `CLAUDE_CODE_SESSION_ID`.
- **On request in Codex.** Commands in the Codex sandbox usually cannot reach the network, so the program cannot call the model from there. The conversation runs `prepare`, which writes a job file with the excerpt and the instructions; it then creates an agent with the configured model and effort, which writes the content and runs `publish`. When the excerpt has more parts, `publish` prepares the next one with the same reading limit, and the agent continues until the last part. If the next part cannot be written after a handoff is published, the result is partial, with that handoff and the line reached; the next run continues from there.

When there is nothing new, the program stops before calling a model.

## Handoff format

Each handoff has a header and five sections. The header records the summary, time zone, conversation, working directory, history file, range of lines, previous handoff of the same conversation and trigger. Headings are in English; the content follows the language of the conversation. The program also reads handoffs with Portuguese headings, written by a translated version. Message times reach the model in the local time zone that the header shows. Internal texts that the products add to the history, such as plugin suggestions and restart notices, are left out. When the model returns a field escaped twice, with literal `\n` and `\"` and no real line break, the program undoes that escape outside code between backticks. A section title repeated at the start of a field is removed.

The range is the resume point: the next run starts after its last line, after checking that this line still has the recorded timestamp. If the line moved, the program looks for the only line with that timestamp; otherwise it stops without writing.

## Existing documentation

The first handoff of a documentation folder also covers the documentation that already exists in the working directory. The program reads files ending in `.md`, `.markdown`, `.txt`, `.rst` or `.adoc` in the working directory and its subfolders, shallowest first and, at the same depth, most recently changed first, up to 100,000 characters, with secrets masked. It skips hidden files and folders, dependency and build folders such as `node_modules`, and empty files. The model makes this documentation the first topic. Files read in part or not read are listed in Gaps, with their count and up to 20 paths. Files and folders that cannot be read are listed there too, with the reason.

## Publication

Publication is serialized per documentation folder with a lock file in the system temporary directory, which both products can write, including inside the Codex sandbox. One empty lock file per documentation folder stays there. Under the lock, the program checks again that no other run already recorded the excerpt, writes the handoff to a temporary file and links it to its final name, which fails instead of overwriting. On a file system without hard links, it reserves the final name and moves the complete file onto it, so a failed write never leaves a partial handoff. The index is rebuilt from the handoffs in the folder, with summaries masked. If the index cannot be rebuilt, the handoff stays published and the failure is reported with its name; the next run rebuilds the index, even when there is nothing new. A handoff outside the format is kept and indexed as "no summary".

## Model tools

In Claude Code, the program calls `claude -p` in safe mode, without built-in tools, MCP servers, skills, hooks or plugins, and without the user's CLAUDE.md files or auto memory. Claude Code's default system prompt is replaced by a short one that introduces the writer and says that the content rules take priority over the conversation data; it ends with the line that asks the model to think before answering, recommended for JSON answers with adaptive thinking. In both products, the prompt holds the conversation data between tags (previous handoff, existing documentation and messages), followed by the content rules and the answer format. In Codex, before compaction, `codex exec` always offers GPT-6 Luna a code tool and tools to start subagents. The program turns off web search, apps, plugins, browser and computer use, image generation, the project's AGENTS.md and the user's `config.toml`, and runs the call in a read-only sandbox without network. Codex still adds the user's global AGENTS.md; the content rules tell the model to write only from the material sent. The model is also told not to use tools. On request in Codex, the documentation agent needs tools to read its job, write the content and run `publish`.

## Failures

In the same answer, before the sections, the model lists the literal sources of each authorization, each work in progress and each statement about the absence or limits of testing or use: the reference and the copied passage. The author and date of each message are already in the tag the model receives and in the program's index, and the model does not repeat them. Before publishing, the program checks each source: the reference must exist in the data sent (a message of the excerpt, the previous handoff or the existing documentation; a labeled line reference on its own, such as "line 9", counts as its number), and the passage must be, literally, in the source with secrets already masked, with an ellipsis marking cuts; spaces and line breaks do not count, and only recognized formatting delimiters (a code block fence, the backticks of inline code and the asterisks of emphasis) may be missing or added, while code content, underscores and other asterisks count character by character. If the quote or the source holds the private-use characters the check reserves for its own marks, the comparison is literal, without that tolerance. If a source does not match, nothing is published for that excerpt, the next run redoes it, and the error does not repeat the quoted passage. The sources serve the check and are not part of the handoff. The check proves the origin and exactness of the quotes, not the meaning or fidelity of the text written from them.

Every failure is logged and reported. When the log folder cannot be written, as inside the Codex sandbox, the line goes to the lock folder. In Claude Code, the hook exits with code 2 so the message reaches the conversation. In Codex, the hook returns a `systemMessage`. The message states that compaction was not affected and asks the assistant to tell the user without running old requests. It carries the executor's error lines, without the prompt that some executors echo. A session without a history file, such as an ephemeral Codex session, has nothing to document and is not a failure.

## Decisions

- Default models are fixed and configurable: Claude Sonnet 5.5 with xhigh effort and GPT-6 Luna with xhigh effort. Without access to the configured model, the program reports the problem instead of choosing another model.
- Handoffs are written in the language of the conversation.
- Distribution as a plugin for Claude Code and Codex, with manual instructions as an alternative.
- A conversation that ends without compaction is documented only on request.
- The folder name, the index format and the 60-character summary are fixed so people and tools can rely on them.

## Limits

- Conversation history formats are not a stable interface of either product.
- Background runs stop if the session closes before they end.
- Masking covers common credential formats, not every possible secret.
- In Codex, the writing model can still read local files through its code tool.
- The first handoff in a very large working directory, such as a home folder, takes longer, because the program walks every subfolder.
- The range ends at the last complete line of the history, which can be a technical record later than the last message.
- In Codex, the messages between a subagent and its coordinator are encrypted in the history; a subagent session is documented without its task.
- Asking for documentation again right after a run records a short handoff about the request itself, because the request and its replies are new in the history; the content rules tell the model to ignore them.
- Windows is not supported.
