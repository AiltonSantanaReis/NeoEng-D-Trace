# Etapa 10 — Encerramento técnico de acessibilidade e usabilidade

**Documento:** `EVID-F10-ACCESSIBILITY-CLOSURE-20260824`
**Status:** `PENDING_HUMAN_REVIEW`
**Versão:** 1.0
**Etapa:** 10 — Acessibilidade e usabilidade
**Requisito:** `REQ-F10-UI-ACCESSIBILITY`
**Feature:** `FEAT-UI-ACCESSIBILITY`
**Commit da implementação auditada:** `6ba06acd75e401f03228f949c9bf4279830c63cb`
**Branch:** `main`

Este documento registra o resultado técnico observável da Etapa 10. Ele não declara aprovação humana, merge remoto ou conclusão formal da etapa. Esses estados dependem da revisão humana prevista na governança.

## 1. Documentos ativos e autoridade

- [Governança de Integridade, Execução e Antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Índice Documental Ativo](../INDICE_DOCUMENTAL_ATIVO_2026-08-24.md)
- [Registro de IDs do produto](../REGISTRO_IDS_PRODUTO_PROFISSIONAL_2026-08-24.yaml)
- [Adendo Normativo de Automação e IDs](../ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md)
- [Plano de Interface Moderna e Profissional](../PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md)
- [Análise de impacto da Etapa 10](ETAPA_10_ACESSIBILIDADE_ANALISE_IMPACTO_2026-08-24.md)

Nenhum requisito, threshold, regra de aprovação, baseline ou etapa posterior foi alterado para obter o resultado.

## 2. Resultado técnico observado

O pacote executável de auditoria `EVID-F10-ACCESSIBILITY-AUDIT` produziu `PASS`, sem falhas detectadas, no commit exato da implementação.

| Critério | Teste | Observação | Evidência | Resultado técnico |
|---|---|---|---|---|
| Metadados de controles reais | `TEST-UI-ACCESSIBILITY-METADATA` | 68 controles interativos descobertos; nomes, descrições, tooltips e foco validados | `report.json`, `visual/desktop-1920x1080.png` | PASS |
| Teclado e foco | `TEST-UI-KEYBOARD-FOCUS` | Atalhos reais `1` e `X`, ordem de tabulação e foco verificados | `visual/desktop-xray-keyboard.png`, `visual/compact-inspector-focus.png` | PASS |
| Mouse e feedback de estado | `TEST-UI-MOUSE-FEEDBACK` | Pan, seleção, snap e estado visual verificados em fluxo separado | `visual/desktop-mouse-state.png` | PASS |
| Erro acionável | `TEST-UI-ERROR-FEEDBACK` | Falha sem seleção gera mensagem acionável e foco utilizável | `report.json` e teste focado | PASS |
| Contraste e estados não cromáticos | `TEST-UI-CONTRAST-STATES` | Contraste primário 14.9334, secundário 7.6400 e foco 10.9634 | `report.json` | PASS |

## 3. Comandos e resultados reproduzíveis

```text
python -m pytest tests/test_stage10_accessibility.py -q
5 passed

python tools/baseline_integrity.py --verify
Baseline verified: 2950 files

scripts/audit_stage10_accessibility.py
status: PASS
controls_discovered: 68
failures: []
```

O teste focado foi executado contra a janela Qt real em `QT_QPA_PLATFORM=offscreen`; não é um teste de existência de widget. A auditoria aciona teclado, mouse, foco, erro, estado e contraste através dos contratos reais da interface.

## 4. Build dedicada para revisão humana

Build isolada, destinada exclusivamente à revisão da Etapa 10:

- diretório de build: `.stage10-build-clean-6ba06ac/release-stage10-accessibility-20260824-6ba06ac/`;
- executável portátil: `.stage10-build-clean-6ba06ac/release-stage10-accessibility-20260824-6ba06ac/portable/NeoEng-D-Trace/`;
- arquivo: `NeoEng-D-Trace-0.3.0-win64-portable.zip`;
- tamanho: `122040440` bytes;
- SHA-256 do ZIP: `08f173d56edd0d1bf0edfc48d0cde2e467822e178386ece699d15916cf8c3589`;
- arquivos no pacote: `353`;
- commit de origem declarado pelo manifesto: `6ba06acd75e401f03228f949c9bf4279830c63cb`;
- validação oficial da build: `SUCCESS`.

O smoke da build validou versão CLI, projeto versionado, projetos headless, JSON, GLB, perfis Godot/Unity, abertura e fechamento da GUI e diretório de estado do usuário. Essa build não autoriza testes ou conclusão das etapas 11/12.

## 5. Integridade do pacote

Pacote de evidências: `artifacts/stage10-accessibility-20260824/BUILD-F10-ACCESSIBILITY-20260824-6BA06AC/`

- manifesto: `manifest.json`;
- relatório: `report.json`;
- hashes: `hashes.sha256`;
- capturas: cinco PNGs determinísticos;
- validação executada: todos os hashes de `hashes.sha256` conferidos contra os arquivos presentes; resultado `STAGE10_HASHES PASS`.

O relatório registra artefatos históricos não rastreados presentes no workspace. Eles foram preservados e não foram adicionados à implementação; isso não é apresentado como workspace globalmente limpo. O commit da implementação não possui alterações rastreadas pendentes.

## 6. Aviso de build e limitações explícitas

O PyInstaller emitiu um aviso de análise relacionado a módulos opcionais/condicionais, incluindo referências de plataforma e dependências opcionais. O artefato contém `_internal/_zoneinfo.pyd`, a build concluiu, o manifesto foi gerado e o smoke oficial passou. Portanto o aviso não foi ocultado nem convertido em `PASS` por supressão; sua existência e o impacto observado ficam registrados. Não foi observado erro de execução nos smoke tests desta build.

Limitações que não podem ser inferidas além da evidência:

- backend Qt `offscreen` comprova comportamento determinístico e pixels do teste, mas não substitui uma inspeção em monitor físico com DPI nativo;
- as imagens `compact-1280x720.png` e `compact-inspector-focus.png` possuem o mesmo hash no backend offscreen; o foco é comprovado pelo teste de teclado e não por diferença visual dessa captura;
- este pacote comprova somente a Etapa 10. Não comprova renderizador final, construtor de cenários, partículas, luzes, efeitos, runtime ou qualquer etapa posterior.

## 7. Critério de revisão humana

A revisão deve abrir a build dedicada e inspecionar as cinco capturas, o menu, a barra superior, o viewport, as barras laterais, o inspetor, os estados de foco, o fluxo de erro e os atalhos. O revisor deve confirmar que os comportamentos observados correspondem ao requisito `REQ-F10-UI-ACCESSIBILITY` e que a build não está sendo usada para validar etapas posteriores.

Até existir registro explícito de `APROVADO`, este documento permanece `PENDING_HUMAN_REVIEW`; não há autorização para avançar para a Etapa 11 ou Etapa 12.
