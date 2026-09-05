# NeoEng-D-Trace

> **P2D-05 — lote de idioma/status, atualizado em 05/09/2026:** sobre
> `4b873c3`, ainda em pré-commit. Mensagens legíveis, detalhes seguros e idioma
> tiveram a rodada local registrada: 1.968 testes passaram, dois symlinks
> pulados por privilégio; revisão humana, PRECOMMIT e gates limpos pendentes.
> PR #170 permanece em rascunho, sem merge/tag/release.
> [Fronteira e acompanhamento do lote](docs/P2D05_LOTE_IDIOMA_STATUS_2026-09-04.md).

**Ferramenta desktop local-first para preparação, edição e exportação de assets 2D para jogos.**

O NeoEng-D-Trace concentra em um fluxo verificável a seleção assistida, criação e correção de máscaras, edição de contornos, polígonos e curvas Bézier, configuração de colisões, preparação de sprites/atlas e integração com engines. O produto não é apresentado como editor de imagens completo, engine de jogos ou modelador 3D.

> **Versão de referência:** `v0.3.0` — evolução do snapshot público `v0.2.0`, com o estado técnico atual do `main` preservado em evidências e com rollback explícito.
> **Plataforma oficial:** Windows 11. Linux é utilizado no CI para validação automatizada, mas não é anunciado como plataforma pública suportada.
> **Operação:** local/offline por padrão; imagens, projetos e assets permanecem no ambiente do usuário.

## Estado operacional atual — requalificação P2D-05

Na branch `Ailton/error-presentation-contract-20260904`, o SHA `35727d9`
passou no CI Linux/Windows `33932398814`; os dois symlinks passaram sem skip
no Windows. A PR `#170` permanece em rascunho. O proprietário autorizou
preservação privada e sincronização de `main` na candidata, sem merge da PR.
A integração documental com `b9557e6` exige requalificação do SHA resultante;
revisão humana atual, Ready for review, merge, tag e release não estão aprovados.
Consulte o [acompanhamento vivo](docs/P2D05_REQUALIFICACAO_ATUAL.md) para
evidências, fronteira de autorização e roteiro de revisão.

## Snapshot histórico — candidata integrada da Etapa 7

A revisão corrente é a integração da PR `#168` em `main`, pelo merge commit
`9a25f0be0ea47a092e90c0194797ddcaf33a7dcf`. O produto foi validado no SHA
`6ede2f6073f6d2aaf5a394e4043019a3ac85a5e4`; o commit-fonte da PR foi
`9adb66a5ab9cfaabc1703d4b9b225b141473ec52`.

O CI pós-merge `33871734689` passou integralmente em Linux (`test`) e Windows
(`test-windows`). C12 e C13 estão `PASS` no escopo comprovado; a prova VMware
continua scoped à reconstrução identificada e o empacotamento portátil mantém
a limitação de proveniência documentada. Snapshots legados foram preservados.
Tag e release não foram aprovadas.

## Snapshot histórico — pós-merge técnico da Etapa 7 / PR #166

A PR `#166`, originada na branch
`fix/legacy-27-functional-regressions`, foi integrada no merge commit
`8a97ae14e8f84eb86fcacfaefed61f014830fbf9`, a partir do commit-fonte
`c6a2d18f9c6bcd48dba65b0df333a813ad6b86b3`. O CI pós-merge
`33794660766` passou nos jobs Linux `100779319495` e Windows
`100779319836`.

O pós-merge confirmou baseline de `3213` arquivos, integridade de `130`
manifestos, Linux com `1919 passed` e Windows com runner `ACCEPTED` em
`189/189` arquivos, `1919` testes, `0` falhas, `0` erros e `0` skips. Cobertura,
Stage 4B.5, lock, tipos, segurança e gate formal passaram. Os contratos de
symlink continuam comprovados no JUnit Windows; a prova VMware permanece
scoped à reconstrução identificada do ZIP/patch.

O estado da Etapa 7 é `APROVADO NO ESCOPO DA PR #166`; o plano global continua
`IN_PROGRESS` e tag, release e aprovação global continuam bloqueados. A falha
anterior e o snapshot pré-merge permanecem preservados. Evidência:
`docs/evidence/ETAPA_7_ENCERRAMENTO_POS_MERGE_PR166_2026-09-03.md`.

## Snapshot técnico e rastreabilidade

O estado integrado anterior à preparação da `v0.3.0` é o merge da PR `#101`, commit
`1d7fee0e30128f51e17e579f52807fb84fb8f5cb`. O CI pós-merge desse snapshot foi
aprovado em Linux e Windows. O ponto de restauração integral foi preservado na tag
`backup/main-before-v0.3.0`, que aponta para o mesmo commit.

A release `v0.2.0` permanece disponível como snapshot histórico anterior:
[GitHub Releases — v0.2.0](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/releases/tag/v0.2.0).
Ela não deve ser confundida com o estado atual nem com a linha `v0.3.0`.

O fechamento documental da Etapa 13 foi integrado no commit
`b4d9390dbd1274c283a3e3985d6d79be47de45d6`, com CI pós-merge
`31705652046`; `R-011` foi encerrado no escopo aprovado. A Etapa 14 foi
registrada e encerrada posteriormente no escopo técnico validado. A release oficial histórica `v0.2.0`, ancorada em `1feb2d134cea8c5a1d2346665280b31c051f5574`,
foi publicada sem assinatura; isso permanece uma limitação declarada, não uma
alegação de certificação.

## O que o projeto entrega

```text
Imagem 2D
   ↓
Seleção/detecção assistida e máscara
   ↓
Contorno, polígonos, Bézier e edição visual
   ↓
Camadas, grupos, transformações e undo/redo
   ↓
Colisão estática, validação e decomposição
   ↓
Sprite, atlas, pivô, metadados e GLTF/GLB 2D
   ↓
Adaptador source-only para Godot/Unity ou pipeline próprio da engine
```

### Capacidades integradas

| Área | Estado atual |
|---|---|
| Projeto | `.ndtproj`, identidade `neoeng-d-trace-project` e schema v1 estrito |
| Interface | PySide6, tema escuro, português/inglês, painéis, paleta de comandos e atalhos |
| Seleção e detecção | Seleção retangular, elíptica, laços, caneta, laço magnético e pipeline OpenCV assistido |
| Geometria | Contornos, polígonos, vértices, Bézier, simplificação, validação topológica e transformações |
| Colisão | Colisores estáticos, compostos, validação, preview e exportação |
| Sprites e atlas | Exportação individual/lote, pivô, metadados, packing e validação de limites |
| Engines | Perfis Generic, Godot, Unity e Phaser; adaptadores source-only Godot e Unity |
| Cenários parallax | Câmera, profundidade, camadas, overlays, autoria visual, schema lateral e exportação no escopo aprovado |
| GLTF/GLB | Geometria 2D no plano XY, com contrato e validação específicos |
| Automação | CLI/headless e interface gráfica usando o mesmo núcleo de operações |

## Cenários parallax e paleta de comandos

O módulo de cenários permite organizar objetos, camadas, profundidade, câmera e
molduras de visualização no editor. A paleta de comandos coexiste com os menus
tradicionais para preservar descoberta e acelerar o fluxo de usuários experientes.

O escopo entregue é de autoria, preview e exportação estrutural. Partículas,
shaders, pós-processamento, triggers, streaming de texturas e runtime completo de
engine permanecem fora do MVP e não são anunciados como funcionalidades concluídas.
O ADR de runtime integra a Etapa 5 para preview CPU
determinístico de pós-processamento, com fallback explícito e sem adaptadores
nativos Godot/Unity. Essa capacidade foi integrada no merge 159b1241b012 após CI Linux/Windows PASS e validação pós-merge. O suporte permanece limitado ao preview CPU explicitamente descrito no ADR.

## Integrações nativas

- **Godot:** addon source-only, importação de sprites, colisões, atlas, animações,
  tilesets, diagnóstico e sincronização controlada.
- **Unity:** pacote UPM source-only, assemblies Runtime/Editor, importação,
  colisões, animações, tilesets, sincronização, overrides e rollback conforme os
  contratos versionados.

As integrações não carregam binários ou dependências baixadas automaticamente. A
validação real registrada para Godot e Unity permanece vinculada aos fixtures,
versões e evidências indicados em `docs/evidence`.

## Validação histórica — Etapa 7 / PR #168

O estado documentado abaixo é a candidata da PR #168 integrada em `main`, com
gates locais e CI pós-merge concluídos no escopo comprovado, não uma release.
Não qualifica o HEAD P2D-05 ou a sincronização da PR #170. O produto foi
validado no SHA `6ede2f6073f6d2aaf5a394e4043019a3ac85a5e4`; a documentação da
candidata foi publicada no HEAD `ac96825fa36edf686a173f7fad9e51d9ff41705d`,
na branch-fonte `Ailton/legacy26-closure-audit`, integrada pela PR `#168` no merge `9a25f0be…`:

- gates locais completos no produto: suíte `1922 passed, 2 skipped`, runner
  Windows `190/190` arquivos e `1924` testes, cobertura `92,67%` de linhas e
  `85,15%` de branches; política, estática, segurança, Stage 4B.5, Stage 9,
  runner formal e integridade: `PASS`;
- empacotamento: `SUCCESS`, `11` smoke checks, ZIP de `314` arquivos,
  `124214125` bytes, SHA-256
  `2e9df7157aa55411fabdd2336df30f3697a573c41748f18d972ab41dc6c345fd`;
- runner histórico preservado: retorno `1`, `15` exatos, `11` assinaturas
  divergentes e `12` ausências; `42` testes substitutos passaram sem editar
  snapshots;
- VMware: validação dos symlinks ficou scoped ao ZIP/patch identificado; no
  host atual, os dois testes dependentes de privilégio continuam `skip` por
  `WinError 1314`;
- CI pós-merge `33871734689`: Linux `test` e Windows `test-windows`, `PASS`.

O relatório final está em
`docs/evidence/ETAPA_7_GATES_FINAIS_2026-09-04-6EDE.md`, com a atualização
pós-merge e os artefatos hashados em
`docs/evidence/artifacts/pen-tool-revalidation-20260904-6ede/`. O plano está
`APROVADO / CONCLUÍDO NO ESCOPO COMPROVADO` para C12/C13; o merge está
registrado no commit `9a25f0be…`. Tag e release continuam sem autorização.

Os artefatos e hashes que sustentam essas afirmações estão nos documentos de
`docs/evidence`; o README não substitui os logs nem reclassifica testes não
executados.

## Instalação e uso no Windows

### Release publicada

A distribuição da versão `v0.3.0` deve ser obtida na página de releases:
[GitHub Releases](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/releases).
Os artefatos oficiais são o bundle portátil, o instalador MSI e seus manifestos
SHA-256. A ausência de assinatura digital é declarada e não é apresentada como
certificação.

### Execução a partir do código-fonte

Requisitos operacionais:

- Python `>=3.11,<3.12`;
- Poetry 2.4.1;
- Windows 11 para a validação gráfica oficial.

```powershell
poetry check --lock --strict
poetry sync --no-interaction --no-ansi
poetry run python .\app.py
```

Para consultar a CLI:

```powershell
poetry run python .\app.py --help
poetry run python .\app.py --version
```

## Build e rollback

O build oficial exige uma árvore Git limpa, usa o lockfile e valida o bundle e o
MSI antes de concluir:

```powershell
.\scripts\build_windows.ps1
.\scripts\build_installer.ps1
```

A tag `backup/main-before-v0.3.0` é o rollback do estado anterior à release. Para
inspecioná-la sem alterar `main`:

```powershell
git fetch origin --tags
git switch --detach backup/main-before-v0.3.0
```

Uma restauração de desenvolvimento deve ser feita em branch própria a partir
dessa tag. Nenhum arquivo de usuário deve ser sobrescrito sem backup e validação.

## Limitações declaradas

- A detecção automática é assistida e depende da imagem, iluminação, contraste e
  configuração; não é prometida como segmentação perfeita universal.
- O GLTF/GLB atual não inclui UV, materiais, extrusão ou runtime 2.5D.
- Física dinâmica completa, modelagem 3D, rigging, fotogrametria e suporte nativo
  completo ao Unreal estão fora do escopo entregue.
- Linux e macOS não são plataformas públicas suportadas nesta versão.
- Os adaptadores nativos permanecem source-only; não incluem binários proprietários
  nem downloads automáticos.
- Assinatura digital, certificação e formalizações jurídicas não são alegadas nem
  tratadas como gates técnicos obrigatórios.

## Documentação canônica

- [Plano de Cenários Parallax e Paleta](docs/PLANO_CENARIOS_PARALLAX_E_PALETA_2026-08-18.md)
- [Definição do produto](docs/DEFINICAO_DO_PRODUTO.md)
- [Matriz de funcionalidades](docs/MATRIZ_FUNCIONALIDADES_ATUAL.md)
- [Política de qualidade e evidências](docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md)
- [Política de não regressão](docs/POLITICA_NAO_REGRESSAO.md)
- [Checklist de release pública](docs/CHECKLIST_RELEASE_PUBLICA.md)
- [Índice de evidências](docs/evidence/README.md)
- [Contrato GLTF/GLB](docs/CONTRATO_GLTF_GLB_NEOENG_D_TRACE.md)
- [Contrato da CLI](docs/CONTRATO_CLI.md)
- [Changelog](CHANGELOG.md)
- [Política de segurança](SECURITY.md)
- [NOTICE](NOTICE.md)

Snapshots históricos são preservados. Documentos vivos distinguem o estado atual,
a evidência de um SHA específico e o histórico do projeto.

## Licença e publicação

NeoEng-D-Trace é um projeto proprietário com repositório público; não há licença
open source atribuída. Este README descreve o produto e suas validações técnicas,
não constitui parecer jurídico, certificação de conformidade ou promessa de
suporte fora das limitações declaradas.

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
