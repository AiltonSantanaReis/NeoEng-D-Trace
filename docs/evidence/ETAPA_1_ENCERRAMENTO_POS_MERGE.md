# Evidência — Etapa 1: encerramento pós-merge

## Identificação

- Etapa: `1 — Ambiente reproduzível e CI Windows/Linux`
- Pull request integrado: `#7`
- Merge commit: `6b7375502df0e2019ebd8202fe4dfa364c9e2a89`
- Primeiro pai: `c660fce8dd012ff87177dc48cf3656fec6ae5ebf`
- Segundo pai: `b185febb6c4458ed3b8a9a056c63ea934d750dca`
- Branch validada após o merge: `main`
- Data do merge no GitHub: `2026-07-31T09:29:59Z`
- Responsável: Ailton Santana Reis

## Objetivo

Registrar permanentemente a validação executada depois da integração do PR
`#7` na `main`.

Este documento complementa
`ETAPA_1_AMBIENTE_REPRODUZIVEL_CI_WINDOWS_LINUX.md`, que preserva as
evidências anteriores ao merge.

## Estrutura do merge

A estrutura do merge commit foi validada localmente:

- primeiro pai: estado anterior da `main`;
- segundo pai: HEAD aprovado do PR;
- integração realizada por merge commit;
- nenhum squash ou rebase foi utilizado;
- o commit aprovado do PR está contido na `main`.

## Validação local pós-merge

Ambiente observado:

- plataforma: Windows;
- Python: `3.11.9`;
- pytest: `9.1.1`;
- pytest-cov: `7.1.0`;
- Poetry: `2.4.1`.

Resultados:

- manifesto inicial: `Baseline verified: 207 files`;
- `poetry check --lock`: aprovado com avisos de metadados obsoletos;
- compilação das fontes: aprovada;
- flake8 fatal: `0`;
- Black: `94 files would be left unchanged`;
- isort: aprovado;
- mypy: `Success: no issues found in 58 source files`;
- pytest: `161 passed in 4.28s`;
- manifesto final: `Baseline verified: 207 files`;
- árvore de trabalho: limpa.

## CI da main após o merge

- Workflow: `Private validation`
- Evento: `push`
- Execução: `#32`
- Run ID: `30620151264`
- Commit: `6b7375502df0e2019ebd8202fe4dfa364c9e2a89`
- Branch: `main`
- Estado: `completed`
- Conclusão: `success`

### Windows

- Job: `test-windows`
- Job ID: `91122560712`
- Sistema: Microsoft Windows Server 2025
- Python: `3.11.9`
- Poetry: `2.4.1`
- Instalação pelo lockfile: `40 installs`, `0 updates`, `0 removals`
- SHA-256 canônico do lockfile:
  `43aaa1fd290d83f69c55ecf6bdc4abb7f55c170aa3172444f8828af01abeca86`
- manifesto antes e depois: `Baseline verified: 207 files`
- flake8 fatal: `0`
- relatório flake8 não bloqueante: `125`
- Black: `94 files would be left unchanged`
- mypy: `Success: no issues found in 58 source files`
- pytest: `161 passed in 13.00s`
- cobertura global: `48%`
- conclusão: `success`

Artefato:

- Nome: `validation-windows-python-3.11`
- Artifact ID: `8789061353`
- Tamanho: `22935 bytes`
- Expirado no momento da validação: `false`
- SHA-256:
  `6bb6ae3cf58dc3887d2eab5cf0a44cf3f0f0172c1aadfced66ed0c929a50c560`

### Linux

- Job: `test`
- Job ID: `91122560744`
- Sistema: Ubuntu 24.04.4 LTS
- Python: `3.11.15`
- Poetry: `2.4.1`
- Instalação pelo lockfile: `39 installs`, `0 updates`, `0 removals`
- SHA-256 canônico do lockfile:
  `43aaa1fd290d83f69c55ecf6bdc4abb7f55c170aa3172444f8828af01abeca86`
- manifesto antes e depois: `Baseline verified: 207 files`
- flake8 fatal: `0`
- relatório flake8 não bloqueante: `125`
- Black: `94 files would be left unchanged`
- mypy: `Success: no issues found in 58 source files`
- pytest: `161 passed in 10.70s`
- cobertura global: `48%`
- conclusão: `success`

Artefato:

- Nome: `validation-linux-python-3.11`
- Artifact ID: `8789049942`
- Tamanho: `23000 bytes`
- Expirado no momento da validação: `false`
- SHA-256:
  `270c824cf92dc0b4d5f6edb8c2dbd178c496b6d306dca35b7b2c522f8139dfe6`

## Falha de codificação detectada antes do commit

A primeira preparação local deste documento não foi aprovada porque os textos
foram gravados com mojibake.

Causa raiz:

- o script estava em UTF-8 sem BOM;
- o Windows PowerShell 5.1 interpretou os literais não ASCII usando a página de
  código legada;
- o manifesto foi atualizado para os bytes corrompidos, mas nenhum commit ou
  push foi executado;
- a inspeção explícita de Unicode detectou a falha antes da publicação.

Correção:

- os documentos foram regravados por Python 3.11 com UTF-8 explícito, sem BOM;
- o manifesto foi regenerado somente depois da correção;
- a validação completa foi repetida;
- a inexistência de sequências de mojibake foi verificada programaticamente.

## Outras ocorrências observadas

Nenhum erro bloqueante de código foi encontrado na validação pós-merge.

Ocorrências não bloqueantes que permanecem registradas:

- houve timeout transitório ao consultar a API do GitHub; a repetição posterior
  obteve os dados e não alterou o resultado do CI;
- o `pyproject.toml` usa campos antigos do Poetry e produz avisos de
  depreciação;
- o relatório completo do flake8 contém `125` ocorrências;
- o mypy não verifica por padrão o corpo de funções sem tipagem;
- os wheels de NumPy e PySide6 contêm avisos relacionados a entradas em
  diretórios `__pycache__`;
- as Actions ainda exibem avisos da migração forçada de Node 20 para Node 24.

## Cobertura residual

A cobertura global permanece em `48%`, abaixo das metas do plano mestre.

Módulos observados com cobertura de `0%` nos jobs pós-merge:

- `src/collision/__init__.py`;
- `src/collision/sat2d.py`;
- `src/tools/lasso.py`;
- `src/ui/layers_panel.py`;
- `src/ui/theme_qss.py`.

Outros módulos operacionais permanecem com cobertura baixa, incluindo
ferramentas de edição, seleção, colisão, canvas e inicialização.

## Limites da aprovação

Esta aprovação cobre exclusivamente:

- ambiente reproduzível por `poetry.lock`;
- instalação equivalente no Windows e no Linux;
- CI multiplataforma;
- proteção pelos checks `test` e `test-windows`;
- integridade do manifesto;
- integração controlada do PR `#7`;
- validação local e remota da `main` depois do merge.

Ela não aprova o produto como comercialmente pronto e não valida:

- inventário funcional completo;
- persistência e contrato de projeto;
- ciclo Abrir/Salvar;
- Undo/Redo completo;
- exportação completa de colisões;
- CLI/headless completo;
- Bézier e geometria completa;
- física e colisão completas;
- validação nas engines declaradas;
- cobertura integral da interface;
- segurança e limites operacionais;
- build final do Windows.

## Decisão

**APROVADO — ETAPA 1 ENCERRADA APÓS VALIDAÇÃO PÓS-MERGE**

A Etapa 1 está aprovada no escopo definido pelo plano mestre.

A Etapa 2 somente poderá iniciar depois que este registro permanente, o índice
de evidências e o manifesto atualizado forem revisados, validados pelo CI e
integrados na `main`.
