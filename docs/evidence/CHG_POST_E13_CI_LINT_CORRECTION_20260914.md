# Registro de mudança — correção do lint do pacote de consolidação

**ID:** `CHG-POST-E13-CI-LINT-CORRECTION-20260914`
**Status:** `IN_PROGRESS`
**Data:** 2026-09-14
**Escopo:** correção de qualidade estática identificada pelo CI do PR #174
**Requisitos afetados:** `REQ-F12-QUALITY-GATES`
**Feature/componente:** `FEAT-QA-EVIDENCE-PACKAGE`, módulos de UI e ferramentas de evidência 3D
**Testes afetados:** `TEST-QA-EVIDENCE-COMMIT`, `TEST-QA-EVIDENCE-MANIFEST`

## Causa comprovada

O commit remoto `f24bd9b` passou pelos gates de baseline, manifesto de
evidências, lock de dependências e compilação, mas falhou no passo oficial
`Run full lint` do PR #174, execução `34881395619`, nos jobs Linux
`104101286454` e Windows `104101286209`.

O comando oficial foi:

```text
poetry run flake8 src tests tools app.py pack_for_ai.py
```

O log apontou somente violações `E501` de comprimento de linha nos arquivos
de autoria/UI, testes e geradores/validadores de asset 3D, além de um `F401`
para o import `os` não utilizado em `tools/create_reference_3d_asset.py`.
Não houve erro funcional, de compilação, de dependência ou de baseline nesse
run.

Na execução seguinte `34884085236`, o `flake8` passou nos dois ambientes, mas
o passo oficial `Check formatting` também foi reprovado nos jobs Linux
`104110264166` e Windows `104110264428`. O diff do Black identificou seis
arquivos que ainda precisavam da formatação canônica: o painel vetorial, os
testes de symlink, o teste de viewport, o teste do harness Unity e os dois
geradores/validadores de asset 3D.

Na execução `34885099513`, lint, Black e isort passaram nos dois ambientes,
mas `mypy src` falhou nos jobs Linux `104113680758` e Windows `104113680941`
com sete diagnósticos em `src/core/unity_integration.py` e
`src/ui/unity_integration_settings.py`. Os diagnósticos eram de inferência de
tipo no reuso de uma variável `str | None` como `Path` e de passagem de um
`str` genérico onde a API exige `ExecutableKind` (`"hub"` ou `"editor"`).

Na execução `34886148389`, lint e Black passaram nos dois ambientes e mypy não
foi alcançado por causa da falha anterior de isort. O único diagnóstico de
isort foi a ordem dos nomes na importação de `src/ui/unity_integration_settings.py`:
as constantes `UNITY_*` devem preceder `ExecutableKind` conforme o perfil
canônico do projeto.

Na execução `34887077924`, os gates anteriores passaram, mas o passo oficial de
cobertura funcional falhou nos jobs Linux `104120265823` e Windows
`104120265537`. O Linux executou `2651` testes (`2650 passed, 1 failed,
2 skipped`), atingiu `91.29%` de cobertura e reprovou a asserção de
`tests/test_reference_3d_asset.py::test_reference_asset_generation_and_contract`
(`mesh_count == 23`; observado `22`). O Windows reproduziu a mesma causa no
shard `test_post_e13_boundary_contracts.py`, encerrando com `839` testes,
`0` failures, `1` error e `2` skips. A falha não era de threshold: era um
defeito funcional no gerador do asset. O `parts.append(boot)` estava fora do
laço bilateral, portanto somente `Boot_R` era publicado e `Boot_L` era
silenciosamente perdido.

Na execução `34889646296`, os gates de baseline, evidências, lock, qualidade
estática, tipagem e teste funcional passaram até os gates finais, mas ainda
houve dois bloqueios independentes. No Linux (`104128799195`), a suíte completa
passou, porém a política integrada reprovou a cobertura de branches em
`84.92%`, abaixo do mínimo previamente definido de `85.00%`. No Windows
(`104128799376`), o executor encerrou `test_post_e13_boundary_contracts.py`
sem erro e falhou em
`tests/test_legacy_phase4_contracts.py::`
`test_phase4_real_segment_timeout_cancels_and_discards_late_result`:
o teste observou `0` payloads onde esperava `1`. O log oficial identifica uma
condição de corrida: o worker de timeout curto podia publicar o sinal antes de
o teste registrar o observador. O prazo não era estendido nem o teste era
ignorado; a falha ocorreu no ciclo de entrega do resultado terminal.

Na execução `34892412623`, a correção do ciclo assíncrono foi confirmada pelo
Windows: `247/247` arquivos, `2654` testes, `0` falhas, `0` erros e `2` skips
controlados, sem repetição do erro de payload. O Linux também concluiu a suíte,
com `2652 passed` e `2 skipped`; os dois ambientes, contudo, reprovaram somente
na política integrada de branches, com `84.96%` no Linux (`104128075383`) e
`84.94%` no Windows (`104138075326`), abaixo do mínimo não alterado de
`85.00%`. A execução permanece `IN_PROGRESS` até uma execução oficial superar
esse gate.

Na execução `34894893066`, o novo contrato de seleção encontrou uma falha de
asserção em ambos os ambientes durante `test_unity_integration_flow.py`: o
teste comparava a palavra inglesa `missing`, embora a tradução efetiva do
estado fosse `Not found`. O log Windows confirmou `11 passed, 1 failed`; o
Linux também falhou no passo de testes antes de produzir cobertura. A falha é
corrigida ajustando a expectativa para a saída observável e o caminho
selecionado, sem alterar a tradução nem o comportamento do diálogo.

Na execução `34897091060`, Linux passou a suíte completa com `2653 passed` e
`2 skipped`, a cobertura total foi `91.36%` e a política integrada passou. No
Windows, os `247/247` arquivos e `2655` testes passaram, com `0` falhas, `0`
erros e `2` skips controlados; a única reprovação foi a política integrada,
que observou `9414/11076` branches cobertos (`84.99%`) contra o mínimo fixo de
`85.00%`. A causa não foi funcionalidade quebrada: faltava executar um caminho
de erro do diálogo Unity, mantendo a mudança `IN_PROGRESS` até nova execução.

Na execução `34899805281`, o Linux executou `2653 passed` e `2 skipped`, mas
o teste recém-adicionado falhou ao assumir que a mensagem de Hub ausente
conteria literalmente `not found`; a mensagem real é a instrução localizada
para selecionar ou instalar o Unity Hub. No Windows, a execução nem chegou à
suíte: o passo de sincronização das dependências terminou com
`ReadTimeoutError`/`ConnectionError` de rede. Ambos os resultados ficam
preservados como evidência; a correção da asserção não altera o comportamento
do produto e a nova execução deverá repetir os gates completos.

Na execução `34900838985` (`b8dc409`), Linux passou integralmente. Windows
chegou a `239/247` arquivos e falhou somente no novo cenário de Hub ausente:
a descoberta automática encontrou um Hub instalado no runner, portanto a
mensagem observada foi `Could not open Unity Hub`, não `Unity Hub not found`.
O teste agora fornece um caminho temporário explicitamente inexistente,
verificado por `exists()`, antes de tentar abrir o Hub. Isso preserva a
descoberta real do produto e torna a entrada do teste independente do software
instalado no runner. A sincronização com `main` incorpora somente o histórico
do merge #173; o diff de conteúdo staged desse merge foi vazio.

Na execução `34905321843` (`e2ef42d`), a política de higiene documental
detectou um caminho pessoal absoluto no registro do ambiente local deste
documento. Linux encerrou com `2653 passed`, `1 failed` e `2 skipped`;
Windows interrompeu no arquivo `129/247`, com `1307` testes, `1` falha,
`0` erros e `2` skips. A referência foi corrigida para um caminho relativo
à raiz do projeto, preservando as versões e os resultados observados.
O teste de higiene e suas regras permanecem inalterados.

## Correção aplicada

- Quebra mecânica de expressões, chamadas, literais e mensagens longas para o
  limite configurado de 88 colunas.
- Aplicação do diff indicado pelo `black --check --diff`, incluindo somente
  agrupamento de expressões, normalização de linhas em testes controlados e
  espaços em branco.
- Separação explícita entre o valor textual de ambiente e a raiz `Path` do
  editor, além da tipagem dos métodos UI com o alias `ExecutableKind`; o fluxo
  de descoberta e seleção permanece o mesmo.
- Reordenação da importação Unity conforme o diff oficial do isort; nenhum
  símbolo foi adicionado ou removido.
- Correção da publicação bilateral de botas em `build_parts`: o registro de
  cada bota agora ocorre dentro do laço `L/R`, restaurando as duas malhas e o
  contrato de 23 componentes; o teste também fixa explicitamente a presença de
  `Boot_L` e `Boot_R`.
- Início adiado por um turno do Qt para o worker de timeout curto, permitindo
  que consumidores legítimos registrem seus observadores antes da emissão do
  payload terminal; o deadline continua ancorado no instante de criação do
  worker e não é ampliado.
- Ampliação dos contratos de preflight do Unity para cobrir rejeição de caminho
  acima do limite, executável inválido e deduplicação de candidatos vindos do
  ambiente e do `PATH`; esses testes exercitam comportamento defensivo real e
  não alteram a política de cobertura.
- Inclusão de um teste funcional de recuperação do diálogo Unity para Hub não
  encontrado, falha de inicialização do processo e falha de abertura de URL;
  esses caminhos são observáveis pelo usuário e cobrem a lacuna de branch sem
  mudar o threshold nem introduzir skips.
- Remoção somente do import `os` comprovadamente não utilizado.
- Renomeação de um identificador de teste excessivamente longo, sem mudar o
  cenário, as asserções ou o contrato verificado.
- Nenhuma regra de lint foi relaxada, nenhum `noqa`, `skip`, `xfail`, filtro ou
  bypass foi adicionado.
- Nenhum arquivo de produto, evidência histórica ou artefato foi removido.

## Validação local disponível

PASS:

```text
git diff --check
python -m compileall -q -f app.py src tests pack_for_ai.py tools
verificação de comprimento: nenhum arquivo tocado possui linha > 88 colunas
tools/baseline_integrity.py --verify --git-blob
Baseline verified: 3902 files
```

PENDENTE DE EVIDÊNCIA: a execução local de `poetry run flake8`,
`poetry run black --check`, `poetry run isort --check-only`, `poetry run mypy`
e dos testes pytest não está disponível neste
checkout porque `poetry`, Black e pytest não estão instalados. O novo CI deverá
executar os comandos oficiais nos dois ambientes e será a prova final desta
mudança; ausência local não será tratada como sucesso.

Atualização da retomada: foi localizado o ambiente existente
`.venv/Scripts/python.exe` na raiz principal do projeto, com Python
3.11.9, pytest 9.1.1 e PySide6 6.10.1. A execução focada
`-m pytest tests/test_unity_integration_flow.py` passou os 13 testes em 5,61 s;
Black e isort também passaram para esse arquivo. Essa evidência é
`DIAGNOSTIC_ONLY`, anterior ao CI completo, e corrige a limitação de descoberta
do ambiente relatada acima. Não houve ativação de licença ou abertura real do
Hub/navegador nessa execução de contratos.

## Impacto e não regressão

A mudança combina correções de qualidade estática com correções funcionais
localizadas no gerador de asset de referência, no ciclo de entrega assíncrona
do laço magnético e nos contratos defensivos de preflight do Unity. Ela não
altera schemas, persistência, renderer, UI, seleção oficial de testes ou limites
de cobertura; restaura a bota esquerda já prevista, elimina a corrida de
observadores no timeout e aumenta a eficácia dos testes de descoberta. O
baseline será regenerado a partir do conteúdo staged e verificado contra blobs
Git para incluir os hashes dos arquivos corrigidos.

## Dependências documentais

- [Governança de Integridade, Execução e Antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Índice Documental Ativo Canônico](../INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md)
- [Registro Canônico de IDs](../REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml)
- `baseline_manifest.json`
- `CHG_POST_E13_BASELINE_RECONCILIACAO_20260914.md`
