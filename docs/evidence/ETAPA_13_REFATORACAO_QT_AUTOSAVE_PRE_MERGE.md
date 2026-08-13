# Evidência — Etapa 13: refatoração Qt e autosave pré-merge

## Identificação

- data: 13 de agosto de 2026;
- branch: `etapa-13-refatoracao-qt-autosave`;
- base integrada da `main`: `fc81c2ea10e751c15a39627d462ddfff390eeb04`;
- commits técnicos: `2d8543264e98e73440da53900d0e476fe8bb1b05`,
  `46f090f96c25f44d546764b3bc9c9ca5f119fa11` e
  `58ef2ac5091683ac81a9ee93a6ca6db2e617dd63`;
- estado desta evidência: aprovado localmente, ainda não integrado;
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

## Limitações e riscos residuais

- os testes locais e as provas externas não equivalem a integração na `main`;
- o CI da PR ainda precisa reproduzir Linux e Windows, cobertura, legado,
  proveniência e higiene recursiva dos artefatos;
- a margem de branches continua pequena, de `0,02` ponto percentual;
- o autosave não substitui backups nem garante recuperação diante de falha do
  dispositivo ou corrupção fora do processo;
- `R-011` permanece aberto até merge autorizado e CI pós-merge auditado;
- Etapa 14 não foi iniciada;
- build standalone, instalador e validação real de release não foram aprovados.

## Rollback

O rollback técnico é realizado revertendo, em ordem inversa, os commits
`58ef2ac5091683ac81a9ee93a6ca6db2e617dd63`,
`46f090f96c25f44d546764b3bc9c9ca5f119fa11` e
`2d8543264e98e73440da53900d0e476fe8bb1b05`. Nenhum arquivo de projeto do
usuário precisa ser migrado para desfazer a funcionalidade, pois o autosave é
um envelope separado do schema `.ndtproj` v1.

## Decisão

**APROVADO LOCALMENTE / NÃO INTEGRADO.** A implementação está pronta para PR e
auditoria de CI, mas isso não encerra `R-011`, não conclui a Etapa 13 e não
aprova release.

```text
BASE_MAIN=fc81c2ea10e751c15a39627d462ddfff390eeb04
TECHNICAL_HEAD=58ef2ac5091683ac81a9ee93a6ca6db2e617dd63
LOCAL_TESTS_PASSED=951
LINE_COVERAGE=11578/12469
BRANCH_COVERAGE=3370/3964
MODULES_BELOW_30=0
LEGACY_RECONCILIATION=27/27
LOCAL_VALIDATION_STATUS=ACCEPTED
PRE_MERGE_CI_STATUS=NOT_RUN
R011_CLOSED=NO
STAGE13_COMPLETED=NO
STAGE14_STARTED=NO
RELEASE_APPROVED=NO
```
