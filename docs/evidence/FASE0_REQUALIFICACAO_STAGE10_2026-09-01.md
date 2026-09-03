# Fase 0 — requalificação após incorporação da evidência Stage 10

**Projeto:** NeoEng-D-Trace
**Etapa:** `P2D-COMP-01/LEGACY-26-RECON`
**Fase:** `Fase 0 — gate de entrada e congelamento da fronteira`
**Status:** `APROVADO — GATE REABERTO PARA FASE 1`
**Data da requalificação:** 01/09/2026 (America/Sao_Paulo)
**Commit validado:** `72b4e5cb7447c565f18130067fcf2bcea26e2d0b`
**Commit anterior do gate bloqueado:** `ab07c6a`
**Branch:** `fix/legacy-27-functional-regressions`
**Relatório bloqueado anterior:** `docs/evidence/FASE0_GATE_ENTRADA_LEGACY_26_2026-09-01.md`
**Plano:** `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`

Este relatório é uma requalificação posterior e não reescreve o snapshot
histórico da Fase 0 que foi corretamente classificado como `BLOQUEADO`. A
requalificação cobre exclusivamente o tratamento autorizado do pacote Stage 10,
a integridade do novo HEAD e a reabertura do gate. Nenhuma implementação,
fixture, teste substituto ou correção das 26 falhas foi iniciada nesta fase.

## 1. Decisão autorizada e execução

O proprietário autorizou incorporar integralmente, como evidência rastreada, o
pacote:

`docs/evidence/artifacts/stage10-accessibility-20260824/BUILD-F10-ACCESSIBILITY-20260824-2151EF1/`

Foram incorporados exatamente os 8 arquivos autocontidos:

- `manifest.json`;
- `report.json`;
- `hashes.sha256`;
- `visual/compact-1280x720.png`;
- `visual/compact-inspector-focus.png`;
- `visual/desktop-1920x1080.png`;
- `visual/desktop-mouse-state.png`;
- `visual/desktop-xray-keyboard.png`.

Nenhum outro arquivo untracked foi incluído. O pacote foi commitado em:

`72b4e5cb7447c565f18130067fcf2bcea26e2d0b`

## 2. Regras consultadas

Antes da incorporação e da decisão de requalificação foram consultados:

- `docs/POLITICA_NAO_REGRESSAO.md`;
- `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
- `docs/evidence/README.md`;
- `tools/run_legacy_tests.py`;
- `quality/legacy_tests/manifest.json`;
- `quality/legacy_tests/reconciliation.json`;
- `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`;
- `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`;
- `docs/evidence/FASE0_GATE_ENTRADA_LEGACY_26_2026-09-01.md`.

As regras aplicadas foram mantidas sem alteração:

- snapshots históricos permanecem imutáveis;
- manifest e referências devem ser rastreados e ter hashes/bytes coerentes;
- `skip`, `xfail`, filtros, thresholds e exceções silenciosas não são válidos;
- evidência antiga não pode ser apresentada como validação de um novo HEAD;
- arquivo preexistente não pode ser removido ou sobrescrito para limpar o gate;
- `APROVADO` somente pode ser usado para o requisito efetivamente coberto.

## 3. Identidade e ambiente verificados

| Item | Resultado |
|---|---|
| HEAD | `72b4e5cb7447c565f18130067fcf2bcea26e2d0b` |
| Branch | `fix/legacy-27-functional-regressions` |
| Plataforma | `Windows-10-10.0.26200-SP0` |
| Python | `3.11.9` |
| PySide6 | `6.10.1` |
| Qt | `6.10.1` |
| Push/merge/release | não executados |

## 4. Integridade do pacote incorporado

### 4.1 Rastreamento

| Verificação | Resultado |
|---|---|
| Manifest Stage 10 rastreado pelo Git | `True` |
| Manifest Stage 10 ignorado pelo Git | `False` |
| Arquivos incorporados | `8/8` |
| Conteúdo fora do diretório Stage 10 incluído | `0` |
| `manifest.json` original editado | `não` |
| `report.json` original editado | `não` |
| Capturas originais editadas | `não` |

### 4.2 Referências e hashes

O `manifest.json` continua declarando o pacote histórico Stage 10 para o commit
`2151ef1aed06e2660a5e04f1d9d0b4651cb5bcce`. Isso é proveniência histórica e não
é apresentado como execução do HEAD `72b4e5c`.

As verificações read-only confirmaram:

- `6/6` arquivos referenciados pelo manifest existem;
- `0` referências ausentes;
- `0` divergências entre hashes declarados e conteúdo;
- `7/7` entradas do `hashes.sha256` conferem, incluindo o próprio manifest;
- o pacote contém limitações explícitas de DPI nativo e de escopo Stage 10.

O Git normalizou os três arquivos textuais para LF no blob, conforme a política.
O gate foi executado sobre o blob staged/commitado e confirmou a integridade;
nenhuma atualização manual de digest foi usada para fabricar `PASS`.

## 5. Re-inventário da árvore

O inventário posterior à incorporação foi executado no HEAD acima:

| Inventário | Resultado |
|---|---:|
| Arquivos rastreados por `git ls-files` | `3108` |
| Arquivos governados pelo baseline | `3107` |
| Arquivos untracked restantes | `3330` |
| Alterações rastreadas pendentes | `0` |
| Manifest Stage 10 rastreado | `sim` |
| SHA-256 do status normalizado pós-incorporação | `bcdc345ac9655f943030c7018423ce27fec8b7acc1e3db51a9d81e390657adbd` |
| SHA-256 do snapshot legado | `061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a` |

Os `3330` untracked restantes continuam fora da fronteira desta etapa. Eles não
foram apagados, movidos, ignorados ou incorporados. O fato de permanecerem no
workspace é registrado; não impede este gate porque não há manifest não
rastreado restante que o `evidence_integrity.py` considere dentro do escopo
validável.

## 6. Snapshots históricos

O manifesto histórico continua com:

- arquivo: `quality/legacy_tests/manifest.json`;
- tamanho: `21489` bytes;
- SHA-256: `061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a`;
- `source_commit`: `cf749564ab5d961772d66dc363d0e990cebf8da3`;
- `24` arquivos e `196` testes declarados;
- integridade validada pelo runner em retorno `0`.

Nenhum snapshot foi alterado. As 26 falhas legadas continuam sendo um trabalho
de reconciliação separado; o rastreamento da evidência Stage 10 não as converte
em passadas.

## 7. Gates executados nesta requalificação

| Gate | Resultado |
|---|---|
| `tools/evidence_integrity.py --require-tracked --git-blob` | `PASS — 121 manifests validated` |
| `tools/baseline_integrity.py --verify --git-blob` | `PASS — 3107 files` |
| `git diff --cached --check` antes do commit | `PASS` |
| status rastreado pós-commit | limpo |
| snapshots históricos | `PASS`, sem alteração |
| suite oficial ou correção das 26 falhas | não executado nesta Fase 0; fora do escopo do gate de evidência |

Os dois últimos itens não são uma omissão: a Fase 0 é um gate de entrada e não
uma qualificação funcional das Fases 1–7. A suíte completa e os testes
substitutos deverão ser executados integralmente dentro de suas próprias fases,
sem serem representados por este relatório.

## 8. Segurança e preservação

- O pacote foi incorporado sem executar arquivos de entrada.
- O manifest, relatório, índice de hashes e capturas foram preservados como
  evidência histórica do commit declarado.
- Não foram encontrados campos de segredo/token no conteúdo textual auditado.
- O pacote não foi publicado remotamente; push, merge, release e tag não foram
  executados.
- Os demais untracked foram preservados para evitar perda de dados ou alteração
  fora da autorização.
- O baseline e o gate de evidências foram verificados sobre o conteúdo efetivo
  rastreado, não sobre uma cópia não commitada.

## 9. Decisão da Fase 0

`APROVADO — o bloqueador específico do manifest Stage 10 foi resolvido por
incorporação integral e rastreada, com hashes, referências, baseline e evidence
integrity aprovados.`

Este `APROVADO` é limitado à requalificação da entrada da Fase 0. Ele não
declara que as 26 falhas foram corrigidas, não aprova a reconciliação histórica,
não aprova o projeto inteiro e não autoriza push, merge ou release.

## 10. Próximo passo autorizado

O gate permite iniciar a **Fase 1 — contratos substitutos e fábrica de
fixtures**, respeitando o plano integral. Antes de qualquer alteração de produto
ou teste, as regras deverão ser consultadas novamente e o inventário desta
requalificação deverá ser usado como base.

A Fase 1 deverá produzir seu próprio relatório completo. Nenhuma Fase 1–7 será
declarada concluída por cobertura parcial, teste sintético isolado ou evidência
incompleta. Commit, push e merge continuam condicionados aos gates finais da
etapa integral.
