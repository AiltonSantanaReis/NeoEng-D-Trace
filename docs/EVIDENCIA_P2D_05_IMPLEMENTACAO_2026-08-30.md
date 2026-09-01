# Evidência P2D-05 — implementação e qualificação pré-commit

**Status:** `QUALIFICATION READY — PRECOMMIT PENDING`
**Data:** 30/08/2026 (UTC-03)
**Decisão:** `P2D-05 ACEITO — contrato de performance, limites, formatos e erros`
**Branch:** `p2d-05-quality-hardening`
**HEAD-fonte da execução:** `fc59ff571e4e4d99ddd40a8ec318d50b8edd77f3`
**Base de produção/rollback:** `f55b07b85ef2cf65160f2c10ffac5e63b45732ac`

Este registro documenta a execução corrente da implementação controlada. O
lote ainda não foi commitado, publicado, mesclado ou selado. Portanto, este
registro não declara P2D-05 concluída e não autoriza a próxima etapa.

## 1. Estado e fronteira

O aceite do proprietário autorizou somente a implementação dentro da
fronteira da decisão. A produção permanece ancorada na base de rollback; o
HEAD indicado é o commit documental que antecede as alterações de trabalho.

Na prova final da árvore:

- branch: `p2d-05-quality-hardening`;
- HEAD: `fc59ff571e4e4d99ddd40a8ec318d50b8edd77f3`;
- mudanças tracked: `13` — dois documentos de decisão/plano e 11 arquivos de produção já tracked;
  o novo `src/persistence/p2d05_errors.py` permanece untracked até o commit;
- mudanças untracked de qualificação não foram incluídas na contagem tracked;
- `git diff --check`: `PASS`; os avisos de conversão CRLF/LF não indicaram
  erro de conteúdo;
- nenhum commit, build, push, tag, merge ou release foi realizado neste lote.

Arquivos de produção alterados dentro da fronteira:

- `src/core/logger.py`;
- `src/exporters/scene_authoring_export.py`;
- `src/persistence/scene_authoring_io.py`;
- `src/persistence/p2d05_errors.py`;
- `src/ui/scenario_authoring_actions.py`;
- `src/ui/scenario_editor_window.py`;
- `src/ui/scenario_panel.py`;
- `src/ui/scene_asset_panel.py`;
- `src/ui/scene_authoring_group_stack.py`;
- `src/ui/scene_authoring_inspector.py`;
- `src/ui/scene_authoring_layer_stack.py`;
- `src/ui/scene_authoring_viewport.py`.

Arquivos de qualificação autorizados:

- `tests/test_p2d_05_quality_contract.py`;
- `scripts/benchmark_p2d_05.py`;
- `scripts/audit_p2d_05_evidence.py`;
- este documento, o registro de boundary e a atualização do plano vivo;
- artefatos locais sob `artifacts/p2d05/`, com exclusão explícita dos caches
  brutos de engines da evidência publicável.

Impacto declarado: `G=0`; em `B`, somente observabilidade e orientação de
recuperação para falhas já existentes. Não foram alterados limites normativos,
schemas, versões, bytes canônicos válidos, mapeamentos, QAction, atalhos,
árvore de widgets, geometria, editor legado ou linhas independentes.

## 2. Resultado funcional da implementação

### 2.1 Limites e atomicidade

- a serialização canônica rejeita o primeiro payload acima de
  `MAX_PROJECT_FILE_BYTES` antes de qualquer escrita;
- a exportação rejeita o primeiro payload acima do mesmo limite antes de
  substituir o destino;
- o destino preexistente permanece byte a byte inalterado no teste negativo;
- nenhum valor de `src/core/operational_limits.py` foi alterado;
- recovery válido, atomicidade, ordenação e hash do conteúdo válido foram
  preservados.

### 2.2 Formatos e exportação

- V1 e V2 continuam explícitos; não há migração silenciosa;
- exportações `generic`, `godot` e `unity` continuam determinísticas;
- `source_path` continua fora do payload portátil;
- a nova verificação de tamanho não modifica o payload válido, apenas impede
  a escrita de payload excedente;
- a matriz completa foi emitida por
  `artifacts/p2d05/audit-precommit.json` com `mapping_errors=0`.

### 2.3 Mensagens e recuperação

O novo classificador `src/persistence/p2d05_errors.py` mantém a exceção de
domínio, mas apresenta código estável, causa resumida, ação recomendada e
estado preservado. Caminhos de host, credenciais e segredos são removidos de
mensagens e logs. O stream e o arquivo de log usam a mesma proteção.

## 3. Gates executados

| Gate | Resultado corrente |
|---|---|
| Teste focal P2D-05 | `17 passed` |
| Suíte completa sem cobertura | `1859 passed, 2 skipped, 1 warning` |
| Suíte completa com cobertura | `1859 passed, 2 skipped, 1 warning` |
| Cobertura de linhas no XML | `23547/25424 = 92,62%` |
| Cobertura de branches no XML | `6569/7726 = 85,02%` |
| `tools/check_coverage_policy.py coverage.xml` | `PASS` |
| Compileall de app/src/tests/tools | `PASS` |
| Flake8 completo | `PASS` |
| Black completo | `345 files would be left unchanged` |
| Isort completo | `PASS` |
| Mypy de `src` | `PASS — 145 source files` |
| Bandit `src -lll` | `PASS` |
| Pip-audit | `No known vulnerabilities found`; o pacote local não foi auditado por não existir no índice |
| Auditoria da matriz P2D-05 | `PASS`; 25 limites, 2 formatos, 11 erros, 0 mapeamentos inválidos |
| Varredura de privacidade dos candidatos | `PASS` |
| Varredura dos relatórios sanitizados de engines | `PASS` |

O único warning da suíte é uma depreciação de construtor `QMouseEvent` em
teste histórico; não é falha introduzida pelo lote.

## 4. Performance medida

Artefato primário: `artifacts/p2d05/benchmark-precommit.json`.
Auditoria correlata: `artifacts/p2d05/audit-precommit.json`.

Ambiente registrado pelo benchmark:

- Windows, `os_release=10`;
- Python `3.11.9` da `.venv`;
- arquitetura `AMD64`;
- processador reportado: `AMD64 Family 25 Model 33 Stepping 2, AuthenticAMD`;
- `16` CPUs lógicas;
- PySide6/QT sem override de backend no benchmark
  (`qt_qpa_platform=default`);
- commit-fonte e branch registrados no próprio JSON;
- 20 medições por operação, 2 aquecimentos e sessão prolongada de 100 ciclos,
  com amostra a cada 10 ciclos.

Os workloads são medições controladas, não novos tetos de produto:

| Workload | Objetos | Bytes da cena | Serialize p95 | Load/validate p95 | Save/recovery p95 | Reload p95 | Edit/history p95 | Preview p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `small` | 1 | 1.970 | 1,001 ms | 2,498 ms | 13,079 ms | 2,477 ms | 1,062 ms | 7,782 ms |
| `reference` | 64 | 39.748 | 16,590 ms | 7,200 ms | 42,530 ms | 7,093 ms | 14,727 ms | 38,058 ms |
| `bounded-stress` | 512 | 309.129 | 129,727 ms | 39,477 ms | 190,026 ms | 39,564 ms | 112,120 ms | 291,200 ms |

| Workload | Generic export p95 | Godot export p95 | Unity export p95 | Erros | Bytes determinísticos |
|---|---:|---:|---:|---:|---|
| `small` | 12,320 ms | 12,375 ms | 11,915 ms | 0 | `true` |
| `reference` | 84,048 ms | 84,421 ms | 83,537 ms | 0 | `true` |
| `bounded-stress` | 567,886 ms | 551,940 ms | 557,996 ms | 0 | `true` |

Memória observada pelo `tracemalloc`:

| Workload | Inicial | Pico | Final | Sessão prolongada: primeiro → último | Crescimento observado |
|---|---:|---:|---:|---:|---:|
| `small` | 0 B | 1.120.916 B | 70.941 B | 91.385 → 91.761 B | 376 B |
| `reference` | 0 B | 1.678.354 B | 600.370 B | 1.195.158 → 1.195.566 B | 408 B |
| `bounded-stress` | 0 B | 12.485.167 B | 4.045.995 B | 8.769.871 → 8.770.279 B | 408 B |

Os pontos de sessão prolongada são observacionais e monotônicos nesta
execução; o relatório declara expressamente que isso não é veredicto isolado
de ausência de leak.

A referência de runtime existente permanece `60 FPS` e p95 de frame
`<=16,7 ms`, mas não foi medida por este benchmark de operações do editor.
Nenhuma meta de runtime foi reescrita.

## 5. Proposta de orçamento normativo — aceite ainda pendente

O contrato exige aceite explícito; os valores abaixo são proposta de engenharia
para o workload `reference` (64 objetos, hardware acima), em p95. Não são
limites de produto enquanto não forem aceitos.

| Operação | Medido p95 | Orçamento proposto p95 | Estado |
|---|---:|---:|---|
| Serialize | 16,590 ms | <=25 ms | pendente de aceite |
| Load/validate | 7,200 ms | <=15 ms | pendente de aceite |
| Save/recovery atômico | 42,530 ms | <=60 ms | pendente de aceite |
| Reload | 7,093 ms | <=15 ms | pendente de aceite |
| Edit/history | 14,727 ms | <=20 ms | pendente de aceite |
| Preview sync | 38,058 ms | <=50 ms | pendente de aceite |
| Export genérico | 84,048 ms | <=120 ms | pendente de aceite |
| Export Godot | 84,421 ms | <=120 ms | pendente de aceite |
| Export Unity | 83,537 ms | <=120 ms | pendente de aceite |

O workload `bounded-stress` é diagnóstico de degradação e não recebe um novo
orçamento normativo por inferência. O proprietário deve aceitar ou revisar a
matriz acima antes de o lote poder receber `PRECOMMIT ACCEPT`.

## 6. Formatos e compatibilidade efetivamente verificados

| Formato | Entrada/saída | Versões/alvos | Regra de incompatibilidade | Prova |
|---|---|---|---|---|
| Authoring | `.ndtscene.json` | V1 e V2 | UTF-8 estrito, schema explícito, sem migração silenciosa | `tests/test_stage5_scene_authoring_persistence.py` |
| Export | `SceneAuthoringDocumentV2` → `.runtime.json` | versão 1; `generic`, `godot`, `unity` | alvo, capability ou schema incompatível é rejeitado | `tests/test_stage5_scene_authoring_persistence.py` e `tests/test_p2d_04_persistence_recovery_export.py` |

Foram confirmados bytes canônicos, ordenação, newline, SHA-256, remoção de
`source_path` do export portátil, orientação, escala, pivot, flip e rejeição
de BOM, UTF-8 inválido, JSON não objeto, números não finitos, chaves
duplicadas, versão e target incompatíveis.

## 7. Validação real de engines

As provas foram executadas contra o exportador corrente e o fixture
assimétrico, reutilizando o validador oficial do repositório:

- Godot `4.7-stable.official.5b4e0cb0f`: `SUCCESS`, retorno `0`,
  materialização de câmera/parallax/objeto e `14.400` pixels visíveis;
- Unity `6000.5.7f1`: `SUCCESS`, retorno `0`, materialização e `266`
  pixels visíveis.

Referências publicáveis:

- `artifacts/p2d05/engine-evidence-final/godot-validation.json`;
- `artifacts/p2d05/engine-evidence-final/unity-validation.json`;
- `artifacts/p2d05/engine-evidence-final/godot-professional-capture.png`;
- `artifacts/p2d05/engine-evidence-final/unity-professional-capture.png`.

O diretório bruto de trabalho do Unity contém caches gerados pelo engine com
caminhos locais. Ele foi preservado localmente para rastreabilidade, mas está
explicitamente excluído de qualquer commit, review package ou seal. Somente
os quatro artefatos sanitizados acima são publicáveis.

## 8. Catálogo de erros

| Código | Categoria | Ação apresentada | Estado preservado |
|---|---|---|---|
| `P2D05-FORMAT` | formato/schema/UTF-8 inválido | corrigir JSON, campos obrigatórios e versão | documento ativo não substituído |
| `P2D05-LIMIT` | limite excedido | reduzir tamanho e tentar novamente | nenhuma alteração parcial |
| `P2D05-ASSET` | asset ausente, externo ou alterado | relink/replace e tentar novamente | último documento válido preservado |
| `P2D05-TARGET` | alvo/capacidade não suportado | escolher alvo suportado | export incompleto não gravado |
| `P2D05-READ` | falha de leitura | verificar arquivo/acesso ou recuperar último válido | documento ativo não substituído |
| `P2D05-WRITE` | falha de gravação | verificar permissão/espaço e tentar novamente | arquivo salvo anterior inalterado |
| `P2D05-RECOVERY` | recovery inválido/indisponível | manter corrente e escolher recovery válido | nenhum documento substituído |
| `P2D05-LOCK` | seleção bloqueada | desbloquear objeto/camada/grupo | nenhuma alteração aplicada |
| `P2D05-REFERENCE` | item referenciado ausente | atualizar e selecionar item existente | nenhuma alteração aplicada |
| `P2D05-PREVIEW` | preview não atualizado | verificar documento/assets e tentar novamente | documento autoral inalterado |
| `P2D05-OPERATION` | operação rejeitada | verificar seleção/estado e tentar novamente | nenhuma alteração aplicada |

O teste focal inclui fluxo Qt real de falha tipada de gravação em
`ScenarioEditorWindow`, verificando código, orientação e ausência do caminho
de fixture na mensagem. Os testes existentes de P2D-04/P2D-03 continuam
cobrindo recovery, retry, exportação, cancelamento e preservação do estado
válido.

## 9. Capturas e auditoria visual

Foram executados o capturador real da aplicação e o auditor visual:

- offscreen: `16` PNGs, captura e auditoria com `exit=0`,
  `finding_count=0`;
- Windows nativo: `16` PNGs, captura e auditoria com `exit=0`,
  `finding_count=0`;
- resoluções cobertas: `720p_Compacta`, `768p_Minima` e `1080p_FHD`;
- a captura Windows registrou escala nativa de `3840x2120` para janela lógica
  de `1920x1060`; essa diferença é DPI documentado, não alteração de layout.

Artefatos: `artifacts/p2d05/ui-capture/`,
`artifacts/p2d05/ui-audit/`, `artifacts/p2d05/ui-capture-windows/` e
`artifacts/p2d05/ui-audit-windows/`.

## 10. Privacidade, integridade e limitações

- candidatos P2D-05: nenhum caminho pessoal, nome de provedor, credencial ou
  segredo encontrado;
- relatórios sanitizados de engines: nenhum caminho pessoal ou credencial;
- o logger agora redige caminhos e atribuições de credenciais tanto no stream
  quanto no arquivo;
- o relatório de benchmark não registra nome de host nem usuário;
- `poetry` não está instalado neste ambiente; `poetry check --lock --strict`
  e `poetry sync` do CI não foram declarados como executados;
- CI Linux/Windows, checks protegidos, build final, revisão humana,
  commit/postcommit, seal e publicação remota permanecem pendentes e não são
  simulados por esta evidência.

## 11. Decisão atual

A implementação está tecnicamente qualificada nos gates locais listados, mas
P2D-05 permanece aberta por três razões formais:

1. os orçamentos normativos de operações do editor ainda aguardam aceite
   explícito;
2. o ciclo de commit, CI remoto e requalificação pós-commit ainda não foi
   autorizado/executado;
3. build e revisão humana final ainda não foram concluídas para este lote.

Próxima decisão necessária do proprietário: aceitar ou revisar a matriz da
seção 5. Somente depois disso a revisão de fronteira poderá solicitar
`P2D-05 PRECOMMIT ACCEPT`; nenhum commit ou publicação é permitido antes
desse aceite.
