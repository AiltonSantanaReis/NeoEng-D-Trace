# Contrato da CLI e do modo headless

**Estado:** candidato técnico da Etapa 7 validado localmente em 10 de agosto de 2026; integração e CI pós-merge pendentes.

## Entradas oficiais

| Entrada | Uso | Propagação do código |
|---|---|---|
| `python app.py` | checkout de desenvolvimento | `SystemExit(main())` |
| `python -m src.launcher` | execução direta do módulo | `SystemExit(main())` |
| `neoeng-d-trace` | script instalado definido no pacote | retorno de `src.launcher:main` |

## Códigos de saída

| Código | Significado | Canal principal |
|---:|---|---|
| `0` | ajuda, versão, operação headless concluída ou encerramento normal da GUI | `stdout` para ajuda, versão e sucesso headless |
| `1` | contrato operacional inválido, entrada ausente/malformada, exportação ou persistência falhou | mensagem iniciada por `ERROR:` em `stderr` |
| `2` | erro do parser, como argumento desconhecido, valor ausente ou fontes mutuamente exclusivas | diagnóstico do `argparse` em `stderr` |

Exceções inesperadas do modo headless são convertidas em código `1`, sem traceback no contrato normal. Exceções fatais da GUI continuam sendo propagadas depois do registro de validação, para não mascarar falhas.

## Matriz de argumentos

| Argumento | Modo acionado | Pré-condição | Efeito/saída | Falha esperada |
|---|---|---|---|---|
| nenhum | GUI | dependências e display disponíveis | abre a aplicação | exceção de runtime propagada |
| `-h`, `--help` | parser | nenhuma | ajuda em `stdout`; código `0` | não aplicável |
| `--version` | parser | nenhuma | versão em `stdout`; código `0` | não aplicável |
| `--headless` | headless | exige ao menos uma entrada ou saída | nenhum arquivo por si só | código `1` |
| `--image ARQUIVO` | headless | arquivo regular e imagem válida | carrega e valida a imagem | código `1` se ausente ou inválida |
| `--project ARQUIVO` | headless | arquivo regular e projeto válido | carrega e valida o projeto | código `1` se ausente ou inválido |
| `--export-scene-gltf ARQUIVO` | headless | cena com geometria exportável | GLB atômico com magic `glTF` | código `1` se não houver geometria ou a escrita falhar |
| `--export-object-gltf ARQUIVO` | headless | requer `--object-id` existente e válido | GLB atômico do objeto | código `1` se o ID faltar, não existir ou for inválido |
| `--object-id ID` | headless | requer `--export-object-gltf` | seleciona o objeto da exportação GLB | código `1` quando isolado |
| `--export-json ARQUIVO` | headless | metadados serializáveis | JSON substituído atomicamente | código `1` se serialização ou escrita falhar |
| `--save-project ARQUIVO` | headless | destino persistível | projeto `.ndtproj` reabrível | código `1` se persistência falhar |
| `--validation-log ARQUIVO` | GUI | não pode ser combinado com modo headless | log JSONL da sessão manual | código `1` quando combinado com operação headless |
| argumento desconhecido | parser | não aplicável | nenhum efeito | código `2` |

## Combinações

- `--image` e `--project` são mutuamente exclusivos no parser e a combinação retorna `2`.
- Os argumentos de saída acionam headless mesmo sem `--headless`; isso evita que sejam silenciosamente ignorados pela GUI.
- `--project` pode ser combinado com JSON, salvamento e GLB de cena/objeto na mesma execução.
- `--image` ou `--project` isolados executam validação de carregamento e retornam `0` apenas quando a entrada é realmente aberta.
- `--export-json` e `--save-project` sem fonte produzem, respectivamente, metadados e projeto de uma cena vazia válida.
- As operações seguem ordem fixa e fail-fast: imagem, projeto, GLB de cena, GLB de objeto, JSON e projeto.

## Garantias e limites

- Entradas precisam ser arquivos regulares; diretórios não são aceitos como imagem ou projeto.
- JSON, GLB e projeto usam os mecanismos atômicos dos exportadores/persistência correspondentes.
- Um destino JSON existente é preservado quando a substituição atômica falha.
- A execução com múltiplas saídas não é uma transação conjunta: se uma operação posterior falhar, arquivos anteriores já concluídos permanecem. Essa limitação deve ser tratada na etapa de contratos de exportação, sem alegação de atomicidade global.
- A CLI não valida importação dos GLBs em engines externas; essa prova pertence à etapa de exportadores e engines.
- O código `0` comprova somente o contrato solicitado naquela execução; não aprova release nem elimina riscos de outras etapas.

## Testes de referência

O contrato é exercitado por `tests/test_stage_7_cli_contract.py`, incluindo parser, despacho, entradas reais e malformadas, saídas reabertas, falhas de escrita, execução por `app.py`, execução por módulo e restauração/salvamento do estado GUI com dublês controlados.
