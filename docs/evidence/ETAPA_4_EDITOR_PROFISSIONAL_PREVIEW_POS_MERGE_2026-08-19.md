# Evidência — Etapa 4 profissional: encerramento pós-merge

## Identificação

- Etapa: `4 — preview profissional de câmera, parallax e sockets`;
- PR: `#107`;
- commit candidato validado: `aac3a9a4d24f18159c2e3085f2f2a439a10bffb6`;
- merge commit: `19f3cfdd6f41dc872cb8e4f12130de003f740669`;
- CI: `Private validation`, execução `32314410332`;
- estado do CI: `success` em Linux e Windows;
- decisão: **INTEGRADA E ENCERRADA NO ESCOPO COMPROVADO**.

O relatório `ETAPA_4_EDITOR_PROFISSIONAL_PREVIEW_2026-08-19.md` permanece como
snapshot pré-merge e não foi reescrito. Este documento registra somente o estado
posterior comprovado.

## Escopo integrado

- contrato V2 explícito com migração V1→V2;
- câmera ortográfica, profundidade/parallax e sockets tipados;
- preview determinístico no viewport profissional;
- inspector e interação de objetos/sockets;
- Undo/Redo transacional;
- capturas em 1280x720, 1366x768 e 1920x1080 com auditoria visual automatizada.

## Validação local do candidato final

- suíte completa: `1373 passed, 2 skipped`;
- os 2 skips são históricos e condicionados à permissão de symlink no Windows;
- `coverage.xml`: `92,96%` de linhas e `85,27%` de branches;
- `tools/check_coverage_policy.py coverage.xml`: **PASS**;
- Black, isort, mypy, flake8, pip-audit e bandit: **PASS**;
- baseline contra blobs Git: `1558` arquivos verificados;
- integridade de evidências contra blobs Git: `59` manifests validados;
- auditoria visual da Etapa 4: **PASS; 0 achados**.

## Gates remotos

A execução `32314410332` concluiu com sucesso nos dois jobs. Foram aprovados,
sem skips novos, o lint, formatação, import ordering, mypy, auditoria de
dependências, bandit, cobertura branch, auditoria Stage 4B.5, suíte legada e
verificação de árvore limpa.

## Limitações preservadas

Esta etapa não implementa runtime completo de partículas, shaders, iluminação,
pós-processamento, triggers ou streaming. Esses itens continuam fora do escopo
comprovado e não são apresentados como concluídos.

## Rollback

O rollback do escopo integrado é a reversão do merge `19f3cfd` ou a restauração
controlada da referência anterior `f477b6d`, sempre por PR e pelos mesmos gates.
Nenhum arquivo de usuário é migrado por este fechamento.