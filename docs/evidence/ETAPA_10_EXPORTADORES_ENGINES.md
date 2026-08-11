# Evidência — Etapa 10: exportadores e engines

## Identificação

- Branch: `etapa-10-exportadores-engines`.
- Base auditada: `f2d44c9ce6645a343e5e515303cc6c3c75443ae7`.
- Commit técnico: `bb849d1b19959198b34a123cd6d07cda2ae82cd2`.
- Data local: 10 de agosto de 2026.
- Estado: concluído após as PRs `#42` e `#43` e o CI pós-merge corretivo `31469610508`.

## Objetivo e escopo

Validar os contratos JSON Generic, Godot 4 e Unity, o GLB 2D e o conjunto
PNG/JSON de atlas. A validação cobre estrutura, geometria, pivô, colisão,
Unicode, caminhos, sobrescrita, rollback de múltiplos arquivos e importação em
engines reais. Build, instalador, autosave, 2.5D e release não pertencem a esta
decisão.

## Falhas confirmadas antes da correção

1. O perfil Godot calculava o deslocamento com coordenadas absolutas e sinal
   incorreto. O caso `x=100`, `y=50`, `w=40`, `h=20`, pivô `(10, 5)` gerava
   `(-110, -55)` em vez de `(10, 5)`.
2. O caminho de cena Godot não chamava o formatador específico e devolvia o
   registro genérico.
3. O caminho de cena Unity iniciava o pivô em `(0.5, 0.5)` pixels e depois o
   normalizava, produzindo `(0.0125, 0.025)` para um retângulo `40x20`.
4. Cena e objeto tinham implementações divergentes para os mesmos perfis.
5. `save_atlas()` podia substituir o PNG e falhar antes do JSON, deixando um
   conjunto misto. A escrita preparava ambos os temporários, mas não restaurava
   destinos após falha no segundo commit.
6. O Unity Editor não importa GLB nativamente. Sem pacote importador, o
   validador terminou com `InvalidDataException: glb-import`.

## Correções

- validação comum de retângulo e pivô finitos em
  `src/exporters/profiles/common.py`;
- schemas versionados independentes para Godot e Unity;
- pivô local em pixels na entrada, offset Godot com direção correta e pivô
  Unity normalizado;
- despacho único dos perfis para exportação de cena e objeto;
- identificadores de formato e versão no JSON genérico;
- transação de atlas protegida por rollback, com restauração dos destinos
  anteriores e remoção do novo arquivo parcial após falha injetada;
- harness reproduzível em `tools/validate_engine_exports.py`;
- validadores rastreados em `tools/godot_engine_validator.gd` e
  `tools/unity_engine_validator.cs`;
- importador oficial Unity `com.unity.cloud.gltfast=6.19.0` fixado no harness.

## Ambiente real

- Windows 64 bits.
- Python `3.11.9`.
- Godot `4.7.stable.official.5b4e0cb0f`.
- Unity Editor `6000.5.7f1`.
- Unity Hub `3.20.1`, executável com assinatura digital válida da Unity.
- Licença Unity Personal atribuída e sem expiração, validada pelo próprio log
  do Editor; nenhum dado de autenticação foi armazenado.
- glTFast `6.19.0`, resolvido pelo registro oficial com requisito mínimo Unity
  `6000.0`.

## Ocorrências de ambiente preservadas

- O pacote comunitário do Hub `3.19.5` esperava SHA-256
  `06d09ea17e7973ff9889e46b20ddc9b61221b6c3e9e722d69e34b508616f0497`,
  mas a URL oficial passou a entregar Hub `3.20.1`, SHA-256
  `58fd1d3dbb9225e4cea6efe85df5bc419c7ad4e0c6737b945937930e95f9a73e`.
  A divergência não foi ignorada: a assinatura foi verificada antes da
  instalação direta por usuário.
- A primeira execução do Editor sem ativação terminou com código `198` e
  `No valid Unity Editor license found`.
- Depois da ativação, uma primeira criação de projeto devolveu código de
  processo `1` apesar de o log terminar anunciando `0`; a tentativa não foi
  aprovada. Uma execução independente devolveu `0`.
- Outra primeira importação falhou no `ApiUpdater` interno ao processar um DLL
  do Editor, sem saída diagnóstica. A repetição do mesmo projeto devolveu `0`.
  O harness aceita no máximo uma repetição somente quando o projeto foi criado;
  qualquer falha persistente continua bloqueando.
- A validação Unity sem glTFast falhou em `glb-import`. Somente a execução com
  a versão oficial fixada foi aprovada.

## Comandos reproduzíveis

```powershell
python tools/validate_engine_exports.py --engine godot --work-dir etapa10-godot-unicode --report etapa10-godot-report.json
python tools/validate_engine_exports.py --engine unity --executable <unity-editor> --work-dir etapa10-unity-unicode --report etapa10-unity-report.json
python -m pytest tests/test_stage_10_engine_profiles.py tests/test_atomic_export_replacement.py tests/test_json_exporter_contract.py tests/test_gltf_exporter_contract.py tests/test_regression_core_contracts.py tests/test_export_dialog_metadata.py -q
python -m pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term-missing
python tools/run_legacy_tests.py --group all --timeout-seconds 180
python -m mypy src
python -m pip_audit
python -m bandit -q -r src -lll
```

Os diretórios usados na execução final continham caracteres acentuados. O
fixture também usou o nome `sprite_ação`, exigido pelos dois validadores.

## Resultados locais

- testes específicos da etapa: `17 passed`;
- pacote focal de exportadores e UI: `58 passed`;
- suíte oficial completa após a correção pós-merge: `730 passed`;
- suíte histórica: `196` executados, `27/27` divergências previstas
  reconciliadas, zero inesperadas, zero ausentes e integridade aprovada;
- cobertura: `8.582/11.634` linhas (`73,77%`), `2.146/3.706` branches
  (`57,91%`) e `69,93%` combinada;
- mypy: zero erros em `70` arquivos fonte;
- compileall, flake8, Black e isort: aprovados no escopo integral;
- pip-audit: nenhuma vulnerabilidade conhecida; o pacote local não publicado
  não é auditável no índice público;
- Bandit de alta severidade: aprovado;
- Godot em caminho Unicode: dois processos com código `0`, importação PNG/GLB,
  `AtlasTexture`, `Sprite2D`, colisão e marcador `ENGINE_VALIDATION=SUCCESS`;
- Unity em caminho Unicode: criação e validação com códigos `0`, JSON, PNG,
  pivô, colisão, GLB via glTFast e marcador `ENGINE_VALIDATION=SUCCESS`.

## Hashes dos artefatos finais

| Engine | Artefato | Bytes | SHA-256 |
|---|---:|---:|---|
| Godot | `probe-godot.json` | 862 | `b532ab281ed1bbd583580bdf3b69968c72c547c845ac1192a87cb58c8b928b43` |
| Godot | `source.png` | 229 | `06285ffb8f9c4b564f4f9624858a729c067693df4677273f70270259cf9554cc` |
| Godot | `scene.glb` | 968 | `de8ece4d8259af59f7ff61abd783b869eae8767771fc4c5256f5c842e5125fde` |
| Godot | relatório | 4.128 | `25bf09cabf6cc7ebd08689f34a796f70420c787dc00ebc27cab2f802282199d4` |
| Unity | `probe-unity.json` | 897 | `3e6ec9c1dc5fc9242c6ae1ddcd6bae105471b0c66472a89ec8008a5c0d7deccf` |
| Unity | `source.png` | 229 | `06285ffb8f9c4b564f4f9624858a729c067693df4677273f70270259cf9554cc` |
| Unity | `scene.glb` | 968 | `de8ece4d8259af59f7ff61abd783b869eae8767771fc4c5256f5c842e5125fde` |
| Unity | relatório | 967 | `08a7dc5ed463f1c54ce03e1c05998b4a6f0bb48cff4c4f87db4d3445acba38de` |

## Auditoria remota da PR 42

- A execução `31450335289` aprovou os gates Linux e Windows no commit
  `17ac9b614ea5cc17a16112add8201f2c525c7e45`.
- O resultado verde não foi aceito isoladamente. A inspeção dos artefatos
  demonstrou que a lista fixa do workflow não publicava este relatório.
- O resumo da suíte histórica usava `source_commit` para o commit de origem da
  captura, sem registrar separadamente o commit efetivamente testado. A origem
  histórica estava correta, mas o campo era ambíguo para auditoria operacional.
- A PR permaneceu sem merge. O upload foi generalizado para `docs/evidence/**`
  e o resumo passou a separar `tested_commit`, `source_head_commit` e
  `legacy_source_commit`, registrar `working_tree_dirty` e falhar se o HEAD da
  branch não pertencer à revisão efetivamente testada pelo CI.
- A execução `31451363518` aprovou novamente os gates e publicou todos os
  arquivos de evidência. Mesmo assim, foi rejeitada: o resumo registrou o merge
  sintético `1b37e0a30607498da7555b60d96e5c7c7a49d801`, mas não continha o
  HEAD fonte `680120cf21b4491b861d08507354796a14a5b07b`; essa relação só era
  demonstrável por metadado externo do serviço remoto.
- O schema v4 agora registra `tested_commit` e `source_head_commit` e exige que
  o segundo seja ancestral do primeiro.
- A execução `31452032479` aprovou gates, upload e proveniência v4. A auditoria
  recursiva, porém, encontrou `26` ocorrências repetidas de caminhos pessoais e
  metadados de integração externa em ZIPs históricos aninhados. O resultado foi
  rejeitado.
- Mediante autorização explícita, quatro ZIPs foram sanitizados, os checksums
  internos e hashes externos foram recalculados e um teste passou a examinar
  arquivos rastreados e ZIPs aninhados.
- A execução `31457937902` aprovou Linux e Windows no HEAD fonte
  `5411193014d49b185bf5a3c297b61d74df79d8cb`. A inspeção independente confirmou
  `729` testes por sistema, merge sintético `0394d55501e32e2fa38acbcc4d1e3c5e126954ce`
  com ancestralidade válida, worktree limpa, cobertura exata, reconciliação
  `27/27`, `44` arquivos de evidência idênticos e zero violações recursivas.
- A PR `#42` foi integrada em `9b22bdc54b13992658172d4748bfab44f3127c8e`.
- O CI pós-merge `31463873481` terminou verde, mas foi rejeitado após os XMLs
  mostrarem uma linha e um branch cobertos a menos no Linux. A causa e a
  correção estão em `ETAPA_10_CORRECAO_COBERTURA_POS_MERGE.md`.
- O CI pré-merge corretivo `31464786333` foi aceito após auditoria integral; a
  PR `#43` foi integrada em `f8caec3e7156d308f03046f81d2c89996f959466`.
- O CI pós-merge corretivo `31469610508` foi aceito após confirmar `730` testes,
  cobertura idêntica nos dois sistemas, legado `27/27`, `45` evidências e zero
  violações em `1.410` payloads.

## Limitações e riscos residuais

- A recuperação do atlas protege falhas observáveis de processo, mas nenhum
  filesystem comum oferece commit físico instantâneo de dois arquivos contra
  perda abrupta de energia. O teste aprovado injeta falha no segundo replace e
  prova restauração integral nesse modelo.
- A primeira validação Unity exige rede para resolver o pacote oficial; as
  execuções seguintes usam o cache e o lock do projeto temporário.
- O GLB permanece no escopo 2D documentado. UV, materiais, 2.5D e os limites de
  índice continuam fora desta etapa.
- Cobertura integral da interface é a Etapa 11 e ainda não foi iniciada.
- Build, instalador, autosave e validação de release continuam pendentes.
- Três CIs funcionais foram rejeitados, um pré-merge funcional foi aceito e o primeiro pós-merge foi rejeitado; a correção foi integrada e reproduzida no pós-merge `31469610508`.

## Decisão

**CONCLUÍDO NO ESCOPO APROVADO.** Os critérios funcionais da Etapa 10 foram
integrados e demonstrados nas duas engines reais. O primeiro CI pós-merge foi
rejeitado, a correção determinística foi integrada pela PR `#43` e o novo CI
pós-merge `31469610508` reproduziu cobertura idêntica em Linux e Windows.
Release permanece **NÃO APROVADA**.
