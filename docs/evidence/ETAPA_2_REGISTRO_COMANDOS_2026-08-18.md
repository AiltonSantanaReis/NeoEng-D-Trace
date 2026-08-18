# Evidência — Etapa 2: registro de comandos e Ctrl+K

**Escopo:** registro central de comandos, IDs estáveis, estados derivados das
QAction existentes e solicitação global Ctrl+K.
**Estado funcional:** implementado no commit técnico
`13a5cc71ec5b1ff2093e387366b927ae151a4e7b`.

## Decisão arquitetural

- O adaptador que depende de Qt permanece em `src/ui`; `src/core` continua
  independente de Qt conforme o gate da Etapa 13.
- `CommandRegistry` mantém uma relação 1:1 entre ID estável e QAction.
- O estado habilitado/desabilitado é lido da QAction e propagado por sinal;
  não existe cópia paralela de estado executável.
- `Ctrl+K` emite `command_palette_requested` por um `QShortcut` de janela.
- A paleta visual, busca, localização e acessibilidade não fazem parte desta
  etapa e permanecem NÃO INICIADAS, conforme a ordem do plano.

## Contratos implementados

Foram registrados 19 IDs determinísticos para ações de arquivo, edição,
visualização, exportação e colisão. O registry rejeita IDs inválidos, IDs
duplicados, QAction duplicada e lotes inconsistentes sem mutação parcial.

## Comandos e resultados locais

```text
.\.venv\Scripts\python.exe -m pytest -q tests/test_stage2_command_registry.py tests/test_stage1_scenario_characterization.py
RESULTADO: 10 passed em 0.82s

.\.venv\Scripts\python.exe -m pytest -q tests/test_stage_13_qt_refactor_autosave.py::test_non_adapter_layers_are_qt_independent_and_main_window_is_reduced
RESULTADO: 1 passed em 0.70s

.\.venv\Scripts\python.exe -m pytest -q
RESULTADO: 1212 passed, 2 skipped, 10 warnings em 20.40s

MainWindow
RESULTADO: 1194 linhas; limite governado de 1200 respeitado
```

Black, isort, Flake8, py_compile e git diff --check foram executados no escopo
alterado. Os dois skips são condicionais preexistentes e não foram criados,
removidos ou usados para obter aprovação.

## Falhas encontradas e corrigidas durante a etapa

1. O primeiro desenho colocou QAction em `src/core`; o teste de isolamento Qt
   falhou legitimamente. O adaptador foi movido para `src/ui`.
2. A extração inicial deixou MainWindow com 1220 linhas; o gate de redução
   falhou legitimamente. O binding foi extraído para `command_bindings.py` e a
   janela ficou com 1194 linhas.
3. O primeiro teste de Ctrl+K enviava a tecla ao objeto de janela sem foco no
   Qt offscreen. A reprodução com o canvas focado confirmou o comportamento e
   o teste passou a usar o widget focável real, sem emissão artificial.

## Encerramento pós-merge

- Não existe ainda uma paleta visual; não há alegação de busca ou UX concluída.
- Não há cenário parallax, câmera, overlay ou schema lateral nesta etapa.
- O CI remoto `32118071443` passou em Linux e Windows, incluindo os gates de
  cobertura, isolamento, integridade de evidências e preservação da suíte
  legada.
- A PR `#95` foi integrada no merge `9cef8a0eabd0f6c6e087fc3a5251ddb9df02da18`.
  O registry, os 19 IDs estáveis, os estados derivados das QAction e o
  gatilho Ctrl+K estão integrados no `main`.
- A paleta visual, busca, localização, acessibilidade e o módulo parallax
  permanecem pendentes para etapas posteriores; não são declarados como
  concluídos por esta evidência.
