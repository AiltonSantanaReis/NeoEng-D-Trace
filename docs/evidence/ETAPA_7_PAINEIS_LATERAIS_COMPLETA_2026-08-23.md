# Etapa 7 — Painéis laterais — validação local completa — 2026-08-23

## Escopo e linhagem

Este documento é um addendum vivo à Etapa 7. O snapshot
`docs/evidence/ETAPA_7_PAINEIS_LATERAIS_2026-08-22.md` continua histórico e
cobre somente a toolbar compacta do `GroupsPanel`; não foi reescrito.

A retomada atual fecha as lacunas reproduzidas nos quatro painéis ativos:
`Objects`/`SidePanel`, `LayersPanel`, `GroupsPanel` e `CollisionPanel`. O
editor principal e os handles `QPushButton` legados foram preservados. As
novas toolbars compactas e os menus de contexto apontam para os mesmos
handlers; não houve remoção silenciosa de comandos.

## Implementação versionada

- Checkpoint anterior das toolbars, estados e seleção: `e734d2b`.
- Checkpoint desta correção de menus de contexto: `8334f87bd58ff2e33c5e7041217bf6354844bd2e`.
- Arquivos funcionais: `src/ui/side_panel.py`, `src/ui/layers_panel.py`,
  `src/ui/groups_panel.py` e `src/ui/collision_panel.py`.
- Teste focal: `tests/test_stage7_side_panels_completion.py`.
- Auditor nativo: `scripts/audit_stage7_side_panels_complete.py`.

Defeitos reais encontrados e corrigidos:

1. seleção real de objeto não atualizava o inspector de transformação;
2. ações das toolbars de camadas/grupos não tinham metadado de comando;
3. o auditor usava APIs Qt incorretas para geometria de `QAction` e contagem
   de itens de `QComboBox`;
4. a compactação preservava tooltips, mas não preservava menus de contexto,
   contrariando o plano vivo. Esse último ponto foi integrado no checkpoint
   `8334f87` e coberto por teste, sem alterar thresholds ou regras.

## Ambiente e proveniência

- Sistema: Windows `10.0.26200`.
- Python: `3.11.9` 64-bit.
- Qt backend: `windows`.
- Branch: `Ailton/stage7-side-panels-completion-20260823`.
- Commit funcional auditado: `8334f87bd58ff2e33c5e7041217bf6354844bd2e`.
- Execução feita em PowerShell elevado por causa dos bloqueios ACL observados.
- O relatório nativo registra `worktree_clean=false` porque existem diretórios
  locais não rastreados de auditorias históricas. Eles foram preservados e não
  são apresentados como evidência da Etapa 7. O SHA do código auditado é exato;
  a condição de árvore limpa continua um gate separado.

## Testes e gates locais

Comandos executados no commit técnico, sem bypass:

```text
.\.venv\Scripts\python.exe -m py_compile <6 arquivos focais>
.\.venv\Scripts\python.exe -m black --check <6 arquivos focais>
.\.venv\Scripts\python.exe -m isort --check-only <6 arquivos focais>
.\.venv\Scripts\python.exe -m flake8 <6 arquivos focais>
.\.venv\Scripts\python.exe -m pytest -q tests/test_stage7_side_panels_completion.py
.\.venv\Scripts\python.exe -m pytest -q
```

Resultados observados:

- compilação, Black, isort e Flake8: `PASS`;
- teste focal: `4 passed`;
- suíte integral: `1625 passed, 2 skipped`;
- os dois skips existentes permanecem os mesmos testes de integração
  condicionais; não foram criados skips novos nesta etapa.

O teste focal realizou seleção via `QTest.mouseClick`, verificou habilitação
do inspector, executou colisão real, acionou uma ação pelo menu de contexto,
criou camada e verificou os quatro painéis em `1280x720`.

## Artefatos reais e validação cruzada

Pacote oficial:
`docs/evidence/artifacts/ui-modernization-stage7-20260823-final/`

O auditor nativo Windows gerou 12 PNGs reais: quatro painéis em cada uma das
resoluções solicitadas `1920x1080`, `1366x768` e `1280x720`. O relatório registra
as dimensões efetivas da janela, geometrias Qt, visibilidade, limites das
QToolBars, tamanho 16x16 dos ícones, ícones não nulos, tooltips, chaves de
comando, listas, seleção e rolagem.

Resultado do relatório `stage7-side-panels-complete-report.json`:

- `status`: `PASS`;
- `findings`: `0`;
- `captures`: `12`;
- `source_state.commit`: `8334f87bd58ff2e33c5e7041217bf6354844bd2e`.

O auditor de IO `png-io-validation.json` leu os 12 PNGs com Pillow e OpenCV,
comparou dimensões e cruzou cada SHA-256 com o relatório nativo:
`status=PASS`, `capture_count=12`. O `artifact-index.json` contém 16 arquivos
hashados, incluindo capturas, relatórios, fixture de projeto e imagem fixture.

A pasta oficial contém apenas o pacote final desta execução. As tentativas
intermediárias com falhas de auditor foram mantidas fora do pacote oficial e
não são usadas para sustentar PASS.

## Revisão visual e decisão

A inspeção automática de geometria, dimensões, hashes e decodificação foi
concluída. A revisão visual humana não foi executada: o visualizador local
falhou com bloqueio ACL mesmo após a execução elevada. Portanto, não há
alegação de aprovação visual humana e não há falso PASS baseado somente no CI.

Classificação atual:

- `PASS_LOCAL_AUTOMATED`: implementação e gates automatizados locais no
  escopo acima;
- `HUMAN_VISUAL_REVIEW`: `BLOQUEADA / NÃO EXECUTADA`;
- `REMOTE_GATES`: `PENDENTES` — push, PR, CI no SHA exato, merge e validação
  pós-merge ainda não ocorreram;
- `ETAPA 7`: não formalmente aprovada enquanto os gates pendentes não forem
  concluídos.

A Etapa 8 não pode iniciar com base neste relatório. Nenhuma regra,
governança, threshold ou teste foi alterado para obter PASS.
