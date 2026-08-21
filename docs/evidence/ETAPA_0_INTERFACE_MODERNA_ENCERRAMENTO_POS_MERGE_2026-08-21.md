# Etapa 0 — Encerramento pós-merge da baseline visual — 2026-08-21

## Estado formal

**APROVADO somente para caracterização reproduzível da baseline visual.**
Nenhuma implementação de redesign, aprovação de release ou conclusão das
etapas posteriores é inferida deste documento.

- PR: `#129`.
- CI da PR: run `32521765023`; jobs Linux e Windows concluídos com sucesso.
- Merge: `61165a58bfa6d5b6a10bcbee89dd8d7e7c6fe643`.
- Branch pós-merge: `main`.
- HEAD local e `origin/main`: `61165a58bfa6d5b6a10bcbee89dd8d7e7c6fe643`.
- Confirmação humana independente: `NOT_CONFIRMED`; a revisão visual do agente
  permanece registrada separadamente e não é apresentada como confirmação
  humana.

## Validação pós-merge executada

Os checks abaixo foram executados após o merge, no `main` local apontando para
o SHA acima:

- Suíte integral: `1576 passed, 2 skipped in 42.19s`.
- Integridade de evidências: `82 manifests validated`.
- Auditor visual sobre os PNGs versionados: `finding_count: 0`,
  `status: PASS`.
- Baseline verificado com `--git-blob` em worktree temporária limpa:
  `Baseline verified: 1867 files`, código de saída `0`.
- Árvore rastreada: limpa e sincronizada com `origin/main`.
- Os diretórios locais de builds anteriores não rastreados foram preservados;
  eles não foram usados como evidência nem incluídos no baseline Git-blob.

O auditor visual pós-merge reutilizou somente o pacote versionado em
`docs/evidence/artifacts/ui-modernization-stage0-20260821/`, incluindo as
capturas das três resoluções, os cinco estados por resolução, os manifests,
os hashes e as imagens anotadas. Nenhum PNG antigo de build foi promovido a
evidência do merge.

## CI e avisos observados

O CI aprovado registrou dois avisos não bloqueantes já analisados:

- o empacotamento do Poetry ignorou arquivos `__pycache__`, que não são fonte
  versionada;
- `pip-audit` não encontrou o pacote local `neoeng-d-trace` no índice PyPI.

Esses avisos não foram ocultados nem convertidos em sucesso artificial; não
alteraram o resultado dos jobs obrigatórios.

## Reconciliação documental

`ETAPA_0_INTERFACE_MODERNA_2026-08-21.md` permanece preservado como snapshot
da captura pré-merge, com o SHA e o estado correspondentes àquela execução.
Este documento é o encerramento vivo pós-merge e registra a validação no SHA
`61165a5`.

## Limitações e findings mantidos

O auditor automático encontrou zero violações de bytes, dimensões, alpha,
clipping, geometrias, sobreposição ou paleta. Isso não significa que o design
esteja modernizado. Permanecem findings de baseline para etapas futuras:

1. barra esquerda predominantemente textual e com bordas laranjas espessas;
2. barra superior com agrupamento visual inconsistente e excesso de texto;
3. indicador `VIEW/ZOOM` dentro do viewport;
4. painéis legíveis nesta execução, mas ainda densos para a modernização;
5. diferença entre dimensões lógicas e físicas sob DPI local de 200%.

Nenhuma dessas observações foi mascarada para obter `PASS`, e nenhuma foi
declarada corrigida na Etapa 0.

## Decisão

**Etapa 0 concluída formalmente apenas no escopo de baseline visual e contrato
de escopo.** A Etapa 1 continua `PLANEJADA / NÃO INICIADA`; não deve ser
iniciada antes de nova autorização e de seus próprios gates.
