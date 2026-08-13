# Evidência — Etapa 12: segurança e limites operacionais (pré-merge)

## Identificação

- Data local: 13 de agosto de 2026.
- Branch: `etapa-12-limites-operacionais`.
- Base técnica original: `a22a90088220e586c3382c3ed5dc1075a3ff7e6b`.
- `main` reconciliada: `2e9cad4cb7879aa7ceb8ee0a1e096b738674a984`.
- Commit técnico: `da7611b543bb0ceb4eb8e67a7900aadcb8f04a5f`.
- HEAD fonte auditado no CI: `a42b54b07d8e9e10feb8d283adc664b52f9d25d3`.
- Estado durante as execuções finais: worktree limpa; suíte oficial e legado vinculados ao commit técnico exato.
- Decisão: **APROVADO TECNICAMENTE PRÉ-MERGE / INTEGRAÇÃO PENDENTE**.
- `R-012`: **ABERTO** até merge autorizado e auditoria pós-merge.
- Etapa 12: NÃO CONCLUÍDA.
- Release: **NÃO APROVADA**.

## Ambiente reproduzido

- Plataforma reportada pelo Python: `Windows-10-10.0.26200-SP0`.
- Python: `3.11.9`.
- Poetry: `2.4.1`.
- `poetry.lock` SHA-256: `b7e94da9a7074347d5a4432cc68ae1f59953af60d1aa62dc970ee7f98579d7b7`.
- Pillow `12.3.0`; Pydantic `2.12.5`; PySide6 `6.10.1`; OpenCV `4.12.0`; NumPy `2.2.6`.

## Falhas reproduzidas antes da correção

Seis regressões foram escritas primeiro e falharam contra a base:

1. configuração aceitava campos desconhecidos;
2. coleções de configuração não tinham teto operacional;
3. projetos aceitavam polígonos acima de 2.000 pontos;
4. a grade uniforme aceitava célula zero e AABB com expansão patológica;
5. GLTF deixava escapar `OverflowError` ao ultrapassar índice `uint16`;
6. arquivo de log não rotacionava e preservava caminho pessoal absoluto.

Medição geométrica anterior ao teto, no mesmo computador:

| Pontos | Validação de polígono |
|---:|---:|
| 250 | 0,0320 s |
| 500 | 0,1318 s |
| 1.000 | 0,5206 s |
| 2.000 | 2,0922 s |

O crescimento observado é compatível com o algoritmo quadrático de interseção de segmentos. O teto de 2.000 pontos e a complexidade agregada de 4.000.000 são limites de segurança, não promessa de baixa latência.

## Limites implementados

| Superfície | Contrato fail-closed |
|---|---|
| Configuração | 1 MiB; UTF-8 estrito; JSON sem duplicatas ou não finitos; campos/tipos estritos; 100 recentes; 100 perfis; gravação atômica |
| Imagem | 256 MiB em disco; eixo até 8.192; até 16.777.216 pixels; até 128 MiB decodificados; formato/extensão coerentes; uma imagem por arquivo |
| Projeto | 64 MiB; 100.000 objetos; 1.000.000 pontos; 2.000 pontos por polígono/colisão; 1.999 segmentos Bézier; geometria válida antes da adoção |
| Detecção | imagem e memória validadas; `downscale` em `(0, 1]`; contornos/resultados limitados pelos tetos do projeto; Chaikin até 8 iterações e 2.000 pontos resultantes |
| Atlas | eixo até 8.192; 16.777.216 pixels por página; 10.000 itens; 16 páginas; agregado de entrada limitado; argumentos validados antes do canvas |
| Broadphase | célula inteira positiva; AABB finita e ordenada; até 100.000 células por AABB; atualização inválida preserva o registro anterior |
| GLTF | índice máximo `65.535`; excesso retorna falha controlada sem arquivo parcial |
| Logs | 5 MiB e 3 backups para logs textuais; 20 MiB e 3 backups para JSONL de validação; evento até 256 KiB; caminhos absolutos pessoais sanitizados |

## Testes e gates executados

```text
poetry run flake8 src tests tools app.py pack_for_ai.py
poetry run black --check --diff src tests tools app.py pack_for_ai.py
poetry run isort --check-only --diff src tests tools app.py pack_for_ai.py
poetry run mypy src
poetry run pip-audit
poetry run bandit -q -r src -lll
poetry run pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term --cov-report=xml
poetry run python tools/run_legacy_tests.py --group all --output .stage12-legacy-local
```

Resultados locais mais recentes:

- suíte focal da Etapa 12: `50 passed`;
- suíte oficial: `928 passed`, `0 failed`, `0 skipped`, `0 blocked`;
- linhas: `11.174/12.040` (`92,81%`);
- branches: `3.309/3.892` (`85,02%`);
- cobertura combinada: `90,91%`;
- mypy: zero erros em `73` arquivos;
- pip-audit: nenhuma vulnerabilidade conhecida; o pacote local do projeto não existe no índice público e foi informado como não auditável;
- Bandit de alta severidade: zero achados;
- legado: `196` testes, `27` falhas históricas esperadas, `27/27` conciliadas, zero inesperadas, zero ausentes, zero erros e zero skips;
- `coverage.xml` SHA-256: `dba7b46b34405e347a48e5be02d1bb512f8c7375964f031d05233e654e154ba8`;
- resumo legado temporário SHA-256: `1869b13ce3e96a4aec4232a6acfb74611a081f66b2a360989e1bf620c89be858`.

Uma primeira suíte completa desta etapa terminou com `907 passed` e uma falha real: colisão inválida passou a interromper a inicialização durante o cálculo de assinatura documental. A validação de persistência foi mantida; a janela recebeu assinatura determinística de fallback para estado inválido. Depois da regressão específica, as execuções completas seguintes aprovaram `910/910` e, após ampliar branches de segurança, `928/928`.

Na revisão do gate de logs, uma reprodução real de rollover intercalando o logger da aplicação e um logger de módulo revelou PermissionError/WinError 32 no Windows: dois handlers mantinham o mesmo arquivo aberto. A implementação passou a compartilhar uma única instância de RotatingFileHandler entre as duas rotas, e o teste focal agora força rollover real, alterna ambas as rotas e falha se o subsistema emitir erro interno de logging. A sanitização também cobre caminhos absolutos com espaços.

A auditoria das leituras encontrou ainda duas janelas de crescimento concorrente: o JSON de projeto usava leitura integral depois do stat, e o hash de imagem podia continuar lendo além do tamanho inspecionado. O projeto agora lê no máximo 64 MiB mais um byte; hashes usam leitura em blocos com teto, detectam truncamento, crescimento e alteração de metadados. Regressões específicas confirmam os limites sem adoção parcial do projeto.

Após esse endurecimento, a primeira suíte completa ficou em 3.307/3.892 branches, ou 84,97%, abaixo da meta documental. A segunda chegou a 3.308/3.892, ou 84,99%, ainda insuficiente. Nenhum desses resultados foi aceito por arredondamento. Regressões de arquivo ausente, arquivo acima do teto e truncamento durante hash elevaram a execução final a 3.309/3.892, ou 85,02%.

## Benchmarks locais

Entradas sintéticas simples, três repetições por operação; estes números não são SLA:

| Entrada | X-ray CPU modo 1, mediana | Detecção básica, mediana |
|---|---:|---:|
| 2.048×2.048, 4 MiB | 0,009357 s | 0,006656 s |
| 4.096×4.096, 16 MiB | 0,039351 s | 0,019615 s |

Validação e decodificação de PNG real:

| Entrada | Arquivo | Decodificado | Inspeção | Decode |
|---|---:|---:|---:|---:|
| 2.048×2.048 RGBA | 21.240 B | 16 MiB | 0,007117 s | 0,041131 s |
| 4.096×4.096 RGBA | 75.549 B | 64 MiB | 0,008519 s | 0,161732 s |
| 8.192×2.048 RGBA | 71.402 B | 64 MiB | 0,008974 s | 0,168730 s |

Imagem quadrada 8K excede 16.777.216 pixels e é rejeitada deliberadamente antes do processamento integral. Nenhum benchmark de pipeline 8K quadrado é apresentado como aprovado.

## CI pré-merge auditado

- PR draft: `#49`.
- Workflow `Private validation`: `31684136128`, conclusão `success`.
- HEAD fonte: `a42b54b07d8e9e10feb8d283adc664b52f9d25d3`.
- Merge sintético testado: `4a55943f102c569d6175da84aec74d127e69697b`, com pais `2e9cad4cb7879aa7ceb8ee0a1e096b738674a984` e `a42b54b07d8e9e10feb8d283adc664b52f9d25d3`.

| Sistema | Job | Artefato | Digest SHA-256 da API/ZIP bruto |
|---|---:|---:|---|
| Linux | `94396143432` | `9174746367` | `4c44616df7833a5568b6bf6cf7d69354a18374f24f7feb8643c2b6b7ab328bdf` |
| Windows | `94396143273` | `9174781465` | `8a706f2fd16d0a3e27ce4d250e7818f58bca5e89c9f8d2d30a0d5426f881daef` |

Os dois jobs aprovaram `928` testes, `11.174/12.040` linhas, `3.309/3.892` branches, `90,91%` combinada, baseline de `325` arquivos, mypy em `73` arquivos, pip-audit sem vulnerabilidades conhecidas e Bandit sem alta severidade. Não houve anotações de check-run, erro de comando de workflow ou traceback não legado nos logs.

Os `coverage.xml` extraídos confirmaram as contagens exatas; SHA-256 Linux `9fe4bb8e1b7605909175f4503ecf6e02994c209911d55560de8216d7d89226f2` e Windows `164fb2c70b4df114c252310aa886d5f86036509f832760ebb8e9b5fccc6e646d`. O artefato Windows confirmou o legado no merge sintético, com `source_head_commit` igual ao HEAD fonte, `working_tree_dirty=false`, `196` testes e `27/27` divergências conciliadas; SHA-256 do resumo `01a8b14d6c523f064d3be62ec4c39e737313e08f7a4d0fa16afb788ce048d309`.

A comparação com a árvore fonte encontrou `54` arquivos: `52` idênticos byte a byte e `2` documentos idênticos após normalização exclusiva de CRLF/LF, sem diferença textual. A varredura recursiva validou checksums internos e inspecionou `60` arquivos, `1.419` payloads e `1.359` entradas de arquivos aninhados, com zero referência proibida ou caminho pessoal. Os pacotes temporários foram removidos após a auditoria.

## Limitações e riscos residuais

- O CI pré-merge foi aceito para o HEAD fonte `a42b54b07d8e9e10feb8d283adc664b52f9d25d3`; qualquer alteração posterior exige novo CI antes do merge.
- O resumo legado final foi gerado fora do repositório com `tested_commit` e `source_head_commit` iguais a `da7611b543bb0ceb4eb8e67a7900aadcb8f04a5f`, `working_tree_dirty=false`, conciliado e removido após o cálculo do hash.
- A cobertura de branches está apenas 0,02 ponto percentual acima da meta; qualquer mudança exige nova medição integral.
- Benchmarks usam imagens sintéticas simples e não representam pior caso de imagens ruidosas, muitos contornos, atlas cheio ou hardware diferente.
- Os 27 testes históricos divergentes continuam registrados; não são falhas novas, mas também não foram apagados.
- Autosave, refatoração Qt, build standalone, instalador e validação real de release pertencem às Etapas 13–14 e seguem pendentes.
- Nenhuma auditoria automatizada prova ausência total de vulnerabilidades.

## Decisão pré-merge

**APROVADO TECNICAMENTE PRÉ-MERGE / INTEGRAÇÃO PENDENTE.** A validação local e o CI do HEAD fonte foram aceitos após auditoria dos artefatos. Não há base para encerrar `R-012`, concluir a Etapa 12, iniciar a Etapa 13 ou aprovar release antes de merge explicitamente autorizado e auditoria pós-merge.
