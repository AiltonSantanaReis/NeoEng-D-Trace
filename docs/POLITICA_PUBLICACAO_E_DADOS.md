# Política de Publicação e Dados — NeoEng-D-Trace

**Status:** DECISÃO DO PROPRIETÁRIO REGISTRADA; assinatura, licenciamento e trâmites jurídicos não são gates obrigatórios de release

**Objetivo:** registrar o comportamento de dados conhecido e os critérios para
uma futura publicação pública. Este documento não é aprovação jurídica, contrato
de licença nem declaração de conformidade regulatória.

## Escopos de distribuição

### Build de validação

- Pode ser distribuída a avaliadores identificados sem assinatura de código.
- Pode ser identificada como build técnica quando esse for o objetivo, mas isso
  não cria um bloqueio para publicação posterior.
- Deve informar que o Windows pode exibir aviso de publicador desconhecido.
- Cada build deve estar vinculada a um commit, manifesto e relatório de validação.

### Release oficial inicial

Pode ser disponibilizada sem assinatura de código por decisão expressa do
proprietário. Não é obrigatório rotulá-la como release de validação. Os
artefatos devem continuar vinculados a commit/hash, acompanhados deste pacote
documental e descritos honestamente como não assinados. Isso registra uma
decisão de risco de publicação; não certifica conformidade jurídica.

### Releases futuras

A assinatura, o licenciamento, as atribuições formais e outros trâmites podem
ser executados quando o proprietário decidir, especialmente se houver demanda
de usuários e clientes. Os critérios técnicos de instalação, atualização,
desinstalação, privacidade e suporte continuam obrigatórios sempre que o
candidato mudar.

## Dados tratados no escopo atual

O fluxo aprovado é local/offline para a operação principal. O aplicativo trata
arquivos que o usuário seleciona ou gera, incluindo imagens, projetos, assets,
exportações, logs e snapshots de recuperação quando esses recursos são usados.

Essa descrição não autoriza a afirmação ampla de que “nenhum dado é coletado”
sem uma revisão final do código, das dependências, do empacotamento e dos canais
de distribuição.

## Decisões ainda necessárias

- responsável legal e nome de publicação;
- licença ou modelo comercial da distribuição;
- endereço de contato para suporte e solicitações de dados;
- existência ou não de telemetria, atualização automática e serviços remotos;
- prazo de retenção e procedimento de exclusão de logs, projetos e snapshots;
- inventário e atribuições das dependências e conteúdos de terceiros;
- jurisdição e revisão jurídica aplicável.

## Critério de aprovação

Este documento registra dados reais e não constitui gate jurídico/comercial.
O proprietário pode atualizar anexos quando necessário.
Nenhum campo pendente deve ser preenchido com dados inventados ou suposições.

## Relação com riscos

- `R-015` tem a decisão de roadmap registrada: a formalização jurídica, de
  licenciamento e atribuições pode ficar para futuras versões e não bloqueia a
  release.
- A assinatura de código é tratada separadamente em `R-014` e foi deliberadamente
  adiada para futuras builds/releases, após validação de usuários e crescimento
  do projeto. Ela não bloqueia a primeira release oficial por decisão do
  proprietário.
- O roteiro operacional da primeira release está em
  `docs/RELEASE_INICIAL_VALIDACAO.md`.
