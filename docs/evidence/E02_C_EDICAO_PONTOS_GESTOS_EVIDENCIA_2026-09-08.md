# E02-C — edição de pontos, curvas e gestos

Data de abertura: 2026-09-08
Estado: TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING
Branch: Ailton/e02-primitives-20260908
Commit de implementação atual: `f5d2f30bd184e809d3e3321fedff9ce2ad4f9754`

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

- Testes focados: `24 passed`.
- Suíte oficial: `1993 passed, 2 skipped, 1 warning`.
- `mypy src`: `Success: no issues found in 154 source files`.
- Black, isort, Flake8, compileall e `git diff --check`: aprovados.
- Symlink: não executado; reservado à auditoria final conforme decisão vigente.

## Gates concluídos e proveniência

- Testes focados: `24 passed`.
- Suíte oficial: `1993 passed, 2 skipped, 1 warning`.
- Estática: mypy sem erros em 154 arquivos; Black, isort, Flake8,
  compileall e `git diff --check` aprovados.
- Build: r11, source commit `dc2d586c3e1b541a0579615e6899a8ed97f3e62b`,
  branch `Ailton/e02-primitives-20260908`.
- Binário: SHA-256
  `880888345CE1E8D38F5DA7F59FD32FF85EFAA250EF0DF8FD76982AF0FF42663B`.
- Arquivo portátil: SHA-256
  `A437DF526CEE48D646EE1C37E8F6064823E9A4A2A1127DD8AE69BFF896B3A4E3`.
- Smoke portátil: 11 checks, `SUCCESS`.
- Registro usado na build: SHA-256
  `C4094C0F211A675B8CD1C7527D4C88350C9E32EECA14427F6F8414F402CFDB8D`.
- Manifesto das capturas: `docs/evidence/E02_C_R11_CAPTURAS_MANIFESTO.json`.

O roteiro de captura foi corrigido para registrar a imagem durante a prévia
inválida antes do `Escape`, separada da captura posterior de cancelamento.

## Capturas reais do binário r11

Pacote `artifacts/e02-primitives-20260908/captures-r11-point-edit-save/`,
janela do cenário `1986x1431`:

- `04-independent-scene-point-edit-mode.png`: modo de edição e três handles.
- `05-independent-scene-point-preview-invalid.png`: handles vermelhos e
  mensagem PT-BR `Prévia inválida` durante o arraste nativo.
- `06-independent-scene-point-edit-cancelled.png`: `Escape` cancela e
  restaura a geometria aceita.
- `07-independent-scene-point-edit-finalized.png`: arraste válido finalizado.
- `10-independent-scene-after-reopen.png`: save/reopen após edição válida,
  com três objetos e geometria persistida.

O lote também foi executado no pacote `captures-r11-authoring-save` para
transformação, duplicação, remoção, diálogos de salvar/abrir e reabertura.

## Decisão do checkpoint

E02-C está aprovado como checkpoint técnico. A revisão humana final continua
`PENDING_EVIDENCE` por autorização explícita, e symlink continua
`DEFERRED_UNTIL_FINAL_AUDIT`; nenhum dos dois estados foi convertido em PASS.

## Correção adicional registrada

O preview agora rejeita pontos quase coincidentes antes da validação/mutação,
com distância mínima determinística de 24 pixels documentais. O estado muda
para `preview_invalid`, a geometria aceita permanece intacta e o canvas deve
exibir handles/status de erro; `Escape` continua cancelando sem deixar
alteração parcial. O teste focado negativo cobre este contrato.

## Finding visual intermediário r8

A captura real `artifacts/e02-primitives-20260908/captures-r8-baseline/03-independent-scene-primitives.png`
mostrou que a nova ação `Editar pontos` empurrou `Remover/Desfazer/Refazer`
para o overflow da primeira barra. O finding foi corrigido em
`7569854f0f42d2a410ff5b62864888133685ee6b` separando a barra de arquivo/criação
da barra de edição/histórico; r9 deve ser a única build usada para a validação
final deste lote.
