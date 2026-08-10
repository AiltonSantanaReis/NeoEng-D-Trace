# Plano Mestre de Estabilização — NeoEng-D-Trace

Baseline oficial: `a3f376af2a1f738bb36c107320757d0339300c78`.

## Estado operacional de referência — 10 de agosto de 2026

Este bloco é um snapshot vivo condicionado à verificação do repositório e do GitHub.

- repositório: `AiltonSantanaReis/NeoEng-D-Trace`;
- commits técnico/documental da Etapa 6: `3c80bb7f0f72a26f5f4972c5aeb483b8d16e2e98` e `321ccf3a692c7c1916eeeb61e7a041ee8bcef035`;
- PR `#33`, merge `73a128ec44cde17867bbac6a7854ce86a43aba5a`;
- CI da PR `31431473940` e pós-merge `31431739320`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9079413130`, Windows `9079450269`;
- validação local de fechamento: 543 testes, cobertura combinada 62.45%, mypy sem erros em 66 arquivos;
- `R-005`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 6: CONCLUÍDA;
- gate atual: elevar cobertura nos módulos críticos e executar a Etapa 7;
- Etapa 7: não iniciada; release: NÃO APROVADA.

### Snapshot histórico imediatamente anterior — encerramento da Etapa 5

- âncora técnica integrada e auditada: `574be9bd0268e70c384903f93f16cf6e73aa57a2`;
- PR funcional: `#27`, fechada e mesclada;
- HEAD funcional v4.1: `9bf83af0d58b5984ccfefc59a543428379b02632`;
- HEAD documental final da PR: `8ce44c238aaea79dafa64b8e1bba3ba5a8a7157e`;
- Pacotes 1, 2A, 2B, 3A, 3B, 3B.1, 4A, 4B, 4C, 5A, 5B e 5C: integrados;
- gate funcional Windows/Python 3.11.9: 95 testes focais, 16 documentais, 517 totais e 66% de cobertura;
- validação visual: manual aprovada e automática aprovada em 17/17 estados;
- CI final pré-merge: workflow `Private validation` `#83` (`31135700216`) com Linux e Windows em `success`;
- CI pós-merge da `main`: workflow `Private validation` `#84` (`31136893143`) com Linux e Windows em `success`;
- artefatos pós-merge: Linux `8978309717` (`25ee252a77fb43796a6c5b1cbbf10c5987791187a6e860a11c17e9980d45b091`) e Windows `8978326062` (`0432e2e7ccc11d21d8769f160268f820ccf62af7edb5fd6f5a2070bcca4c912f`);
- branch funcional: preservada no remoto;
- PR de fechamento: `#28`, HEAD `ab71e148c0b7441bd36f489472856d0b4adfaa1e`, mesclada em `56533b65f81d21fd9c762aa10c0d3e6747d742ca`;
- pacote técnico final: PR `#29`, HEAD `956db473a88641bfdcfbd49ed122479f3fa2c51d`, merge `574be9bd0268e70c384903f93f16cf6e73aa57a2`;
- CI pós-merge técnico: `31425585259`, Linux e Windows em `success`, zero anotações;
- `R-004`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 5: CONCLUÍDA;
- gate naquele snapshot: planejar a Etapa 6 sem iniciá-la implicitamente e manter release bloqueada;
- naquele snapshot, Etapa 6: não iniciada.

O fechamento de `R-004` e a conclusão da Etapa 5 foram executados com evidência
remota. Naquele snapshot, o início da Etapa 6 ainda era um gate independente.

## Reavaliação auditada publicada — 10 de agosto de 2026

A recomendação anterior foi bloqueada durante auditoria rigorosa e somente
restabelecida depois das correções descritas em
`docs/evidence/AUDITORIA_RIGOROSA_2026-08-10.md`.

Estado remoto atual:

- segurança de dependências e Bandit de alta severidade: aprovados;
- suíte oficial: `532 passed`;
- suíte legada: 196 executados, 26 divergências previstas reconciliadas, zero
  inesperadas;
- mypy estrito: zero erros em 65 arquivos;
- cobertura combinada linhas/branches: `62.18%`, com piso CI de
  62%; metas finais de 90%/85% ainda abertas;
- publicação: commit `236eefd41ee51c7085e21d52fc80074eede0a793`, HEAD final `ab71e148c0b7441bd36f489472856d0b4adfaa1e`, PR `#28` mesclada;
- CI final da PR: `31422901244`, Linux e Windows em `success`;
- CI pós-merge corretivo: `31423386971`, Linux e Windows em `success`;
- CI pós-merge técnico final: `31425585259`, Linux e Windows em `success`;
- decisão: **ETAPA 5 FORMALMENTE ENCERRADA**;
- release: **NÃO APROVADA**.

## Regras inegociáveis

1. `main` representa somente estados aprovados.
2. Nenhuma afirmação de sucesso sem evidência reproduzível.
3. Estados permitidos: APROVADO, REPROVADO, BLOQUEADO, NÃO TESTADO e PARCIAL.
4. NÃO TESTADO, BLOQUEADO e PARCIAL nunca equivalem a APROVADO.
5. É proibido remover, enfraquecer, ignorar ou maquiar teste para obter resultado verde.
6. Toda falha corrigida exige teste de regressão.
7. Nenhuma etapa avança com perda de dados, regressão, build quebrado, comportamento não determinístico ou evidência insuficiente.
8. Funcionalidade nova fica congelada até a conclusão dos bloqueadores de estabilização.

## Definição de concluído

Uma tarefa somente termina quando possuir requisito objetivo, reprodução anterior, causa raiz, implementação completa, testes unitários e de integração, testes de UI quando aplicáveis, cenários negativos, cobertura sem redução, compilação, lint, tipagem, documentação, evidências e revisão do diff.

## Evidências obrigatórias

Cada etapa deve registrar:

- commit testado;
- sistema operacional e Python;
- dependências instaladas;
- comandos completos;
- quantidade de testes aprovados, reprovados, ignorados e bloqueados;
- cobertura por módulo;
- hashes de entradas e saídas relevantes;
- limitações e riscos residuais;
- conclusão formal.

Os relatórios permanentes ficam em `docs/evidence/`. Resultados brutos devem ser publicados como artefatos do CI.

## Estratégia de testes

- unitários para domínio e serviços;
- propriedades para invariantes geométricos e round-trip;
- integração com arquivos temporários reais;
- UI com `pytest-qt`;
- ponta a ponta para importar, editar, salvar, reabrir e exportar;
- compatibilidade em Windows 11 e Linux;
- segurança para entradas malformadas, limites e permissões;
- desempenho com baseline reproduzível.

## Metas de cobertura

- nenhum módulo operacional em 0%;
- 100% dos fluxos críticos mapeados;
- persistência, Undo/Redo e exportadores: 95% de linhas e 90% de branches;
- núcleo geométrico: 90% de linhas e 85% de branches;
- cobertura global: 90% de linhas e 85% de branches;
- exclusões somente com justificativa explícita.

## Ordem obrigatória

0. Governança e proteção da baseline.
1. Ambiente reproduzível e CI Windows/Linux.
2. Inventário funcional e testes de caracterização.
3. Persistência e contrato versionado de projeto.
4. Ciclo Abrir/Salvar na interface.
5. Undo/Redo completo.
6. Exportação de colisões.
7. CLI e modo headless.
8. Bézier e geometria.
9. Física, colisão e APIs duplicadas.
10. Exportadores e validação nas engines declaradas.
11. Cobertura integral da interface.
12. Segurança e limites operacionais.
13. Refatoração protegida por testes.
14. Build Windows, auditoria final e candidato a release.

Nenhuma etapa pode ser pulada. Retorno a uma etapa anterior deve ser registrado como lacuna ou regressão descoberta.
