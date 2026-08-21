# Etapa 7 do ADR de runtime — streaming

**Estado:** ENCERRADA NO ESCOPO APROVADO
**Branch:** `Ailton/runtime-stage7-streaming`
**Base:** `1e6b4c8f08f2237ec4dcc2ff8a5c6368515be1c9`
**ADR:** `docs/ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md`

Esta é a caracterização técnica da RUNTIME-ETAPA-7; o encerramento pós-merge está em documento separado. Ela não substitui a governança global, não reclassifica snapshots históricos e não declara release ou suporte de engine.

## Escopo implementado

O sidecar `neoeng-d-trace-runtime-streaming` permanece separado dos contratos
de autoria. Ele registra origem hash-bound, assets com caminhos POSIX relativos,
tamanho e SHA-256 exatos, prioridades, flags de retenção e limites lógicos.
O runtime carrega arquivos reais sob uma raiz confinada, agenda requisições de
forma determinística, limita trabalho concorrente, mantém cache LRU, impede
descarte de assets referenciados ou fixados, expõe cancelamento e falhas,
permite retry explícito e mantém persistência atômica do sidecar.

`runtime.streaming` foi anunciado como capacidade própria no `RuntimeHost`. O
contrato não altera `.ndtproj` v1, o editor, o gizmo, os exportadores existentes
ou os adaptadores Godot/Unity. Bytes não canônicos, caminhos inseguros,
hashes/tamanhos incorretos, duplicidades e limites inválidos são rejeitados.

## Baseline e testes reais

A baseline anterior à alteração foi o merge
`1e6b4c8f08f2237ec4dcc2ff8a5c6368515be1c9`. A caracterização foi executada
contra bytes Git-blob antes da criação do código da Etapa 7.

Comando focal:

```text
.\.venv\Scripts\python.exe -m pytest -q tests/test_stage7_runtime_streaming.py --tb=short
```

Resultado reproduzido: **11 passed**.

Os testes cobrem round-trip canônico, hashes, arquivo real, prioridade estável,
limite de pendências, eviction LRU, referência que impede eviction,
cancelamento observável, reativação após `CANCELLED`/`EVICTED`, hash incorreto,
retry explícito, limite de cache, persistência atômica, caminhos inseguros,
duplicidades, bytes não canônicos, limites e capacidade anunciada.

Gates focais reproduzidos: Black PASS, isort PASS, Flake8 PASS e mypy PASS no
runtime e no auditor.

## Falha reproduzida e correção

A primeira execução reproduziu um defeito real: ao concluir um asset, o
agendador transformava todos os demais assets pendentes sem requisição em
`CANCELLED`. Uma requisição posterior não reativava esse estado, o asset não era
carregado e o evento de eviction esperado não aparecia. A causa foi confirmada
com fixture local mínimo e loader real.

A correção removeu o cancelamento implícito de pendências sem requisição,
reativa `CANCELLED`/`EVICTED` em nova requisição e emite evento explícito de
cancelamento. O caso virou teste regressivo. Nenhum limiar, scanner, asserção
histórica ou regra de governança foi alterado.

## Auditoria reproduzível

```text
.\.venv\Scripts\python.exe scripts/audit_runtime_streaming_phase7.py --output <new-directory>
```

A primeira execução local em árvore modificada produziu todos os checks
funcionais como `true`, mas registrou `FAIL` exclusivamente por
`source_tree_clean=false`. Esse FAIL foi legítimo e esperado antes do
checkpoint; não foi tratado como PASS parcial.

Após o checkpoint local `b456248972e046e44b06eb00b07f5d1d58f0fd84`, a execução em
árvore limpa produziu `PASS` em todos os checks. A correção de ordenação isort
foi registrada em `89109440f9ed867501e6326a1b3c59d12b3796bc`; a auditoria foi
reexecutada nesse HEAD e confirmou leitura assíncrona real, payload, prioridades,
cache, recuperação, limites, persistência, hash, privacidade e
`source_tree_clean=true`. A suíte integral reproduziu `1535 passed, 2 skipped` e
a política integrada de cobertura passou com linhas e branches dentro dos
limites vigentes.

Pacote PASS final desta caracterização, vinculado ao HEAD
`89109440f9ed867501e6326a1b3c59d12b3796bc`, versionado em
`docs/evidence/artifacts/runtime-streaming-phase7-post-isort-2026-08-20/`. O
pacote anterior em `runtime-streaming-phase7-2026-08-20/` permanece preservado
como evidência do checkpoint anterior:

- `stage7-runtime-streaming-report.json`: 2104 bytes; SHA-256 `68a0de35ec899d0a65c4fc9a0e8581f76b15216d10951948b0108d1a4f6bee80`;
- `streaming-sidecar.json`: 1168 bytes; SHA-256 `be1d2bfe30873d54062d66dcb987b9680ae5daa9fc5d6795399cf40e94160fd6`;
- `artifact-index.json`: 382 bytes; SHA-256 `12b9a012b0bbc2892aaaddeb13d28772a2045a8feef225f02a6f01eef531e0d9`.

O índice foi gerado pelo próprio auditor no HEAD corretivo e os hashes acima
foram recalculados localmente após a geração do pacote.
## Encerramento e fronteira

Os gates foram concluídos no merge `f0d350ad7b61e2e9bc7865515768f3662804c953`: CI Linux/Windows no run `32430267567`, suíte integral, cobertura, baseline Git-blob, integridade de evidências, auditoria limpa e validação pós-merge. Consulte `docs/evidence/ETAPA_7_RUNTIME_STREAMING_ENCERRAMENTO_POS_MERGE_2026-08-20.md`. Streaming GPU, residência de VRAM e integração nativa Godot/Unity continuam fora do escopo desta etapa.