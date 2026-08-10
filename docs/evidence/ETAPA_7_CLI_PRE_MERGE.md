# Evidência — Etapa 7: CLI e modo headless

## Identificação

- commit técnico: `a940ef13018aabc430126db3fd705b521fc1be06`;
- estado Git: commit técnico isolado, ainda não integrado à `main`;
- data: 10 de agosto de 2026;
- responsável: execução técnica automatizada; decisão humana de release pendente.

## Ambiente

- sistema: Windows, execução local real;
- Python: `3.11.9`;
- Poetry: `2.4.1`;
- pytest: `9.1.1`;
- ambiente Qt dos testes: `offscreen` conforme configuração da suíte;
- dependências resolvidas pelo lock vigente, validado com `poetry check --lock --strict`.

Nenhum endereço absoluto do computador integra esta evidência. As saídas temporárias dos testes foram criadas por `tmp_path` e descartadas pela suíte.

## Objetivo e escopo

Fechar a matriz da Etapa 7 para argumentos, despacho GUI/headless, efeitos em arquivos, canais de saída e códigos de processo. O pacote também corrige a execução direta por módulo, que antes chamava `main()` sem propagar o retorno ao sistema operacional.

## Entradas e integridade

| Arquivo | Bytes | SHA-256 no commit técnico |
|---|---:|---|
| `src/launcher.py` | 11589 | `c66a58da9756e70012f139f55ba503d23731da5bc90adaacdeccf256720cb4a2` |
| `tests/test_stage_7_cli_contract.py` | 11901 | `75b90c44aae7f443d570d3dd7d670aec8dede4ecaebb2488b2f02e2d361dcde5` |

## Comandos executados

```text
poetry check --lock --strict
python -m compileall -q -f app.py src tests pack_for_ai.py tools
python -m flake8 src tests tools app.py pack_for_ai.py
python -m black --check --diff src tests tools app.py pack_for_ai.py
python -m isort --check-only --diff src tests tools app.py pack_for_ai.py
python -m mypy src
python -m pip_audit
python -m bandit -q -r src -lll
python -m pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term-missing --cov-report=xml
python tools/run_legacy_tests.py --group all
python tools/baseline_integrity.py --verify
git diff --check
python app.py --help
python app.py --version
python app.py --headless
python -m src.launcher --headless
```

## Resultados

- testes focais de CLI e entradas: `47 passed`, `0 failed`;
- suíte oficial do commit técnico: `620 passed`, `0 failed`, `0 skipped`;
- suíte após inclusão do contrato documental: `621 passed`, `0 failed`, `0 skipped`;
- cobertura combinada de linhas e branches: `68.53%`;
- cobertura de `src/launcher.py`: `85%`, contra `18%` no snapshot anterior;
- mypy: zero erros em `66` arquivos;
- Flake8, Black, isort, compilação e lock: aprovados;
- pip-audit: nenhuma vulnerabilidade conhecida nas dependências auditáveis; o pacote local, ausente do índice público, foi explicitamente ignorado pela ferramenta;
- Bandit em alta severidade: zero achados;
- suíte legada: `196` testes executados, `26/26` divergências previstas reconciliadas, zero inesperadas e zero ausentes;
- baseline do commit técnico: `280` arquivos verificados;
- baseline do pacote documental: `282` arquivos verificados;
- `app.py --headless`: código real `1` com diagnóstico em `stderr`;
- `python -m src.launcher --headless`: código real `1` com diagnóstico em `stderr`;
- `app.py --help` e `app.py --version`: código real `0` e saída em `stdout`;
- varredura do conteúdo rastreado: nenhuma referência proibida encontrada.

## Falhas observadas durante o gate

1. A primeira tentativa usou `python -m poetry`, mas Poetry não pertence à virtualenv do projeto. O gate parou antes das análises e foi retomado com o executável Poetry `2.4.1` disponível no ambiente.
2. A primeira passagem do Flake8 rejeitou uma linha em branco excedente no teste novo. A execução parou no lint.
3. A primeira correção de espaçamento não encontrou a combinação real de finais de linha e o Flake8 voltou a rejeitar o mesmo ponto. Nenhuma aprovação foi declarada.
4. O espaçamento foi corrigido de forma exata, o arquivo isolado passou no Flake8 e o gate integral posterior passou.

Essas tentativas não são contabilizadas como sucesso. Somente a execução integral final fundamenta a decisão local.

## Evidência comportamental

- ajuda, versão e argumento desconhecido foram executados em subprocessos reais;
- contratos inválidos retornaram `1` ou `2`, conforme a camada responsável, sem traceback;
- imagem PNG real foi aberta;
- projeto real foi carregado, exportado para JSON, salvo e reaberto;
- GLBs reais de cena e objeto foram gerados e validados pelo magic `glTF`;
- objeto inexistente e exporter retornando falso produziram código `1` sem falso sucesso;
- falha simulada de substituição JSON preservou o destino anterior;
- execução combinada validou ordem e conclusão das saídas;
- restauração e persistência do estado GUI foram exercitadas com dublês Qt controlados.

## Limitações e riscos residuais

- o pacote ainda não possui CI Linux/Windows de PR nem CI pós-merge vinculados ao SHA;
- múltiplas saídas são sequenciais, não uma transação conjunta; uma falha tardia não remove saídas anteriores válidas;
- a entrada de console instalada não foi reconstruída neste pacote; `app.py` e execução por módulo foram testados localmente, e build/instalador pertencem à Etapa 14;
- importação dos GLBs em engines externas permanece fora desta etapa;
- metas globais finais de cobertura permanecem abertas em `R-003`;
- release permanece não aprovada.

## Decisão

**APROVADO LOCALMENTE / NÃO INTEGRADO.**

`R-006` permanece aberto até merge e CI pós-merge aprovados. A Etapa 8 não deve ser declarada iniciada antes desse fechamento formal.
