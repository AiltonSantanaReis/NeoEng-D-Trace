# Checklist de Release Pública — NeoEng-D-Trace

**Status atual:** NÃO APROVADA

Este checklist separa uma build técnica de uma release pública. Um item marcado
como “futuro” não pode ser apresentado como concluído.

## Gates obrigatórios

| Gate | Estado atual | Critério para fechar |
|---|---|---|
| R-014 — assinatura | Deferido para a primeira release pública | GUI, CLI, DLLs distribuídas e MSI assinados; cadeia e timestamp verificados |
| R-015 — publicação e dados | Aberto | Política, licença, atribuições, identidade visual e contato aprovados |
| R-016 — builder MSI | Validado tecnicamente / governança pendente | WiX 4.0.6 fixado, build reproduzível, instalação, upgrade, reparo e remoção validados; revisar termos da toolchain no gate de release |
| Qualidade funcional | Técnico aprovado | CI Linux/Windows, testes, cobertura, legado reconciliado e baseline íntegra |
| Engines externas | Validado no fixture canônico | Repetir quando o candidato de release mudar |

## Evidências exigidas para o candidato final

- commit-fonte e árvore limpa;
- versões de Python, dependências, toolchain e Windows;
- manifestos e hashes dos artefatos;
- logs sem caminhos pessoais ou segredos;
- assinatura verificada por processo independente;
- instalação, execução, exportação, atualização, reparo e desinstalação;
- política e documentação aprovadas pelo responsável do projeto.

## Decisão de roadmap

Builds de validação podem ser entregues a avaliadores sem assinatura, desde que
sejam rotuladas como pré-release técnica. A primeira release pública oficial
deve reabrir este checklist e fechar os gates pendentes; não há aprovação
automática por crescimento do projeto ou por CI verde.
