# Plano Mestre de Estabilização — NeoEng-D-Trace

Baseline oficial: `a3f376af2a1f738bb36c107320757d0339300c78`.

## Estado operacional de referência — 13 de agosto de 2026

Este bloco é um snapshot vivo condicionado à verificação do repositório e do GitHub.

Etapa 11 integrada e concluída no escopo aprovado:

- PR funcional `#45` integrada em `2a38b89e542390b3b4396a88d9a416f3695caadc`; PR de fechamento `#46` integrada em `a22a90088220e586c3382c3ed5dc1075a3ff7e6b`;
- 145 testes comportamentais novos; suíte oficial `877 passed` no Windows/Python 3.11.9;
- cobertura exata `10.787/11.628` linhas (`92,77%`), `3.147/3.700` branches (`85,05%`) e `90,91%` combinada;
- zero módulos abaixo de 30% em linhas ou branches mensuráveis;
- CIs funcional `31491221322` e final de fechamento `31495971632` aceitos após auditoria integral de Linux/Windows, proveniência, legado, hashes e conteúdo recursivo;
- `R-003` encerrado no escopo aprovado após integração e CI pós-merge auditado;
- Etapas 11 e 12 concluídas nos escopos aprovados; Etapa 13 aprovada localmente e não integrada; release não aprovada.

Etapa 12 — integrada e concluída no escopo aprovado:

- `928` testes oficiais aprovados no Windows/Python 3.11.9;
- cobertura exata `11.174/12.040` linhas (`92,81%`), `3.309/3.892` branches (`85,02%`) e `90,91%` combinada;
- limites centrais e cenários malformados implementados para configuração, imagem, projeto, geometria, detecção, broadphase, atlas, GLTF e logs;
- pip-audit sem vulnerabilidades conhecidas, Bandit de alta severidade limpo, mypy sem erros em `73` arquivos e legado `27/27` conciliado;
- commit técnico `da7611b543bb0ceb4eb8e67a7900aadcb8f04a5f` validado em worktree limpa; PR `#49` integrada em `872bf079d228d13d0203d22b844052b1f920e99b` e CI funcional `31686321925` auditado; fechamento pela PR `#50` em `fc81c2ea10e751c15a39627d462ddfff390eeb04`; CI final `31688307089` auditado em Linux/Windows;
- pacote documental de fechamento: `929` testes locais e baseline de `326` arquivos, sem alteração na cobertura do código-fonte;
- `R-012`: ENCERRADO NO ESCOPO APROVADO; Etapa 12: CONCLUÍDA; Etapa 13: APROVADA LOCALMENTE / NÃO INTEGRADA; release: NÃO APROVADA.

Etapa 13 — aprovada localmente, ainda não integrada:

- base integrada `fc81c2ea10e751c15a39627d462ddfff390eeb04`; commit corretivo local `426cef118fdb0a334e639ec962b2e514cfd59b0a`;
- sessão de documento, caminhos de estado, conversão de imagem, traduções e coordenação do autosave extraídos; `main_window.py` reduzido de `1.306` para `1.175` linhas;
- autosave local versionado, atômico, limitado e recuperável explicitamente, com quarentena, fingerprint da origem e preservação da decisão adiada;
- `953` testes, `11.581/12.478` linhas, `3.370/3.964` branches, `90,93%` combinada, zero módulos abaixo de 30% e baseline de `335` arquivos;
- mypy em `80` arquivos, Black, isort, Bandit e pip-audit aprovados no escopo vigente; legado `27/27` conciliado;
- provas externas aprovadas com `QTimer` real e processos distintos; CI verde `31693639653` rejeitado por divergência Linux/Windows; correção portátil aguarda novo CI;
- `R-011`: CORREÇÃO VALIDADA LOCALMENTE / ABERTO ATÉ MERGE E CI PÓS-MERGE; Etapa 13: NÃO CONCLUÍDA; Etapa 14: NÃO INICIADA; release: NÃO APROVADA.

Snapshot integrado anterior — encerramento formal da Etapa 10:

- branch funcional `etapa-10-exportadores-engines`, HEAD final `2d2afff2c57cd779750bcb9c02b24c421d73dc0c`, PR `#42` integrada em `9b22bdc54b13992658172d4748bfab44f3127c8e`;
- primeiro CI remoto `31450335289`: gates Linux/Windows aprovados, mas resultado rejeitado porque o artefato omitiu a evidência atual e o resumo legado não identificou separadamente o HEAD testado;
- segundo CI remoto `31451363518`: gates aprovados e upload corrigido, mas resultado rejeitado porque o resumo portátil identificava somente o merge sintético testado, não o HEAD fonte da PR;
- terceiro CI remoto `31452032479`: gates, upload e schema v4 aprovados, mas resultado rejeitado porque o scanner recursivo encontrou referências proibidas em ZIPs históricos aninhados;
- quatro ZIPs sanitizados mediante autorização explícita, checksums internos e hashes externos recalculados;
- quarto CI remoto `31457937902`: Linux e Windows aprovados com `729` testes, merge sintético `0394d55501e32e2fa38acbcc4d1e3c5e126954ce`, HEAD fonte comprovado, `44` arquivos de evidência idênticos ao repositório e varredura recursiva sem violações; resultado pré-merge aceito;
- CI pós-merge `31463873481`: jobs verdes e artefatos íntegros, mas resultado rejeitado porque Linux registrou `8.581` linhas e `2.145` branches cobertos, contra `8.582` e `2.146` no Windows;
- teste determinístico força o par inverso da broadphase; CI pré-merge corretivo `31464786333` aceito, PR `#43` integrada em `f8caec3e7156d308f03046f81d2c89996f959466` e pós-merge `31469610508` aceito após auditoria integral;
- perfis Godot/Unity corrigidos e unificados entre cena e objeto;
- rollback multi-arquivo do atlas comprovado por falha injetada;
- Godot `4.7` e Unity `6000.5.7f1` aprovados em caminhos Unicode, inclusive GLB;
- `17` testes da etapa, `730` oficiais e `196` históricos com reconciliação `27/27`;
- cobertura `73,77%` de linhas, `57,91%` de branches e `69,93%` combinada; mypy sem erros em `70` arquivos;
- Etapa 10: CONCLUÍDA; Etapa 11: NÃO INICIADA; release: NÃO APROVADA.

### Snapshot histórico — encerramento formal da Etapa 9

- commit técnico local `28273dfb7cb0e0aeab1f8f9f3a99c07df3b08a76`;
- 39 testes da etapa, 702 oficiais e 196 históricos; reconciliação 27/27;
- cobertura global 73.65% de linhas, 57.65% de branches e 69.79% combinada;
- API pública única de colisão estática; namespace histórico sem implementações concorrentes;
- PR `#40`, merge `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`; CI final da PR `31445205968` e pós-merge `31445518755`: Linux e Windows em `success`, zero anotações;
- `R-008`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 9: CONCLUÍDA; Etapa 10: NÃO INICIADA; release: NÃO APROVADA.

### Snapshot histórico imediatamente anterior — encerramento da Etapa 8

- repositório: `AiltonSantanaReis/NeoEng-D-Trace`;
- commits técnico/documental da Etapa 7: `a940ef13018aabc430126db3fd705b521fc1be06` e `51e55a37021c506471111ef1f4e7bc9abe67c65d`;
- PR `#36`, merge `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`;
- CI da PR `31436763095` e pós-merge `31437000772`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9081388807`, Windows `9081419753`;
- validação local: 620 testes no commit técnico, 621 no pacote pré-merge e 622 no fechamento, cobertura combinada 68.53%, launcher 85% e mypy sem erros em 66 arquivos;
- cobertura crítica integrada pela PR `#35`; `R-003` permanece aberto para as metas finais;
- `R-006`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 7: CONCLUÍDA;
- Etapa 8 integrada pela PR `#38`, merge `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`;
- CI da PR `31440755594` e pós-merge `31441024001`: Linux e Windows em `success`, zero anotações;
- validação local: 125 testes focais, 661 totais no pacote pré-merge e 662 no fechamento; núcleo geométrico com 95.59% de linhas e 93.29% de branches;
- `R-007`: ENCERRADO NO ESCOPO APROVADO; Etapa 8: CONCLUÍDA;
- gate naquele snapshot: executar a auditoria de física, colisão e APIs da Etapa 9;
- naquele snapshot, Etapa 9: não iniciada; release: NÃO APROVADA.

### Snapshot histórico imediatamente anterior — encerramento da Etapa 6

- commits técnico/documental: `3c80bb7f0f72a26f5f4972c5aeb483b8d16e2e98` e `321ccf3a692c7c1916eeeb61e7a041ee8bcef035`;
- PR `#33`, merge `73a128ec44cde17867bbac6a7854ce86a43aba5a`;
- CI da PR `31431473940` e pós-merge `31431739320`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9079413130`, Windows `9079450269`;
- validação local de fechamento: 543 testes, cobertura combinada 62.45%, mypy sem erros em 66 arquivos;
- `R-005`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 6: CONCLUÍDA;
- naquele snapshot, Etapa 7: não iniciada; release: NÃO APROVADA.

### Snapshot histórico anterior — encerramento da Etapa 5

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
