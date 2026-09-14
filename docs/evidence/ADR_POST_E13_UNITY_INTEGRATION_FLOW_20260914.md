# ADR — Integração do Unity e fluxo externo de licença

**ID:** `ADR-POST-E13-UNITY-INTEGRATION-FLOW`
**Data:** 2026-09-14
**Status:** `PASS`
**Commit auditado:** `b9e305551dc41098fb032ca719755a2fb0eb6978`
**Escopo:** pós-E13, integração local do NeoEng-D-Trace com Unity Hub/Editor
**Requisitos/features:** `REQ-F14-UNITY-INTEGRATION-PREFLIGHT`,
`FEAT-UNITY-HUB-PREFLIGHT`
**Módulo/componente:** `MOD-INTEGRATION-UNITY`,
`CMP-UNITY-INTEGRATION-SETTINGS`

## Decisão

O NeoEng-D-Trace não será um gerenciador de licenças Unity. Login, entitlement,
ativação e validade do plano permanecem sob responsabilidade do Unity Hub e da
conta Unity do usuário. O aplicativo oferecerá uma superfície de integração
para:

1. detectar ou configurar, no estado local do usuário, o executável do Unity
   Hub e o executável do Editor Unity;
2. apresentar um diagnóstico explícito do pré-requisito sem afirmar que a
   licença está ativa;
3. abrir o Unity Hub e a documentação oficial de licenciamento/login;
4. manter o fluxo utilizável com Unity Personal, Plus, Pro, Enterprise ou
   named user, desde que o próprio Unity Hub/Editor esteja instalado e
   autorizado no ambiente do usuário.

O estado salvo conterá somente caminhos absolutos normalizados dos executáveis.
O projeto não lerá, copiará, armazenará ou transmitirá `.ulf`, tokens,
credenciais, cookies, IPC de licensing ou dados de entitlement.

## Contexto e evidência técnica

O bloqueio observado nas execuções controladas pertence ao ciclo de inicialização
do Unity/Unity Hub, e não ao schema, renderer ou editor de cenários do
NeoEng-D-Trace. A integração precisa de um login externo para que o Unity
gerencie o plano Personal; o projeto não pode converter um arquivo local em
prova de entitlement.

Essa decisão evita que a UI apresente um seletor de licença como se ele pudesse
resolver o fluxo Personal ou substituir o Unity Hub. A ação será chamada
**Integração do Unity** e explicará essa fronteira diretamente ao usuário.

## Impacto

### Preservado

- editor de cenário canônico, renderer, runtime, schema de projeto e exportação;
- `view.settings`, seus atalhos e sua identidade de `QAction`;
- estado do projeto e todos os arquivos de licença existentes fora do projeto;
- compatibilidade com configurações anteriores sem migração destrutiva.

### Ampliado

- configuração local com `unity_hub_path` e `unity_editor_path` opcionais;
- comando `integration.unity` acessível pelo menu View, barra de referência e
  paleta de comandos;
- diagnóstico somente leitura e links oficiais para a etapa externa de login.

### Riscos e contenções

| Risco | Contenção |
|---|---|
| Usuário interpretar o diagnóstico como ativação de licença | estado explícito `não verificado pelo NeoEng` e texto de fronteira |
| Executar programa incorreto | seleção validada por nome/extensão e `QProcess` sem shell |
| Expor segredo em configuração ou log | nenhum conteúdo de licença/token é lido; apenas caminhos locais |
| Quebrar menus/atalhos existentes | nova `QAction`; ações canônicas anteriores permanecem as mesmas |
| Auto-detecção esconder configuração inválida | caminho explícito continua visível e recebe estado `ausente` |

## Critérios de aceite

- configuração antiga carrega com os defaults sem alteração;
- seleção e persistência de caminhos ocorre somente após confirmação do diálogo;
- Hub/Editor detectados e ausentes exibem estados distintos;
- abrir Hub usa caminho selecionado/detectado sem shell e sem argumentos
  controlados por texto livre;
- a UI PT-BR e EN mantém rótulos, descrições e acessibilidade coerentes;
- testes focados, de contrato, integração de UI e segurança passam sem
  `skip`, `xfail` ou redução de escopo; a suíte completa preserva e registra
  somente os dois `skipped` controlados preexistentes de symlink;
- qualquer validação nativa de licença continua registrada como evidência
  externa e não é reivindicada pelo aplicativo.

## Resultado da validação

O fluxo foi exercitado na build portátil r2 com o binário nativo em execução:
menu `Visualizar` → `Integração do Unity...` → diagnóstico de pré-requisitos.
Hub e Editor foram detectados no host de validação; o diálogo informa que
login/licença é gerenciado pelo Unity Hub e apresenta o caminho Personal. Isso
comprova a ergonomia do fluxo do projeto, não o entitlement da conta Unity.
Testes focados e suíte oficial, smoke da build e hashes das capturas estão
registrados em
`EVD_POST_E13_UNITY_INTEGRATION_PREFLIGHT_20260914.md`.

O commit auditado `b9e305551dc41098fb032ca719755a2fb0eb6978` vincula a decisão
à implementação, aos testes e à evidência nativa.

## Plano de reversão

Se os gates falharem, remover apenas a nova ação, o diálogo, o módulo de
diagnóstico, os campos aditivos de configuração e os testes/documentos desta
decisão. Não executar reset destrutivo e não alterar o editor canônico.

## Dependências documentais

- [Governança de Integridade, Execução e Antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Índice Documental Ativo Canônico](../INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md)
- [Registro Canônico de IDs](../REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml)
- [Evidência do pré-voo Unity](EVD_POST_E13_UNITY_INTEGRATION_PREFLIGHT_20260914.md)
