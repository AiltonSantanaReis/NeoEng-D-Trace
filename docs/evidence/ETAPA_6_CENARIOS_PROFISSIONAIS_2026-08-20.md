# Evidência — Etapa 6: testes reais, auditoria visual e desempenho

## Estado da etapa

A Etapa 6 foi executada localmente no Windows e aprovada pelos gates definidos no
plano de cenários. A evidência foi capturada com o commit de código
`01399c24ef52f7e506628b71cd48ac2d21e30a1d`, no branch de trabalho da etapa, com
worktree limpo no início e durante as capturas. O pacote ainda não está
integrado ao `main`: PR, CI remoto e merge permanecem pendentes.

Decisão: **APROVADO LOCALMENTE / NÃO INTEGRADO**.

## Escopo comprovado

- MainWindow real em 1920×1080, 1366×768 e 1280×720;
- estados reais sem projeto, projeto com painéis, janela de validação, modal de
  validação e feedback do gizmo;
- editor profissional de cenário real nas três resoluções, com estado vazio,
  projeto carregado e feedback do gizmo;
- Pillow e OpenCV para decodificação, dimensões, transparência e hashes;
- geometria real dos widgets Qt, clipping, sobreposição e paleta QSS escura;
- saídas anotadas para cada PNG suspeito, com auditoria fail-closed;
- determinismo do exportador/runtime, projeção de preview e overlays;
- benchmark local com limites de segurança explícitos;
- varredura de privacidade e índice de bytes/SHA-256.

## Execuções reais

Comandos principais executados:

```text
python scripts/audit_stage6_scenario_quality.py --output docs/evidence/artifacts/stage6-professional-scene-2026-08-20
python -m pytest -q
python -m pytest -q --cov=src --cov-branch --cov-report=xml:<temporario> --cov-report=term
python tools/check_coverage_policy.py <temporario>/coverage.xml
python -m pytest -q tests/test_stage6_scenario_quality.py
python -m isort --check-only scripts/audit_stage6_scenario_quality.py tests/test_stage6_scenario_quality.py
python -m flake8 scripts/audit_stage6_scenario_quality.py tests/test_stage6_scenario_quality.py
python -m mypy --explicit-package-bases --follow-imports=skip scripts/audit_stage6_scenario_quality.py tests/test_stage6_scenario_quality.py
```

Resultados:

- suíte completa: `1409 passed, 2 skipped`;
- os dois skips são os cenários históricos de symlink já declarados no contrato;
- cobertura oficial: 91% de linhas e 91% de branches; política aprovada;
- testes específicos da Etapa 6: `5 passed`;
- Black, isort, Flake8, mypy e compilação Python: aprovados;
- orquestrador da etapa: JSON com `status=PASS`;
- auditoria visual MainWindow: `PASS`, `finding_count=0`;
- auditoria visual do editor profissional: `PASS`, `finding_count=0`;
- worktree limpo na captura: `true`;
- vazamentos de caminhos/identidade nos relatórios: nenhum.

## Desempenho e determinismo

Os limites abaixo são tetos de segurança desta execução, não promessa de FPS nem
baseline histórico:

| Operação | Iterações | Tempo observado | Limite | Resultado |
|---|---:|---:|---:|---|
| serialização runtime | 500 | 0,056846 s | 10 s | PASS |
| projeção de preview | 10.000 | 0,704535 s | 5 s | PASS |
| geometria de overlays | 10.000 | 0,025242 s | 5 s | PASS |

O runtime export foi determinístico em cinco execuções, com 867 bytes e hash
`28d64edc4e599e01fa1c1cbaa03a86b0f46e48bdf45787f4fb9d1649b626c04c`. A entrada
da cena permaneceu inalterada.

## Artefatos e hashes

O pacote completo está em
`docs/evidence/artifacts/stage6-professional-scene-2026-08-20/`.
O índice contém 59 referências para 60 arquivos físicos; o próprio índice não
entra no conjunto de hashes para evitar auto-referência.

- `stage6-report.json` — SHA-256
  `ee495638feaf000f81bf83d9bdd9282ba9effc2c7c2b9c942ccd019ec7fc8b01`;
- `artifact-index.json` — SHA-256
  `7c53db1a4c5c8bc65088eb450f0ab65d1f5204585b3b3518a4db6ac19f0084a7`;
- `main-window/audited/visual-audit-report.json` — zero achados em 16 imagens;
- `professional-editor/stage4-capture-report.json` — zero achados em 9 imagens;
- cada PNG, log e relatório restante possui `bytes` e `sha256` no índice.

## Limitações declaradas

- A medição não é benchmark histórico nem alegação de FPS.
- Partículas, streaming, runtime completo e VFX não determinísticos continuam
  fora do contrato desta etapa.
- A execução real dos adaptadores Godot/Unity continua vinculada à evidência
  real da Etapa 5; esta etapa não reclassifica suporte ausente como falha nem
  o apresenta como suporte novo.
- A abertura visual manual dos PNGs não é usada como critério de aprovação; a
  decisão depende do auditor Pillow/OpenCV/Qt fail-closed e dos artefatos
  hashados.

## Rollback e decisão

O rollback local é a reversão dos commits de proveniência e evidência desta etapa, identificados por 01399c24ef52f7e506628b71cd48ac2d21e30a1d4ef52f7e506628b71cd48ac2d21e30a1d e pelo commit de evidências que o sucede. O merge 57f29d4 da Etapa 5 permanece como base anterior. Nenhum arquivo de usuário é migrado ou apagado por esta etapa.

A etapa está aprovada localmente porque todos os gates executáveis nesta máquina
passaram. A integração remota, CI remoto, revisão de PR e merge ainda não foram
executados e não são inferidos por esta evidência.