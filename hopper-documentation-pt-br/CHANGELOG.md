# Registro de mudanças

## 0.1.1

Nome de exibição do plugin fixado em `hopper-documentation`, igual ao nome da skill e ao identificador usado nas CLIs. Sem alterações na skill, no programa ou nos hooks.

## 0.1.0

Primeira versão.

- Handoffs em `docs-by-hopper-documentation`, com um índice e um handoff por trecho documentado.
- Documentação automática antes da compactação, por meio de um gatilho (hook) `PreCompact` compartilhado pelo Claude Code e pelo Codex.
- Documentação a pedido: em segundo plano no Claude Code e, no Codex, por meio de um agente com o modelo configurado.
- Programa para o trabalho mecânico: leitura do histórico a partir da última linha registrada, ocultação de segredos, uma chamada ao modelo por parte, conferência das fontes citadas pelo modelo, publicação sem sobrescrever e reconstrução do índice.
- No primeiro handoff de uma pasta, a documentação que já existe no diretório de trabalho vira a primeira pauta.
- As respostas do usuário às perguntas estruturadas da IA e os planos aprovados entram na documentação.
- Modelos padrão: Claude Sonnet 5.5 com esforço xhigh e GPT-6 Luna com esforço xhigh, configuráveis.
- O modelo que escreve roda sem ferramentas no Claude Code e, no Codex, só com as ferramentas que o modelo exige.
