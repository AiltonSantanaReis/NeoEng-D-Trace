# Fase 0 — gate de entrada, inventário e integridade histórica

**Projeto:** NeoEng-D-Trace
**Etapa:** `P2D-COMP-01/LEGACY-26-RECON`
**Fase:** `Fase 0 — gate de entrada e congelamento da fronteira`
**Status:** `BLOQUEADO`
**Data da execução:** 01/09/2026 (America/Sao_Paulo)
**Commit sob inspeção:** `96ab35d8a51d198f60a6b5dfa82007ccbc28ab59`
**Branch:** `fix/legacy-27-functional-regressions`
**Plano aplicável:** `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`

Este relatório registra a execução integral da Fase 0 após o commit local
`96ab35d`. A fase foi executada somente com inspeções e verificações de leitura;
nenhuma implementação, fixture, teste substituto, snapshot histórico ou
artefato preexistente foi alterado. O gate não foi aprovado porque existe um
manifest de evidência dentro de `docs/evidence/` que não é rastreado pelo Git.

`BLOQUEADO` é o resultado correto desta fase. Não significa aprovação parcial,
nem autoriza iniciar a implementação das fases seguintes.

## 1. Objetivo e limite

O objetivo foi confirmar, antes de qualquer implementação da nova etapa:

1. regras de governança aplicáveis;
2. commit e branch efetivamente sob inspeção;
3. fronteira rastreada e alterações controladas;
4. inventário da árvore, incluindo arquivos untracked;
5. integridade e hashes dos snapshots históricos;
6. origem, conteúdo, referências e hashes do manifest não rastreado;
7. tratamento formal, não destrutivo, do bloqueador de evidências;
8. condições objetivas para liberar ou interromper a etapa.

Esta fase não autoriza alterar `quality/legacy_tests/reconciliation.json`,
modernizar fixtures, executar correções de produto, modificar o manifest antigo,
remover arquivos ou aceitar qualquer falha histórica como resolvida.

## 2. Regras consultadas antes das decisões

Foram consultados, na árvore atual:

- `docs/POLITICA_NAO_REGRESSAO.md`;
- `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
- `docs/evidence/README.md`;
- `tools/run_legacy_tests.py`;
- `quality/legacy_tests/manifest.json`;
- `quality/legacy_tests/reconciliation.json`;
- `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`;
- `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`;
- decisões e evidências vigentes de `P2D-05/O-2`.

As regras aplicadas foram:

- evidência antes de qualquer afirmação de correção, equivalência, segurança
  ou conclusão;
- falha conhecida deve permanecer reproduzível e visível;
- perda silenciosa, alteração parcial e diagnóstico encoberto são proibidos;
- snapshots históricos não podem ser reescritos para obter `PASS`;
- manifest, hash, tamanho, referência e arquivo precisam concordar exatamente;
- todo manifest sob `docs/evidence/` está sujeito ao gate de rastreamento;
- resultado `BLOQUEADO`, `PARCIAL` ou `NÃO TESTADO` não equivale a aprovado;
- a etapa deve parar diante de divergência não explicada, arquivo fora da
  fronteira ou evidência incompleta.

## 3. Ambiente e identidade da execução

| Item | Resultado |
|---|---|
| HEAD | `96ab35d8a51d198f60a6b5dfa82007ccbc28ab59` |
| Branch | `fix/legacy-27-functional-regressions` |
| Plataforma | `Windows-10-10.0.26200-SP0` |
| Python | `3.11.9` |
| PySide6 | `6.10.1` |
| Qt | `6.10.1` |
| Alterações rastreadas após o commit | `0` |
| Push/merge/release | não executados |

Uma primeira tentativa de consulta do Qt usou um nome de símbolo incorreto e
falhou no próprio comando de inspeção. O comando foi corrigido imediatamente; a
consulta final acima passou. Isso foi um incidente do comando de diagnóstico,
não uma falha do produto, e não foi usado como evidência funcional.

## 4. Comandos executados e resultados

| Comando | Resultado verificável |
|---|---|
| `git rev-parse HEAD` | `96ab35d8a51d198f60a6b5dfa82007ccbc28ab59` |
| `git branch --show-current` | `fix/legacy-27-functional-regressions` |
| `git diff HEAD --stat` | vazio; nenhum delta rastreado após o commit |
| `git status --short --untracked-files=all` | `3338` entradas untracked; alterações rastreadas `0` |
| `git diff --cached --check` antes do commit | passou |
| `tools/run_legacy_tests.py --list --group all` | retorno `0`; integridade dos snapshots validada pelo runner; `24` arquivos e `196` testes declarados |
| `tools/evidence_integrity.py --require-tracked --git-blob` | retorno `1`; bloqueado pelo manifest Stage 10 não rastreado |
| verificação dos arquivos referenciados pelo manifest | `6` referências existentes; `0` ausentes; `0` divergências de hash |
| verificação de `hashes.sha256` | `7` entradas; `0` divergências |

O runner histórico foi usado aqui somente para verificar integridade/listagem do
snapshot. A listagem não é uma execução da suíte legada e não transforma as 26
falhas em aprovação.

## 5. Inventário da árvore

### 5.1 Contagens e identificadores

| Inventário | Resultado |
|---|---:|
| Arquivos rastreados por `git ls-files` | `3099` |
| Arquivos governados pelo baseline | `3098` |
| Entradas untracked no status completo | `3338` |
| Alterações rastreadas após o commit | `0` |
| SHA-256 do texto normalizado de `git status --porcelain=v1 --untracked-files=all` | `c59bbdb1f14421082074fb146ddce56e97e3cb3593b9d442a907cdeea55c2068` |
| SHA-256 do texto normalizado de `git ls-files` | `9db256960f11d0334e3010441a2b1283aa6fc6e5b057e51f9670dcc08dc28b04` |

Os `3099` arquivos rastreados incluem o arquivo de controle do baseline; os
`3098` correspondem ao conjunto governado verificado pelo
`baseline_integrity.py`. Essa diferença é registrada para evitar interpretar as
duas contagens como o mesmo universo.

### 5.2 Distribuição untracked observada

O inventário completo contém artefatos históricos, capturas, relatórios,
ambientes temporários e resíduos de execuções anteriores. A distribuição por
raiz, após normalização dos caminhos do status, foi:

```text
--help=16
--output=16
.build-worktree-4824e7b=1
.codex_patch_probe.txt=1
artifacts=3068
coverage-stage9-20260823.xml=1
docs=91
integrations=3
scripts=3
src=1
tests=1
tmp_fix_evidence_whitespace.ps1=1
tmp-legacy27-patch-work=6
tmp-p2d-02a-flow-offscreen=9
tmp-p2d-02a-flow-offscreen-r2=9
tmp-p2d-02a-flow-offscreen-r3-20260829=9
tmp-p2d-02a-flow-offscreen-r4-20260829=9
tmp-p2d-02a-flow-offscreen-r5-20260829=9
tmp-p2d-02a-flow-windows-20260829=9
tmp-p2d-02a-flow-windows-postcommit-20260829=9
tmp-p2d-02b-flow-offscreen-20260829=11
tmp-p2d-02b-flow-offscreen-20260829-r2=11
tmp-p2d-02b-flow-offscreen-postcommit-20260829=11
tmp-p2d-02b-flow-windows-20260829=11
tmp-p2d-02b-flow-windows-20260829-r2=11
tmp-p2d-02b-flow-windows-postcommit-20260829=11
```

A árvore está suja por estado preexistente. Nenhuma dessas entradas foi
removida, movida, adicionada ao commit ou usada para ampliar a fronteira do
lote. O inventário foi registrado para impedir que um `git diff` incompleto seja
interpretado como inventário completo.

## 6. Confirmação dos snapshots históricos

| Campo | Resultado |
|---|---|
| Arquivo | `quality/legacy_tests/manifest.json` |
| Tamanho | `21489` bytes |
| SHA-256 | `061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a` |
| `source_commit` | `cf749564ab5d961772d66dc363d0e990cebf8da3` |
| Arquivos declarados | `24` |
| Testes declarados | `196` |
| Integridade dos arquivos declarados | confirmada pelo runner, retorno `0` |

O manifest e seus testes históricos não foram editados. O resultado da suíte
legada continua separado da suíte oficial e da reconciliação.

Uma falha histórica somente poderá ser considerada reconciliada quando existir
contrato substituto real, teste equivalente aprovado, diagnóstico correspondente
e entrada formal na reconciliação. Reduzir a contagem bruta, remover a
expectativa ou reescrever o snapshot não é uma correção.

## 7. Auditoria do manifest não rastreado

### 7.1 Identidade e rastreamento

| Campo | Resultado |
|---|---|
| Caminho | `docs/evidence/artifacts/stage10-accessibility-20260824/BUILD-F10-ACCESSIBILITY-20260824-2151EF1/manifest.json` |
| Tamanho | `1501` bytes |
| SHA-256 | `a70f9f5c19663301882f0d65801ec9d91924cf03645beb5dc03ada9e18afac5b` |
| Última escrita UTC | `2026-08-24T23:29:07.7402605Z` |
| Rastreado pelo Git | `não` |
| Ignorado pelo Git | `não` |
| Status do manifest | `PASS` dentro do pacote Stage 10 antigo |
| Commit declarado pelo pacote | `2151ef1aed06e2660a5e04f1d9d0b4651cb5bcce` |
| Commit declarado existe localmente | `sim` |

### 7.2 Conteúdo e referências

O manifest referencia `report.json` e cinco capturas visuais. A auditoria
read-only confirmou:

- `6/6` referências existem;
- `0` arquivos ausentes;
- bytes das cinco capturas conferem com o manifest;
- SHA-256 das seis referências conferem;
- o índice auxiliar `hashes.sha256` contém `7/7` hashes corretos, incluindo o
  próprio manifest;
- o relatório declara Stage 10, requisito `REQ-F10-UI-ACCESSIBILITY`, branch
  `main` e commit antigo `2151ef1...`;
- o conteúdo não declara ser evidência do HEAD atual `96ab35d...`;
- o pacote possui limitações explícitas para DPI nativo e escopo de Stage 10.

O pacote é internamente coerente, mas não é evidência atual rastreada. A
coerência dos bytes não elimina o bloqueio de rastreamento nem autoriza
apresentar o `PASS` antigo como validação deste commit.

### 7.3 Tratamento formal adotado

O tratamento nesta Fase 0 é:

1. preservar o diretório e todos os arquivos no local atual;
2. não editar o manifest, o relatório, os hashes ou as capturas;
3. não remover, mover, ignorar ou sobrescrever nenhum arquivo;
4. não estagiar automaticamente um pacote de evidência de uma etapa anterior;
5. classificar o gate como `BLOQUEADO — manifest de evidência não rastreado`;
6. exigir decisão formal de escopo/propriedade antes de qualquer inclusão no
   pacote candidato;
7. se o pacote for mantido no repositório, incluir o conjunto autocontido,
   atualizar referências/registro e baseline, e executar novamente o gate;
8. se for considerado externo ao escopo, registrar decisão de retenção e
   localização compatível com a política, sem exclusão silenciosa e sem deixar
   manifest sob `docs/evidence/` fora do gate;
9. somente depois da decisão repetir `evidence_integrity.py
   --require-tracked --git-blob`.

Nenhuma dessas alternativas foi executada automaticamente porque representa
mudança de escopo e potencial alteração de evidência histórica. A preservação é
a única ação segura até a decisão formal.

## 8. Resultado do gate de entrada

| Critério | Estado | Fundamentação |
|---|---|---|
| Regras consultadas | `PASS` | políticas e contratos lidos antes das decisões |
| Commit/branch identificados | `PASS` | HEAD e branch confirmados |
| Fronteira rastreada do commit | `PASS` | zero delta rastreado após `96ab35d` |
| Inventário da árvore | `PASS COM RISCO REGISTRADO` | `3338` untracked identificados e hash do inventário registrado |
| Snapshots históricos | `PASS` | manifest de `24/196` íntegro, sem alteração |
| Manifest Stage 10 | `BLOQUEADO` | não rastreado e não ignorado sob `docs/evidence/` |
| Integridade de evidências | `BLOQUEADO` | `tools/evidence_integrity.py` falhou no manifest untracked |
| Autorização para implementar Fases 1–7 | `NÃO CONCEDIDA` | gate de entrada não aprovado |

### Decisão da Fase 0

`BLOQUEADO — resolver formalmente o manifest não rastreado antes de iniciar
fixtures, implementação, testes substitutos ou evidências das Fases 1–7.`

O bloqueio é de governança/integridade de evidência, não uma autorização para
alterar regras, snapshots ou critérios. A etapa não está aprovada para
implementação parcial.

## 9. Critérios para reabrir o gate

O gate somente poderá ser reaberto quando existir decisão registrada sobre o
manifest Stage 10 e, conforme a decisão:

- o pacote completo estiver rastreado e incluído na fronteira, com manifest,
  hashes, referências e baseline coerentes; ou
- a retenção fora do escopo estiver formalizada de maneira compatível com a
  política, sem manifest abandonado sob `docs/evidence/`;
- `tools/evidence_integrity.py --require-tracked --git-blob` passar;
- a árvore e a fronteira candidata forem re-inventariadas;
- hashes dos snapshots históricos forem confirmados novamente;
- o relatório vivo for atualizado com o commit efetivamente sob inspeção;
- somente depois forem autorizadas as Fases 1–7 integrais.

## 10. Próximo passo obrigatório

O próximo passo não é implementar uma fixture nem alterar o produto. É decidir
formalmente o destino do pacote Stage 10, preservando-o até a decisão, e repetir
o gate de evidências e o inventário no estado resultante. Enquanto isso não
ocorrer, a nova etapa permanece `BLOQUEADA` e nenhum resultado parcial poderá ser
apresentado como progresso aprovado.
