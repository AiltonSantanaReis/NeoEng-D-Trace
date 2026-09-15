# Adendo 01 — Portabilidade de Hash e EOL Canônico

**ID:** `ADDENDUM-REAL-01-20260915`
**Estado documental:** `ATIVO / CORREÇÃO CONTROLADA`
**Plano protegido:** `PLANO_IMUTAVEL_PRODUTO_REAL_2026-09-15.md`
**Política:** `ADDENDUM_ONLY`

## 1. Autoridade e escopo

Este documento é um adendo numerado ao plano imutável e ao adendo normativo de
realidade. Ele corrige exclusivamente a portabilidade do mecanismo de hashes
entre checkouts Windows e Linux. Não altera requisitos do produto, não reabre
etapas concluídas e não converte evidência parcial em `PASS`.

O plano original, a governança superior e o adendo normativo de realidade
continuam preservados byte a byte. Esta correção é aditiva e será selada por um
novo lock e um novo commit protegido.

## 2. Falha real que motivou o adendo

O PR `#175`, no commit `c8857bea92b770ca53bf8af47e47797e79efbe23`, foi executado
no GitHub Actions em Linux e Windows. O gate fail-closed encontrou:

- Linux: `FAIL` — `governance hash mismatch`;
- Windows: `FAIL` — `immutable plan hash mismatch`;
- todas as etapas posteriores dependentes foram `BLOCKED`/skipped pelo próprio
  fluxo de falha, e o merge foi corretamente impedido.

Essa evidência é preservada no histórico do CI e não será reclassificada.

## 3. Causa técnica confirmada

O checkout local usava `core.autocrlf=true`, enquanto os cinco arquivos
hash-bound não tinham uma regra explícita de EOL no `.gitattributes`. Assim, o
hash do worktree Windows podia conter `CRLF`, enquanto o runner Linux lia
`LF`; arquivos novos também podiam sofrer conversão no checkout Windows.

O problema estava no contrato de representação dos bytes, não na tolerância do
gate. Alterar o hash para aceitar ambas as formas seria uma redução de
integridade e é proibido.

## 4. Decisão corretiva

Os documentos normativos hash-bound passam a ter representação canônica
`UTF-8` com finais de linha `LF`, declarada explicitamente no `.gitattributes`:

1. governança superior;
2. adendo normativo de realidade;
3. este adendo;
4. plano imutável;
5. lock criptográfico;
6. índice documental ativo.

O lock será recalculado somente sobre esses bytes canônicos. O validador
continuará comparando bytes reais do arquivo, sem normalização permissiva,
fallback, tolerância, baseline alternativa ou filtro de plataforma.

O novo lock também fixa o caminho e o hash deste adendo. Recibos de etapa
deverão declarar sua leitura integral e o hash de todos os documentos
normativos obrigatórios, incluindo este adendo.

## 5. Critérios de aceite

Esta correção só poderá ser promovida quando todos os itens a seguir tiverem
evidência real:

- `eol=lf` presente para cada documento hash-bound;
- hashes do lock iguais aos bytes efetivamente lidos no Linux e no Windows;
- gate `plan` PASS em ambos os runners;
- suíte oficial completa executada sem falha, warning, skip, xfail ou erro;
- árvore limpa, lock e adendo rastreados;
- PR atualizado e aprovado sem bypass;
- proteção remota de `main` aplicada após o merge, com histórico preservado.

Até esse conjunto estar comprovado, o estado desta correção é `IN_PROGRESS` ou
`BLOCKED`, conforme a evidência observada; nunca será declarado concluído por
inferência.

## 6. Não escopo

Este adendo não autoriza build de produto, testes Unity/Godot, shutdown,
symlink, soak, captura visual, promoção de assets ou qualquer teste perigoso no
computador principal. Esses fluxos continuam sujeitos ao plano imutável e às
restrições de ambiente controlado.
