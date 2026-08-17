# Decisão de escopo — adaptadores nativos first-party

## Identificação

- data da decisão: 2026-08-17;
- base documental e técnica: `main` integrado em `f9c8d8f`;
- escopo: resolver a divergência entre a definição do produto e o plano de
  integração dos adaptadores nativos;
- etapa 8: ainda não iniciada nesta decisão.

## Divergência encontrada

A definição do produto excluía “plugins de terceiros” da versão 1.0 e também
descrevia integrações Godot/Unity como possibilidade futura. O plano posterior
de integração dos plugins nativos passou a prever adaptadores source-only
first-party em dez etapas, sem registrar explicitamente que eles não são
plugins de terceiros.

## Decisão formal

1. Plugins de terceiros, dependências de marketplace e integrações externas não
   aprovadas continuam fora da versão 1.0.
2. Adaptadores first-party source-only para Godot e Unity são uma linha própria
   de integração do NeoEng-D-Trace e podem ser desenvolvidos sob o plano de
   adaptadores nativos.
3. Os adaptadores não podem conter DLLs, executáveis auxiliares, bibliotecas
   nativas ou downloads automáticos.
4. O núcleo do D-Trace permanece a fonte de verdade para imagem, metadados,
   geometria, colisão, pivô, atlas, tileset e animação.
5. Esta decisão não promove nenhuma etapa, não substitui testes reais, não
   aprova release e não autoriza declarar engine validada sem artefatos
   reproduzíveis.

## Alterações documentais vinculadas

- `docs/DEFINICAO_DO_PRODUTO.md` distingue plugins de terceiros dos adaptadores
  first-party source-only;
- `docs/PLANO_INTEGRACAO_PLUGINS_NATIVOS_2026-08-16.md` registra esta decisão e
  mantém as etapas 8–10 como não iniciadas;
- os gates de qualidade, não regressão, evidência íntegra e promoção do plano
  continuam obrigatórios.

## Limitações

Nenhum código de adaptador foi promovido por esta decisão. A Etapa 8 ainda
exige baseline própria, contrato completo, testes negativos, execução real em
Godot e Unity, artefatos versionados e CI antes de qualquer commit de
implementação ser considerado apto.

## Decisão

`SCOPE_DECISION=APPROVED`

`NATIVE_ADAPTERS_FIRST_PARTY=IN_SCOPE_AS_SEPARATE_INTEGRATION_LINE`

`THIRD_PARTY_PLUGINS=OUT_OF_SCOPE_FOR_VERSION_1_0`

`STAGE8_STATUS=NOT_STARTED`

`RELEASE_APPROVED=NO`
