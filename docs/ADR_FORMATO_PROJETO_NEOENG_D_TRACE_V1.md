# ADR — Formato de projeto NeoEng-D-Trace v1
## Decisão aprovada para implementação na Etapa 3

- Status: `APROVADO`
- Data: `2026-07-31`
- Base: `0ff7e66767cedd0ad949a86fc8dae476d7c6594c`
- Etapa: `3 — persistência e contrato versionado`

## Contexto

O formato legado salva layers, objetos, grupos e apenas os IDs das colisões.
Ele não possui identificador, versão, validação estrita, escrita atômica,
imagem, geometria de colisão personalizada ou Bézier.

## Decisão aprovada

### Identidade

- `format_id`: `neoeng-d-trace-project`
- `schema_version`: `1`
- extensão: `.ndtproj`
- mídia: JSON UTF-8 sem BOM

### Conteúdo persistente

- referência externa da imagem;
- layers em ordem;
- objetos em ordem;
- polígono;
- layer do objeto;
- colisão completa por objeto;
- Bézier completo;
- grupos em ordem;
- membros de grupos;
- metadados mínimos do documento.

### Conteúdo transitório excluído

- imagem em memória;
- seleção atual;
- histórico Undo/Redo;
- listeners;
- `CommandManager`;
- `auto_repair`;
- configuração global do aplicativo;
- estado temporário das ferramentas;
- estado da UI.

### Imagem

- não será embutida;
- a referência terá caminho e tipo `relative` ou `absolute`;
- SHA-256 será opcional;
- o parser não abrirá o arquivo apontado;
- a Etapa 4 decidirá quando localizar, confirmar e carregar a imagem.

### Validação

- Pydantic 2 em modo estrito;
- campos desconhecidos proibidos;
- números não finitos proibidos;
- IDs e referências validados;
- versão futura rejeitada;
- documento inteiro validado antes de substituir a cena.

### Legado

Documento sem `format_id` e `schema_version` poderá ser reconhecido como
legado apenas se corresponder à estrutura conhecida.

A migração:

- preservará layers, objetos, grupos e ordem observável;
- converterá colisões legadas para o polígono visual porque o legado não
  contém a geometria personalizada;
- definirá Bézier e imagem como ausentes;
- retornará avisos explícitos;
- nunca fingirá ter recuperado dados inexistentes.

### Escrita

- arquivo temporário no mesmo diretório;
- flush;
- `fsync`;
- `os.replace`;
- limpeza do temporário em falha;
- destino anterior preservado quando a substituição não ocorrer;
- JSON determinístico com `sort_keys=True`, `indent=2`,
  `ensure_ascii=False` e newline final.

### Limites propostos

- arquivo: 64 MiB;
- objetos: 100.000;
- pontos somados: 1.000.000;
- Bézier: quatro pontos por segmento;
- profundidade: fixa pelo schema.

### Backup

Nenhum backup automático na v1. A escrita atômica será obrigatória. Política
de backup adicional poderá ser aprovada posteriormente sem alterar o
significado do schema v1.

## Consequências

### Positivas

- fim da perda silenciosa de colisão e Bézier;
- formato identificável e migrável;
- falhas controladas;
- testes determinísticos;
- compatibilidade com a API atual da cena;
- sem antecipar a UI da Etapa 4.

### Custos

- novos modelos e serviço;
- migração explícita;
- testes extensos;
- arquivos futuros exigirão nova versão ou migração.

## Registro de aprovação

- Decisão do responsável: `ADR APROVADO`
- Data da aprovação: `2026-07-31`
- Base autorizada:
  `0ff7e66767cedd0ad949a86fc8dae476d7c6594c`
- Branch autorizada:
  `feat/etapa-3-persistencia-versionada`

A aprovação autoriza a criação controlada da branch e a implementação do
contrato v1 dentro do escopo revisado. Ela não autoriza alterações de UI,
exportadores, física, ferramentas de desenho ou revisão ampla da CLI.
