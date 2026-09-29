# Índice de documentos

- [README](README.md): objetivo, requisitos, instalação, uso, configuração, privacidade e limites.
- [Skill](skills/hopper-documentation/SKILL.md): o que o assistente faz a pedido e as regras de conteúdo enviadas ao modelo.
- [Programa](scripts/hopper_documentation.py): leitura do histórico, ocultação de segredos, chamada ao modelo, publicação e índice.
- [Gatilho (hook)](hooks/hooks.json): o gatilho `PreCompact` compartilhado pelo Claude Code e pelo Codex.
- [Notas de design](docs/design.md): divisão do trabalho, caminhos, formato, documentação existente, publicação, ferramentas do modelo, falhas, decisões e limites.
- [Testes](docs/testing.md): testes unitários, o que as execuções reais conferiram e o que ainda não foi verificado.
- [Referências](docs/references.md): documentação oficial consultada.
- [Código dos testes](tests/test_hopper_documentation.py): testes unitários que não chamam nenhum modelo.
- [Registro de mudanças](CHANGELOG.md): versões e mudanças.
- [Como contribuir](CONTRIBUTING.md), [Política de segurança](SECURITY.md), [Código de conduta](CODE_OF_CONDUCT.md) e [Licença](LICENSE).
- Manifestos do plugin: [Claude Code](.claude-plugin/plugin.json), [Codex](.codex-plugin/plugin.json); catálogos (marketplaces): [Claude Code](.claude-plugin/marketplace.json), [Codex](.agents/plugins/marketplace.json).

- [English](../hopper-documentation-en/index.md): plugin e documentação equivalentes, publicados na mesma versão.
