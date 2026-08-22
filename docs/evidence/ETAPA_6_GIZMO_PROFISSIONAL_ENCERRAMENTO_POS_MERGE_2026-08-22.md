# Etapa 6 — Gizmo profissional — validação pós-merge

**Estado:** `CONCLUÍDA NO ESCOPO APROVADO`
**Data:** 2026-08-22\n**Revisão visual humana:** aprovada pelo proprietário do projeto após visualização das capturas anotadas versionadas.
**Release:** não aprovada por este documento

## Proveniência

- PR: `#144` — merge normal, sem force ou bypass.
- Commit da implementação/documentação na PR: `93fa015aee79fe702d4c6a860dcc272fe8c657fe`.
- Commit de merge no `main`: `d01e42f7348265f4cfe4df65a8d6c2761e0730e8`.
- CI: run `32591309209`.
- Linux: job `97076129247` — `success`.
- Windows: job `97076128666` — `success` após reexecução. A primeira execução falhou exclusivamente por resposta HTTP `503 Backend is unhealthy` do PyPI durante `pip-audit`; não houve alteração de código, regra ou teste para contornar o erro.

O `main` local foi atualizado por `git fetch`, `git checkout main` e `git pull --ff-only origin main`. Ao final, `HEAD` local e `origin/main` coincidiram byte a byte no commit de merge acima.

## Gates pós-merge reproduzidos localmente

Executados no Windows, no `main` em `d01e42f...`:

```text
python tools/baseline_integrity.py --verify --git-blob
Baseline verified: 2270 files

python tools/evidence_integrity.py --require-tracked --git-blob
Evidence integrity passed: 100 manifests validated.

pytest -q [testes focados reais do gizmo e transformações]
30 passed in 5.07s

pytest -q
1609 passed, 2 skipped in 49.78s

git diff --check
PASS
```

Os dois skips permanecem os casos históricos condicionados a symlink/permissão do Windows; não foram criados, alterados ou usados para mascarar uma falha nesta etapa.

Os jobs remotos da PR executaram os gates completos do repositório, incluindo baseline, integridade de evidências, lock de dependências, compilação, lint, formatação, import ordering, mypy, pip-audit, Bandit, testes com cobertura, política de cobertura, auditoria Stage 4B.5, suíte legada reconciliada e verificação de árvore de origem.

## Evidência visual

O auditor Windows versionado da etapa permanece íntegro no `main`:

- `capture_count=12`;
- `decision=PASS`;
- `failure_count=0`;
- backend Qt `windows`;
- três resoluções lógicas e quatro estados por resolução;
- PNGs brutos e anotados hashados no manifesto de evidências.

A revisão visual humana das capturas anotadas versionadas foi realizada e aprovada pelo proprietário do projeto. A aprovação é específica para os estados e resoluções capturados; não amplia o escopo para release ou para etapas posteriores.

## Estado da árvore local

Não há alterações rastreadas locais. Permanecem seis diretórios históricos não rastreados, preservados deliberadamente e não usados como evidência de árvore limpa. Essa condição foi reportada, não ocultada.

## Decisão

A implementação do gizmo profissional está integrada no `main`, validada pelos gates remotos, pela suíte pós-merge reproduzida localmente e pela revisão visual humana aprovada. A Etapa 6 está formalmente concluída no escopo aprovado. A Etapa 7 permanece apenas como próxima etapa planejada e exige autorização própria.
