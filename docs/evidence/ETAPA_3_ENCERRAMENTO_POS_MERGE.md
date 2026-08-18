# Evidência — Etapa 3: encerramento pós-merge

## Identificação

- Pull request funcional: `#97`
- Head aprovado: `21bff1ddab4ac27261cd81f4f3975c0f653a0537`
- Merge commit: `5d4c0829adabfcd51741d95151f808722d43857c`
- Branch validada depois do merge: `main`
- CI pós-merge: run `32125768535`, evento `push`, conclusão `success`
- Jobs: Linux `95675864634` e Windows `95675864866`, ambos `success`

## Validação pós-merge

O `main` local foi atualizado por fast-forward até o merge commit e comparado
com `origin/main`; ambos apontaram para `5d4c0829adabfcd51741d95151f808722d43857c`
com árvore de trabalho limpa.

O CI pós-merge executou baseline, integridade de evidências, compilação, lint,
formatação, isort, mypy, pip-audit, Bandit, cobertura de branches, política
integrada e a suíte legada reconciliada em Linux e Windows. Todos os gates
concluíram com sucesso.

## Estado integrado

- paleta visual não modal integrada à `MainWindow` e ao `CommandRegistry`;
- busca por rótulo, atalho e ID estável;
- execução exclusiva de `QAction` habilitada, com estados desabilitados protegidos;
- Ctrl+K, Up/Down, Enter, Escape e restauração de foco;
- localização en/pt e acessibilidade dos controles;
- capturas reais em três resoluções e dois idiomas, com hashes, Pillow/OpenCV e geometrias Qt;
- parallax, câmera, overlays, schema lateral e runtime permanecem planejados e fora desta etapa.

## Decisão

`APROVADO / INTEGRADO` no escopo da Etapa 3. Esta decisão não promove o módulo
de cenários parallax nem altera o estado da release publicada `v0.2.0`.
