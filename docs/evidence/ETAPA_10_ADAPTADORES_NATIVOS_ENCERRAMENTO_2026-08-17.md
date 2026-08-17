# Evidência — Etapa 10 dos adaptadores nativos

## Identificação

- Escopo: fechamento técnico local dos adaptadores source-only Godot/Unity.
- Baseline de entrada: `de50709586e6e3605efc347a85521ba40ff57ef3`.
- Commit local validado: `a713b8d9a28818bae2c72a2fab35e79f2f4e157d`.
- Data da execução: 2026-08-17.
- Estado do merge: PR #84 mesclada no commit `bca43f399928d69cb81e133e40991b7c011a0c10`; head validado `5fef53296d3c37495b26a4b2ec2f503103dc6604`; CI pós-merge `32028639637` PASS em Linux e Windows.

Este documento é operacional e não altera snapshots históricos. Em particular, `DECISAO_ESCopo_ADAPTADORES_NATIVOS_2026-08-17.md` e `ETAPA_10_EXPORTADORES_ENGINES.md` continuam sendo registros históricos com seus próprios estados e não são reinterpretados por esta evidência.

## Ambiente

- Sistema operacional: Windows local.
- Python: 3.11.9, ambiente virtual do projeto.
- Godot real: 4.7.stable.
- Unity real: 6000.5.7f1.
- Dependências: lockfile e ambiente já existentes no projeto.

## Objetivo e escopo

Validar o fechamento executável da Etapa 10: fixtures reais para Godot e Unity, importação source-only, dry-run, aplicação, repetição determinística, conflitos manuais, drift de hash, isolamento de projetos independentes, regressão das Etapas 4 e 6, integridade de artefatos e decisão explícita de release.

O harness utilizado foi `scripts/audit_native_stage10.py`. Ele falha fechado quando a engine não é encontrada, quando o marcador de validação não aparece, quando uma saída esperada diverge, quando há caminho inseguro, quando a repetição não é determinística ou quando os artefatos não passam pela sanitização e pelos hashes.

## Entradas e artefatos

- Relatório estruturado: `docs/evidence/artifacts/native-stage10-2026-08-17/stage10-report.json`.
- Índice SHA-256: `docs/evidence/artifacts/native-stage10-2026-08-17/stage10-index.json`.
- Fixtures, PNGs, manifests e logs reais: mesmo diretório de artefatos.
- Suíte completa: `docs/evidence/artifacts/native-stage10-2026-08-17/stage10-full-pytest.log`.
- Histórico das falhas intermediárias: `docs/evidence/artifacts/native-stage10-2026-08-17/stage10-intermediate-failures.log`.

O índice foi recalculado depois da inclusão do log completo e do resumo de falhas. A verificação independente de SHA-256 não encontrou arquivo ausente ou divergente. A varredura de privacidade não encontrou caminhos locais, identidade de máquina, identificadores de sessão, PIDs ou endpoints locais nos artefatos finais.

## Comandos executados

```text
.\.venv\Scripts\python.exe scripts/audit_native_stage10.py --failure-dir <diretorio-diagnostico>
.\.venv\Scripts\python.exe -m black scripts/audit_native_stage10.py tests/test_stage10_closure.py
.\.venv\Scripts\python.exe -m isort scripts/audit_native_stage10.py tests/test_stage10_closure.py
.\.venv\Scripts\python.exe -m flake8 scripts/audit_native_stage10.py tests/test_stage10_closure.py
.\.venv\Scripts\python.exe -m py_compile scripts/audit_native_stage10.py tests/test_stage10_closure.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_stage10_closure.py tests/test_stage_10_engine_profiles.py tests/test_stage7_native_sync_contracts.py --tb=short
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/evidence_integrity.py
```

Os diretórios usados em `--failure-dir` são temporários de diagnóstico, não entradas da evidência. O nome genérico acima evita registrar endereços locais.

## Resultados

### Harness real das engines

- Godot real: PASS.
- Unity real: PASS.
- Fixtures determinísticos: PASS.
- Fixtures de regressão das Etapas 4 e 6: PASS.
- Dry-run, aplicação, repetição, conflito manual, drift de hash e caminhos inseguros: PASS no relatório estruturado.
- Resultado do harness: `NATIVE_STAGE10=SUCCESS`.
- Release: `RELEASE_APPROVED=NO`; a validação técnica não autoriza publicação.

### Gates locais

- Testes focais: `28 passed`.
- Suíte completa: `1173 passed, 2 skipped, 10 warnings`.
- Os dois skips são os testes de symlink condicionados à permissão do Windows; não foram removidos, desabilitados nem convertidos artificialmente em PASS. Eles já possuem execução administrativa separada registrada no fechamento da Etapa 9 como `2 passed, 0 skipped`.
- `mypy src`: sem erros em 91 arquivos.
- Black, isort, flake8 e py_compile: PASS nos arquivos novos.
- Integridade de evidências: `35 manifests validated`.
- Hashes do índice: PASS.
- Privacidade: PASS.

## Falhas intermediárias e correções

As primeiras seis execuções falharam por erros reais de sintaxe do fixture Godot, ordem incorreta de captura do snapshot, comparação excessivamente estrita de metadados internos do Unity e vazamento/colisão de logs. Todas foram mantidas no registro de falhas, corrigidas no harness e reexecutadas. A sétima execução foi a primeira execução completa aprovada. O resumo verificável está em `stage10-intermediate-failures.log`; nenhuma execução intermediária foi usada para declarar sucesso.

## Limitações e riscos residuais

- A CI atual valida Python, tipagem, cobertura e integridade, mas não inicializa dinamicamente Godot/Unity; as execuções reais das engines desta etapa são evidências locais reproduzíveis.
- O harness não aprova release, não assina binários e não prova instalação por marketplace.
- Não há garantia contra perda de energia durante uma operação externa; o escopo validado é atomicidade, dry-run, conflito, drift e rollback conforme os contratos existentes.
- Nota histórica do fechamento: a baseline ainda precisava ser regenerada naquele ponto; a verificação posterior foi concluída e está registrada abaixo.

## Decisão

**APROVADO TECNICAMENTE NO COMMIT `a713b8d9a28818bae2c72a2fab35e79f2f4e157d`; NÃO APROVADO PARA RELEASE.**

A Etapa 10 está promovida no plano técnico após push, CI, auditoria e merge. A release continua não aprovada.
## Reconciliação posterior do estado de release
O marcador acima é preservado como decisão do fechamento técnico da Etapa 10.
Ele não é o estado atual da política de release. Em 17 de agosto de 2026, a
decisão vigente removeu assinatura, formalização jurídica e execução dinâmica
de Godot/Unity no CI como gates obrigatórios e aprovou a governança do R-016.
A baseline atual foi verificada com `tools/baseline_integrity.py --verify`,
