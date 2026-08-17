# Checklist de Release Pública — NeoEng-D-Trace

**Status atual:** RELEASE OFICIAL `v0.2.0` PUBLICADA; `R-014`, `R-015` e a execução dinâmica das engines não são gates obrigatórios.

Este checklist registra a release pública `v0.2.0` e separa gates concluídos de riscos aceitos/deferidos. Um item marcado
como “futuro” não pode ser apresentado como concluído.

## Gates obrigatórios

| Gate | Estado atual | Critério para fechar |
|---|---|---|
| R-014 — assinatura | RISCO ACEITO; NÃO É GATE | Assinatura é melhoria opcional futura; a ausência deve ser declarada, nunca apresentada como existente |
| R-015 — publicação e dados | ROADMAP NÃO BLOQUEANTE | Formalizações podem ser adicionadas conforme decisão do proprietário; não são pré-condição técnica para publicar ou comercializar |
| R-016 — builder MSI | APROVADO | WiX 4.0.6 fixado, build reproduzível, instalação, upgrade, reparo e remoção validados |
| Qualidade funcional | Técnico aprovado | CI Linux/Windows, testes, cobertura, legado reconciliado e baseline íntegra |
| Engines externas | Validado no fixture canônico | Repetir quando o candidato mudar; execução dinâmica no CI não é requisito |

## Evidências exigidas para o candidato final

- commit-fonte e árvore limpa;
- versões de Python, dependências, toolchain e Windows;
- manifestos e hashes dos artefatos;
- logs sem caminhos pessoais ou segredos;
- instalação, execução, exportação, atualização, reparo e desinstalação;
- documentação do estado real, limitações e riscos;
- política e documentação do projeto sem dados inventados ou alegações jurídicas não comprovadas.

## Decisão vigente

Uma release pode ser distribuída e comercializada sem assinatura de código;
assinatura e formalizações de `R-015` são opcionais e não bloqueiam o release.
A execução dinâmica de Godot/Unity no CI não é requisito; as execuções reais
locais reproduzíveis permanecem válidas. CI verde não substitui a análise de
evidências, mas a ausência de CI dinâmico também não invalida provas locais.
Consulte a decisão vigente de reconciliação para o estado completo.
`docs/evidence/RECONCILIACAO_GATES_RELEASE_2026-08-17.md`.
