# Encerramento pós-merge — Reconciliação do plano da interface moderna

## Proveniência

- PR técnica: `#156`.
- Merge confirmado em `5f895b9773647d0899591005cd26f29b7597391b`.
- A validação abaixo foi executada depois do merge, no `main` local sincronizado com `origin/main`.
- Escopo: reconciliação do plano documentado da interface moderna e regeneração do baseline correspondente. Este registro não constitui aprovação de release.

## Checks remotos da PR

- Workflow `#453`: concluído com `success`.
- `test`: `success`, job `97200559343`.
- `test-windows`: `success`, job `97200559224`.
- Commit de origem dos checks: `1f038c6380b369969a050703b8816171f882a3d0`.

## Validação pós-merge local

Comandos executados no PowerShell elevado, a partir do `main`:

```text
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
.\\.venv\\Scripts\\python.exe tools/baseline_integrity.py --verify --git-blob
.\\.venv\\Scripts\\python.exe tools/evidence_integrity.py --git-blob --require-tracked
.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_repository_reference_hygiene.py tests/test_documentation_state_contracts.py tests/test_evidence_integrity.py tests/test_baseline_integrity.py --tb=short
.\\.venv\\Scripts\\python.exe -m pytest -q --tb=short
```

Resultados observados:

- `HEAD` e `origin/main`: `5f895b9773647d0899591005cd26f29b7597391b`.
- Baseline Git-blob: `PASS`, `2619 files`.
- Integridade de evidências: `PASS`, `110 manifests validated`.
- Testes direcionados: `53 passed` em `8.54s`.
- Suíte completa: `1625 passed, 2 skipped` em `40.94s`.

## Transparência da execução

A primeira tentativa do comando direcionado referenciou `tests/test_docs_integrity.py`, que não existe no repositório. Essa tentativa foi inconclusiva e não foi usada como evidência de aprovação. O conjunto real de testes foi descoberto no próprio repositório e executado novamente com os quatro arquivos existentes; somente a segunda execução, com `53 passed`, foi considerada válida.

## Estado da árvore

- Não há alterações rastreadas locais após a sincronização do `main` e a validação pós-merge.
- Existem diretórios históricos locais não rastreados, preexistentes e fora do escopo desta reconciliação. Eles foram preservados, não foram incluídos no commit, não foram apagados e não foram usados para declarar artificialmente uma árvore totalmente limpa.

## Decisão

A reconciliação do plano da interface moderna e a regeneração do baseline estão confirmadas no `main` após o merge, com CI Linux/Windows aprovado e validação local reproduzível. A evidência deste encerramento deve ser versionada em um checkpoint próprio antes de ser considerada parte do registro oficial do repositório.
