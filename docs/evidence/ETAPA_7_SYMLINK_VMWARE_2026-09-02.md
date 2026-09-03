# Evidência — Etapa 7 — validação de symlink no VMware

## Identificação

- Commit de referência/base do candidato: `eaa28b9a75194d25741323b4b72911426a740349`.
- Commit do conteúdo candidato testado: inexistente no pacote ZIP; o conteúdo foi reconstruído a partir do ZIP-base e do patch identificado abaixo.
- Branch de referência: `fix/legacy-27-functional-regressions`.
- Data/hora: `02/09/2026`; o horário não foi registrado na transcrição fornecida.
- Responsável/proveniência: transcrição do terminal fornecida pelo operador autorizado do ambiente VMware nesta conversa.
- Natureza: evidência de execução no ambiente Windows/VMware, não uma nova execução local reproduzida por este agente.

## Ambiente

- Sistema operacional: Windows 11 em máquina virtual VMware; o build exato do Windows não foi registrado.
- Developer Mode: flag de registro observada como `1`.
- Shell: Windows PowerShell.
- Python: `3.11.0`.
- Poetry: `2.4.1`.
- Pytest: `9.1.1`.
- Pluggy: `1.6.0`.
- Plugin pytest-cov: `7.1.0`.
- Dependências/lockfile: `poetry check --lock --strict` retornou `All set!`; `poetry sync --no-interaction --no-ansi` terminou sem erro.
- Observação de instalação: a sincronização registrou warnings do instalador de wheels relacionados a `__pycache__` em pacotes NumPy/PySide6; não houve código de saída não-zero.

## Objetivo e escopo

Comprovar, no Windows 11 da VM com Developer Mode habilitado, que o processo consegue criar symlinks reais e que os dois contratos de segurança de integração rejeitam os destinos perigosos esperados:

- escape por symlink de diretório;
- destino de saída que já é symlink.

O teste usa `Path.symlink_to` real e espera `IntegrationSecurityError`. Não foram adicionados skips, xfails, filtros de falha ou tolerâncias.

## Entradas

- `neoeng-base-eaa.zip` — `64.977.183` bytes; SHA-256 `5668b579260ff0e098e407f9c5a588d2113cfd5cd37f6cf7a763d7a331545e8e`.
- `neoeng-candidate.patch` — `621.637` bytes; SHA-256 `ed477bb5c6d204005fa684b866886456bce9d5010d25cc47fb49eebde4f5950d`.
- Arquivo de teste: `tests/test_integration_sync.py`.
- Índice de evidência normalizado: `docs/evidence/artifacts/symlink-vmware-2026-09-02/symlink-vmware-index.json`.

## Comandos executados

Após a reconstrução do candidato e a preparação do ambiente:

```text
poetry env use 3.11
poetry check --lock --strict
poetry sync --no-interaction --no-ansi
poetry run pytest "tests\test_integration_sync.py" -k symlink -q -rs
```

O comando de teste foi executado sem o separador PowerShell `;` no caminho.

## Resultados

- Itens coletados: `31`.
- Testes selecionados: `2`.
- Itens deselecionados: `29`.
- Aprovados: `2`.
- Reprovados: `0`.
- Ignorados: `0`.
- Bloqueados: `0`.
- Código de saída: `0`.
- Resultado: `2 passed, 29 deselected in 0.15s`.
- Casos selecionados: `test_plan_rejects_symlink_escape` e `test_plan_rejects_symlink_destination`.
- Cobertura: não coletada neste teste focal; não aplicável ao objetivo de capacidade de symlink.

## Artefatos

- Log normalizado da transcrição: `docs/evidence/artifacts/symlink-vmware-2026-09-02/symlink-vmware-console-normalized.log`.
- Índice SHA-256 do log: `docs/evidence/artifacts/symlink-vmware-2026-09-02/symlink-vmware-index.json`.
- Este relatório: `docs/evidence/ETAPA_7_SYMLINK_VMWARE_2026-09-02.md`.

Os caminhos locais do host e da VM foram sanitizados no log versionado. A transcrição original permanece a fonte de proveniência desta execução.

## Falhas e causa raiz

Não houve falha nos dois testes selecionados. A criação real dos symlinks prosseguiu e as rejeições de segurança foram obtidas conforme o contrato.

A execução acidental anterior da suíte completa no ZIP registrou `1903 passed, 7 failed, 1 warning`. As sete falhas foram classificadas separadamente como limitação de transporte: seis dependiam de metadados Git ausentes e uma dependia do manifesto F02 ausente. Esse resultado não é usado para classificar o teste focal de symlink.

## Limitações e riscos residuais

- O ZIP não contém `.git`; portanto, não existe commit próprio da candidata reconstruída. O commit-base e os hashes de transporte identificam a fronteira sem fabricar proveniência.
- O ZIP não contém `artifacts/evidence/F02/BUILD-F02-GOVERNANCE-20260824-4E05A34/manifest.json`, exigido por um gate formal da suíte completa.
- CI e empacotamento ainda não foram confirmados nesta candidata.
- O build exato do Windows e o horário da execução não constam da transcrição.
- A evidência é uma transcrição fornecida pelo operador; não foi reexecutada localmente nesta sessão.
- A prova resolve a capacidade de symlink no ambiente VMware e os dois contratos focais; não aprova a integração global, release ou equivalência histórica.

## Decisão

`APROVADO` — somente no escopo da capacidade real de symlink e dos dois contratos focais no Windows 11/VMware. O bloqueio global da Fase 7 permanece ativo até a repetição dos gates em pacote completo, a confirmação de CI e a validação de empacotamento.

Não houve alteração de código na VM, nem commit, push, merge, tag ou release.
