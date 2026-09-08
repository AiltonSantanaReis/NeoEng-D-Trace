# E02-C — edição de pontos, curvas e gestos

Data de abertura: 2026-09-08
Estado: IN_PROGRESS
Branch: Ailton/e02-primitives-20260908

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
