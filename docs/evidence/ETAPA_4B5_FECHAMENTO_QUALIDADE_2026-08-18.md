# Evidência — Etapa 4B.5: benchmark, determinismo e regressão

## Identificação

- Escopo: fechamento técnico da câmera/parallax e do cenário lateral após as etapas 4A a 4B.4.
- Estado: **APROVADO NO ESCOPO LOCAL; PR, CI e merge permanecem pendentes neste snapshot**.
- Branch de execução: feature branch (identifier omitted by repository hygiene gate).
- HEAD de execução do auditor: `3be4a92db76a6fdb5474e2b458a4be1e9d152541`.
- Auditor reproduzível: `scripts/audit_stage4b5_quality.py`.
- Artefatos: `docs/evidence/artifacts/stage4b5-quality-2026-08-18/`.

## Procedimento real

O auditor carregou os fixtures versionados de autoria da Etapa 4B.3 por
`load_scenario`, exportou o documento por `serialize_scenario_runtime_export`,
projetou pontos por `project_layer_points` e construiu overlays por
`build_overlay_geometry`. Não houve mock de exportação, bypass de validação ou
alteração do fixture de entrada.

Comando executado no Windows local:

```text
.venv\Scripts\python.exe scripts/audit_stage4b5_quality.py
```

Entradas verificadas:

| Entrada | Bytes | SHA-256 |
|---|---:|---|
| `stage4b3-authoring-2026-08-18/authoring_fixture.ndtproj` | 30 | `6b112cd645d9b382303cebd7c78a8408137ed6aba9e033db4e2ac273a05159db` |
| `stage4b3-authoring-2026-08-18/authoring_fixture.ndtscenario.json` | 733 | `c4fb3456d8ca49baf4dc1c456b9413bef9945f56cbb53ef136ca9e572888d7fe` |

## Resultados reproduzidos

- Exportação runtime repetida 5 vezes com bytes e hash idênticos.
- Hash do runtime: `b289ed758fae15d3d24ce834ea4d7adb471d3afa69c0b356f9cdf47420e310fb`.
- Projeção do preview repetida 5 vezes com resultado idêntico.
- Geometria de overlay repetida 5 vezes com resultado idêntico.
- Serialização do input antes/depois idêntica; não houve mutação do documento.
- Duas cópias do runtime gerado possuem bytes idênticos.
- Saída do processo: `STAGE4B5=PASS`.

## Benchmark local

Os limites são tetos de segurança para detectar regressão severa, não uma
afirmação de FPS nem uma comparação histórica. Não existia baseline temporal
anterior à 4B.5; esta execução registra o primeiro baseline reproduzível.

| Operação | Execuções | Tempo | Operações/s | Limite | Resultado |
|---|---:|---:|---:|---:|---|
| Serialização runtime | 500 | 0,057728 s | 8.661,293 | 10 s | PASS |
| Projeção preview | 10.000 | 0,693242 s | 14.424,973 | 5 s | PASS |
| Geometria overlay | 10.000 | 0,024869 s | 402.110,274 | 5 s | PASS |

Os valores acima são os registrados pelo artefato desta execução; o relatório
JSON é a fonte integral dos dados e não deve ser alterado manualmente.

## Regressão e gates locais

- Suíte integral: `1323 passed, 2 skipped, 10 warnings`.
- Cobertura XML: `14988/16164` linhas (92,72%) e `4393/5162` branches (85,10%); cobertura exibida pelo pytest: 90,88%.
- Política de cobertura: `PASS`; baseline, privacidade, integridade documental e higiene de referências foram executados sem bypass.

- Testes focais do auditor: `3 passed`.
- Black, isort e flake8 dos arquivos modificados: `PASS`.
- Sintaxe Python: `PASS`.
- O workflow CI foi ampliado nos jobs Linux e Windows para executar o mesmo
  auditor em diretório temporário, sem reescrever evidências versionadas.
- O gate de integridade de evidências continua obrigatório e não foi relaxado.

## Artefatos e privacidade

O índice `artifact-index.json` registra bytes e SHA-256 de cinco arquivos,
sem auto-referência. Os artefatos contêm apenas fixtures, payloads e relatório
com caminhos relativos ao repositório; não registram diretório de usuário,
identificador de máquina, PID, token ou endpoint local.

## Limitações declaradas

- Esta etapa mede os contratos puros de exportação/preview do editor; não
  declara runtime de engine, partículas, shaders ou FPS.
- Ainda não há baseline temporal histórico para afirmar melhora ou regressão
  estatística entre commits.
- O estado integrado só poderá ser afirmado após PR, checks obrigatórios e CI
  pós-merge sobre o SHA resultante.

## Decisão

**APROVADO NO ESCOPO LOCAL DA ETAPA 4B.5.** A implementação do auditor,
determinismo, benchmark de segurança, não mutação, privacidade e geração de
artefatos foram comprovados. A promoção para PR/merge permanece condicionada à
validação do diff, cobertura completa, integridade com arquivos rastreados e
checks reais do CI.
