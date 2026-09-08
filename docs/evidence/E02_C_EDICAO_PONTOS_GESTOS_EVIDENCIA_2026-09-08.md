# E02-C — edição de pontos, curvas e gestos

Data de abertura: 2026-09-08
Estado: IN_PROGRESS
Branch: Ailton/e02-primitives-20260908
Commit de implementação: `2c3cd0f24f10d1136b4f4e2e1fcbe7e28ab41ba2`

## Escopo

Edição livre de pontos/pivôs, curvas abertas/fechadas, estados de ferramenta
ociosa/criando/editando/prévia inválida/finalizada, clique vazio, finalização,
duplo clique, Escape, reativação e negativos de cancelamento/objeto bloqueado.

## Dependência

E02-B possui checkpoint técnico com seleção, transformação, duplicação,
remoção, histórico e save/reopen no binário r7. Este sub-lote deve preservar
esse fluxo e adicionar somente edição geométrica observável.

## Saída obrigatória

Contrato de gesto, implementação sem dependência do widget de imagem, testes
unitários/negativos/UI, suíte completa, build oficial, capturas reais e
comparação de persistência. Symlink e revisão humana permanecem reservados à
auditoria final.

## Implementação técnica registrada

- `IndependentScenePointEditGesture` mantém pontos originais e pontos de
  prévia sem mutar o documento durante o arraste.
- Prévia inválida entra em `preview_invalid` e mantém a geometria anterior;
  `Escape`/clique vazio cancela; `Enter`/duplo clique finaliza.
- O commit de geometria gera uma única entrada de histórico e respeita
  objetos bloqueados.
- O canvas nativo desenha handles e aceita arraste real por coordenadas de
  janela; a implementação não depende do widget de imagem.

## Gates locais antes da build

- Testes focados: `23 passed`.
- Suíte oficial: `1992 passed, 2 skipped, 1 warning`.
- `mypy src`: `Success: no issues found in 154 source files`.
- Black, isort, Flake8, compileall e `git diff --check`: aprovados.
- Symlink: não executado; reservado à auditoria final conforme decisão vigente.

## Evidência pendente

Build r8, smoke, captura automatizada do binário, arraste real de ponto,
prévia inválida/cancelamento e save/reopen serão anexados antes da promoção
do lote.
