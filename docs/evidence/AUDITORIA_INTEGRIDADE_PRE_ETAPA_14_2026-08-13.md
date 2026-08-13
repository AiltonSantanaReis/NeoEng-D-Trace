# Auditoria de integridade pré-Etapa 14 — 2026-08-13

## Decisão

Não foi encontrada evidência técnica de fabricação deliberada de testes ou de resultados. Também não é correto declarar garantia absoluta: foram encontrados controles permissivos e limitações reais de cadeia de custódia. A Etapa 14 não deve usar os pacotes históricos sanitizados como prova autossuficiente; deve gerar evidência nova a partir do código integrado.

## Escopo

- histórico entre o baseline `a3f376a` e `f042ceb2e5c41c4acbe445da82fe41b1164767f2`;
- workflow, configuração de pytest, mypy, cobertura e segurança;
- 960 testes oficiais pós-correção, 955 na âncora inicial, e 196 testes históricos preservados;
- 17 referências de testes substitutos, coletadas como 23 casos parametrizados;
- seis ZIPs históricos, incluindo conteúdo aninhado;
- 65 IDs de workflow citados nos documentos;
- persistência, CLI, colisão, Bézier, APIs, limites, Qt e autosave;
- importação real de exports pelos editores Godot e Unity instalados.

## Achados

### A-001 — piso de cobertura desatualizado — alto — corrigido

O piso `--cov-fail-under=62` foi criado como incremento na Etapa 5 e nunca foi reduzido. Entretanto, permaneceu após a Etapa 11 atingir 90% de linhas e 85% de branches. Um teste documental ainda exigia o valor 62. Isso permitiria regressão material com CI verde, embora não prove manipulação de resultado anterior.

Correção:

- piso combinado elevado para 90 nos dois sistemas;
- gate separado de 90% de linhas e 85% de branches;
- gate de 30% por módulo mensurável;
- testes positivos e negativos do validador.

### A-002 — reconciliação legada podia apontar para teste inexistente — alto — corrigido

O executor verificava hash, ID, tipo e assinatura das 27 falhas históricas, mas aceitava qualquer texto não vazio em `replacement_tests`. Assim, uma referência fictícia não bloqueava a reconciliação.

Correção:

- coleta real por node ID antes da execução legada;
- falha fechada para referência inválida, inexistente ou não coletável;
- resumo schema 5 separa `raw_test_status: failed` de reconciliação `status: reconciled`;
- 17 referências atuais coletam 23 casos e passam.

### A-003 — ZIPs sanitizados não são autossuficientes — alto — aberto e delimitado

A auditoria recursiva encontrou 111 arquivos ZIP aninhados e 1.179 payloads. Os 284 registros em `SHA256SUMS.txt`/`sha256_manifest.json` que apontam para payloads fecham sem mismatch. Porém, a sanitização posterior reescreveu ZIPs e não atualizou todos os hashes e tamanhos armazenados em índices JSON internos.

Foram observadas 85 ocorrências por repetição dos mesmos pacotes em artefatos aninhados. A causa direta inclui sete referências do índice bruto da Etapa 2 e a referência do pacote bruto no resumo pós-merge da Etapa 3. O documento de sanitização registra hashes antigos e novos, mas isso não restaura a autossuficiência dos índices internos.

Decisão:

- não reescrever novamente a evidência histórica nesta auditoria;
- preservar os pacotes como registro histórico com limitação explícita;
- não usá-los isoladamente para aprovar release;
- gerar evidência nova, coerente e reprodutível na Etapa 14.

### A-004 — ID remoto inexistente na matriz — médio — corrigido

A matriz citava `30742145009`, que não existe. O pacote, o manifesto e o documento da Etapa 4 registram `30741145009`, existente e concluído com sucesso. Foi um erro documental introduzido posteriormente, sem impacto no run usado no fechamento.

### A-005 — evidência manual da Etapa 4 tem garantia limitada — médio — aberto e delimitado

O pacote manual registra `gate: APPROVED`, 15 verificações marcadas como aprovadas e zero falhas manuais, mas também `internal_summary_status: FAILURE`. O próprio pacote atribui esse resumo aos dois cenários negativos esperados e registra zero falha inesperada.

Os projetos produzidos foram omitidos do pacote por conterem referências absolutas; restaram hashes e invariantes. Portanto, os 15 itens manuais são atestações humanas apoiadas por logs, não uma prova integralmente reproduzível a partir do ZIP. A funcionalidade atual de abrir/salvar foi reproduzida pela suíte Qt local, mas isso não transforma retroativamente a evidência manual em evidência automática.

### A-006 — descoberta inicial do Unity limitada ao `PATH` — médio — corrigido

A busca inicial por `Get-Command` foi insuficiente e produziu uma conclusão incorreta sobre a disponibilidade do editor. A instalação gerenciada pelo Unity Hub foi então localizada e o Unity `6000.5.7f1` foi executado realmente em modo batch com `com.unity.cloud.gltfast=6.19.0`. A validação aprovou metadados, textura, colisão, GLB externo e GLB importado pela engine, com código de processo zero e relatório preservado. Um timeout de serviço externo apareceu somente no encerramento, depois de `ENGINE_VALIDATION=SUCCESS`, da gravação do resultado e do retorno zero; ele não foi ocultado nem interpretado como falha do contrato validado.

## Auditoria do histórico de testes

- nenhum arquivo de teste foi removido entre o baseline e a âncora auditada;
- não houve inclusão de `xfail`;
- vários `importorskip` de PySide6 foram removidos quando a dependência passou a ser obrigatória;
- a execução oficial local terminou com zero skip;
- mudanças de nomes detectadas eram formatação ou atualização de contrato;
- o teste genérico de decomposição removido foi substituído por 18 contratos de geometria e triangulação;
- o workflow evoluiu de validação parcial para lint, formatação, mypy, auditoria de dependências, Bandit, branches, Windows e legado reconciliado;
- não foi encontrada redução histórica do piso de cobertura: a falha foi não elevar o piso após a meta final ser atingida.

## Confronto remoto

Dos 65 IDs de workflow citados, 64 existem no repositório remoto e correspondem a execuções concluídas. O único ID inexistente era o typo A-004. Runs falhos das Etapas 8 e 9 continuam documentados, o que é evidência contra ocultação sistemática de falhas.

## Execuções locais desta auditoria

- 955/955 testes oficiais aprovados antes da correção, zero skip;
- 960/960 testes oficiais aprovados após o endurecimento, zero skip;
- 11.581/12.478 linhas: 92,81%;
- 3.370/3.964 branches: 85,02%;
- cobertura combinada: 90,93%, aprovada com piso 90;
- 247/247 testes focais das Etapas 3 e 6–13 aprovados;
- 23/23 casos substitutos aprovados;
- legado bruto: 196 testes, 27 falhas, zero erro, zero skip;
- reconciliação: 27/27 assinaturas esperadas, zero inesperada e zero ausente;
- Godot 4.7 real: `SUCCESS` em metadados, textura, colisão, GLB externo e GLB importado pela engine.
- Unity 6000.5.7f1 real com glTFast 6.19.0: `SUCCESS` nos mesmos cinco contratos, em duas execuções batch com código zero.

## Conclusão

Não há base técnica para acusar fabricação deliberada. Há base técnica para afirmar que dois controles permitiam confiança excessiva: cobertura com piso obsoleto e referências substitutas não verificadas. Ambos foram endurecidos.

As evidências históricas sanitizadas e a validação manual da Etapa 4 devem ser tratadas como registros de garantia limitada, não como prova autossuficiente. Godot e Unity foram reproduzidos localmente no código-fonte identificado; isso não recria retroativamente execuções históricas nem aprova release. Esses limites devem continuar visíveis durante a Etapa 14 e na decisão de release.
