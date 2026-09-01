# Evidência — P2D-05 — correção de ciclo de vida dos callbacks Qt

## Identificação

- Commit avaliado: `830b2ec28ad396d323afcec03968efe148d9c77b`
- Branch: `p2d-05-ui-crash-root-cause`
- Base corretiva: `0ab59eb40f8c31e482d9cad51543e7fd5e2090d5`
- PR: [#165](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/pull/165)
- Data da validação: 2026-09-01
- Execução remota: [33483154348](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33483154348)
- Job Linux: [99777079387](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33483154348/job/99777079387)
- Job Windows: [99777079057](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33483154348/job/99777079057)
- Artefato Windows: [validation-windows-python-3.11 / 9790924978](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33483154348/artifacts/9790924978)

## Objetivo e escopo

Corrigir o risco de callbacks Qt diferidos sobreviverem ao objeto que deveriam atualizar, sem remover testes, introduzir `skip`, usar `xfail`, reduzir limiares ou alterar regras de CI. O escopo é limitado ao ciclo de vida de callbacks usados pelo viewport e pelos componentes de preview:

- `CanvasView.flash_effect`;
- `MaskViewerDialog` no ajuste de viewport após layout;
- `ReferenceToolPalette` no posicionamento do menu da aplicação;
- `ResponsivePanelLayout` na atualização geométrica agendada.

O adendo histórico [EVIDENCIA_P2D_05_WINDOWS_QT_DIAGNOSTICO_2026-09-01.md](EVIDENCIA_P2D_05_WINDOWS_QT_DIAGNOSTICO_2026-09-01.md) permanece imutável e continua registrando que a captura nativa original não havia determinado a causa-raiz.

## Investigação e causa técnica

A revisão do código encontrou callbacks criados por `QTimer.singleShot` sem um objeto proprietário nos quatro fluxos acima. O experimento local de teardown reproduziu uma manifestação determinística do problema: depois que a janela era destruída, o callback de posicionamento da paleta tentava acessar um `QToolButton` já destruído, produzindo `RuntimeError: Internal C++ object (PySide6.QtWidgets.QToolButton) already deleted`.

A correção substitui esses callbacks por timers `QTimer` de disparo único parent-owned. O timer da paleta também é interrompido quando o botão registrado é destruído. Após a alteração, uma busca em `src` e `tests` encontrou somente o `QTimer.singleShot` do launcher, cujo callback é encerrado com o próprio processo e não atualiza um widget destruível.

Esta evidência demonstra a causa no nível de ownership/ciclo de vida Qt-Python e sua correção. Ela não inventa uma stack nativa: o vínculo definitivo com o `access violation` histórico continua sem dump ou módulo nativo identificado.

## Testes e comandos executados

Validações locais:

- `pytest -q tests/test_qt_lifecycle_regression.py`: 4 passed;
- conjunto Stage 5/Stage 6 mais regressão: 26 passed;
- experimento de teardown direcionado pós-correção: 22 passed, 0 errors, sem callback para objeto destruído;
- suíte local integral: `1877 passed, 2 skipped, 1 warning` em 48,57s; os 2 skips são preexistentes em `tests/test_integration_sync.py`;
- `flake8`: passou;
- Black `--check --diff`: passou;
- isort: passou;
- MyPy: passou em 145 arquivos de código;
- verificação do baseline contra blobs Git: `Baseline verified: 3092 files`;
- não há `skipif`, `xfail` ou `pytest.skip` nos testes afetados nem no workflow.

Validação remota no commit acima:

- Linux: job `success` em 2m49s;
- Windows: job `success` em 7m19s;
- suíte principal Windows: `1862 passed, 1 warning` em 88,35s;
- testes coletados pela suíte principal: 1862;
- cobertura total: `90,87%`; a política integrada de cobertura passou;
- integridade de baseline: 3092 arquivos;
- integridade de evidências: 120 manifests;
- árvore-fonte Windows permaneceu inalterada durante os testes;
- não houve falha no pytest, portanto a coleta condicional de dump ficou `skipped` por sua condição declarada;
- inspeção do artefato Windows não encontrou `.dmp` nem `.mdmp`.

## Suíte legada preservada

O job Windows também executou a reconciliação da suíte legada. O resultado bruto permanece visível:

- 196 testes;
- 27 falhas;
- 0 erros;
- 0 skips;
- 12 arquivos com falha;
- 27/27 falhas coincidiram exatamente com as assinaturas esperadas no manifesto de reconciliação;
- 0 falhas inesperadas e 0 expectativas ausentes.

Esse resultado faz o gate de reconciliação passar segundo sua política, mas não significa que a suíte legada esteja verde. As falhas continuam sendo dívida técnica explícita e não foram mascaradas por skips.

## Falhas, causa-raiz e limitações

- Crash nativo Windows nesta execução: não reproduzido.
- Manifestação de ownership Qt-Python: reproduzida localmente antes da correção e eliminada no experimento direcionado após a correção.
- Dump/stack nativa do crash histórico: não disponível.
- Causa nativa definitiva, módulo culpado e confirmação por WER: não determinados.
- Repetições remotas sem crash: evidência de não recorrência nas amostras, não prova de ausência futura.
- A suíte legada preservada possui 27 falhas históricas exatas, conforme detalhado acima.

## Decisão formal

**PARCIAL — BLOQUEADO PARA MERGE.**

O patch é tecnicamente estreito, tem teste de regressão, passou os gates locais e os dois jobs remotos sem reativar qualquer mecanismo de mascaramento. Porém, a evidência disponível ainda não contém a stack nativa que ligue de forma conclusiva o callback Qt ao `access violation` histórico. Portanto, não há base profissional para declarar `APROVADO`, mesclar ou encerrar o P2D-05.

Próximo avanço aceitável: obter uma nova reprodução com dump/stack nativa ou uma prova determinística equivalente em ambiente Windows, mantendo os gates atuais; se a evidência confirmar a hipótese e não surgir regressão, repetir a revisão formal e somente então decidir o merge.
