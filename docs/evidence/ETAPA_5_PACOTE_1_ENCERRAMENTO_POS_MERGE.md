# Evidência — Etapa 5, Pacote 1: encerramento pós-merge

## Identificação

- Commit da `main`: `46cc0664cd8cfe04a6bd3b89bb6dc56e9681f62a`;
- HEAD mesclado: `fb5c72b001e4d8085ec902e383190e04a17dae8c`;
- Pull request: `#15`;
- Branch documental: `docs/etapa-5-pacote-1-encerramento-pos-merge`;
- Data/hora: `2026-08-02T19:45:04.590655-03:00`;
- Responsável: AiltonSantanaReis.

## Ambiente

- Sistema operacional local: `win32`;
- Python: `Python 3.11.9`;
- Poetry: `Poetry (version 2.4.1)`;
- Git: `git version 2.54.0.windows.1`;
- GitHub CLI: `gh version 2.93.0 (2026-05-27)`;
- CI: Linux e Windows com Python 3.11.

## Objetivo e escopo

Registrar permanentemente que o Pacote 1 da Etapa 5 foi integrado à `main`
e aprovado no escopo de contrato observável do gerenciador, atomicidade das
pilhas, rollback da cena e do comando, transação composta e estado das ações
Undo/Redo.

Este encerramento não fecha `R-004`, não conclui a Etapa 5 e não inicia a
Etapa 6.

## Entradas

- Evidência manual: `NeoEng-D-Trace_Etapa5_Pacote1_Manual_20260802_191329.zip`;
- SHA-256 manual:
  `558885490730b335c0b0578e6b6c6d7030ec86c57ba0668c73fb5e30d481aecc`;
- Evidência pós-merge: `NeoEng-D-Trace_Etapa5_Pacote1_PosMerge_20260802_193753.zip`;
- SHA-256 pós-merge:
  `7e0fc5d64cf0edcdef6ab96cc43d23b7d0d3ce7bfd515ad31db50a4ac9dabe41`;
- Tamanho do pacote pós-merge: `940` bytes;
- Membros do pacote: `resultado_pos_merge.json, sha256_manifest.json`.

## Comandos executados

- `gh api -X GET repos/AiltonSantanaReis/NeoEng-D-Trace/pulls/15`;
- `git fetch --prune origin`;
- `git rev-parse origin/main`;
- `gh run list --commit 46cc0664cd8cfe04a6bd3b89bb6dc56e9681f62a --workflow "Private validation" --event push`;
- `gh run view 30769951023`;
- `git switch main`;
- `git pull --ff-only origin main`;
- `poetry run python tools/baseline_integrity.py --verify`;
- gates locais completos desta PR documental.

## Resultados

- PR `#15`: mesclada;
- merge commit: `46cc0664cd8cfe04a6bd3b89bb6dc56e9681f62a`;
- workflow pós-merge: `#55` (`30769951023`);
- Linux `test`: `success` (`91555266247`);
- Windows `test-windows`: `success` (`91555266229`);
- suíte funcional local anterior: `235 passed`;
- cobertura global: `53%`;
- cobertura de `src/core/commands.py`: `60%`;
- validação manual Windows: `9/9`;
- baseline antes desta PR documental: `233` arquivos;
- pacote pós-merge íntegro e sem achados de privacidade.

## Artefatos

- `docs/evidence/raw/NeoEng-D-Trace_Etapa5_Pacote1_PosMerge_20260802_193753.zip`;
- `docs/evidence/ETAPA_5_PACOTE_1_EVIDENCE_MANIFEST.json`;
- artefatos Linux e Windows do workflow `#55`.

## Falhas e causa raiz

Durante a PR funcional houve criação acidental de um arquivo vazio, removido
por commit corretivo normal. A comparação entre o HEAD funcional validado e
o HEAD mesclado retornou zero arquivos diferentes. Não houve force-push.

## Limitações e riscos residuais

Permanecem abertos:

- classificação e migração das 117 mutações candidatas;
- comandos ausentes de movimento e propriedades;
- matriz execute/undo/redo por operação;
- preservação integral de IDs e relações em comandos específicos;
- múltiplos objetos e independência das âncoras temporárias;
- meta de cobertura do Plano Mestre;
- encerramento formal de `R-004`.

## Decisão

**APROVADO NO ESCOPO DO PACOTE 1.**

O Pacote 1 está integrado. `R-004` permanece **CONFIRMADO / ABERTO** e o
próximo gate é o planejamento do Pacote 2 da Etapa 5.
