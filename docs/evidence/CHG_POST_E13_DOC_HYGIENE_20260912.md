# Registro de mudança — higiene documental pós-E13

**ID:** `CHG-POST-E13-DOC-HYGIENE-20260912`
**Versão:** 1.0
**Data:** 2026-09-12
**Estado:** `PASS`
**Commit base:** `2b7e505a7783d5a9e5e0d23a4334ad40692f1382`
**Escopo:** correção textual mínima em documento de prompts adiado.

## Motivo

A suíte oficial encontrou uma violação de higiene documental em
`PROMPTS_PRODUCAO_KIT_FLORESTA_20260912.md:184`: o texto citava literalmente
uma chave específica de provedor. Isso não afeta o contrato do editor nem a
produção de modelos, mas bloqueia a validação oficial do repositório.

## Mudança controlada

O literal específico foi substituído por uma descrição genérica de chave de
API do provedor configurado. O significado operacional do prompt não mudou:
produção continua adiada, nenhum asset foi gerado e a autorização explícita
continua necessária para qualquer fallback.

Nenhum arquivo em `src/`, teste, schema, baseline, build ou runtime foi
alterado. O resultado anterior `FAIL` está preservado no commit base e na
[auditoria das referências de UI/UX](AUDITORIA_REFERENCIAS_UI_UX_INSPETOR_POS_E13_20260912.md).

## Impacto e proteção

- IDs de produto e contratos funcionais: preservados.
- E13: fechado; nenhum requisito foi reaberto.
- Gizmo: permanece `PLANNED`.
- Produção de modelos: permanece `PLANNED`.
- Risco de regressão de runtime: `NOT_APPLICABLE` para esta alteração textual.
- Risco de higiene: deve ser reavaliado pela suíte oficial completa.

## Critérios de aceite

1. O documento continua semanticamente equivalente e sem referência textual
   proibida.
2. A suíte oficial completa deve ser executada sem filtro.
3. O resultado anterior deve permanecer rastreável.
4. A continuidade deve retornar `PASS`.
5. A árvore deve permanecer sem alterações de código.

Antes da reexecução completa, o estado desta mudança era `IN_PROGRESS`.

## Verificação executada

- suíte oficial sem filtros: `2620 passed, 2 skipped, 5 warnings` em 77,26 s;
- higiene focada: `2 passed`;
- continuidade: `CONTINUITY_REGISTRY=PASS`;
- `git diff --check`: `PASS`;
- alterações em código, schema, build e runtime: nenhuma.

Os dois skips e os cinco warnings continuam preservados na saída da suíte.
Esta mudança documental pode ser considerada `PASS`; a revisão visual humana
do editor permanece uma etapa separada e ainda `PENDING_EVIDENCE`.
