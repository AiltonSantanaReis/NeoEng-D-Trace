# Evidência — Encerramento pós-merge da Etapa 13

## Identificação

- data: 13 de agosto de 2026;
- PR funcional e documental: `#51`;
- HEAD fonte final: `0b5d3c4e3831ad5efe52ae03a41107c6dafbf535`;
- merge funcional: `e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108`;
- CI pós-merge: `31698961646`;
- release: não aprovada.

## Objetivo

Encerrar `R-011` e a Etapa 13 somente depois de comprovar que a refatoração
Qt e o autosave protegido foram integrados à `main` e reproduzidos no CI
pós-merge em Linux e Windows. Este fechamento não inicia a Etapa 14 e não
aprova build standalone, instalador ou release.

## Falha real descoberta antes do merge

O primeiro CI da PR, `31693639653`, terminou verde, mas foi rejeitado após a
inspeção dos artefatos detectar `11.576` linhas cobertas no Linux contra
`11.578` no Windows. As linhas divergentes pertenciam à quarentena de
snapshots inválidos.

A causa era uma diferença real entre plataformas: `Path.rename` recusava um
destino existente no Windows, enquanto o substituía em sistemas POSIX. Assim,
uma quarentena anterior podia ser sobrescrita no Linux. O commit
`426cef118fdb0a334e639ec962b2e514cfd59b0a` passou a reservar o destino com
criação exclusiva e adicionou regressão que preserva o arquivo anterior em
qualquer sistema.

## Validação local consolidada

No Windows 11, Python `3.11.9` e Qt offscreen quando aplicável:

- `953 passed` na suíte oficial;
- `11.581/12.478` linhas cobertas: `92,81%`;
- `3.370/3.964` branches cobertos: `85,02%`;
- cobertura combinada: `90,93%`;
- zero módulos abaixo de 30%;
- baseline de `335` arquivos verificado;
- Black, isort, flake8 e compilação aprovados;
- mypy sem problemas em `80` arquivos;
- nenhuma vulnerabilidade conhecida nas dependências auditáveis;
- Bandit sem achados de alta severidade;
- suíte legada com `196` testes, `27/27` divergências conciliadas, zero
  inesperadas, zero ausentes, zero erros e zero skips;
- prova real com `QApplication`, `QEventLoop` e `QTimer`;
- prova de persistência e recuperação entre processos distintos.

## CI pré-merge final aceito

O workflow `31696674184` validou o HEAD fonte
`0b5d3c4e3831ad5efe52ae03a41107c6dafbf535` no merge sintético
`9fcc1bfbd3856ddcf14ed40f78feb3397777f9ee`, cujos pais eram a base
`fc81c2ea10e751c15a39627d462ddfff390eeb04` e o próprio HEAD fonte.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `94435927906` | `success` | `9179615953` | `0d0c0ddcb89690f9c3dc9bc6bebc23f35398653af83e7f3eee208d9301fbf31d` |
| Windows | `94435927866` | `success` | `9179650817` | `bbc17e3ddb89a78fc30a39cc0c9a8eba374c1a174063f623e2d8ba1a85ed6c3f` |

A auditoria confirmou `953` testes em ambos os sistemas, cobertura idêntica
ponto a ponto, zero módulos abaixo de 30%, legado `27/27`, `56` documentos
equivalentes e `1.421` payloads sem violações.

## Integração

Mediante autorização explícita, a PR `#51` foi retirada do modo draft e
mesclada em `e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108`. O merge possui como pais
a base `fc81c2ea10e751c15a39627d462ddfff390eeb04` e o HEAD fonte
`0b5d3c4e3831ad5efe52ae03a41107c6dafbf535`; sua árvore é
`0c8cbc1ec1571851c0830424510703bc10761138`.

## Validação pós-merge aceita

O workflow `31698961646` foi disparado por `push` no merge
`e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108`.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `94443159698` | `success` | `9180500171` | `c942f53fb0ff490d091958764b3c98efe0d705d47478c15743bff284682e936a` |
| Windows | `94443159474` | `success` | `9180511616` | `489aa2d895ae2576fc2f478e652dd7f011ba318dbb36cf35c546b8e89306e6c2` |

A aceitação não se baseou apenas no estado verde:

- zero anotações nos dois check-runs;
- `953 passed` em Linux e Windows;
- `11.581/12.478` linhas e `3.370/3.964` branches nos dois sistemas;
- cobertura combinada `90,93%`;
- zero diferenças entre pontos de cobertura;
- zero módulos abaixo de 30%;
- baseline de `335` arquivos aprovado antes e depois dos testes;
- mypy sem problemas em `80` arquivos, dependências auditáveis sem
  vulnerabilidades conhecidas e Bandit sem alta severidade;
- resumo legado schema v4 com commit testado e HEAD fonte iguais ao merge,
  worktree limpa, `196` testes, `27/27` divergências conciliadas, zero
  inesperadas, zero ausentes, zero erros e zero skips;
- `56` documentos comparados e idênticos byte a byte;
- `62` arquivos, `1.421` payloads e `1.359` entradas aninhadas examinados
  recursivamente, com zero violação de referência, caminho pessoal ou
  checksum;
- digests dos artefatos confirmados pela API.

Hashes adicionais da auditoria pós-merge:

- log consolidado:
  `992587698722ef5850e5e360fc625783dce04b18738c5321479022f5641ab7ff`;
- `coverage.xml` Linux:
  `dab4dfe04df7c8b233ea67364a6e30727e0e183008dfb7a4a0b20167b0cf20f1`;
- `coverage.xml` Windows:
  `cb1c786f4879c30f9351987f298adbd7494a0c0dd983e1c41d5347ec8f887e3c`;
- resumo legado:
  `ac92888ec544c2a26f10ef35813203ab0814b8d704de13b237b2ab47e4849989`.

Após adicionar este relatório e seu contrato documental, o pacote local de
encerramento aprovou `955 passed`, baseline de `338` arquivos e preservou
exatamente `11.581/12.478` linhas, `3.370/3.964` branches e cobertura combinada
de `90,93%`. Esse resultado local valida o pacote documental ainda não
integrado; não substitui nem altera a evidência pós-merge funcional acima.

Uma auditoria retrospectiva posterior encontrou uma falha real no scanner de
higiene usado até então: caminhos Windows escapados com separadores duplicados
não eram reconhecidos. Quatro ZIPs históricos continham `60` payloads e `852`
ocorrências do identificador local. A correção autorizada sanitizou os pacotes,
recalculou checksums e fortaleceu o teste; portanto, a alegação de zero
violações do CI `31698961646` deve ser lida como resultado do scanner antigo,
não como prova da regra ampliada. A correção documental/histórica depende de
novo CI antes de integração.

## CI do fechamento e da correção retrospectiva

O workflow `31702428679` validou o HEAD fonte
`344f26fffc976fb95ab5b3922fc8c5dba9763d09` no merge sintético
`af810d378ee7b9d76c4ef0d3fe13d652be2cf5a1`, cujos pais são a base
`e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108` e o próprio HEAD fonte. A árvore
testada é `615c2435826a27bd8d71af54d641f512570485a8`.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `94454577670` | `success` | `9181836961` | `f3c5eb14e6c68a4da7d08d71595c2389e473d71ecc41bc5bcd49d4090107b0b1` |
| Windows | `94454577637` | `success` | `9181873468` | `472109724fc5aed977883c36f8d91e35034b49a0d81b65017035b2122e438633` |

A auditoria independente confirmou zero anotações, `955 passed` nos dois
sistemas, baseline `338` antes/depois, cobertura ponto a ponto idêntica em
`11.581/12.478` linhas e `3.370/3.964` branches, zero módulos abaixo de 30%,
`57/57` evidências byte a byte, legado schema v4 com `196` testes e `27/27`
divergências conciliadas, além de `57` arquivos, `1.416` payloads e `1.359`
entradas aninhadas com zero referência proibida, caminho pessoal ou checksum
divergente.

Hashes da auditoria:

- log consolidado: `71e31a9c9da0447af5a5a48786b4fcb404b4d0af14fd7e4ffd05872e35697a03`;
- `coverage.xml` Linux: `876048382a4f8b576e88f4bf5550def1e0e34f64cb0aa1380d4a9b09d79c884a`;
- `coverage.xml` Windows: `1fda875f485f1f348fe82bd60d243f50e653b5a51fcc5704d07b4a8f512a643d`;
- resumo legado: `9121d5a0a2bfcfc9215435aa5a11e3bbf7276513d354de53fb822309c8a5cba9`.

Esse CI aceita a correção retrospectiva no commit fonte. No momento da coleta,
a PR documental `#52` estava em draft e não integrada; qualquer integração
exigia autorização separada.

## Decisão e limites

- `R-011` está encerrado no escopo aprovado;
- a Etapa 13 está concluída no escopo aprovado;
- o autosave é recuperação local e não substitui backup;
- a margem de branches permanece em apenas `0,02` ponto percentual;
- as `27` divergências legadas continuam registradas e conciliadas, não
  apagadas;
- a Etapa 14 não foi iniciada por este fechamento;
- build Windows standalone, instalador e validações reais de release
  permanecem pendentes;
- release continua não aprovada.

## Marcadores auditáveis

```text
FUNCTIONAL_PR=51
FUNCTIONAL_SOURCE_HEAD=0b5d3c4e3831ad5efe52ae03a41107c6dafbf535
INTEGRATION_COMMIT=e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108
POST_MERGE_CI_RUN=31698961646
POST_MERGE_CI_STATUS=ACCEPTED
POST_MERGE_LINUX_JOB=94443159698
POST_MERGE_WINDOWS_JOB=94443159474
POST_MERGE_LINUX_ARTIFACT=9180500171
POST_MERGE_WINDOWS_ARTIFACT=9180511616
POST_MERGE_TESTS_PASSED=953
POST_MERGE_LINE_COVERAGE=11581/12478
POST_MERGE_BRANCH_COVERAGE=3370/3964
POST_MERGE_PAYLOADS_SCANNED=1421
CLOSURE_LOCAL_TESTS_PASSED=955
CLOSURE_BASELINE_FILES=338
CLOSURE_SOURCE_HEAD=344f26fffc976fb95ab5b3922fc8c5dba9763d09
CLOSURE_CI_RUN=31702428679
CLOSURE_CI_STATUS=ACCEPTED
CLOSURE_SYNTHETIC_MERGE=af810d378ee7b9d76c4ef0d3fe13d652be2cf5a1
CLOSURE_LINUX_JOB=94454577670
CLOSURE_WINDOWS_JOB=94454577637
CLOSURE_LINUX_ARTIFACT=9181836961
CLOSURE_WINDOWS_ARTIFACT=9181873468
RETROSPECTIVE_HYGIENE_FINDING=60_PAYLOADS_852_LOCAL_REFERENCES
RETROSPECTIVE_HYGIENE_LOCAL_STATUS=PASSED
RETROSPECTIVE_HYGIENE_REMEDIATION=CI_ACCEPTED
FINAL_CLOSURE_PR=52
FINAL_SOURCE_HEAD=919ce59c1f4b652f879ab64af23c758272ece985
FINAL_INTEGRATION_COMMIT=b4d9390dbd1274c283a3e3985d6d79be47de45d6
FINAL_POST_MERGE_CI_RUN=31705652046
FINAL_POST_MERGE_CI_STATUS=ACCEPTED
FINAL_LINUX_JOB=94465417952
FINAL_WINDOWS_JOB=94465417937
FINAL_LINUX_ARTIFACT=9183106504
FINAL_WINDOWS_ARTIFACT=9183135065
FINAL_TESTS_PASSED=955
FINAL_PAYLOADS_SCANNED=1416
R011_CLOSED=YES
STAGE13_COMPLETED=YES
STAGE14_STARTED=NO
RELEASE_APPROVED=NO
```

## Integração documental final

Mediante autorização explícita, a PR `#52` foi integrada no merge
`b4d9390dbd1274c283a3e3985d6d79be47de45d6`. Seus pais são a integração
funcional `e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108` e o HEAD documental
`919ce59c1f4b652f879ab64af23c758272ece985`; a árvore
`3800cc8195481a20a0079583b3bd670733a945ac` coincide com o merge sintético
pré-merge auditado.

O CI pós-merge `31705652046` executou no próprio merge e foi aceito somente
após inspeção dos logs e artefatos. Linux e Windows aprovaram `955` testes,
baseline de `338` arquivos, lint, formatação, tipagem, dependências e análise
estática. A cobertura foi idêntica ponto a ponto: `11.581/12.478` linhas e
`3.370/3.964` branches, sem módulo abaixo de 30%.

O legado executou `196` testes, manteve `27/27` divergências conciliadas e
zero inesperada ou ausente; `source_head_commit` e `tested_commit` registraram
o merge real, com árvore limpa. Os artefatos continham `57/57` documentos
idênticos ao checkout da coleta, `1.416` payloads, `1.359` entradas aninhadas e
`327` checksums verificados, sem referência proibida, caminho pessoal ou
divergência de checksum.

Digests dos artefatos brutos:

- Linux: `0e6c8af122af2b3ae9c9e4f190a9690d6c79fab54c33c34f6bca90b8ff88523b`;
- Windows: `8dc430cdea53e853123d593d61425a84fd26538b99d54db8a4fabfdabcbd6673`.

Essa integração atualiza apenas o fechamento documental e a higiene das
evidências. A Etapa 14 permanece não iniciada e a release não aprovada.

## Rollback

Um rollback funcional deve reverter o merge
`e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108` por novo commit, preservar o
histórico e reexecutar todos os gates. Nenhum arquivo de projeto do usuário
precisa ser migrado para remover o autosave, porque o snapshot usa envelope
separado do schema `.ndtproj` v1.

## Decisão final

**ETAPA 13 CONCLUÍDA NO ESCOPO APROVADO.** `R-011` está encerrado após merge
autorizado e CI pós-merge auditado. A Etapa 14 e a release permanecem não
iniciada e não aprovada, respectivamente.
