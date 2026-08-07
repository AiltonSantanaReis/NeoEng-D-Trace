# Evidência — Etapa 5, Pacote 5C: validação pré-merge

## Identificação

- repositório: `AiltonSantanaReis/NeoEng-D-Trace`;
- branch: `feat/etapa-5-pacote-5c-bezier-residual-contracts`;
- base integrada: `ee38a2f1dc85093e34140ddd087312629b4ecb43`;
- HEAD funcional validado: `9bf83af0d58b5984ccfefc59a543428379b02632`;
- PR: `#27`, draft e não integrada;
- data: 6 de agosto de 2026;
- risco: `R-004`, aberto;
- Etapa 6: não iniciada.

## Objetivo

Registrar o estado comprovado depois do commit funcional, push fast-forward,
validação visual e CI, sem autorizar Ready, merge, fechamento de risco ou
transição de etapa. O commit documental que contém este relatório deve receber
novo CI Linux/Windows antes de Ready for review.

## Gate funcional

- escopo: 20 arquivos;
- Windows/Python: Windows 11, Python 3.11.9;
- baseline: 263;
- testes focais: 95 passed;
- testes documentais: 16 passed;
- suíte completa: 517 passed;
- cobertura global: 66%;
- compileall, Flake8 fatal, Black, isort, mypy e `git diff --check`: APROVADOS.

## Validação visual

- manual: aprovada pelo usuário;
- automática: 17/17 estados aprovados;
- ZIP SHA-256: `2981a29d85f8df329bddd0711e16b54665a75d8522447405c476359d6bd2d189`;
- membros: 27;
- round-trip `.ndtproj` e exportação real de sprite: APROVADOS;
- `True`, `1.0` e valor não hashable: rejeitados sem mutação ou histórico.

## Commit e publicação

- commit: `9bf83af0d58b5984ccfefc59a543428379b02632`;
- pai: `4802e24d6dd91a20dda4b56ae526ba33e5544322`;
- mensagem: `fix(stage5): harden bezier geometry and handle contracts`;
- arquivos: 20;
- push: fast-forward;
- force-push: ausente.

## CI do HEAD funcional

- workflow: `Private validation`;
- execução: `#82`;
- run ID: `31115744015`;
- Linux: `success`;
- Windows: `success`;
- tentativa final: 2.

A primeira tentativa Windows falhou antes do checkout por `Service Unavailable`
e `Internal Server Error` do GitHub Actions. O retry passou sem alteração de código.

### Artefatos

- Linux: `validation-linux-python-3.11`, ID `8973550294`, 29951 bytes,
  digest `d6cee9f94f04d706cccb106d6456dcbc3e482e4ed84aec2fa15b6bfa396be435`;
- Windows: `validation-windows-python-3.11`, ID `8973729078`, 5086358 bytes,
  digest `a433a229cdbc1bfe58d03804baa2edb223c5bc2f6c37d17431b90e86f3777aa6`.

## Revisão da PR

- aberta: SIM;
- draft: SIM;
- mergeada: NÃO;
- mergeável na última consulta: SIM;
- comentários, reviews e threads pendentes: nenhum;
- corpo reconciliado com o estado funcional e o CI do HEAD exato.

## Gates pendentes

- criar o commit exclusivamente documental;
- executar CI Linux/Windows no novo HEAD;
- revisar o diff documental;
- Ready for review exige autorização separada;
- merge exige autorização separada;
- `R-004` exige merge, CI pós-merge da `main` e evidência de encerramento;
- Etapa 5 não concluída;
- Etapa 6 não iniciada.

## Decisão

`APROVADO NO ESCOPO PRÉ-MERGE DO HEAD FUNCIONAL. A RECONCILIAÇÃO
DOCUMENTAL FOI AUTORIZADA E EXECUTADA LOCALMENTE. COMMIT, PUSH E NOVO CI
EXIGEM AUTORIZAÇÃO ESPECÍFICA. READY, MERGE, FECHAMENTO DE R-004,
CONCLUSÃO DA ETAPA 5 E INÍCIO DA ETAPA 6 PERMANECEM PENDENTES.`
