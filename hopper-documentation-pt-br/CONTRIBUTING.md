# Como contribuir com o hopper-documentation

Contribuições podem corrigir falhas, esclarecer as regras de conteúdo, dar suporte a novas versões dos produtos ou melhorar a documentação. O plugin e a documentação ficam em inglês em `hopper-documentation-en/` e em português brasileiro em `hopper-documentation-pt-br/`. As políticas e os modelos compartilhados do GitHub ficam na raiz do repositório. Mantenha as duas versões equivalentes; cada release inclui os dois idiomas.

## Comece pelo problema

Em caso de suspeita de vulnerabilidade, siga a [Política de segurança](SECURITY.md) e relate de forma privada.

Use um relato de bug para uma falha reproduzível e uma proposta para uma mudança específica. Use as [Discussions](https://github.com/jonathanpah/hopper-documentation/discussions) para perguntas ou ideias iniciais. Procure nas issues existentes antes de abrir outra.

Para mudanças nas regras de conteúdo, explique a regra atual, o problema que ela cria, o comportamento desejado, as evidências e os prós e contras. Uma proposta não é aprovação para mudar as regras do projeto.

## Preserve o design

- O programa faz o trabalho mecânico, e o modelo escreve só o conteúdo. Não devolva etapas mecânicas ao modelo.
- A seção **Regras de conteúdo** da skill é a fonte única das regras enviadas ao modelo. Mantenha cada regra em uma única linha de lista.
- Handoffs nunca são sobrescritos. Um handoff malformado não pode bloquear novos handoffs.
- O caminho automático não pode atrasar a compactação. As falhas precisam chegar ao usuário.
- Mantenha o programa apenas com a biblioteca padrão do Python e compatível com Python 3.9.
- Não acrescente limites fixos de duração nem tetos de consumo como edições secundárias.
- Diferencie o comportamento observado das afirmações da documentação e das suposições. Não afirme ganhos de velocidade ou de custo sem medições comparáveis.

## Abra um pull request

1. Faça um fork do repositório e crie um branch para uma única mudança coerente.
2. Em cada pasta de idioma que você mudar, rode `python3 -m unittest discover -s tests -v`. Adicione ou atualize testes para o comportamento que você mudar.
3. Abra um pull request para `main`. Explique o problema, o comportamento resultante, a verificação e as limitações.

Um pull request propõe uma mudança. Ele não altera este repositório até que o mantenedor faça o merge.

## Verifique de forma proporcional

- Em mudanças no programa, rode os testes unitários. Quando a mudança afetar chamadas ao modelo ou gatilhos (hooks), faça também uma execução real no produto afetado. Registre a versão do produto e o resultado observado.
- Em mudanças nas regras de conteúdo, compare os handoffs produzidos antes e depois, com a mesma conversa sintética.
- Em afirmações de compatibilidade com um produto, mantenha afirmações separadas para instalação, descoberta da skill, descoberta do gatilho, execução do gatilho e conteúdo do handoff. O sucesso de uma não comprova as outras.

Use conversas sintéticas e pastas descartáveis. Nunca envie senhas, tokens de acesso, chaves privadas, dados pessoais, históricos privados de conversa nem handoffs sem os dados sensíveis removidos.

## Revisão e lançamentos

Jonathan Honorio mantém o projeto e decide se uma mudança é aceita. A revisão não implica promessa de prazo de resposta nem de aceitação. Um lançamento identifica uma versão escolhida e descreve as mudanças e as limitações conhecidas dela.

Ao enviar uma contribuição, você concorda que ela é fornecida sob a [Licença MIT](LICENSE) deste repositório. Siga o [Código de conduta](CODE_OF_CONDUCT.md).
