# Evidência — Etapa 14: encerramento técnico pós-merge

## Identificação

- PR integrada mais recente: `#58`.
- Merge commit: `f15193a55d1a5de0c7031f5bab656107302eee1b`.
- CI pós-merge: `31905237922`, evento `push`, `headSha` igual ao merge.
- Commit-fonte do build MSI: `828cf626b7ce382c360723b1be10c4ce718c4187`.
- Data da auditoria: 15 de agosto de 2026.
- Escopo: fechamento técnico da Etapa 14; não é aprovação de release pública.

## Evidências pós-merge auditadas

O CI executou os jobs Linux e Windows, ambos com conclusão `success`. Os logs
registram:

- `982 passed` em cada sistema;
- `11.621/12.523` linhas cobertas (`92,80%`);
- `3.382/3.978` branches cobertos (`85,02%`);
- cobertura total `90,92%`, com política mínima de linhas, branches e módulos aprovada;
- mypy sem erros em 80 arquivos;
- pip-audit sem vulnerabilidades conhecidas;
- Bandit sem achados de alta severidade;
- baseline íntegra com 359 arquivos.

A comparação dos `coverage.xml` mostrou 80 módulos em cada plataforma e zero
divergências ponto a ponto em taxas, linhas e branches.

## Legado e proveniência

A suíte histórica executou 196 testes e apresentou 27 falhas brutas. O relatório
não mascarou essas falhas: `raw_test_status=failed`. O gate aceitou a execução
somente porque as 27 falhas coincidiram exatamente com as 27 assinaturas
reconciliadas, sem falhas inesperadas, sem expectativas ausentes e com 17
referências de testes substitutos coletadas.

O relatório pós-merge registrou:

- `tested_commit=f15193a55d1a5de0c7031f5bab656107302eee1b`;
- `source_head_commit=f15193a55d1a5de0c7031f5bab656107302eee1b`;
- `working_tree_dirty=false`.

O `project_commit` antigo no manifesto da reconciliação é a âncora histórica
da suíte preservada; não substitui os campos de proveniência do relatório real
da execução. Essa distinção foi conferida no código do gate e nos testes de
contrato.

## Conteúdo dos artefatos

- 60 arquivos de evidência do artefato Windows coincidiram byte a byte com a
  árvore versionada;
- 1.431 payloads e 127 arquivos compactados foram examinados pelo gate, sem
  referências proibidas;
- artefato Linux: ID `9252167708`, digest
  `sha256:429f1b0fc498b7ecc8cbe2e4ce7472c1779e0a42871b55278a5500860cb013f3`;
- artefato Windows: ID `9252176851`, digest
  `sha256:8520f7ad9adcfa1fd93fe02426a1b8cff1320a138bd6732944b29b272693ec87`.

## Decisão

`STAGE14_TECHNICAL_CANDIDATE=PASS`

`STAGE14_COMPLETED=YES`

`RELEASE_APPROVED=NO`

A Etapa 14 está encerrada no escopo técnico validado: build portátil/MSI,
reprodutibilidade, instalação, desinstalação, CLI/GUI, exportação, fixtures
externos, Godot, Unity, integridade e gates de qualidade. A release pública
permanece bloqueada por:

- `R-014`: GUI, CLI e MSI sem assinatura de código;
- `R-015`: pendências jurídicas, política de publicação/dados e identidade
  visual final;
- `R-016`: migração para WiX 4.0.6 validada tecnicamente; permanece apenas a revisão de governança da toolchain no gate de release.
