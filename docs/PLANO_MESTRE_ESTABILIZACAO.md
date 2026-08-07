# Plano Mestre de Estabilização — NeoEng-D-Trace

Baseline oficial: `a3f376af2a1f738bb36c107320757d0339300c78`.

## Estado operacional de referência — 6 de agosto de 2026

Este bloco é um snapshot vivo condicionado à verificação do repositório e do GitHub.

- repositório: `AiltonSantanaReis/NeoEng-D-Trace`;
- `main` integrada conhecida: `ee38a2f1dc85093e34140ddd087312629b4ecb43`;
- etapa ativa: Etapa 5 — Undo/Redo completo;
- risco ativo da etapa: `R-004`;
- Pacotes 1, 2A, 2B, 3A, 3B, 3B.1, 4A, 4B, 4C, 5A e 5B: integrados;
- Pacote 5C: PR `#27`, draft e não integrada; o HEAD funcional `9bf83af0d58b5984ccfefc59a543428379b02632` contém o v4.1 em 20 arquivos e foi aprovado no gate Windows/Python 3.11.9 com 95 testes focais, 16 documentais, 517 totais e 66% de cobertura;
- validação visual: manual aprovada e automática aprovada em 17/17 estados, com ZIP SHA-256 `2981a29d85f8df329bddd0711e16b54665a75d8522447405c476359d6bd2d189`;
- CI do HEAD funcional: workflow `Private validation` `#82` (`31115744015`) com Linux e Windows em `success`; a primeira tentativa Windows falhou antes do checkout por indisponibilidade do GitHub e o retry passou sem alteração de código;
- artefatos: Linux `8973550294` (`d6cee9f94f04d706cccb106d6456dcbc3e482e4ed84aec2fa15b6bfa396be435`) e Windows `8973729078` (`a433a229cdbc1bfe58d03804baa2edb223c5bc2f6c37d17431b90e86f3777aa6`);
- comentários, reviews e threads pendentes: nenhum na verificação pré-merge;
- gate atual: reconciliar documentos vivos e teste documental em novo commit exclusivamente documental, exigir CI Linux/Windows para esse novo HEAD e revisar o diff final;
- depois desse CI, Ready e merge continuam decisões separadas; após eventual merge, a `main` deve passar por CI pós-merge e evidência de encerramento antes de fechar `R-004` ou concluir a Etapa 5;
- Etapa 6: não iniciada.

Ready for review, merge, encerramento de `R-004`, conclusão da Etapa 5 e início da Etapa 6 são gates independentes e não estão implicitamente autorizados.

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
