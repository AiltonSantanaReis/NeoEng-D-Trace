# Checklist de Release Pública — NeoEng-D-Trace

**Status atual:** RELEASE INICIAL DE VALIDAÇÃO PERMITIDA CONDICIONALMENTE; RELEASE PÚBLICA OFICIAL NÃO APROVADA

Este checklist separa uma build técnica de uma release pública. Um item marcado
como “futuro” não pode ser apresentado como concluído.

## Gates obrigatórios

| Gate | Estado atual | Critério para fechar |
|---|---|---|
| R-014 — assinatura | DEFERIDO PARA FUTURAS BUILDS/RELEASES OFICIAIS; não bloqueia release inicial de validação | GUI, CLI, DLLs distribuídas e MSI assinados; cadeia e timestamp verificados quando o gate for ativado |
| R-015 — publicação e dados | Documentos preparados; aprovação do proprietário pendente | Política, licença/termos, atribuições, identidade visual, contato e dados aprovados |
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

As primeiras releases podem ser releases de validação, sem assinatura, desde que
sejam rotuladas como pré-release, vinculadas a hashes e destinadas a usuários
identificados ou a uma pré-release pública claramente rotulada. A assinatura de
`R-014` fica para futuras builds/releases oficiais após validação de usuários e
crescimento do projeto. Isso não aprova a release pública oficial nem substitui
a aprovação de `R-015`; CI verde, isoladamente, nunca aprova publicação.
