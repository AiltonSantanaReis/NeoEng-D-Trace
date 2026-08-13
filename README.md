# NeoEng-D-Trace

**Ferramenta desktop proprietária e local-first para preparar assets de jogos a partir de imagens 2D.**

NeoEng-D-Trace reúne, em um fluxo único, detecção e seleção assistida, correção de contornos, edição de polígonos e curvas Bézier, configuração de colisões e exportação de assets. O foco atual é o pipeline 2D; o projeto não se apresenta como editor de imagens, ferramenta de modelagem 3D completa ou engine de jogos.

> **Estado:** pré-release em desenvolvimento. **Etapa 13 integrada e concluída; Etapa 14 não iniciada; release NÃO APROVADA.**
> **Plataforma oficial inicial:** Windows 11. O CI também executa testes em Linux, mas isso não constitui suporte público ao Linux.
> **Operação:** o fluxo principal é local/offline; imagens, projetos e assets não dependem de serviços em nuvem para o funcionamento aprovado.

## Estado verificável

A última âncora integrada da `main` é
`e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108`, merge autorizado da PR `#51`.
O primeiro CI da PR, `31693639653`, ficou verde, mas foi rejeitado após os
artefatos revelarem uma falha real de preservação de quarentena em POSIX. A
correção foi validada no CI pré-merge final `31696674184` e reproduzida no CI
pós-merge `31698961646`, auditado em Linux e Windows. `R-011` e a Etapa 13
estão encerrados no escopo aprovado; Etapa 14 e release permanecem pendentes.

| Indicador | Estado comprovado |
|---|---|
| Suíte oficial | **953 testes no CI pós-merge integrado da Etapa 13, em Linux e Windows** |
| Cobertura integrada da Etapa 13 | **11.581/12.478 linhas — 92,81%** |
| Branches integrados da Etapa 13 | **3.370/3.964 — 85,02%** |
| Cobertura combinada integrada | **90,93%** |
| Type checking | mypy sem erros em 80 arquivos no commit técnico da Etapa 13 |
| Dependências | auditoria sem vulnerabilidades conhecidas no lock validado |
| Segurança estática | Bandit sem achados de alta severidade no gate vigente |
| Última etapa integrada | **Etapa 13 — R-011 encerrado no escopo aprovado** |
| Próxima etapa | **Etapa 14 — não iniciada** |
| Release | **NÃO APROVADA** |

A Etapa 13 foi integrada pela PR `#51` no merge
`e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108`. O CI pós-merge
`31698961646` reproduziu `953` testes, cobertura idêntica ponto a ponto em
Linux/Windows e legado `27/27`; seus artefatos foram auditados. `R-011` está
**ENCERRADO NO ESCOPO APROVADO**.

Os limites da Etapa 12 cobrem configuração, imagens, projetos, geometria,
detecção, broadphase, atlas, GLTF e logs. O legado executou 196 testes e
conciliou 27/27 divergências históricas, sem falhas inesperadas. Esses
resultados foram reproduzidos no CI pós-merge Linux/Windows. Os tetos são
controles de segurança, não SLA nem prova de ausência total de vulnerabilidades.

## O que o NeoEng-D-Trace resolve

Preparar um asset 2D para uma engine costuma exigir alternar entre edição de
imagem, contorno vetorial, colisão, metadados e exportação. O NeoEng-D-Trace
concentra essas tarefas em uma aplicação desktop com projeto próprio,
operações editáveis e exportadores verificáveis.

Fluxo central:

```text
Imagem 2D
   ↓
Detecção / seleção assistida
   ↓
Contorno, polígonos e Bézier
   ↓
Camadas, grupos e edição
   ↓
Colisão estática
   ↓
Sprite / atlas / metadados / GLTF-GLB no escopo 2D
   ↓
Pipeline da engine
```

## Capacidades comprovadas

| Área | Estado atual |
|---|---|
| Projeto | formato `.ndtproj`, identificador `neoeng-d-trace-project` e **schema v1** estrito |
| Persistência | criar, abrir e salvar projetos com round-trip; autosave e recuperação integrados e auditados na Etapa 13 |
| Interface | UI desktop PySide6 com identidade NeoEng-D-Trace e interface em português/inglês |
| Edição | camadas, grupos, polígonos, vértices, curvas Bézier e histórico Undo/Redo |
| Seleção | ferramentas retangular, elíptica, laço, laço poligonal, caneta e laço magnético |
| Detecção | processamento e detecção assistida com OpenCV no pipeline atual |
| Colisões | criação, visualização, transformação, validação e exportação de colisões estáticas |
| Sprites | exportação de sprite individual e lote |
| Atlas | geração de atlas e metadados com validação de limites |
| Metadados | perfis Generic, Godot, Unity e Phaser disponíveis no exportador |
| GLTF/GLB | exportação de cena e objeto **aprovada somente no escopo 2D atual** |
| Integração real | consumo dos exports da Etapa 10 validado em Godot 4.7 e Unity 6000.5.7f1 com glTFast 6.19.0 |
| Automação | entrada gráfica e CLI/headless pelo mesmo launcher |

### Limite importante do GLTF/GLB

O contrato atual **não** inclui extrusão, UV, materiais ou representação 2.5D.
O exportador aprovado representa a geometria 2D no plano XY e preserva o
escopo explicitamente testado. Esses itens não são anunciados aqui como
funcionalidades entregues.

Os perfis de metadados Godot, Unity e Phaser existem e possuem contratos
automatizados. A validação em engine real registrada na Etapa 10 é específica
para Godot e Unity; não é apresentada como validação equivalente do Phaser.

## Stack técnica

| Camada | Tecnologias |
|---|---|
| Runtime | Python 3.11 |
| Desktop UI | PySide6 |
| Imagem e visão computacional | OpenCV, Pillow |
| Cálculo numérico | NumPy |
| Modelos/validação | Pydantic |
| GLTF/GLB | pygltflib |
| Dependências | Poetry + `poetry.lock` |
| Testes | pytest + pytest-cov |
| Qualidade | Flake8, Black, isort, mypy |
| Segurança | pip-audit, Bandit |
| CI | GitHub Actions em Windows e Linux |

A faixa de Python declarada pelo pacote é `>=3.11,<3.12`; a referência
operacional utilizada nas validações Windows é Python 3.11.9.

## Arquitetura

Existe uma única árvore de implementação:

```text
app.py
src/
├── collision/      # API canônica de colisão
├── core/           # comandos, geometria, configuração e validação
├── exporters/      # sprite, atlas, JSON, colisões e GLTF/GLB
├── models/         # modelo de cena
├── persistence/    # schema, I/O do projeto e snapshot de autosave
├── physics/        # compatibilidade histórica; sem motor dinâmico próprio
├── tools/          # seleção, detecção e edição geométrica
├── ui/             # janela, canvas, painéis, previews e gizmo
└── utils/
```

Não existe uma segunda árvore `neoeng_d_trace/`. A distribuição Python é
`neoeng-d-trace`, enquanto a implementação interna permanece em `src/`.

## Execução a partir do código-fonte no Windows

> **Isto é um fluxo de desenvolvimento/validação, não um instalador de usuário
> final.** Build Windows e instalador ainda não foram aprovados.

Requisitos usados pelo projeto:

- Python 3.11 (`>=3.11,<3.12`);
- Poetry 2.4.1;
- ambiente virtual local recomendado.

Quando `poetry` já está disponível no terminal:

```powershell
poetry check --lock --strict
poetry sync --no-interaction --no-ansi
poetry run python .\app.py
```

Ajuda da CLI:

```powershell
poetry run python .\app.py --help
```

Entrada instalada pelo pacote:

```text
neoeng-d-trace
```

Para uma instalação do zero sem depender do `py` launcher, consulte o
procedimento de ambiente e o workflow reproduzível registrado na documentação
de evidências.

## Qualidade e validação

O gate atual executa, entre outros controles:

```text
baseline_integrity --verify
poetry check --lock --strict
compileall
Flake8
Black --check
isort --check-only
mypy
pip-audit
Bandit
pytest com cobertura de branches
suíte legada reconciliada no Windows
baseline_integrity --verify novamente
```

A validação oficial de interface permanece vinculada ao Windows. Resultados
headless/offscreen ou Linux não são usados para declarar suporte público a uma
plataforma nem para substituir uma prova real quando o comportamento real é o
objeto da validação.

## Limitações e pendências declaradas

O README não transforma roadmap em funcionalidade entregue. No estado atual:

- **autosave e recuperação estão integrados e auditados, mas não substituem backup**;
- **build Windows, executável standalone e instalador ainda não foram
  aprovados**;
- **release não está aprovada**;
- Linux e macOS não são plataformas oficialmente suportadas para a versão 1.0;
- `R-011` está encerrado no escopo aprovado após merge autorizado e CI pós-merge auditado;
- `R-012` está encerrado no escopo aprovado, mas os limites publicados não
  constituem SLA nem garantia de ausência total de vulnerabilidades;
- o GLTF/GLB atual não inclui UV, materiais, extrusão ou 2.5D;
- limites oficiais de resolução, quantidade de objetos/vértices, memória,
  tempo e hardware mínimo ainda não devem ser publicados sem benchmark
  reproduzível no Windows;
- física dinâmica completa, modelagem 3D completa, rigging, animação,
  fotogrametria e suporte nativo completo ao Unreal não fazem parte do escopo
  entregue da versão 1.0.

A matriz exata de formatos de importação também não deve ser ampliada por
inferência a partir de filtros de interface ou bibliotecas instaladas. O
suporte definitivo depende de contrato e teste correspondentes.

## Documentação de engenharia

O README é a porta de entrada do projeto. A rastreabilidade detalhada permanece
nas fontes canônicas:

- [Definição canônica do produto](docs/DEFINICAO_DO_PRODUTO.md)
- [Plano Mestre de Estabilização](docs/PLANO_MESTRE_ESTABILIZACAO.md)
- [Matriz funcional atual](docs/MATRIZ_FUNCIONALIDADES_ATUAL.md)
- [Matriz de riscos](docs/MATRIZ_RISCOS_ESTABILIZACAO.md)
- [Política de qualidade e evidências](docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md)
- [Índice de evidências](docs/evidence/README.md)
- [Contrato GLTF/GLB](docs/CONTRATO_GLTF_GLB_NEOENG_D_TRACE.md)
- [Contrato da CLI](docs/CONTRATO_CLI.md)
- [Changelog](CHANGELOG.md)
- [Política de segurança](SECURITY.md)

Snapshots históricos não são reescritos retroativamente. Documentos vivos
devem continuar distinguindo estado atual, evidência de um SHA específico e
histórico.

## Licença e publicação

NeoEng-D-Trace é um projeto proprietário e o repositório permanece privado. Não
há licença open source atribuída. O texto jurídico comercial final ainda exige
decisão/revisão própria antes de qualquer lançamento público.

Esta atualização registra o encerramento pós-merge auditado da Etapa 13. Ela
não inicia a Etapa 14 e não aprova release.

<details>
<summary><strong>Âncoras históricas preservadas para contratos documentais e auditoria</strong></summary>

Esta seção permanece recolhida por padrão para não transformar a vitrine em um
log operacional, mas conserva as referências que os contratos documentais
atuais verificam. As fontes completas continuam em `docs/` e
`docs/evidence/`.

### Etapa 5

- Pacote 5C integrado; `R-004` encerrado no escopo aprovado.
- PR de fechamento `#28`; HEAD técnico
  `956db473a88641bfdcfbd49ed122479f3fa2c51d`.
- âncora final `574be9bd0268e70c384903f93f16cf6e73aa57a2`.
- CI pós-merge `Private validation` `#84`; CI técnico pós-merge
  `31425585259`.
- o encerramento histórico registrou a transição para a Etapa 6 sem aprovar
  release.

### Etapas 6 a 9

- Etapa 6: merge `73a128ec44cde17867bbac6a7854ce86a43aba5a`, CI
  `31431739320`, `R-005` encerrado.
- Etapa 7: merge `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`, CI
  `31437000772`, `R-006` encerrado.
- Etapa 8: merge `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`, CI
  `31441024001`, `R-007` encerrado.
- Etapa 9: merge `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`, CI
  `31445518755`, `R-008` encerrado.

### Etapa 10

A PR `#42` teve os CIs `31450335289`, `31451363518` e `31452032479`
**rejeitados**. O pré-merge `31457937902` foi **aceito** e a integração
ocorreu em `9b22bdc54b13992658172d4748bfab44f3127c8e`. O pós-merge
`31463873481` foi **rejeitado**. A correção passou pelo CI `31464786333`,
PR `#43`, merge `f8caec3e7156d308f03046f81d2c89996f959466` e pós-merge
`31469610508`, que foi **aceito** após auditoria.

### Etapa 12

A PR funcional `#49` foi integrada em
`872bf079d228d13d0203d22b844052b1f920e99b`; seu CI pós-merge `31686321925`
aprovou `928` testes. O fechamento documental foi integrado pela PR `#50` em
`fc81c2ea10e751c15a39627d462ddfff390eeb04`; o CI pós-merge final
`31688307089` aprovou Linux e Windows com `929` testes. `R-012` foi encerrado
no escopo aprovado, sem aprovação de release.

### Etapa 11

A Etapa 11 foi integrada em
`2a38b89e542390b3b4396a88d9a416f3695caadc`; o CI pós-merge
`31491221322` comprovou `877` testes e `90,91%` de cobertura combinada.
`R-003` foi encerrado no escopo aprovado. A release permaneceu **não aprovada**.

</details>
