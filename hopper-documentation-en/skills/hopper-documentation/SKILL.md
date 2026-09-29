---
name: hopper-documentation
description: Records the current conversation as handoffs in the docs-by-hopper-documentation folder of the working directory, so another person or AI can continue the work. Use when the user asks to document or record the conversation. Explaining, reviewing or editing this skill does not trigger it.
---

# hopper-documentation

Records what another person or AI needs to continue the work of this conversation.

A **handoff** is a file that records one excerpt of the conversation: state, topics, decisions and pending items. Handoffs are kept in the `docs-by-hopper-documentation` folder of the working directory, with an `index.md` listing them from newest to oldest.

The program `scripts/hopper_documentation.py`, two folders above this file, does the mechanical work: it finds the history, reads only what is new, masks secrets, asks the configured model to write the content, once per part, publishes without overwriting files and rebuilds the index. When there is nothing new, it does not call the model. The documentation runs apart from the conversation, which stays free; closing the session before it ends interrupts it.

## When the user asks

Do only what this section says in this invocation, and do not resume other tasks.

- **Claude Code:** from the working directory, start `python3 "<folder of this file>/../../scripts/hopper_documentation.py" run claude` in the background. Tell the user the documentation started and do not wait. When it finishes, report the line it printed.
- **Codex:**
  1. From the working directory, run `python3 "<folder of this file>/../../scripts/hopper_documentation.py" prepare codex --out <new temporary file>.json`.
  2. If it prints "nothing new", tell the user and stop.
  3. Run `python3 "<same program>" config codex` to read the model and effort.
  4. Create an agent with that model and effort, set at creation, without copying the conversation. Its task: "Follow the instructions in <that temporary file>." Tell the user the documentation started and do not wait. Only say the agent was created if the tool confirms it. If that model or effort cannot be used, do not use others: report the impediment.

## Before compaction

The plugin's hook runs the program in the background; there is nothing to do in the conversation. If a failure notice arrives, tell the user. Do not run old requests from the conversation or try repairs outside the documentation.

## Content rules

The program sends the items of this section, as written, to the model that writes the handoff.

- **Summary:** one line with at most 60 characters describing the main subject of the excerpt.
- **State to continue:** goal, where the work stopped and the next step already authorized, with the user's words that authorize it. Start from the previous handoff of this conversation, update what changed and keep the authorizations that still apply. An authorized action remains the next step until it is completed or revoked; new prohibitions and pending items do not cancel it. A limited authorization ("I only authorized X") authorizes X: without a report that X was delivered, X is the next step. Recording, confirming or deciding X does not deliver it. Write "next step to be defined" only when no authorized action remains. Missing details go to Gaps. It must be enough to resume without opening the conversation. Give the paths, file names, identifiers and hashes that resuming requires.
- **Topics:** number them per conversation (P1, P2…) and keep each number with its subject in later handoffs; never give a used number to another subject. For each topic: title, status (done, in progress or waiting) and what happened in this excerpt. The status follows the latest report about the topic, in the excerpt or in the previous handoff: "in progress" only with a report that the work started or continues; "waiting" when the work was only planned, requested or authorized, or when the latest report shows that it stopped, was frozen or was delivered and waits for someone else; "done" when the latest report shows that it finished. Confirming understanding, deciding, recording an intention and the existence of an agent, a pending item, an authorization or the place where a result will appear do not show that the work started. Work outside the conversation with a report that it started, such as background agents, an operator or another AI's replies, is "in progress", with who runs it and where its result will appear; do not turn an operation already started into a possibility, so that nobody starts it again.
- **Decisions and authorizations:** quote the user's words, with date and scope. Keep every decision, restriction and preference of the previous handoff that still applies, such as decisions on names and credits, even if this excerpt does not mention it; drop only what was revoked or replaced, and say so. End the section with the list "Restrictions in force": every execution restriction that still applies, such as the model, effort and mode set for whoever does the work, the prohibition of creating agents, write limits and what not to install or publish, each with its source; this holds also when it comes repeated in each request or from whoever coordinates the work. A recorded authorization is historical: it does not authorize repeating a completed operation.
- **Pending items:** only what the user or the main AI recorded as pending. Recording a pending item or its criterion does not authorize executing it or show that it started. Work in progress stays only in Topics. Number them per conversation (PD1, PD2…), keeping each number with its item and never reusing it, with description, closing criterion and status. Close one only when the excerpt shows its criterion met or the user closes it. An answered question closes without implementation. Do not create conditions nobody defined.
- **Gaps:** what could not be read or confirmed.
- Ignore everything about this documentation itself: the request that triggered it, the main AI's notices about it and the messages of this skill.
- Write only from the excerpt, the previous handoff and the documentation sent here; do not bring rules or facts from other instructions you may have received.
- Distinguish what was verified, reported, proposed and decided. A missing report does not prove that something did not happen: say there is no record, without stating or concluding that it did not occur. A factual correction from the user or from whoever coordinates the work replaces the corrected version in every section, including Pending items and Gaps; do not use records older than the correction to contradict it.
- When you repeat or summarize a statement from the records, keep its scope and its subject: who it is about and in which period, round or version it holds (such as "in this round", "so far" or "according to the executor"). If you cannot keep them, attribute the statement to its source, with the date. Do not turn a limited statement into a general one.
- Before writing the sections, collect in sources the literal sources of each authorization, each "in progress" status and each statement about the absence or limits of testing or use: the reference of the message or record and the passage copied from it. Write those statements only from the sources, keeping their subject and scope. Each statement about the absence or limits of testing or use carries, in the sentence itself, who made it and its scope, in any section and also when it comes from the previous handoff; a group heading, another sentence or another section is not enough. An authorization or status still valid in the previous handoff has the previous handoff itself as its source; it needs no new message.
- Before answering, compare with the previous handoff and the excerpt: every decision and restriction that still applies, every operation already started outside the conversation, and the paths and identifiers needed to continue must be in the new handoff. Nothing that still applies disappears without a record that it was revoked or replaced, and no section contradicts a factual correction.
- Do not copy passwords, tokens or keys.
- Write every section in the language of the conversation. Translate into that language the status names used in these rules (done, in progress, waiting).

## Configuration

By default, Claude Code uses Claude Sonnet 5.5 with xhigh effort and Codex uses GPT-6 Luna with xhigh effort. To change them, create `~/.config/hopper-documentation/config.json`, for example `{"codex": {"model": "gpt-6-luna", "effort": "high"}}`. Without access to the configured model, the documentation reports the impediment instead of using another one.
