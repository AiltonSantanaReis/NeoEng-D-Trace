# Evidência — Etapa 12: segurança e limites operacionais (pré-merge)

## Identificação

- Data local: 13 de agosto de 2026.
- Branch: `etapa-12-limites-operacionais`.
- Base integrada: `a22a90088220e586c3382c3ed5dc1075a3ff7e6b`.
- Commit técnico: PENDENTE nesta versão do relatório.
- Estado durante as execuções: worktree modificada; resultados ainda não estão vinculados a um commit imutável.
- Decisão: **PARCIAL / APROVADO SOMENTE COMO EVIDÊNCIA LOCAL PRÉ-MERGE**.
- `R-012`: **ABERTO** até commit técnico, CI Linux/Windows, merge e auditoria pós-merge.
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
- `coverage.xml` SHA-256: `36d792325967fe6437357106fd83b16e3d63228ec78f9b561513cbddb2cfd933`;
- resumo legado temporário SHA-256: `d254afbd01d0c16dfd9c9f9e5bfb6700d4c6ec37beb9198afe420296ee2c2864`.

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

## Limitações e riscos residuais

- CI Linux e Windows ainda não foi executado para o HEAD técnico desta etapa.
- Os artefatos temporários locais registram a base integrada e `working_tree_dirty=true`; devem ser regenerados em commit imutável antes do fechamento.
- A cobertura de branches está apenas 0,02 ponto percentual acima da meta; qualquer mudança exige nova medição integral.
- Benchmarks usam imagens sintéticas simples e não representam pior caso de imagens ruidosas, muitos contornos, atlas cheio ou hardware diferente.
- Os 27 testes históricos divergentes continuam registrados; não são falhas novas, mas também não foram apagados.
- Autosave, refatoração Qt, build standalone, instalador e validação real de release pertencem às Etapas 13–14 e seguem pendentes.
- Nenhuma auditoria automatizada prova ausência total de vulnerabilidades.

## Decisão pré-merge

**PARCIAL.** A implementação local e os testes são suficientes para publicar um commit técnico e solicitar CI. Não há base para encerrar `R-012`, concluir a Etapa 12, iniciar a Etapa 13 ou aprovar release antes de commit limpo, CI Linux/Windows e auditoria dos artefatos ligados ao SHA exato.
