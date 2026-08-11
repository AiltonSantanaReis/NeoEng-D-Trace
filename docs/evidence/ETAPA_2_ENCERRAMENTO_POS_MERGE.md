# Evidência — Etapa 2: encerramento pós-merge

## Identificação

- Etapa: `2 — Inventário funcional e testes de caracterização`
- Pull request integrado: `#9`
- Commit da branch aprovada:
  `4d507cd443f407cfa0a861d8cc46ff146b9f643e`
- Merge commit:
  `d41093e706d3c8c555f64ef0c15c9ad40219a208`
- Primeiro pai:
  `287f6ef770ec1e65410a0a567dee2747f67c9f3d`
- Segundo pai:
  `4d507cd443f407cfa0a861d8cc46ff146b9f643e`
- Branch validada depois do merge: `main`
- Data do merge no GitHub: `2026-07-31T16:13:45Z`
- Responsável: Ailton Santana Reis

## Objetivo

Registrar permanentemente a validação executada depois da integração da PR
`#9` na `main`.

Este documento complementa:

- `ETAPA_2_INVENTARIO_FUNCIONAL_CARACTERIZACAO.md`;
- `ETAPA_2_EVIDENCE_MANIFEST.json`;
- `NeoEng-D-Trace_Etapa2_Raw_Evidence_Bundle.zip`.

O registro não encerra os riscos funcionais identificados na Etapa 2. Ele
encerra somente a etapa de inventário e caracterização, permitindo que as
correções sejam executadas nas etapas correspondentes do plano mestre.

## Estrutura do merge

A estrutura do merge foi confirmada:

- a PR foi criada sobre `main`;
- o HEAD revisado e aprovado foi
  `4d507cd443f407cfa0a861d8cc46ff146b9f643e`;
- a integração foi realizada por merge commit;
- o merge commit resultante foi
  `d41093e706d3c8c555f64ef0c15c9ad40219a208`;
- nenhum squash ou rebase substituiu o commit aprovado;
- `origin/main` passou a apontar para o merge commit esperado.

## Validação da PR antes do merge

Workflow da PR:

- nome: `Private validation`;
- execução: `#35`;
- Run ID: `30645019894`;
- evento: `pull_request`;
- commit:
  `4d507cd443f407cfa0a861d8cc46ff146b9f643e`;
- estado: `completed`;
- conclusão: `success`.

Jobs:

### Linux

- nome: `test`;
- Job ID: `91204152258`;
- conclusão: `success`.

Artefato:

- nome: `validation-linux-python-3.11`;
- Artifact ID: `8799071198`;
- tamanho: `22999 bytes`;
- digest informado pelo GitHub:
  `sha256:084860a9a51c506921f4721b78f4f9e1b68285e9e9813bdd077a0d9456603d46`.

### Windows

- nome: `test-windows`;
- Job ID: `91204152310`;
- conclusão: `success`.

Artefato:

- nome: `validation-windows-python-3.11`;
- Artifact ID: `8799088718`;
- tamanho: `369035 bytes`;
- digest informado pelo GitHub:
  `sha256:17bfbb8a79ed4f7fe03e5d6dddcdec3321913f5b0b2839175877581ad1784103`.

## CI da `main` depois do merge

Workflow pós-merge:

- nome: `Private validation`;
- evento: `push`;
- execução: `#36`;
- Run ID: `30646258120`;
- commit:
  `d41093e706d3c8c555f64ef0c15c9ad40219a208`;
- branch: `main`;
- estado: `completed`;
- conclusão: `success`.

### Linux

- job: `test`;
- Job ID: `91208257924`;
- conclusão: `success`.

Artefato:

- nome: `validation-linux-python-3.11`;
- Artifact ID: `8799557767`;
- tamanho: `22998 bytes`;
- expirado durante a validação: `false`;
- digest informado pelo GitHub:
  `sha256:c9ee9363877729e56dab048a9fda00c0d0df802d8c5885c935d729416219f54e`.

### Windows

- job: `test-windows`;
- Job ID: `91208257772`;
- conclusão: `success`.

Artefato:

- nome: `validation-windows-python-3.11`;
- Artifact ID: `8799571608`;
- tamanho: `369035 bytes`;
- expirado durante a validação: `false`;
- digest informado pelo GitHub:
  `sha256:997a2452a18e3962dd6623f7b50c71ccd1eaeb8e7d91d2336b0929f66f6c2ecc`.

## Cobertura pós-merge

Os relatórios de cobertura dos dois sistemas apresentaram o mesmo contrato:

- linhas válidas: `8849`;
- linhas cobertas: `4205`;
- taxa de linhas: `0.4752`;
- cobertura arredondada exibida pelo gate: `48%`;
- coverage.py: `7.15.2`.

A igualdade dos totais não prova equivalência absoluta entre sistemas, mas
confirma que a mesma suíte e o mesmo conjunto de fontes foram contabilizados
nos dois jobs aprovados.

## Ambiente registrado nos artefatos

Dependências centrais observadas nos dois artefatos:

- Poetry: `2.4.1`;
- pytest: `9.1.1`;
- pytest-cov: `7.1.0`;
- coverage: `7.15.2`;
- Black: `26.5.1`;
- Flake8: `7.3.0`;
- isort: `8.0.1`;
- mypy: `2.3.0`;
- NumPy: `2.2.6`;
- OpenCV Python: `4.12.0.88`;
- Pillow: `12.0.0`;
- Pydantic: `2.12.5`;
- pygltflib: `1.16.5`;
- PySide6: `6.10.1`;
- shiboken6: `6.10.1`.

Os arquivos `environment-freeze.txt` dos dois jobs vinculam a instalação ao
merge commit validado.

## Integridade das evidências permanentes

Os artefatos Windows da PR e da `main` continham os documentos e o pacote bruto
integrados pela Etapa 2.

Hashes aprovados:

- relatório consolidado, após normalização CRLF para LF:
  `8f0998eb3b14a488247ef87b8ea2d37c0be8451ab70625d86f2b15ba03de167f`;
- manifesto estruturado, após normalização CRLF para LF:
  `9ac1a22071299b5579b16be0908f1c8e4e1ffa9ceabd59bc0f2b1c86571f8926`;
- pacote bruto, sem normalização:
  `37fbff9bc0e07faa60c3c64e0735f7c7466b248875314833fcb446c3e162d7c8`.

A normalização foi aplicada somente aos arquivos textuais porque o checkout do
job Windows usa CRLF. O ZIP binário foi comparado byte a byte.

## Pacote da validação pós-merge

Arquivo:

`NeoEng-D-Trace_Etapa2_PostMerge_Main_20260731_132248.zip`

Propriedades:

- tamanho: `393672 bytes`;
- SHA-256:
  `3aed50811c30d5f49ed7d53695d9e04a73cbac6135121128ff1ac0519a288ffc`;
- membros: `10`;
- path traversal: não detectado;
- membros duplicados: não detectados;
- JSON de validação: íntegro;
- `SHA256SUMS.txt`: íntegro para os dois arquivos de resumo;
- cobertura Linux e Windows: reaberta e validada;
- pacote bruto original: hash exato preservado.

Arquivos de resumo internos:

- `post_merge_main_validation.json`:
  `5f7cba492ec8f02e362f4b8c042198deccda3e7cd9323594ac19664495cf96e1`;
- `post_merge_main_validation.txt`:
  `d92d0a21ad939be552ec3d3ad471a43202eacdd9405c24b81645fc8dd967542e`.

## Resultados da Etapa 2 preservados

A Etapa 2 registrou:

- inventário de `209` arquivos rastreados no snapshot original;
- `208` arquivos protegidos pelo manifesto naquele snapshot;
- `122` arquivos Python;
- `24966` linhas Python;
- `0` erros de sintaxe estática;
- `196` testes históricos coletados;
- `180` testes históricos aprovados;
- `16` falhas históricas preservadas e classificadas;
- caracterização de fluxos Qt atuais;
- caracterização de fluxos core;
- validação de persistência, CLI e GLB;
- sessão GUI controlada no Windows;
- identificação de bloqueadores e riscos residuais.

Depois da integração do relatório, manifesto e pacote bruto, o baseline passou
a proteger `211` arquivos.

## Riscos que permanecem abertos

O encerramento da Etapa 2 não encerra:

- `R-001` — persistência incompleta;
- `R-002` — Abrir/Salvar incompleto na UI;
- `R-003` — cobertura insuficiente de UI e ferramentas;
- `R-004` — Undo/Redo incompleto;
- `R-005` — exportação de colisão inconsistente;
- `R-006` — CLI com falso sucesso;
- `R-007` — Bézier e geometrias inválidas;
- `R-008` — APIs duplicadas;
- `R-011` — acoplamento ao Qt;
- `R-012` — segurança e limites;
- `R-013` — metadados do atlas fora dos limites.

Os riscos `R-009` e `R-010` permanecem encerrados pela Etapa 1.

## Limites da aprovação

Esta aprovação cobre:

- inventário estático;
- preservação e classificação da suíte histórica;
- caracterização dos fluxos atuais;
- registro dos bloqueadores;
- publicação das evidências;
- revisão da PR #9;
- CI Linux e Windows da PR;
- merge com HEAD esperado;
- CI Linux e Windows da `main`;
- integridade dos artefatos pós-merge.

Ela não declara:

- produto comercialmente pronto;
- ausência de bugs;
- persistência completa;
- Open/Save completo;
- Undo/Redo completo;
- exportadores completos;
- segurança concluída;
- cobertura integral;
- build final do Windows;
- release de produção.

## Ocorrências não bloqueantes

Permanecem registradas:

- avisos de depreciação de metadados do Poetry;
- `125` ocorrências no relatório não bloqueante do Flake8;
- cobertura global de aproximadamente `48%`;
- mypy sem verificação automática do corpo de funções não tipadas;
- fallback para CPU quando CuPy não está instalado;
- diferenças CRLF/LF esperadas no checkout Windows;
- módulos de UI e ferramentas com cobertura baixa ou zero.

## Decisão

**APROVADO — ETAPA 2 APTA AO ENCERRAMENTO FORMAL APÓS A INTEGRAÇÃO DESTE
REGISTRO E A VALIDAÇÃO FINAL DA `main`**

A evidência técnica necessária para o encerramento foi produzida e validada.

A Etapa 3 permanece não iniciada durante a integração deste registro. Ela
somente poderá começar depois que:

1. este documento, o manifesto atualizado, o índice de evidências, a matriz de
   riscos e o pacote pós-merge forem integrados por pull request;
2. os jobs Linux e Windows dessa pull request forem aprovados;
3. a integração usar o HEAD revisado;
4. o workflow da `main` depois desse merge também terminar com sucesso.

Depois desses requisitos, a Etapa 2 estará formalmente encerrada e a Etapa 3
poderá iniciar em branch própria criada a partir da `main` validada.
