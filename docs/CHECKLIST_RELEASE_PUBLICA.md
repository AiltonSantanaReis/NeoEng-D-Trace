# Checklist de Release Pública — NeoEng-D-Trace

**Status atual:** RELEASE OFICIAL `v0.2.0` PUBLICADA; ASSINATURA E TRÂMITES JURÍDICOS DEFERIDOS PARA FUTURAS VERSÕES

Este checklist registra a release pública `v0.2.0` e separa gates concluídos de riscos aceitos/deferidos. Um item marcado
como “futuro” não pode ser apresentado como concluído.

## Gates obrigatórios

| Gate | Estado atual | Critério para fechar |
|---|---|---|
| R-014 — assinatura | DEFERIDO PARA FUTURAS BUILDS/RELEASES; não bloqueia a primeira release oficial por decisão do proprietário | GUI, CLI, DLLs distribuídas e MSI assinados; cadeia e timestamp verificados quando o proprietário ativar este gate |
| R-015 — publicação e dados | DECISÃO DE ROADMAP REGISTRADA; formalização futura conforme demanda | Licença/termos, atribuições, identidade visual, contato e dados formalizados quando o proprietário ativar este gate |
| R-016 — builder MSI | Validado tecnicamente / governança pendente | WiX 4.0.6 fixado, build reproduzível, instalação, upgrade, reparo e remoção validados; revisar termos da toolchain no gate de release |
| Qualidade funcional | Técnico aprovado | CI Linux/Windows, testes, cobertura, legado reconciliado e baseline íntegra |
| Engines externas | Validado no fixture canônico | Repetir quando o candidato de release mudar |

## Evidências exigidas para o candidato final

- commit-fonte e árvore limpa;
- versões de Python, dependências, toolchain e Windows;
- manifestos e hashes dos artefatos;
- logs sem caminhos pessoais ou segredos;
- assinatura verificada por processo independente quando `R-014` for ativado;
- instalação, execução, exportação, atualização, reparo e desinstalação;
- política e documentação aprovadas pelo responsável do projeto.

## Decisão de roadmap

A primeira release oficial pode ser distribuída sem assinatura por decisão
do proprietário, desde que os artefatos, hashes, testes, limitações e riscos
sejam descritos com transparência. `R-014` fica para futuras builds/releases
após validação de usuários e crescimento do projeto. A formalização de `R-015`
será executada conforme demanda e decisão do proprietário. CI verde,
isoladamente, nunca substitui a análise de evidências nem certifica
conformidade jurídica.
