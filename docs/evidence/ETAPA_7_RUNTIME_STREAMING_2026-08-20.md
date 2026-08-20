# Etapa 7 do ADR de runtime — streaming

**Estado:** EM DESENVOLVIMENTO / NÃO APROVADA
**Branch:** `Ailton/runtime-stage7-streaming`
**Base:** `1e6b4c8f08f2237ec4dcc2ff8a5c6368515be1c9`
**ADR:** `docs/ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md`

Esta é uma evidência viva da RUNTIME-ETAPA-7. Ela não substitui a governança
global, não reclassifica snapshots históricos e não constitui aprovação,
merge, release ou suporte de engine.

## Escopo em desenvolvimento

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

A execução local em árvore modificada produziu todos os checks funcionais como
`true`, incluindo leitura assíncrona real, payload, prioridades, cache,
recuperação, limites, persistência, hash e privacidade. O status geral foi
`FAIL` exclusivamente por `source_tree_clean=false`. Esse FAIL é legítimo e
esperado antes do checkpoint; não é PASS parcial nem aprovação.

O auditor gera `stage7-runtime-streaming-report.json`,
`streaming-sidecar.json` e `artifact-index.json` com SHA-256. O pacote
intermediário só será evidência final após regeneração em árvore limpa e
validação dos bytes rastreados pelo Git.

## Gates pendentes

- suíte integral e cobertura branch sem redução;
- baseline e manifests contra bytes efetivamente versionados;
- auditoria em árvore limpa e artefatos hashados;
- CI Linux e Windows;
- PR, revisão de checks e merge normal;
- validação pós-merge e reconciliação desta evidência com o commit final.

Até todos os gates passarem, a Etapa 7 permanece **EM DESENVOLVIMENTO / NÃO
APROVADA**. Streaming GPU, residência de VRAM e integração nativa Godot/Unity
continuam fora do escopo desta etapa.
