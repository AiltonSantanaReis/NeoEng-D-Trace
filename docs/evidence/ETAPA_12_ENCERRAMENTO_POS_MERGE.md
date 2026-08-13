# Evidência — Encerramento pós-merge da Etapa 12

## Identificação

- data: 13 de agosto de 2026;
- PR funcional: `#49`;
- HEAD fonte final: `03b4cd2fc57e2f9187836e5a0ffc89ee08e18fba`;
- merge funcional: `872bf079d228d13d0203d22b844052b1f920e99b`;
- CI pós-merge: `31686321925`;
- release: não aprovada.

## Objetivo

Encerrar `R-012` e a Etapa 12 somente depois de comprovar que os limites
operacionais e controles de segurança foram integrados à `main` e reproduzidos
no CI pós-merge em Linux e Windows, com proveniência, logs e artefatos auditados.

## Validação local consolidada

No Windows, Python 3.11.9 e Qt offscreen, o commit técnico validado reproduziu:

- `928 passed` na suíte oficial;
- `11.174/12.040` linhas cobertas: `92,81%`;
- `3.309/3.892` branches cobertos: `85,02%`;
- cobertura combinada: `90,91%`;
- baseline de `325` arquivos verificado;
- mypy sem problemas em `73` arquivos;
- nenhuma vulnerabilidade conhecida nas dependências auditáveis;
- zero achados de severidade alta no código-fonte.

A suíte legada local executou `196` testes e reconciliou as `27/27`
divergências previstas, sem falhas inesperadas, ausentes, erros ou skips.

Após adicionar este pacote documental e seu contrato, a suíte integral local
aprovou `929` testes e o baseline passou a `326` arquivos; as contagens de
linhas e branches do código-fonte permaneceram inalteradas.

## CI pré-merge final aceito

O workflow `31685608005` validou o HEAD fonte
`03b4cd2fc57e2f9187836e5a0ffc89ee08e18fba` no merge sintético
`9791b4797485d588e11654633565f304bd08f82b`, cujos pais eram a base
`2e9cad4cb7879aa7ceb8ee0a1e096b738674a984` e o próprio HEAD fonte.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `94400816974` | `success` | `9175313377` | `5c82951571326259fd07c8f5e3f0c31a43f60514a6cff2f9a6d417781f3f832e` |
| Windows | `94400816866` | `success` | `9175357217` | `4a404ea18ebab474c6faa6cd03e7947a07aabf6297bce2b5f3e18df9865a2b11` |

Os dois jobs reproduziram `928` testes e as métricas exatas. A auditoria
independente confirmou zero anotações, os digests dos ZIPs brutos, o legado
`27/27`, `54` documentos sem diferença substantiva e uma varredura de `60`
arquivos, `1.419` payloads e `1.359` entradas aninhadas sem violações.

## Integração funcional

A PR `#49` foi retirada do modo draft mediante autorização explícita e
mesclada em `872bf079d228d13d0203d22b844052b1f920e99b`. O merge possui como
pais a base `2e9cad4cb7879aa7ceb8ee0a1e096b738674a984` e o HEAD fonte
`03b4cd2fc57e2f9187836e5a0ffc89ee08e18fba`.

## Validação pós-merge aceita

O workflow `31686321925` foi disparado por `push` no merge
`872bf079d228d13d0203d22b844052b1f920e99b`.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `94403113721` | `success` | `9175582216` | `653196abeefca85a8e43ec608c8107bc5d936308ce63ef457c7dab804f262e47` |
| Windows | `94403113862` | `success` | `9175617872` | `108dff398f1ccc6fc3ead017721c41ea910a764162b440de2906008c064ed7b5` |

A auditoria independente confirmou:

- zero anotações nos dois check-runs;
- `928 passed` em Linux e Windows;
- `11.174/12.040` linhas e `3.309/3.892` branches nos dois sistemas;
- cobertura combinada `90,91%`;
- baseline de `325` arquivos aprovado antes e depois dos testes;
- mypy sem problemas em `73` arquivos, dependências auditáveis sem
  vulnerabilidades conhecidas e Bandit sem alta severidade;
- resumo legado com commit testado e HEAD fonte iguais ao merge, worktree
  limpa, `196` testes, `27/27` divergências conciliadas, zero inesperadas e
  zero ausentes;
- `54` documentos comparados: `52` idênticos byte a byte e `2` idênticos
  após normalização exclusiva de CRLF/LF;
- `60` arquivos, `1.419` payloads e `1.359` entradas aninhadas examinados
  recursivamente, com zero violação;
- digests dos ZIPs brutos idênticos aos publicados pela API.

Hashes adicionais da auditoria pós-merge:

- log consolidado: `0d435f0ca4169c6f94491d96d6bba5e3fc2f1421fe96962fa3c0feea72f7f9cb`;
- `coverage.xml` Linux: `d8b4eb55bf8ba07024723c7020db9544eb0ffeedb6a3cf1945617a7cb7659439`;
- `coverage.xml` Windows: `145494af6fbe2f74177382e2ec6b39a227b921f9ba7813e446e1e74903d2a224`;
- resumo legado: `ac90dc1f7fe87ec7e595d54a78e06fb5d3956ae216b0804ea4adbf31d93005a9`.

## Fechamento documental final integrado

Depois do fechamento funcional acima, a PR documental `#50`, com HEAD fonte
`b9426074a08d25e008c2a4441654660103e3cabe`, foi integrada em
`fc81c2ea10e751c15a39627d462ddfff390eeb04`. O workflow pós-merge final
`31688307089`, disparado por `push` nesse merge, foi concluído com `success` e
zero anotações.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `94409501023` | `success` | `9176359924` | `011e9a80ce81f46ed32ae13babf64fd09d8da8548a615f6a1bcd1f8334a44546` |
| Windows | `94409501129` | `success` | `9176393106` | `59eb68cc32570a60eae502ed3f15048707b9a064f9271eaae788227bfd5cb8e1` |

A auditoria final confirmou `929` testes em Linux e Windows, as mesmas
`11.174/12.040` linhas, `3.309/3.892` branches e `90,91%` combinada,
baseline `326`, legado `196` com reconciliação `27/27`, além de `1.420`
payloads sem referência proibida ou caminho pessoal. Esse fechamento substitui
como âncora operacional o merge funcional anterior, mas não reescreve seus
registros históricos.

```text
FINAL_CLOSURE_PR=50
FINAL_CLOSURE_SOURCE_HEAD=b9426074a08d25e008c2a4441654660103e3cabe
FINAL_INTEGRATION_COMMIT=fc81c2ea10e751c15a39627d462ddfff390eeb04
FINAL_POST_MERGE_CI_RUN=31688307089
FINAL_POST_MERGE_CI_STATUS=ACCEPTED
FINAL_LINUX_JOB=94409501023
FINAL_WINDOWS_JOB=94409501129
FINAL_LINUX_ARTIFACT=9176359924
FINAL_WINDOWS_ARTIFACT=9176393106
FINAL_TESTS_PASSED=929
FINAL_PAYLOADS_SCANNED=1420
```

## Decisão e riscos residuais

- `R-012` está encerrado no escopo aprovado;
- a Etapa 12 está concluída no escopo aprovado;
- os limites implementados são tetos de segurança, não SLA nem prova de
  ausência total de vulnerabilidades;
- a margem de branches é de apenas `0,02` ponto percentual e exige medição
  integral após qualquer mudança;
- as `27` divergências legadas continuam registradas e conciliadas, não
  apagadas;
- `R-011` permanece aberto até integração e CI pós-merge da correção da Etapa 13;
- no instante deste fechamento, autosave, build standalone, instalador e
  validações reais de release permaneciam para as Etapas 13 e 14; o estado
  pré-merge posterior do autosave está em `ETAPA_13_REFATORACAO_QT_AUTOSAVE_PRE_MERGE.md`;
- release continua não aprovada.

## Marcadores auditáveis

```text
FUNCTIONAL_PR=49
FUNCTIONAL_PR_MERGED=YES
SOURCE_HEAD=03b4cd2fc57e2f9187836e5a0ffc89ee08e18fba
INTEGRATION_COMMIT=872bf079d228d13d0203d22b844052b1f920e99b
PRE_MERGE_FINAL_CI_RUN=31685608005
PRE_MERGE_FINAL_CI_STATUS=ACCEPTED
POST_MERGE_CI_RUN=31686321925
POST_MERGE_CI_STATUS=ACCEPTED
LOCAL_TESTS_PASSED=928
LINE_COVERAGE=11174/12040
BRANCH_COVERAGE=3309/3892
R012_CLOSED=YES
STAGE12_COMPLETED=YES
STAGE13_STARTED=NO
RELEASE_APPROVED=NO
```

**Etapa 12 concluída no escopo aprovado.** O fechamento final está ancorado em
`fc81c2ea10e751c15a39627d462ddfff390eeb04` e `31688307089`; não autoriza
release, executável ou instalador. O marcador histórico `STAGE13_STARTED=NO`
registra o instante daquele fechamento e não descreve a branch pré-merge atual.
