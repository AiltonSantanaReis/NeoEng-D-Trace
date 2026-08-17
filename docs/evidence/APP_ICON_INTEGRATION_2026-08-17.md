# Integração do ícone da aplicação — 17 de agosto de 2026

## Escopo

O ativo autorizado pelo proprietário foi integrado ao runtime Qt, ao bundle
PyInstaller, ao executável GUI e ao atalho do MSI gerado pelo WiX. O PNG
original não foi alterado.

## Ativos

- Fonte: `assets/branding/neoeng-d-trace-icon-source.png`
- Derivado: `assets/branding/neoeng-d-trace-icon.ico`
- SHA-256 do PNG: `17dde3dc0d616cef8927403cb3b2b15aa818960776605eb2a7d2b99b8e5adedc`
- SHA-256 do ICO: `6120fd1376d3976e6f089ef1bd6da677280234d58ab09add189ce97f4abb3b91`
- Resoluções ICO verificadas: `16`, `32`, `48`, `64`, `128` e `256` pixels
- Transparência do PNG: presente e preservada no derivado

## Implementação

- `src/core/app_icon.py` resolve o ativo tanto no checkout quanto no caminho
  congelado do PyInstaller.
- `src/ui/main_window.py` aplica o ícone à janela real.
- `src/launcher.py` aplica o ícone à `QApplication`.
- `packaging/NeoEng-D-Trace.spec` inclui o ativo no bundle e no executável GUI.
- `tools/package_windows_msi.py` referencia o mesmo ICO no atalho do menu
  Iniciar.
- `tools/generate_app_icon.py` torna a derivação reprodutível.

## Validação real

- Comando focal reproduzível:
  `.\.venv\Scripts\python.exe -m pytest -q tests/test_app_icon.py tests/test_evidence_privacy.py tests/test_stage14_postmerge_closure.py tests/test_documentation_state_contracts.py --tb=short`
- Resultado focal reproduzível: `49 passed`.
- Build PyInstaller real: concluído; executável GUI e ICO presentes no bundle.
- Smoke do executável GUI congelado: `application.opened`,
  `application.closed` e `session.summary` com `SUCCESS`.
- Build WiX 4.0.6 real com o bundle produzido: concluído; MSI temporário
  gerado sem erro de compilação.
- Suíte completa: `1184 passed, 2 skipped, 10 warnings`.
- Os dois skips são os testes de symlink condicionados à permissão do Windows;
  a execução administrativa do proprietário já comprovou `2 passed, 0 skipped`.
- As dez advertências são `DeprecationWarning` históricas do teste de GrabCut;

## Limite declarado

Não foi executada instalação/desinstalação do MSI nesta validação, para evitar
alteração no sistema do proprietário. A compilação real do MSI e a validação
estrutural do atalho foram executadas; o teste de instalação permanece o gate
operacional separado do instalador.
