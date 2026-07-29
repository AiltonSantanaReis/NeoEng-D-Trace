# Etapa 0.6R — Realinhamento documental, privacidade e preparação da renomeação

**Base obrigatória:** checkpoint funcional 0.5.2F3 + reconciliação documental 0.6A1.  
**Natureza:** documentação, metadados de autoria e CI.  
**Alteração funcional:** nenhuma.

## Objetivos

1. consolidar as decisões do produto;
2. formalizar o nome NeoEng-D-Trace;
3. remover dados locais e placeholders de autoria;
4. retirar o envio de cobertura para serviço externo;
5. alinhar a CI ao Python 3.11;
6. estabelecer a estratégia do repositório limpo;
7. preparar a renomeação sem executá-la.

## Arquivos modificados

- `README.md`;
- `CHANGELOG.md`;
- `pyproject.toml`;
- `.github/workflows/ci.yml`;
- `docs/DEFINICAO_DO_PRODUTO.md`;
- `docs/PLANO_RENOMEACAO.md`;
- `docs/ESTRATEGIA_GITHUB.md`;
- `docs/VALIDACAO_ETAPA_0.md`.

## Arquivos adicionados

- `docs/DECISAO_IDENTIDADE_NEOENG_D_TRACE.md`;
- `docs/ETAPA_0_6R_REALINHAMENTO_PRIVACIDADE.md`.

## Privacidade

Removido ou bloqueado nesta etapa:

- caminho absoluto da conta local do Windows removido da documentação;
- placeholder genérico de autoria removido;
- upload de cobertura para serviço externo;
- possibilidade de confundir o `.git` histórico com o novo repositório.

Identidade técnica registrada:

```text
NeoEng-D-Trace Maintainer
169040421+AiltonSantanaReis@users.noreply.github.com
```

O nome de usuário público do GitHub permanece visível no endereço `noreply`, mas o e-mail pessoal não é exposto.

## Preservação

A etapa não altera:

- `app.py`;
- qualquer arquivo em `src/`;
- testes ativos;
- algoritmos;
- UI de runtime;
- formatos e exportações;
- índice Git;
- commits, tags ou remotes.

Os quatro hashes críticos da 0.5.2F3 devem permanecer exatos.

## Portões de aplicação

A aplicação deve recusar quando:

- o HEAD histórico esperado não estiver presente;
- houver stage Git;
- existir remote configurado;
- a identidade local não corresponder à aprovada;
- qualquer arquivo-alvo tiver sido editado depois do snapshot auditado;
- algum hash crítico da 0.5.2F3 divergir;
- um arquivo novo já existir com conteúdo diferente.

## Portões de validação

- payload com hashes corretos;
- zero ocorrência do caminho pessoal auditado;
- zero placeholder de autoria;
- zero referência a serviço externo de cobertura;
- zero referência aos nomes de outros projetos auditados;
- nenhum remote;
- stage vazio;
- hashes críticos da 0.5.2F3 intactos;
- testes específicos da 0.5.2F3 aprovados no Windows;
- suíte oficial aprovada no Windows.

## Limites e próximos passos

A Etapa 0.6R não renomeia o runtime. O passo seguinte será uma etapa isolada para criar o módulo central de identidade e migrar strings de runtime sem refatoração funcional.

O baseline novo e o primeiro push somente serão considerados depois da renomeação, auditoria de privacidade, instalação limpa e testes completos.
