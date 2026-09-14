# Evidência — Pré-voo de integração Unity

**ID:** `EVID-F14-UNITY-INTEGRATION`
**Data:** 2026-09-14
**Status:** `PENDING_EVIDENCE`
**Requisito:** `REQ-F14-UNITY-INTEGRATION-PREFLIGHT`
**Feature:** `FEAT-UNITY-HUB-PREFLIGHT`
**Componente:** `CMP-UNITY-INTEGRATION-SETTINGS`
**ADR:** `ADR-POST-E13-UNITY-INTEGRATION-FLOW`

## Escopo

Esta evidência qualificará a nova superfície de integração do Unity sem
executar shutdown, ativação, transporte de licença ou login no host. O teste
do aplicativo deverá comprovar o diagnóstico e a persistência de caminhos,
enquanto a validade do plano continuará sendo responsabilidade do Unity Hub.

## Decisão de escopo

O login, a licença e o entitlement do Unity são pré-requisitos externos do
fluxo do usuário. Eles não são uma limitação funcional do NeoEng-D-Trace:
quem utiliza a integração deve possuir o Unity Hub/Editor instalado e fazer
login pelo próprio Unity Hub. O NeoEng-D-Trace não tenta ativar, vincular,
transportar ou validar a licença. A superfície entregue reduz a fricção do
fluxo ao localizar os executáveis, orientar o caminho Personal e abrir as
fontes oficiais.

O estado `PENDING_EVIDENCE` permanece apenas até o vínculo do commit desta
entrega. A execução e os artefatos abaixo já foram coletados.

## Matriz de comprovação

| ID | Critério | Resultado | Artefato |
|---|---|---|---|
| `TEST-UNITY-INTEGRATION-CORE` | normalização, detecção e estados de caminho | `PASS` | 10 testes focados; suíte oficial repetida |
| `TEST-UNITY-INTEGRATION-UI` | diálogo, menu, acessibilidade, idioma e persistência | `PASS` | 25 testes focados/regressão + capturas nativas 01, 02 e 11 |
| `TEST-UNITY-INTEGRATION-SAFETY` | nenhuma leitura/execução de licença, tokens ou shell | `PASS` | testes estáticos/funcionais de segurança + revisão de código |

## Execuções e artefatos

- Testes focados: `25 passed` em `3.68s`.
- Suíte oficial repetida: `2651 passed, 2 skipped` em `81.76s`; JUnit
  preservado no diretório de artefatos da execução.
- Os dois `skipped` pertencem aos testes controlados de symlink já existentes
  em `tests/test_integration_sync.py`; não foram introduzidos pela integração
  Unity, não ocultam falhas desta etapa e permanecem registrados.
- Build portátil r2: versão `0.3.0`, executável
  `artifacts/unity-integration-build-20260914-r2/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`,
  SHA-256
  `BD4F21F6262988C2303682208E6E73528169ECCE78BB7DFD3B6284F9D2D7D45F`.
- Smoke da build: `11/11` verificações do validador portátil passaram,
  incluindo CLI, projeto headless, GLB, perfis Godot/Unity, abertura/fecho da
  GUI e diretório de estado do usuário.
- Capturas nativas da build r2, desktop Windows real, `3840x2160`:
  - `native-capture-01-start.png` — build aberta;
  - `native-capture-02-view-menu.png` — menu e ação
    `Integração do Unity...` visíveis;
  - `native-capture-11-unity-integration.png` — diálogo real com Hub/Editor
    detectados, fluxo Personal e limite de responsabilidade visível.
- SHA-256 das capturas: `141BE22E4CCD4F95480058275E0F80C850E94F8DC8E068CA4853E001A640B649`,
  `104EEFECCAE5F14039EFDA19268CAD9FB0BCF7CFAC6BA45B10B7BA125B5E3315` e
  `8B4F760EB4C1AEF4AD5CF38CAC0E4A720CF6E1F1DE24971B4A8F3EEF02683F42`.

## Observação de segurança

O código não lê `.ulf`, `UNITY_LICENSE_FILE`, tokens, credenciais, cookies ou
entitlements. A única ação de processo é abrir explicitamente o executável do
Hub selecionado/detectado, sem shell e sem argumentos livres. Login, ativação,
shutdown/licensing e testes de ambiente controlado permanecem fora do escopo
da aplicação e não são alegados como validados por esta evidência.

## Limites conhecidos

- a presença de um executável não comprova instalação funcional do Editor;
- o NeoEng-D-Trace não verifica login, entitlement ou validade de plano;
- a validação nativa do Unity permanece uma etapa externa controlada e não
  será convertida em `PASS` por uma captura da UI do NeoEng.

## Próximo vínculo obrigatório

O estado desta evidência será promovido para `PASS` somente após o commit
auditado da implementação, testes e documentação. O hash do commit deverá ser
registrado nesta seção e no ADR vinculado.
