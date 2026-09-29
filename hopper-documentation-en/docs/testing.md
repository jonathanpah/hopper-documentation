# Testing

## Unit tests

```sh
python3 -m unittest discover -s tests -v
```

The tests call no model and install nothing. They use fake `claude` and `codex` executables and temporary folders. They cover:

- extraction of user messages and assistant replies from both history formats, including the user's answers to structured questions, approved plans and messages sent while the assistant was working, counting records written again after a resume only once, and excluding reasoning, tool calls and results, commands, compaction summaries, side chains, system reminders, injected context and internal texts;
- conversation identity, including a fork whose history starts with another session's records and a history of another session renamed to the requested id, reading limit and resume point, including a moved line and a missing one;
- splitting into parts without splitting a history line, and cutting an oversized line with a note in Gaps;
- text that UTF-8 cannot write, such as half of an emoji in the history or a file name with invalid bytes, replaced instead of stopping the documentation;
- reading of existing documentation: skipped folders, empty files, handoffs in subfolders, the reading order, the reading budget, the list of files read in part or not read, and files and folders that cannot be read;
- secret masking: labeled values, with names read word by word so that counters such as `max_tokens` stay visible, including quoted values with spaces, JSON escaped one to four times and names right after an escape; connection addresses; command options and values stated in prose, quoted or not; access tokens, including whole JWTs with compact or spaced JSON; long generated strings, while keeping hashes (even after letters such as SHA), key fingerprints, UUIDs and technical identifiers; and its time on long inputs without separators;
- publication without overwriting, eight conversations publishing at once, six runs of the same conversation at once, a malformed handoff, a long summary, a masked summary in the handoff and the index, index recovery after a failure, a file system without hard links, a failed write that leaves the excerpt for the next run, a repeated section title and a field the model returned escaped twice;
- checking of the sources quoted by the model: a missing reference, an invented passage or one outside the source, a passage that joins two messages, cuts marked with an ellipsis, Markdown formatting left out or cut (bold, inline code, code blocks and an ellipsis inside code), a change in identifiers, globs, operators and code between backticks, the comparator's reserved characters in the source or the quote, a literal `\n` in the source, a line number written as a number or labeled ("line 9"), an ambiguous or missing reference, a source in the previous handoff, a masked secret quoted back and a failure that neither publishes nor moves the resume point, also in the manual Codex flow;
- hook exit codes and messages for each product, reentry, invalid events, sessions without a history file, product detection, and failure messages that carry the executor's error;
- the `prepare`, `publish`, `run` and `config` commands, including local times in the prompt, the Codex agent flow through every part up to the reading limit, and a partial result when the next part cannot be written;
- the options that turn off tools, hooks, plugins and the user's instruction files in both model calls, and the Claude system prompt.

## Real runs

Real runs used Claude Code and Codex on Linux, and Codex on macOS. On macOS, Claude Code also wrote a handoff with a real model when called from the command line with a synthetic history. They covered:

- real conversations of both products, long ones included, documented in two rounds to check continuation, with every handoff checked against its conversation;
- new sessions of both products resuming the work from the handoffs alone;
- native compaction in the interactive terminal interfaces, manual and automatic in both products (in Claude Code, with a smaller compaction window set for the test), with the conversation continuing while the documentation ran, and failure notices;
- documentation on request in both products, including a Codex agent going through the parts of a long conversation;
- edge cases: runs of the same conversation at once, both products in the same folder, a conversation in English, planted secrets, a large set of existing documentation and a whole home folder;
- installation, update and removal in temporary configurations, from a local folder and from a git repository served over HTTP, with the installed hook run as the product runs it;
- runs over every local history of both products, without a model: identity, parts, a simulated documentation of every part, masking and time;
- failure injection without a model: invalid or missing model output, interruptions at random moments, file system and permission errors, and damaged histories.

Model behavior can vary between runs and product versions, so a change that affects model calls, hooks or content rules needs a new real run in the affected product.

## Not verified yet

- Runs inside the desktop apps of Claude and ChatGPT; the tests used the interactive terminal interfaces of the same products.
- Claude Code on macOS through native compaction or inside the desktop app; on macOS, only the command-line call with a synthetic history was exercised.
- Installation and update from the GitHub repository; the tests used a git repository served over HTTP.
- Automatic compaction in Claude Code with its default window; the tests set a smaller window to trigger it.
