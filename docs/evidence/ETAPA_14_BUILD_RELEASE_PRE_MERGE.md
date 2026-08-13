# Evidência — Etapa 14: build e candidato técnico pré-merge

## Identificação

- Data: 13 de agosto de 2026.
- Commit-fonte técnico: `9cef5a15e357f096312048c0beb9d43384c92fce`.
- Versão: `0.2.0`.
- Estado Git durante os builds: limpo.
- Escopo: candidato local; não integrado e sem decisão de publicação.

## Ambiente

- Windows, Python `3.11.9`, Poetry `2.4.1`.
- PyInstaller `6.22.0`.
- Godot `4.7` (stable official).
- Unity `6000.5.7f1`, pacote `com.unity.cloud.gltfast=6.19.0`.
- Dependências sincronizadas exclusivamente pelo `poetry.lock`.

## Comandos reproduzíveis

```powershell
.\scripts\build_installer.ps1
poetry run pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml
poetry run python tools\check_coverage_policy.py coverage.xml
poetry run python tools\run_legacy_tests.py --group all --output <diretorio-temporario>
poetry run python tools\validate_engine_exports.py --engine godot --executable <godot> --fixture-dir release\smoke\engine-godot --work-dir <diretorio-temporario> --report <relatorio>
poetry run python tools\validate_engine_exports.py --engine unity --executable <unity> --fixture-dir release\smoke\engine-unity --work-dir <diretorio-temporario> --report <relatorio> --unity-package com.unity.cloud.gltfast=6.19.0
```

O build exige árvore limpa, deriva timestamp e commit do Git, fixa `PYTHONHASHSEED=0`, valida o bundle antes de empacotar e rejeita destino fora do workspace.

## Artefatos e reprodutibilidade

| Artefato | Tamanho | SHA-256 | Execuções idênticas |
|---|---:|---|---:|
| `NeoEng-D-Trace-0.2.0-win64-portable.zip` | 122.552.277 | `2c8b9c8847d0c00e9f1d0786f5b14e161832856252d8454db58d0d9e198e0d68` | 2/2 |
| `NeoEng-D-Trace-0.2.0-win64.msi` | 121.958.400 | `85adbdb1b754fc69a7fc717e9e9b4aed5950a8e71b746adb381f4444f589b7c5` | 2/2 |
| manifesto MSI | 734 | `50378b8563d13a52ae7caa74132c23312f56cf4d475c1e3c4a7f044ca5734ca2` | 2/2 |

O manifesto portátil declarou e revalidou `312` arquivos sem ausência, divergência de tamanho ou hash. O MSI contém `313` registros de arquivo, `40` componentes, `1` atalho e `1` condição de lançamento; `ALLUSERS=2`, `MSIINSTALLPERUSER=1` e `LIMITUI=1`.

## Validação funcional real

Duas execuções completas aprovaram:

- versão da CLI e leitura de projeto versionado;
- exportação de projeto, JSON e GLB;
- perfis Godot e Unity;
- abertura e fechamento estruturado da GUI;
- uso de diretório gravável de estado do usuário;
- instalação MSI por usuário com código `0`;
- execução dos binários instalados e das exportações;
- desinstalação com código `0`, remoção completa do aplicativo e preservação de estado do usuário.

Os mesmos fixtures determinísticos foram produzidos nas duas execuções. Godot e Unity aprovaram `metadata`, `texture`, `collision`, `glb-external` e `glb-engine`. Os hashes canônicos estão no manifesto JSON desta etapa.

## Gate local completo

- `978 passed`, zero falhas e zero ignorados na suíte oficial.
- Linhas: `11.621/12.523` (`92,80%`).
- Branches: `3.382/3.978` (`85,02%`).
- Combinada: `90,92%`.
- Todos os módulos mensuráveis em pelo menos `30%`.
- mypy: zero erros em `80` arquivos.
- Flake8, Black, isort, compileall e baseline: aprovados.
- pip-audit: nenhuma vulnerabilidade conhecida nas dependências auditáveis; o pacote local não existe no índice público e foi explicitamente ignorado pela ferramenta.
- Bandit de alta severidade: aprovado.
- Legado: `196` testes executados; `27/27` falhas históricas reconciliadas; zero inesperadas e zero ausentes. Essas 27 falhas não são declaradas como testes funcionais atuais aprovados.

## Integridade e segurança do artefato

- zero referências proibidas ou caminhos locais no bundle final;
- Microsoft Defender: nenhuma ameaça detectada no bundle e no MSI;
- checksum externo e manifesto interno conferidos;
- GUI, CLI e MSI: `NotSigned`.

A varredura antimalware é evidência pontual do host e da data, não prova ausência universal de malware.

## Falhas observadas e tratadas

Nenhuma destas ocorrências foi convertida artificialmente em PASS:

1. o primeiro smoke usou fixture sem polígonos exportáveis e falhou; a entrada foi substituída por fixture versionada funcional e o smoke permaneceu obrigatório;
2. um artefato inicialmente funcional foi rejeitado porque a árvore estava suja e o manifesto não representava todo o estado; o build passou a exigir árvore limpa;
3. o primeiro ZIP não foi reproduzível pela ordem do arquivo Python interno; `PYTHONHASHSEED=0` corrigiu a causa e dois builds posteriores ficaram idênticos;
4. uma tentativa de obter ferramenta externa retornou conteúdo incorreto; o binário alternativo estava sem assinatura e não foi executado; o MSI passou a usar a API nativa do Python 3.11;
5. o primeiro MSI diferiu em quatro bytes de timestamp no armazenamento composto; a normalização foi limitada e estruturalmente validada, e dois MSIs posteriores ficaram idênticos;
6. o perfil `default` da CLI acionou headless indevidamente; o teste detectou a regressão e a condição foi corrigida;
7. uma invocação focal usou nome de arquivo de teste incorreto e falhou antes de coletar casos; o comando correto foi executado;
8. o primeiro gate final terminou com `977 passed, 1 failed`: o teste novo continha literalmente o próprio padrão proibido pelo scanner. A literal foi construída por partes sem mudar a asserção nem o scanner; `16` testes focais e depois os `978` testes passaram;
9. o PyInstaller continua emitindo `242` linhas de módulos ausentes, majoritariamente condicionais/plataforma/ opcionais, e um aviso de `tzdata` ausente. Os smokes, MSI e engines passaram, mas os avisos não são declarados inexistentes.
10. o primeiro CI da PR, run `31736919284`, foi rejeitado: Windows passou, mas Linux terminou com `979 passed, 1 failed` porque o contrato hashava bytes de um JSON textual com finais de linha dependentes da plataforma. A correção usa serialização JSON canônica e continua rejeitando qualquer divergência semântica.

## CI pré-merge corretivo auditado

O run `31737623236`, vinculado ao HEAD fonte `d6516001d3901c253dafc78a5540884cf82dcf58` e ao merge sintético `df7fc52e1e857950e1760848549dbc1ae3286571`, foi aceito somente após inspeção dos artefatos:

- Linux e Windows: `980 passed` por sistema;
- cobertura idêntica ponto a ponto em `80` módulos: `11.621/12.523` linhas e `3.382/3.978` branches;
- política global e piso por módulo aprovados;
- legado Windows: `196` testes, `27/27` falhas históricas reconciliadas, zero inesperadas/ausentes e `17` substitutos coletáveis;
- `66` arquivos de evidência equivalentes ao repositório após normalização textual;
- `1.431` payloads e `127` arquivos ZIP examinados recursivamente, sem referência proibida, caminho local ou checksum interno divergente;
- artefato Linux `9195814077`, digest `65ec4529b82c36116596c5810899fe7b4794d578b929bf3b94345859ddadc2b2`;
- artefato Windows `9195848386`, digest `c3c8a7e3e090c756958a2487f8c6c57ea43c51e410b373217bfbd673226b3aee`.

O run verde foi aceito após essa auditoria; o run anterior `31736919284` permanece rejeitado no histórico.

## Limitações e riscos residuais

- `R-014`: executáveis e MSI sem assinatura de código; bloqueia release pública.
- `R-015`: licença/texto jurídico comercial, política de publicação/dados e ícone oficial pendentes; bloqueia release pública.
- `R-016`: builder MSI usa API descontinuada e removida após Python 3.12; exige migração antes de atualizar o toolchain.
- validação realizada em um único host Windows e no usuário atual com instalação isolada; não equivale a matriz de máquinas limpas, arquiteturas e políticas corporativas;
- resultados externos de Godot/Unity cobrem o fixture canônico, não toda combinação possível de asset;
- logs brutos locais não são versionados porque contêm caminhos do ambiente; os relatórios normalizados e hashes são versionados.

## Decisão

`PRE_MERGE_CI_RUN=31736919284`

`PRE_MERGE_CI_STATUS=REJECTED`

`CORRECTIVE_CI_RUN=31737623236`

`CORRECTIVE_CI_STATUS=ACCEPTED_AFTER_ARTIFACT_AUDIT`

`STAGE14_TECHNICAL_CANDIDATE=PASS`

`STAGE14_COMPLETED=NO`

`RELEASE_APPROVED=NO`

Candidato técnico aprovado localmente para PR e CI. A Etapa 14 não está integrada nem formalmente encerrada, e os bloqueios `R-014` e `R-015` impedem publicação.
