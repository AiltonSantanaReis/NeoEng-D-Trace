# Evidência — Etapa 13: refatoração Qt e autosave pré-merge

## Identificação

- data: 13 de agosto de 2026;
- branch: `etapa-13-refatoracao-qt-autosave`;
- base integrada da `main`: `fc81c2ea10e751c15a39627d462ddfff390eeb04`;
- commits técnicos: `2d8543264e98e73440da53900d0e476fe8bb1b05`,
  `46f090f96c25f44d546764b3bc9c9ca5f119fa11` e
  `58ef2ac5091683ac81a9ee93a6ca6db2e617dd63`;
- commit corretivo: `426cef118fdb0a334e639ec962b2e514cfd59b0a`;
- estado desta evidência: aprovado pré-merge, ainda não integrado;
- release: não aprovada.

## Objetivo e escopo

A Etapa 13 reduz o acoplamento direto da janela principal, move processamento
numérico para uma camada independente de Qt e implementa autosave local com
recuperação explícita. O escopo não inclui build standalone, instalador ou
aprovação de release, que permanecem na Etapa 14.

## Alterações verificadas

- `DocumentSession` concentra assinatura de estado, caminho de projeto,
  normalização e rebase de referências;
- `AutosaveStore` usa envelope versionado estrito, leitura limitada, escrita
  atômica, fingerprint SHA-256 do projeto-fonte e quarentena de snapshot
  inválido;
- `AutosaveCoordinator` concentra timer, mensagens, decisão de recuperação e
  preservação de recuperação adiada;
- conversão para `QImage` e traduções da janela foram extraídas da lógica
  central;
- `ViewProcessor` oferece processamento numérico sem import direto de Qt;
- `main_window.py` caiu de `1.306` para `1.175` linhas físicas;
- a busca estrutural e o teste contratual não encontraram imports diretos de
  PySide6 fora de `src/ui`, `src/tools` e do adaptador de inicialização.

## Contrato do autosave

- ativado por padrão, intervalo padrão de `60` segundos e faixa aceita de
  `15` a `3.600` segundos;
- arquivo local em diretório de estado específico da plataforma;
- gravação atômica e leitura limitada;
- snapshot inválido é preservado em quarentena quando possível;
- recuperação exige decisão explícita;
- escolha de decidir depois preserva o snapshot e bloqueia sobrescrita;
- projeto-fonte alterado ou ausente desanexa o caminho recuperado e exige
  `Salvar como`;
- salvamento explícito bem-sucedido remove o snapshot da sessão atual;
- nenhuma dependência de nuvem foi adicionada.

## Validação local no SHA limpo

Ambiente: Windows 11, Python `3.11.9`, Qt em modo offscreen quando aplicável e
dependências travadas pelo `poetry.lock`.

No commit `58ef2ac5091683ac81a9ee93a6ca6db2e617dd63`, com árvore de trabalho
limpa antes da execução:

- suíte oficial: `951 passed`;
- linhas: `11.578/12.469` (`92,85%`);
- branches: `3.370/3.964` (`85,02%`);
- cobertura combinada: `90,96%`;
- SHA-256 do `coverage.xml` dessa execução:
  `473d6884a3d1a12e9752568b7b08a7dc61bdf59f60e83d20ee6d5ff35a274df7`;
- módulos abaixo de 30% de linhas: zero;
- baseline: `334` arquivos, verificado antes e depois dos gates relevantes;
- testes focais finais da Etapa 13: `22 passed`.

Após adicionar o pacote documental e dois contratos de estado, a suíte integral
aprovou `953 passed`, o baseline passou a `335` arquivos e as métricas do
código-fonte permaneceram exatamente inalteradas.

## Gates estáticos e dependências

- Black no escopo oficial: aprovado em `160` arquivos;
- isort no escopo oficial: aprovado;
- mypy: zero problemas em `80` arquivos-fonte;
- Bandit: zero achados de alta severidade no escopo vigente;
- pip-audit: nenhuma vulnerabilidade conhecida nas dependências auditáveis;
- o pacote local do próprio projeto não existe no índice público e, por isso,
  foi explicitamente informado como não auditável por essa ferramenta.

## Suíte legada preservada

No mesmo commit limpo:

- `196` testes executados;
- `27` falhas históricas;
- `27/27` falhas esperadas conciliadas;
- zero falhas inesperadas;
- zero falhas esperadas ausentes;
- zero erros e zero skips;
- reconciliação: `passed`;
- `working_tree_dirty=false`.

As falhas legadas não foram apagadas nem convertidas artificialmente em
sucesso; permanecem explicitamente registradas pelo manifesto de reconciliação.

## Provas fora do pytest

### Timer Qt real

Uma instância real de `QApplication`, `QEventLoop` e `QTimer`, em modo
offscreen, recebeu uma alteração após a inicialização da janela. Resultado:

- timer ativo: `true`;
- snapshot criado: `true`;
- objeto recuperado pela API pública: `timer-object`.

### Persistência entre processos

Um processo gravador (`PID 25892`) criou o snapshot e outro processo leitor
(`PID 27396`) o carregou e aplicou a uma nova cena. Resultado:

- processos distintos: `true`;
- tamanho do snapshot: `1.187` bytes;
- objeto recuperado: `cross-object`;
- fingerprint do projeto-fonte ainda correspondente: `true`;
- bytes do projeto-fonte inalterados: `true`.

Os diretórios temporários foram eliminados ao fim da execução. Os PIDs apenas
demonstram separação de processos naquela execução e não são identificadores
reutilizáveis.

## Falhas encontradas e correções

1. Os primeiros testes falharam porque os novos módulos ainda não existiam;
   a implementação foi criada antes de qualquer alegação de sucesso.
2. O parser estrito rejeitou timestamp ISO válido gerado pelo próprio
   serializador; o parse explícito e o requisito de timezone foram adicionados.
3. A primeira extração elevou `main_window.py` de `1.306` para `1.409` linhas;
   a regressão estrutural foi rejeitada e novas responsabilidades foram
   extraídas até `1.175` linhas.
4. Uma suíte integral teve `939 passed, 1 failed`: o launcher quebrava um mock
   histórico ao encaminhar um argumento novo; a compatibilidade do construtor
   foi restaurada.
5. A revisão encontrou risco de apagar silenciosamente o snapshot quando a
   pessoa escolhia decidir depois e fechava uma janela limpa; o estado adiado
   passou a preservar os bytes e ganhou regressão automatizada.
6. A primeira medição de branches ficou em `84,71%`; medições intermediárias
   de `84,84%` e `84,91%` também foram rejeitadas. Casos comportamentais de
   falha, plataforma, metadados e fingerprint elevaram o resultado a `85,02%`.
7. A primeira prova externa não gravou porque o harness criou o objeto antes
   da captura do estado limpo; a segunda acessou uma propriedade inexistente
   do schema. O harness foi corrigido para mutar depois da inicialização e usar
   a API pública `apply_to`; somente a terceira execução foi aceita.

## Primeiro CI da PR — verde, mas rejeitado

A PR draft `#51` executou o workflow `31693639653` no merge sintético
`0f43ef78e47b60898983ed2fa4c82f6d3fdb2365`, cujos pais eram a base
`fc81c2ea10e751c15a39627d462ddfff390eeb04` e o HEAD fonte
`63f1ccfb5e5ff6ed295a5f169746c2d4c494cb38`.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `94426333019` | `success` | `9178445539` | `d3b8657963b3e0bbef4e495443d8f80fa8313f0eeae338159010474fc23de507` |
| Windows | `94426333153` | `success` | `9178479814` | `c39ce4650402f1d98ee71ce30025ead32835ba7651b7fab4591e4dbf3257e693` |

Apesar dos jobs verdes e de zero anotações, a execução foi rejeitada após
inspeção dos `coverage.xml`:

- Linux: `11.576/12.469` linhas e `3.370/3.964` branches;
- Windows: `11.578/12.469` linhas e `3.370/3.964` branches;
- diferenças exatas: linhas `301` e `302` de `persistence/autosave.py`;
- hashes dos relatórios: Linux
  `53bc1dcc1a64f9a9b96efde08267c990222a4b2260fbf3ed545a417f177016e1`
  e Windows
  `cf73ac09bfe74027f7bb9c3e0db2688492534c6151da404982832641c26940ec`.

A auditoria também confirmou:

- `953 passed` nos dois sistemas;
- merge sintético e HEAD fonte separados corretamente no resumo legado;
- `196` testes legados, `27/27` conciliados e zero inesperados;
- `56` documentos comparados: `53` iguais byte a byte e `3` iguais após
  normalização exclusiva de CRLF/LF;
- `62` arquivos, `1.421` payloads e `1.359` entradas aninhadas examinados
  recursivamente, sem referência proibida, caminho pessoal ou checksum
  inconsistente.

### Causa raiz e correção

`Path.rename` recusa um destino existente no Windows, porém substitui esse
destino em sistemas POSIX. O teste que produzia uma segunda quarentena cobria
o `FileExistsError` apenas no Windows; no Linux, o snapshot corrompido anterior
era sobrescrito. O CI estava verde porque não existia asserção que preservasse
o conteúdo anterior.

O commit `426cef118fdb0a334e639ec962b2e514cfd59b0a` reserva o nome com
`O_EXCL` e só então move atomicamente o snapshot para o placeholder criado
pelo próprio processo. A regressão exige que a quarentena anterior permaneça
intacta e que a nova use o sufixo `.1` em qualquer sistema.

Validação local limpa do corretivo:

- `953 passed`;
- `11.581/12.478` linhas (`92,81%`);
- `3.370/3.964` branches (`85,02%`);
- cobertura combinada `90,93%`;
- baseline `335`;
- legado `196`, reconciliação `27/27`, zero inesperados;
- Black, isort, mypy, Bandit e auditoria de dependências aprovados.

## CI corretivo da PR — aceito após auditoria

O workflow corretivo `31695151223` validou o HEAD fonte
`c2e21374f2669248da55c6e77110f2b1f80164b2` pelo merge sintético
`e48d88179a74738f64619dcd54714e3d420ae8d5`, com pais
`fc81c2ea10e751c15a39627d462ddfff390eeb04` e
`c2e21374f2669248da55c6e77110f2b1f80164b2`, e árvore
`9b3ac479adf60f765a83019b4375a0b904b09998`.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `94431148305` | `success` | `9179036011` | `0479561d472a2ed9884a61c575c4e4fadd4968720d4ab98ef595fcf9b1fb0643` |
| Windows | `94431148369` | `success` | `9179071334` | `564042b66e97817b6b28a0bc9887dc781e73b8f26a4cf422818a1e7e35db668d` |

A aceitação não se baseou apenas no estado verde:

- zero anotações nos dois jobs;
- `953 passed` em Linux e Windows;
- `11.581/12.478` linhas e `3.370/3.964` branches nos dois sistemas;
- zero diferenças entre pontos de cobertura e zero módulos abaixo de 30%;
- SHA-256 dos `coverage.xml`: Linux
  `d7b775202c265fb1312ecbcbd54d4233da65f40404a74da5c65a638d7b8b2b4e`
  e Windows
  `ff06944f4299ddd2d9d9963ee17d9e06af4ec40391a0d4fa621f80159a547527`;
- legado schema v4: integridade aprovada, `196` testes, `27/27` conciliados,
  zero inesperados, zero ausentes, zero erros, zero skips e árvore limpa;
- `56` documentos comparados: `53` idênticos byte a byte e `3` equivalentes
  após normalização exclusiva de CRLF/LF;
- `62` arquivos, `1.421` payloads e `1.359` entradas aninhadas examinados
  recursivamente, sem violações de referência, caminho pessoal ou checksum.

O CI corretivo foi aceito. A Etapa 13 continua não integrada e `R-011`
continua aberto até merge autorizado e CI pós-merge auditado.

## Limitações e riscos residuais

- os testes locais e as provas externas não equivalem a integração na `main`;
- a validade deste registro depende de seu próprio CI da PR antes da revisão
  final;
- a margem de branches continua pequena, de `0,02` ponto percentual;
- o autosave não substitui backups nem garante recuperação diante de falha do
  dispositivo ou corrupção fora do processo;
- `R-011` permanece aberto até merge autorizado e CI pós-merge auditado;
- Etapa 14 não foi iniciada;
- build standalone, instalador e validação real de release não foram aprovados.

## Rollback

O rollback técnico é realizado revertendo, em ordem inversa, os commits
`426cef118fdb0a334e639ec962b2e514cfd59b0a`,
`58ef2ac5091683ac81a9ee93a6ca6db2e617dd63`,
`46f090f96c25f44d546764b3bc9c9ca5f119fa11` e
`2d8543264e98e73440da53900d0e476fe8bb1b05`. Nenhum arquivo de projeto do
usuário precisa ser migrado para desfazer a funcionalidade, pois o autosave é
um envelope separado do schema `.ndtproj` v1.

## Decisão

**APROVADO PRÉ-MERGE / NÃO INTEGRADO.** O CI corretivo foi aceito após
auditoria dos artefatos, mas isso não encerra `R-011`, não conclui a Etapa 13
e não aprova release.

```text
BASE_MAIN=fc81c2ea10e751c15a39627d462ddfff390eeb04
TECHNICAL_HEAD=58ef2ac5091683ac81a9ee93a6ca6db2e617dd63
LOCAL_TESTS_PASSED=951
LINE_COVERAGE=11578/12469
BRANCH_COVERAGE=3370/3964
MODULES_BELOW_30=0
LEGACY_RECONCILIATION=27/27
LOCAL_VALIDATION_STATUS=ACCEPTED
PRE_MERGE_CI_RUN=31693639653
PRE_MERGE_CI_STATUS=REJECTED
CORRECTIVE_HEAD=426cef118fdb0a334e639ec962b2e514cfd59b0a
CORRECTIVE_LOCAL_TESTS_PASSED=953
CORRECTIVE_LINE_COVERAGE=11581/12478
CORRECTIVE_BRANCH_COVERAGE=3370/3964
CORRECTIVE_CI_SOURCE_HEAD=c2e21374f2669248da55c6e77110f2b1f80164b2
CORRECTIVE_CI_MERGE=e48d88179a74738f64619dcd54714e3d420ae8d5
CORRECTIVE_CI_RUN=31695151223
CORRECTIVE_CI_LINUX_ARTIFACT=9179036011
CORRECTIVE_CI_WINDOWS_ARTIFACT=9179071334
CORRECTIVE_CI_STATUS=ACCEPTED
R011_CLOSED=NO
STAGE13_COMPLETED=NO
STAGE14_STARTED=NO
RELEASE_APPROVED=NO
```
