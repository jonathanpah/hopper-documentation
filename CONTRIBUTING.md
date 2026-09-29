# Contributing to hopper-documentation

Contributions can fix failures, clarify the content rules, support new product versions or improve the documentation. The English plugin and documentation are in `hopper-documentation-en/`, and the Brazilian Portuguese ones are in `hopper-documentation-pt-br/`. Shared GitHub policies and templates remain at the repository root. Keep both versions equivalent; one release covers both languages.

## Start with the problem

For suspected vulnerabilities, follow the [Security Policy](SECURITY.md) and report privately.

Use a bug report for a reproducible failure and a proposal for a specific change. Use [Discussions](https://github.com/jonathanpah/hopper-documentation/discussions) for questions or early ideas. Search existing issues before opening another one.

For changes to the content rules, explain the current rule, the problem it creates, the desired behavior, evidence and tradeoffs. A proposal is not approval to change the project's rules.

## Preserve the design

- The program does the mechanical work and the model writes only the content. Do not move mechanical steps back to the model.
- The skill's **Content rules** section is the single source of the rules sent to the model. Keep each rule as one bullet line.
- Handoffs are never overwritten, and a malformed handoff must not block new ones.
- The automatic path must not delay compaction, and failures must reach the user.
- Keep the program on the Python standard library, compatible with Python 3.9.
- Do not add fixed duration limits or consumption caps as incidental edits.
- Distinguish observed behavior from documentation claims and assumptions. Do not claim speed or cost improvements without comparable measurements.

## Open a pull request

1. Fork the repository and create a branch for one coherent change.
2. In each language folder you change, run `python3 -m unittest discover -s tests -v`. Add or update tests for the behavior you change.
3. Open a pull request to `main`, explaining the problem, the resulting behavior, the verification and the limitations.

A pull request proposes a change; it does not change this repository until the maintainer merges it.

## Verify proportionately

- For program changes, run the unit tests and, when the change affects model calls or hooks, one real run in the affected product. Record the product version and the observed result.
- For content rule changes, compare the handoffs produced before and after on the same synthetic conversation.
- For product compatibility claims, keep separate claims for installation, skill discovery, hook discovery, hook execution and handoff content. Passing one does not establish the others.

Use synthetic conversations and disposable folders. Never submit passwords, access tokens, private keys, personal data, private conversation histories or unredacted handoffs.

## Review and releases

Jonathan Honorio maintains the project and decides whether a change is accepted. Review does not imply a promised response time or acceptance. A release identifies a selected version and describes its changes and known limitations.

By submitting a contribution, you agree that it is provided under this repository's [MIT License](LICENSE). Follow the [Code of Conduct](CODE_OF_CONDUCT.md).
