# Encerramento pós-merge — Etapa 3 da interface moderna profissional

Estado: **CONCLUÍDA no escopo aprovado**.

Este snapshot encerra a Etapa 3 após o merge da implementação da barra esquerda orientada a ações. A evidência pré-commit permanece preservada como histórico em `ETAPA_3_INTERFACE_MODERNA_2026-08-21.md`; este documento é a fonte do resultado pós-merge.

## Proveniência do merge

- PR: `#136`.
- Commit técnico da branch: `c0a4cf5e1de8b281463efa2225069e64c934dd26`.
- Merge commit no `main`: `adb36398b5c239ded610afa07932de7ff9bff340`.
- Branch local validada: `main`.
- `main` local e `origin/main`: sincronizados no mesmo SHA `adb36398b5c239ded610afa07932de7ff9bff340`.
- Worktree: sem alterações rastreadas ou staged; apenas os cinco diretórios históricos `release-stage9-*` permanecem untracked e foram preservados.

## Validação pós-merge local

```text
baseline_integrity.py --verify --git-blob: PASS (2040 arquivos)
evidence_integrity.py --require-tracked --git-blob: PASS (89 manifests)
pytest --cov=src --cov-branch --cov-fail-under=90: 1589 passed, 2 skipped
Cobertura total: 91,19%
check_coverage_policy.py: PASS
```

Os mesmos resultados foram reproduzidos depois do merge no Windows/Python 3.11.9. Nenhum teste foi removido, relaxado ou marcado como skip para obter o resultado.

## CI pós-merge

Run `32541997929` — evento `push` no `main` após o merge:

- Linux `test`, job `96953655319`: sucesso em 2m25s;
- Windows `test-windows`, job `96953655113`: sucesso em 5m41s;
- baseline e integridade de evidências: sucesso nos dois jobs;
- compilação, lint, Black, isort, mypy, auditoria de dependências e Bandit: sucesso nos dois jobs;
- cobertura de branches e política integrada: sucesso nos dois jobs;
- auditoria de qualidade Stage 4B.5 e suíte legada preservada: sucesso no Windows;
- verificação de árvore de origem inalterada: sucesso nos dois jobs;
- artefatos CI publicados: `validation-linux-python-3.11` e `validation-windows-python-3.11`, não expirados no momento da revisão.

O CI verde foi usado como um gate necessário, não como única prova: ele foi cruzado com os testes locais, manifests Git-blob, auditoria Qt, capturas reais e relatórios hashados da PR.

## Resultado funcional

A Etapa 3 está integrada e preserva os contratos anteriores:

- paleta esquerda implementada como `QToolBar` vertical, fixa e orientada a ícones;
- nove ações de ferramentas, dois separadores e seleção exclusiva;
- ícones não nulos, tooltips, nomes acessíveis e foco de teclado verificados;
- feedback de ferramenta desabilitada verificado;
- idioma e atalhos globais preservados;
- auditoria estrutural Qt PASS;
- três estados e 15 PNGs por backend, com auditoria visual automática sem findings;
- captura nativa Windows analisada com os avisos de DPI e fonte documentados, sem ocultar dimensões observadas.

## Limites mantidos

O encerramento não inclui a realocação do Gizmo, a janela do Mask Viewer, a reforma dos painéis laterais nem a padronização total da barra superior. Esses pontos continuam no escopo dos gates posteriores do plano de interface moderna e não foram declarados como resolvidos por esta etapa.

Nenhuma regressão foi evidenciada pelos testes, pela cobertura, pelas auditorias ou pelo CI. As limitações de backend offscreen e DPI nativo são limitações de observação documentadas, não foram convertidas em falso PASS nem tratadas como falha funcional sem evidência.

## Decisão

**Etapa 3 — Interface moderna profissional: CONCLUÍDA no escopo aprovado e validado pós-merge.**

Isto não aprova release nem encerra as etapas posteriores do plano.
