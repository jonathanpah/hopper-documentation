# Document index

- [README](README.md): purpose, requirements, installation, use, configuration, privacy and limits.
- [Skill](skills/hopper-documentation/SKILL.md): what the assistant does on request, and the content rules sent to the model.
- [Program](scripts/hopper_documentation.py): history reading, secret masking, model call, publication and index.
- [Hook](hooks/hooks.json): the `PreCompact` hook shared by Claude Code and Codex.
- [Design notes](docs/design.md): division of work, paths, format, existing documentation, publication, model tools, failures, decisions and limits.
- [Testing](docs/testing.md): unit tests, what real runs checked and what is not verified yet.
- [References](docs/references.md): official documentation consulted.
- [Tests](tests/test_hopper_documentation.py): unit tests that call no model.
- [Changelog](CHANGELOG.md): versions and changes.
- [Contributing](../CONTRIBUTING.md), [Security Policy](../SECURITY.md), [Code of Conduct](../CODE_OF_CONDUCT.md) and [License](LICENSE).
- Plugin manifests: [Claude Code](.claude-plugin/plugin.json), [Codex](.codex-plugin/plugin.json); marketplaces: [Claude Code](.claude-plugin/marketplace.json), [Codex](.agents/plugins/marketplace.json).

- [Português (Brasil)](../hopper-documentation-pt-br/index.md): equivalent plugin and documentation, released with the English version.
