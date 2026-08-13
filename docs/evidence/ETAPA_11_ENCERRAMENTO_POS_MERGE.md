# Evidência — Encerramento pós-merge da Etapa 11

## Identificação

- data: 11 de agosto de 2026;
- PR funcional: `#45`;
- HEAD documental final: `3cd1616fed60101bbd809f530667227a5006c409`;
- merge funcional: `2a38b89e542390b3b4396a88d9a416f3695caadc`;
- release: não aprovada.
- PR de fechamento formal: `#46`;
- HEAD de fechamento formal: `89d13d7e3ee7a4cd926912aed8e3ae7e3d5505bb`;
- merge de fechamento formal: `a22a90088220e586c3382c3ed5dc1075a3ff7e6b`.

## Objetivo

Encerrar `R-003` e a Etapa 11 depois de comprovar a integração dos seis pacotes
e a reprodução das metas globais de cobertura no CI pós-merge ligado ao SHA
resultante da `main`. A transição formal foi autorizada explicitamente após a
auditoria completa das evidências.

## Validação local consolidada

No Windows, Python 3.11.9 e Qt offscreen, o estado final reproduziu:

- `877 passed` na suíte oficial;
- `10.787/11.628` linhas cobertas: `92,77%`;
- `3.147/3.700` branches cobertos: `85,05%`;
- cobertura combinada: `90,91%`;
- zero módulos abaixo de 30% em linhas ou branches mensuráveis;
- baseline de 319 arquivos verificado;
- mypy sem problemas em 70 arquivos;
- nenhuma vulnerabilidade conhecida nas dependências auditáveis;
- zero achados de severidade alta no código-fonte.

A suíte legada local executou 196 testes e reconciliou exatamente as 27
divergências previstas, sem falhas inesperadas, ausentes, erros ou testes
ignorados.

## CI pré-merge documental aceito

O workflow `31489594270` validou o merge sintético
`24c578df87f50370f95df6eb2b25df49a2c7fb05`, cujos pais eram a base
`5e88c8d548e2b60612601f83e1bf24aeb91081bb` e o HEAD fonte
`3cd1616fed60101bbd809f530667227a5006c409`. A árvore do merge sintético era
idêntica à árvore do HEAD fonte.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `93772672006` | `success` | `9100512735` | `14c23eecab8def2117f045ece1d7581243e8a23f674bf7b92c4117a95ba26ba9` |
| Windows | `93772672083` | `success` | `9100539788` | `b0a566aa3e010fc269324e23cf7524ee83ec1f6c046e5da8a0642487a269f6c2` |

Os dois jobs reproduziram 877 testes, cobertura exata, baseline 319, tipagem e
portões de segurança. A auditoria recursiva examinou 129 ZIPs, 1.417 payloads
e 1.137 payloads textuais, sem referência proibida nem caminho pessoal local.

## Integração funcional

A PR `#45` foi retirada do modo draft mediante autorização explícita e
mesclada em `2a38b89e542390b3b4396a88d9a416f3695caadc`. O merge possui como pais a
base `5e88c8d548e2b60612601f83e1bf24aeb91081bb` e o HEAD documental
`3cd1616fed60101bbd809f530667227a5006c409`.

Nove branches antigas, todas associadas a PRs já mescladas e integralmente
contidas na base, foram removidas dos refs locais e remotos por utilizarem
nomenclatura vedada. Nenhum ref ativo com essa nomenclatura permaneceu.

## Validação pós-merge aceita

O workflow `31491221322` foi disparado por `push` no merge
`2a38b89e542390b3b4396a88d9a416f3695caadc`.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `93777947832` | `success` | `9101145671` | `0f6b2638e1302722293176625eabed1c3c5ebde3c4a2e17cce3cdde8b1266780` |
| Windows | `93777947784` | `success` | `9101167058` | `01379f3c392d0983793281a1952ffb7b0b67ea4716c22d29a0f7f9d93ab4110b` |

A auditoria independente confirmou:

- zero anotações nos dois check-runs;
- `877 passed` em Linux e Windows;
- `10.787/11.628` linhas e `3.147/3.700` branches nos dois sistemas;
- cobertura combinada `90,91%` e XMLs semanticamente idênticos ao resultado local;
- baseline de 319 arquivos aprovado antes e depois dos testes;
- resumo legado schema v4 com commit testado e HEAD fonte iguais ao merge;
- 196 testes históricos, reconciliação `27/27`, zero inesperadas e zero ausentes;
- 129 ZIPs, 1.417 payloads e 1.137 payloads textuais examinados recursivamente;
- zero referências proibidas e zero caminhos pessoais locais;
- digests dos ZIPs brutos idênticos aos publicados pelo GitHub.

## Fechamento formal e auditoria pós-merge final

A PR `#46` integrou o fechamento documental no merge
`a22a90088220e586c3382c3ed5dc1075a3ff7e6b`. O workflow pós-merge
`31495971632`, disparado por `push` nesse SHA, foi aceito somente após
inspeção independente dos jobs, logs, digests e conteúdo recursivo.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `93793644185` | `success` | `9103009810` | `b641039fc068950dfa8b9fe3a161136ffd7ade8d2ba9fde8c93142665bfcafba` |
| Windows | `93793644105` | `success` | `9103050616` | `95e95de0b5fdcaa1795adb8565e23827ce9b9b93c88bd945711390aba46271f0` |

A auditoria final confirmou:

- zero anotações nos dois check-runs;
- `877 passed` em Linux e Windows;
- `10.787/11.628` linhas e `3.147/3.700` branches nos dois sistemas;
- baseline de 320 arquivos e mypy sem problemas em 70 arquivos;
- nenhuma vulnerabilidade conhecida nas dependências auditáveis;
- 196 testes históricos, reconciliação `27/27`, zero inesperadas e zero ausentes;
- commit testado e HEAD fonte iguais ao merge, com worktree limpa;
- 129 ZIPs e 1.418 payloads examinados recursivamente;
- zero referências proibidas e zero caminhos pessoais locais;
- hashes dos ZIPs brutos idênticos aos digests publicados pelo GitHub.

Esta segunda validação pós-merge é necessária porque a PR `#46` alterou os
marcadores formais de encerramento e elevou a baseline de 319 para 320 arquivos.

## Decisão e riscos residuais

- `R-003` está encerrado no escopo aprovado;
- as metas globais 90% de linhas e 85% de branches foram superadas;
- a Etapa 11 está concluída no escopo aprovado;
- `R-012` permanece aberto; a Etapa 12 foi iniciada para auditar e implementar
  limites operacionais, sem aprovação funcional até este ponto;
- `R-011` permanece aberto para a refatoração Qt protegida da Etapa 13;
- autosave, build, instalador e validações reais de release permanecem para as
  Etapas 13 e 14;
- release continua não aprovada.

## Marcadores auditáveis

```text
FUNCTIONAL_PR=45
FUNCTIONAL_PR_MERGED=YES
INTEGRATION_COMMIT=2a38b89e542390b3b4396a88d9a416f3695caadc
POST_MERGE_CI_RUN=31491221322
POST_MERGE_CI_STATUS=ACCEPTED
LOCAL_TESTS_PASSED=877
LINE_COVERAGE=10787/11628
BRANCH_COVERAGE=3147/3700
COVERAGE_TARGETS_MET=YES
R003_CLOSURE_RECOMMENDED=YES
R003_CLOSED=YES
STAGE11_COMPLETED=YES
CLOSURE_PR=46
CLOSURE_HEAD=89d13d7e3ee7a4cd926912aed8e3ae7e3d5505bb
CLOSURE_MERGE=a22a90088220e586c3382c3ed5dc1075a3ff7e6b
FINAL_POST_MERGE_CI_RUN=31495971632
FINAL_POST_MERGE_CI_STATUS=ACCEPTED
STAGE12_STARTED=YES
STAGE12_COMPLETED=NO
R012_CLOSED=NO
RELEASE_APPROVED=NO
```

**Etapa 11 concluída no escopo aprovado.** O encerramento não autoriza release,
executável ou instalador.
