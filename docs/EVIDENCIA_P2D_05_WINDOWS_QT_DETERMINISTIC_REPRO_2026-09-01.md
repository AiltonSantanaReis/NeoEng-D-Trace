# Evidência — P2D-05 — reprodução determinística do callback Qt

## Identificação

- Commit pré-correção: `5b3d9e9ba3a52620b8bbdd76791c53e153d508e0`.
- Commit da correção: `830b2ec28ad396d323afcec03968efe148d9c77b`.
- Branch: `p2d-05-ui-crash-root-cause`.
- PR: [#165](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/pull/165).
- Data da campanha: 2026-09-01.
- Evidência relacionada: [EVIDENCIA_P2D_05_WINDOWS_QT_LIFECYCLE_FIX_2026-09-01.md](EVIDENCIA_P2D_05_WINDOWS_QT_LIFECYCLE_FIX_2026-09-01.md).

## Objetivo

Obter uma reprodução nativa com dump/stack ou uma prova determinística equivalente para o crash intermitente do Windows observado após a reativação dos 11 testes de viewport/gizmo. Nenhum teste, asserção, limiar ou regra de CI foi alterado para produzir esta evidência.

## Procedimento A/B

Foi criado um worktree isolado no commit pré-correção e executado o mesmo comando no worktree corrigido, usando o mesmo Python 3.11, as mesmas dependências locais, `QT_QPA_PLATFORM=offscreen`, `CI=true` e a política de cobertura vigente:

```text
python -m pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml
```

O Windows LocalDumps foi configurado temporariamente para `python.exe` com dump completo (`DumpType=2`, `DumpCount=20`) em diretório temporário separado por fase. Não havia configuração anterior para esse executável; a chave foi removida ao final de cada fase. Os logs stdout/stderr e os diretórios de dump foram preservados fora do repositório.

## Resultados da campanha integral

| Fase | Execuções | Coletados por execução | Resultado por execução | Crash/dump |
|---|---:|---:|---|---|
| Pré-correção (`5b3d9e9`) | 3 | 1858 | `1856 passed, 2 skipped, 1 warning` | Não reproduzido; 0 dumps |
| Correção (`830b2ec`, antes do novo probe persistente) | 3 | 1879 | `1877 passed, 2 skipped, 1 warning` | Não reproduzido; 0 dumps |

Os dois skips da campanha são os skips preexistentes de `tests/test_integration_sync.py`; nenhum skip foi criado ou modificado nesta investigação. O código de saída foi `0` em todas as seis execuções.

## Reprodução determinística equivalente

Um probe temporário executado contra o commit pré-correção destrói o `QToolButton` depois de registrar o menu e antes de processar o callback diferido. O resultado foi determinístico:

```text
FAILED tests/test_qt_lifecycle_probe.py::test_old_reference_menu_callback_after_button_destroyed
src/ui/reference_chrome.py:124: button.adjustSize()
RuntimeError: Internal C++ object (PySide6.QtWidgets.QToolButton) already deleted.
```

O mesmo cenário foi incorporado ao teste versionado `test_reference_menu_callback_is_cancelled_when_button_is_destroyed`. No código corrigido, o teste completo de lifecycle passou `5 passed`, exigindo que o sinal `destroyed` limpe a referência e interrompa o timer parent-owned antes do processamento do callback.

A reprodução não fabrica um `access violation`: ela demonstra de forma repetível a violação concreta de ownership Qt-Python no mesmo caminho de menu que aparece no diagnóstico histórico. O patch elimina o callback não proprietário e cobre os outros três fluxos análogos com timers parent-owned.

## Validação após persistir o probe

Após adicionar o cenário ao teste permanente, a suíte integral local coletou 1880 testes e terminou com:

- `1878 passed`;
- `2 skipped`, ambos preexistentes;
- `1 warning`;
- cobertura total `90,94%`.

Também passaram, no ambiente local disponível, flake8 pelo executável do `.venv`, Black `--check --diff`, isort e MyPy em 145 arquivos de código. A CI remota no SHA que incluirá este documento e o novo teste ainda é obrigatória.

## Limitações

- O crash nativo `Windows fatal exception: access violation` não ocorreu nas seis execuções integrais locais nem nas execuções remotas anteriores.
- Nenhum dump ou stack nativa foi produzido; portanto, módulo nativo culpado e confirmação WER permanecem indisponíveis.
- A prova determinística é equivalente no nível observável Qt-Python e demonstra o defeito de ownership, mas não permite afirmar qual componente nativo converteu essa violação em heap corruption ou access violation.
- As 27 falhas históricas da suíte legada continuam sendo reportadas pela reconciliação e não são convertidas em sucesso silencioso.

## Decisão formal nesta etapa

**PARCIAL — BLOQUEADO PARA MERGE ATÉ A CI DO SHA FINAL.**

A alternativa de prova determinística equivalente foi obtida e formalizada. Ainda faltam o commit/push deste teste e documento, a CI completa no SHA final, a revisão do artefato correspondente e, se esses gates permanecerem verdes, a decisão normal de merge seguida da validação independente pós-merge. Nenhuma dessas etapas será presumida a partir da campanha local.
