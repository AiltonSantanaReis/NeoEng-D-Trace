# Estratégia do repositório privado NeoEng-D-Trace

## 1. Repositório de destino

```text
SSH:   git@github.com:AiltonSantanaReis/NeoEng-D-Trace.git
HTTPS: https://github.com/AiltonSantanaReis/NeoEng-D-Trace.git
```

O repositório deve estar **privado** antes do primeiro push.

## 2. Separação obrigatória do histórico

O repositório local atual contém 15 commits históricos com metadados antigos de autoria. Esse `.git` será preservado somente para recuperação local e não será enviado.

O novo repositório será criado a partir de uma árvore limpa após:

1. realinhamento documental e privacidade;
2. renomeação técnica;
3. testes completos no Windows;
4. auditoria de segredos e caminhos;
5. revisão de arquivos versionáveis;
6. criação de baseline novo sem o histórico antigo.

Proibido no repositório histórico:

```text
git push --all
git push --mirror
git remote add origin <repositório-novo>
```

## 3. Identidade de commits

```text
NeoEng-D-Trace Maintainer
169040421+AiltonSantanaReis@users.noreply.github.com
```

A identidade deve ser configurada com `--local` no novo repositório e verificada antes do primeiro commit.

## 4. Privacidade

Não versionar:

- `.venv`;
- caches e bytecode;
- logs;
- cobertura local não aprovada;
- configurações pessoais;
- caminhos absolutos de usuário;
- arquivos recentes;
- imagens/projetos particulares;
- backups e snapshots;
- tokens, chaves, senhas ou credenciais;
- bundles do histórico local;
- pacotes de auditoria com dados desnecessários.

Nenhum serviço externo receberá cobertura, telemetria, assets ou logs sem decisão formal. A CI poderá guardar artefatos de curta retenção dentro do próprio GitHub privado.

## 5. Preparação antes do primeiro push

1. confirmar visibilidade privada;
2. preservar o projeto histórico e bundle local;
3. criar diretório novo sem `.git` antigo;
4. copiar somente arquivos aprovados pelo manifesto;
5. aplicar a renomeação validada;
6. remover arquivos gerados e locais;
7. verificar segredos, autoria e caminhos;
8. instalar do zero em Python 3.11;
9. executar testes unitários, integração, Qt e smoke test;
10. revisar README, licença e limitações;
11. criar o primeiro commit com identidade `noreply`;
12. adicionar o remote apenas no repositório novo;
13. realizar push somente da branch `main`.

## 6. Primeiro histórico recomendado

Não comprimir limpeza, renomeação, refatoração e funcionalidade em um commit opaco. A árvore de distribuição poderá começar com:

1. `chore: import audited NeoEng-D-Trace baseline`;
2. `docs: add verified product and privacy decisions`;
3. `chore: establish reproducible Python 3.11 environment`;
4. `test: establish baseline validation suites`;
5. `fix: resolve confirmed baseline defects`.

A composição final será decidida após a renomeação, sem transportar os 15 commits locais.

## 7. Branches

- `main`: sempre instalável e com checks obrigatórios aprovados;
- branches curtas: `fix/...`, `refactor/...`, `feat/...`, `docs/...`, `build/...`.

Fases são milestones/issues, não branches permanentes.

## 8. Proteções de `main`

- pull request obrigatório quando a plataforma permitir;
- checks obrigatórios;
- branch atualizada antes do merge;
- impedir force push;
- impedir exclusão;
- checklist de revisão mesmo com um mantenedor;
- squash ou commits convencionais conforme decisão registrada.

## 9. CI mínima

### Windows

- Python 3.11;
- instalação reproduzível;
- compilação;
- testes unitários e de integração;
- testes Qt;
- smoke test da aplicação;
- build PyInstaller em job separado.

### Linux

- algoritmos puros;
- lint e type check;
- testes headless;
- Qt offscreen quando aplicável.

Testes Linux não significam suporte oficial ao sistema.

### Serviços externos

- serviço externo de cobertura removido;
- nenhuma telemetria;
- artefatos de cobertura limitados ao GitHub privado e com retenção curta;
- ações de terceiros devem ser versionadas e revisadas antes de produção.

## 10. Issues e rastreabilidade

Labels sugeridas:

- `priority:P0`, `priority:P1`, `priority:P2`;
- `area:domain`, `area:ui`, `area:imaging`, `area:physics`, `area:export`, `area:build`;
- `type:bug`, `type:refactor`, `type:test`, `type:docs`, `type:decision`;
- `status:blocked`, `status:needs-reproduction`, `status:verified`.

Todo bug deve conter versão/commit, ambiente, reprodução, esperado, obtido, log, arquivo mínimo autorizado, frequência e indicação de regressão.

## 11. Pull requests

Checklist mínimo:

- escopo único;
- arquivos alterados listados;
- nenhum arquivo gerado ou local;
- testes adicionados/atualizados;
- comandos e resultados anexados;
- impacto no formato de projeto;
- impacto de segurança e privacidade;
- documentação atualizada;
- rollback.

## 12. Tags e versões

- `baseline-import-YYYYMMDD`;
- `v0.3.0-alpha.1` após ambiente reproduzível;
- `v0.5.0-alpha.1` após formato versionado;
- `v0.8.0-beta.1` após feature freeze;
- `v1.0.0` somente com todos os critérios de lançamento.

Antes de 1.0, qualquer quebra de formato ainda exige migrador e nota explícita.

## 13. Regra de publicação

Não tornar público até que:

- nome e marca estejam validados;
- licença jurídica esteja definida;
- dados pessoais e caminhos tenham sido removidos;
- README represente o estado real;
- instalação e testes do zero sejam aprovados;
- vulnerabilidades críticas conhecidas estejam resolvidas;
- formato de projeto e política de migração estejam definidos.
