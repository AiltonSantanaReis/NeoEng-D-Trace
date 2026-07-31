# Evidência — Etapa 1: ambiente reproduzível e CI Windows/Linux

## Identificação

- Commit tecnicamente validado: `837aa6ac170e34868a87036ac2d33032eac99188`
- Branch: `chore/etapa-1-ci-windows-lockfile`
- Pull request: `#7`
- Workflow: `Private validation`
- Execução: `#29`
- Run ID: `30556955141`
- Data da execução: 2026-07-30
- Responsável: Ailton Santana Reis

## Objetivo

Comprovar instalação reproduzível a partir do `poetry.lock` e validação real
em Windows e Linux.

Esta evidência está relacionada aos riscos:

- `R-009`: CI anteriormente restrito ao Linux;
- `R-010`: dependências transitivas anteriormente sem lockfile.

O relatório não declara o produto comercialmente pronto e não encerra os
demais riscos registrados no projeto.

## Entradas validadas

- `.github/workflows/ci.yml`
- `baseline_manifest.json`
- `poetry.lock`
- `pyproject.toml`
- commit `837aa6ac170e34868a87036ac2d33032eac99188`

## Dependências e lockfile

- Poetry: `2.4.1`
- Formato do lockfile: `2.1`
- Faixa Python declarada: `>=3.11,<3.12`
- Pacotes registrados no lockfile: `40`
- Operações de instalação observadas: Windows `40`; Linux `39`.
- SHA-256 canônico do `poetry.lock`:
  `43aaa1fd290d83f69c55ecf6bdc4abb7f55c170aa3172444f8828af01abeca86`

O mesmo hash canônico foi registrado nos ambientes Windows e Linux.

## Ambiente Windows

- Runner: `windows-latest`
- Sistema observado: Microsoft Windows Server 2025
- Job: `test-windows`
- Job ID: `90919758232`
- Conclusão: `success`
- Python: `3.11.9`
- Poetry: `2.4.1`
- Manifesto antes e depois dos testes: `206 arquivos`
- mypy: zero problemas em `58` arquivos
- pytest: `161 passed in 11.21s`
- Cobertura global: `48%`

## Ambiente Linux

- Runner: `ubuntu-latest`
- Sistema observado: Ubuntu 24.04.4 LTS
- Job: `test`
- Job ID: `90919758259`
- Conclusão: `success`
- Python: `3.11.15`
- Poetry: `2.4.1`
- Manifesto antes e depois dos testes: `206 arquivos`
- mypy: zero problemas em `58` arquivos
- pytest: `161 passed in 10.30s`
- Cobertura global: `48%`

## Verificações executadas

Nos dois sistemas, o workflow executou:

1. checkout da árvore do pull request;
2. configuração do Python 3.11;
3. verificação do manifesto;
4. instalação do Poetry 2.4.1;
5. validação do lockfile;
6. instalação por `poetry sync`;
7. registro do ambiente instalado;
8. compilação das fontes Python;
9. flake8 para erros fatais;
10. relatório não bloqueante de dívida flake8;
11. Black em modo de verificação;
12. isort em modo de verificação;
13. mypy sobre `src`;
14. pytest com cobertura;
15. nova verificação do manifesto;
16. upload dos artefatos de evidência.

## Resultados bloqueantes

- Workflow aprovado.
- Jobs Windows e Linux aprovados.
- Instalação pelo lockfile aprovada nos dois sistemas.
- Compilação aprovada.
- Flake8 fatal: zero erros.
- Black e isort aprovados.
- mypy: zero erros em 58 arquivos.
- pytest: 161 testes aprovados nos dois sistemas.
- Manifesto íntegro antes e depois dos testes.
- Nenhum teste foi removido ou ignorado para obter resultado verde.
- Nenhuma falha bloqueante foi registrada.

## Cobertura

- Total de instruções: `8849`
- Não cobertas: `4644`
- Cobertura global: `48%`

A cobertura foi registrada como evidência, mas ainda não atende aos objetivos
futuros do plano mestre.

## Artefatos

### Windows

- Nome: `validation-windows-python-3.11`
- Artifact ID: `8765255412`
- Tamanho: `22937 bytes`
- SHA-256:
  `c5fdc67da515c1cec83bfd0416b85767949b0bd9a1059478e381a14b9f9ffb28`

### Linux

- Nome: `validation-linux-python-3.11`
- Artifact ID: `8765217747`
- Tamanho: `23000 bytes`
- SHA-256:
  `c310f10dfd774a59651438f6c27b8ea4cbc09d2cd315f4f21e3a032af3016390`

Os artefatos foram vinculados ao commit
`837aa6ac170e34868a87036ac2d33032eac99188`.

## Limitações e dívida residual

- A cobertura global permanece em 48%.
- O relatório não bloqueante do flake8 registrou 125 ocorrências.
- Permanecem imports não utilizados, complexidade elevada e outras dívidas de estilo.
- O mypy ainda informa que corpos de funções não tipadas não são verificados por padrão.
- O `pyproject.toml` ainda utiliza campos antigos do Poetry que geram avisos de depreciação.
- Wheels de NumPy e PySide6 geraram avisos por entradas em diretórios `__pycache__`.
- O GitHub Actions apresentou avisos relacionados à transição de Node 20 para Node 24.
- Esta etapa não valida persistência completa, Abrir/Salvar, Undo/Redo ou exportação completa de colisão.

## Decisão técnica

**APROVADO TECNICAMENTE — INTEGRAÇÃO DA EVIDÊNCIA PENDENTE**

O commit técnico comprovou ambiente reproduzível e validação equivalente em
Windows e Linux.

Os riscos R-009 e R-010 somente poderão ser formalmente encerrados depois que
este relatório e a atualização correspondente da matriz forem integrados e
aprovados por uma nova execução completa do CI.
