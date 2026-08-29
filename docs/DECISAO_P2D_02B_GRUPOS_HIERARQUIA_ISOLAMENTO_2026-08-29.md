# NeoEng-D-Trace — Decisão P2D-02B

**Status:** ACTIVE — execução autorizada
**Data:** 29/08/2026 (UTC-03)
**Baseline de entrada:** `d152b214b1bccb717911001396936c1f93b23714`
**Subetapa:** P2D-02B — grupos, hierarquia/membership e isolamento
**Dependência fechada:** P2D-02A — ordem visual, camadas, visibilidade e locking seguro

## 1. Evidência que abriu a subetapa

A auditoria do fluxo da usuária e do código profissional encontrou:

- `SceneGroupAuthoringRecord` já existe com `members`, `visible` e `locked`;
- `SceneAuthoringModel` só expõe `add_group` e `group_selection`;
- `SceneAuthoringSession` não expõe operações transacionais de grupo;
- a janela profissional não possui uma superfície de grupos/membership;
- o viewport não considera visibilidade ou lock herdados de grupos;
- não existe estado transitório de isolamento na sessão profissional;
- o modelo legado possui `GroupsPanel`, mas pertence a outra arquitetura e não
  pode ser usado como fallback direto no editor profissional.

Portanto, a lacuna é de produto no editor profissional, não de ausência do
conceito no repositório inteiro.

## 2. Decisão de contrato

P2D-02B implementará uma hierarquia profissional explícita:

```text
Group
├── Group (subgroup, opcional)
└── Object
```

As relações são definidas assim:

1. `SceneAuthoringDocumentV1` permanece imutável e continua sem informação de
   hierarquia nova.
2. `SceneAuthoringDocumentV2` recebe `parent_group_id` opcional nos registros
   de grupo. Ausência significa grupo raiz; cenas V2 existentes continuam
   legíveis sem migração destrutiva.
3. `members` continua contendo somente IDs de objetos. Subgrupos são
   relacionados exclusivamente por `parent_group_id`; não se misturam tipos no
   campo de membership.
4. Um objeto pode permanecer membro de mais de um grupo para preservar dados
   existentes. A UI não remove memberships não selecionadas implicitamente.
5. Ciclos, auto-parenting e referências a grupo inexistente são inválidos e
   devem ser rejeitados pelo schema antes de chegar à UI.
6. Excluir um grupo não exclui objetos: memberships do grupo são removidas e
   subgrupos são promovidos ao pai do grupo removido.
7. Reordenar grupos altera somente a ordem persistida entre irmãos; não altera
   `transform.position.z`, layer, IDs, assets ou objetos.
8. Visibilidade e lock de grupo são herdados por subgrupos e objects. Qualquer
   grupo ancestral invisível oculta o objeto; qualquer grupo ancestral locked
   bloqueia edição.
9. Isolamento é estado de edição transitório da sessão. Ele não altera o
   documento, não entra no undo/redo, não marca dirty e é limpo ao recarregar
   ou resetar a cena.

## 3. Escopo de implementação

### Incluído

- validação e round-trip de parentage V2;
- operações model/session de criar, renomear, excluir, reparentar, reordenar,
  adicionar/remover membership e alternar visible/locked;
- árvore profissional com grupos, subgrupos, objetos membros e objetos sem
  grupo;
- seleção de grupo/subgrupo pelos objetos descendentes;
- comandos de criação a partir da seleção, add/remove membership e delete sem
  perda de objetos;
- isolamento de um grupo ou subgrupo no viewport;
- bloqueio seguro de transformações por lock herdado;
- undo/redo das mutações persistentes e round-trip save/load;
- testes de contrato, fluxo Qt e auditoria nativa Windows como a usuária faria.

### Fora de escopo

- pastas, tags, filtros de busca ou colunas de metadados;
- transformação própria de grupo com pivot independente;
- alteração de layer ou `position.z` causada por membership;
- instanciamento/prefab, entidades/componentes, tilemap, colisão, NavMesh,
  iluminação ou VFX;
- qualquer alteração no modelo legado, no editor principal ou nas linhas
  externas do roadmap;
- alteração do significado histórico de campos V1 ou dos baselines C3/G/V/B.

## 4. Invariantes bloqueantes

- nenhum ID de objeto, grupo, layer ou asset pode mudar por uma operação de
  grupo;
- nenhum objeto pode ser apagado ao excluir/desagrupar;
- nenhuma operação rejeitada pode alterar documento, dirty state, histórico ou
  gesto ativo;
- isolamento não pode aparecer no JSON salvo nem no export como mutação
  editorial;
- locked group deve produzir mensagem de usuário e rejeição segura;
- visibility de grupo deve ser refletida no viewport e no preview determinístico;
- salvar e carregar deve conservar grupos, parentage, memberships, flags e
  ordem entre irmãos;
- o editor principal e o modelo legado devem permanecer sem modificações.

## 5. Aceite obrigatório

P2D-02B só poderá ser marcada `ACCEPTED` quando houver, no mesmo conjunto de
evidências:

1. schema/round-trip aprovado, incluindo parentage e ciclo inválido;
2. operações model/session cobertas por testes e undo/redo;
3. árvore profissional observável no fluxo Qt;
4. membership, visibilidade, lock herdado e isolamento exercitados;
5. tentativa de editar grupo locked sem exceção nem alteração parcial;
6. save → reload preservando hierarquia e flags, com isolamento limpo;
7. suíte completa sem regressão;
8. captura Windows, auditoria visual e revisão humana sem finding bloqueante;
9. fronteira tracked revisada e commit local próprio;
10. documentação e índice canônicos reconciliados com o hash final.

Até esses itens serem comprovados, esta decisão permanece `ACTIVE` e nenhuma
capacidade de P2D-02B será apresentada como concluída.
