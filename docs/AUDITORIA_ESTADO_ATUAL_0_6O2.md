# Auditoria do estado atual — NeoEng-D-Trace 0.6O2

Data da auditoria: 2026-07-29

## Escopo e origem examinada

A análise foi feita sobre o arquivo `polygontool.rar` fornecido como captura do projeto atual.

- tamanho do RAR: `256548602` bytes;
- SHA-256 do RAR: `A276F42F51CC9DD8637449CD199FCF3E763724F993D952185FDBBFA0C7C84D62`;
- versão de Python registrada na `.venv` do projeto: `3.11.9`;
- PySide6 registrado: `6.10.1`;
- pytest registrado: `9.0.1`;
- pygltflib registrado: `1.16.5`.

A extração foi somente leitura. Nenhuma operação Git de escrita foi executada.

## Estado estrutural encontrado

- entrada de desenvolvimento: `app.py`;
- única árvore de runtime: `src/`;
- árvore duplicada `neoeng_d_trace/`: ausente;
- configuração canônica: `config.json` na raiz;
- `config.json` é JSON válido;
- `config.json.corrupted` existe como cópia inválida e está ignorado pelo `.gitignore`;
- não foram encontrados padrões de chaves de API ou blocos de chave privada nos arquivos Python, testes, ferramentas, benchmarks e workflows examinados.

### Estado Git observado, sem alteração

- branch: `feature/physics-ui`;
- HEAD: `cf749564ab5d961772d66dc363d0e990cebf8da3`;
- remoto: não foi usado;
- estado relativo ao HEAD antigo: `345` entradas no `git status --porcelain`;
  - `182` arquivos rastreados ausentes;
  - `54` arquivos rastreados modificados;
  - `109` arquivos não rastreados.

Isso significa que o diretório atual contém uma evolução extensa ainda não consolidada em um baseline Git limpo. A auditoria não interpreta o HEAD antigo como representação da aplicação atual e não recomenda publicar esse histórico.

## Testes executados antes da correção

No código recebido, em Linux/Python 3.13.5:

- compilação de `app.py`, `src/` e `tests/`: aprovada;
- suíte ativa não-Qt com a dependência real `pygltflib`: `91 passed, 7 skipped`;
- coleta integral: quatro módulos Qt não puderam ser coletados porque este ambiente não possui uma distribuição nativa Linux do PySide6;
- exportadores reais: sprite PNG, metadados JSON, atlas PNG/JSON, GLB da cena e GLB do objeto foram produzidos e reabertos com sucesso.

A ausência de PySide6 neste ambiente é uma limitação da auditoria, não uma aprovação nem uma reprovação dos testes GUI.

## Defeitos confirmados no estado recebido

### OBS-EXPORT-DIALOG-001

O modo de validação manual dependia dos seletores nativos de arquivo e pasta. Quando o seletor devolvia caminho vazio, a ação era registrada como `CANCELLED`, mesmo que o objetivo da sessão fosse testar o exportador de forma determinística.

### OBS-SUMMARY-001

`session.summary` podia receber status `SUCCESS` quando não havia exceção explícita, apesar de ações obrigatórias não terem sido concluídas. O resumo detalhava as ausências, mas o status principal era enganoso.

### OBS-TOKEN-001

Tokens de objetos eram derivados por SHA-256 truncado sem segredo. Identificadores simples poderiam ser testados por dicionário. A alteração usa HMAC com chave aleatória não persistida.

### OBS-TRACEBACK-001

O registro de uma exceção fora de um bloco `except` podia produzir `NoneType: None` em vez da exceção real.

### OBS-DUP-ERROR-001

Uma exceção tratada podia aparecer como evento de domínio e também como `python.log`, inflando a contagem de falhas. Logs já associados a um evento estruturado agora são marcados para não serem capturados pela segunda rota.

### IO-REPLACE-GAP-001

JSON, sprite, atlas e GLB removiam o destino antes da renomeação do arquivo temporário. Uma falha entre essas operações podia deixar o usuário sem a versão anterior e sem a nova. A gravação passa a usar `os.replace` sem pré-exclusão.

### DOC-STALE-001

O README continha um caractere de controle no exemplo de `app.py` e ainda tratava `CLI-LAZY-001` e `LOG-DUP-001` como abertos, embora os contratos atuais já tenham testes para esses casos.

## Correções incluídas em 0.6O2

- sandbox exclusivo por sessão para as cinco exportações observadas;
- seletores normais preservados fora de `--validation-log`;
- pós-condições reais para PNG, JSON, atlas e GLB;
- `SUCCESS`, `INCOMPLETE` e `FAILURE` distintos no resumo;
- captura de exceções não tratadas em threads;
- traceback real para exceções registradas programaticamente;
- HMAC process-local para tokens de objetos;
- supressão da rota duplicada de erro quando já existe evento estruturado;
- substituição atômica por arquivo, sem apagar previamente o destino;
- testes de regressão para substituição de arquivos existentes;
- documentação corrigida.

## Testes executados depois da correção

### Suíte ativa não-Qt real

Ambiente: Linux/Python 3.13.5, pytest 9.0.2, Pillow, NumPy, OpenCV e `pygltflib` real.

Resultado final:

- `102 passed`;
- `7 skipped` por dependência Qt indisponível;
- `0 failed`;
- duração: aproximadamente 3 segundos.

Essa execução inclui GLB real, JSON real, PNG real, atlas real, substituição de arquivos existentes, sandbox por sessão, privacidade dos tokens, resumo incompleto/falha e exceção em thread.

### Integração dos cinco fluxos do diálogo

Os métodos reais de `ExportDialog` foram executados com doubles mínimos das interfaces Qt, porque PySide6 nativo não está disponível neste ambiente. Os cinco exportadores reais foram chamados e produziram arquivos reais:

- `export.sprite`: `SUCCESS`;
- `export.metadata`: `SUCCESS`;
- `export.atlas`: `SUCCESS`;
- `export.gltf.scene`: `SUCCESS`;
- `export.gltf.object`: `SUCCESS`;
- `session.summary`: `SUCCESS`;
- nenhum seletor nativo foi chamado.

Esse teste prova a integração lógica do diálogo com os exportadores, mas não substitui um teste visual ou de eventos nativos do PySide6 no Windows.

### Suíte histórica não-Qt

Resultado final preservado:

- `113` testes executados;
- `108` aprovados;
- `5` falharam;
- `0` erros de coleta.

As cinco falhas são as mesmas já classificadas no projeto, e não foram escondidas nem alteradas para forçar resultado verde:

1. decomposição convexa: fixture/expectativa histórica pendente;
2. Sobel: teste espera `float64`, contrato atual é `float32` por memória/desempenho;
3. atlas: teste espera duas páginas porque pressupõe ausência de rotação, mas a melhoria atual usa uma página;
4. comando de alça: fixture usa três pontos colineares, rejeitados corretamente;
5. simplificação circular: contagem de vértices não mede o erro geométrico.

As classificações de origem permanecem em `docs/ETAPA_0_5_2_CLASSIFICACAO_FALHAS.csv` e `docs/ETAPA_0_5_2E_CLASSIFICACAO_RESTANTE.csv`.

### Outros controles

- AST/compilação: `60` arquivos Python de runtime mais `app.py`, sem erro;
- `app.py --help`: aprovado sem importar PySide6;
- árvore única `src/`: confirmada;
- formatos de saída: contratos ativos aprovados;
- bytes determinísticos dos exportadores comparados com a base de teste: sem regressão observada.

## Limites que permanecem abertos

- `PERF-MAGNETIC-001`;
- `UI-RESIZE-PT-001`;
- `POLY-VALIDATION-UX-001`;
- `GLTF-2D-001`;
- `GLTF-UV-001`;
- `GLTF-MATERIAL-001`;
- `GLTF-U16-001`;
- `GLTF-CLEANUP-001`;
- formato de projeto versionado;
- autosave;
- 2.5D;
- build Windows;
- validação completa em engines.

O atlas grava PNG e JSON com substituição atômica individual. Não existe transação atômica única para o par de arquivos; uma falha excepcional entre as duas substituições ainda pode produzir versões desencontradas. O diálogo valida ambos e não declara sucesso nesse caso, mas a limitação de transação em par permanece.

## Portão Windows ainda obrigatório

Esta auditoria não executou PySide6 nativo nem PowerShell, pois o ambiente disponível é Linux. Portanto, a etapa não deve ser declarada integralmente validada para Windows antes de:

1. aplicar o pacote transacional no estado-base exato;
2. executar a suíte completa no Python 3.11.9 da `.venv`;
3. obter exatamente `157 passed`;
4. executar a sessão manual observada no PySide6 real;
5. obter `session.summary = SUCCESS` e os cinco eventos de exportação como `SUCCESS`.

Nenhuma operação Git de escrita faz parte desse portão.
