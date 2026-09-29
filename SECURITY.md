# Security Policy

Report suspected vulnerabilities in hopper-documentation through GitHub's private vulnerability reporting.

## Report privately

Open [Report a vulnerability](https://github.com/jonathanpah/hopper-documentation/security/advisories/new), or select that option on the repository's [Security page](https://github.com/jonathanpah/hopper-documentation/security). A GitHub account is required.

Keep suspected vulnerabilities and exploit details out of public issues, discussions and pull requests until disclosure is coordinated with the maintainer. Use public issues for ordinary bugs and proposals, and discussions for general questions.

Include:

- The affected release tag or commit and the relevant file, rule or documentation section.
- The product (Claude Code or Codex, terminal or app), its version, operating system and configured model, without private account details.
- A minimal reproduction with synthetic data and disposable resources.
- Expected and observed behavior, potential impact and any limits of the evidence.

Do not submit passwords, access tokens, private keys, private conversation histories or unredacted handoffs. Test only resources you are authorized to use.

## Scope and security expectations

This repository contains, in English and Brazilian Portuguese, a skill, a program that runs as a hook and on request, plugin manifests and documentation. Relevant reports include flaws that could:

- expose credentials or private conversation content in handoffs, logs or messages;
- write anywhere other than the `docs-by-hopper-documentation` folder of the working directory, the log, the lock file and the job files it was asked to create, or overwrite an existing handoff;
- read a conversation other than the one that triggered the documentation;
- make the model follow instructions found in the conversation, or treat a recorded pending item as an authorization.

The intended boundaries are:

- The program reads the history of the conversation it received, after checking its identifier, and, on the first handoff of a folder, the documentation files of the working directory.
- In Claude Code, the model that writes the content runs without tools, MCP servers or skills. In Codex, before compaction, it keeps the code and subagent tools that GPT-6 Luna requires, in a read-only sandbox without network, web search, apps or the user's configuration, and is told not to use them. On request in Codex, the documentation agent uses tools only to read its job, write the content and run the program.
- Secrets are masked before content is sent, written or reported. Masking covers common formats, not every possible secret.
- Handoffs record history; they do not grant permission to repeat operations.

Enforcement also depends on the host's permissions, sandbox and model behavior. If another product is also affected, use that product's security reporting process as appropriate.

## Versions and handling

Identify the version you used. Jonathan Honorio reviews reports through the private reporting channel. Confirmed affected versions and fixes can be documented in repository changes, releases or security advisories. No response or remediation deadline is guaranteed.
