# Política de Publicação e Dados — NeoEng-D-Trace

**Status:** RASCUNHO PENDENTE DE APROVAÇÃO

**Objetivo:** registrar o comportamento de dados conhecido e os critérios para
uma futura publicação pública. Este documento não é aprovação jurídica, contrato
de licença nem declaração de conformidade regulatória.

## Escopos de distribuição

### Build de validação

- Pode ser distribuída a avaliadores identificados sem assinatura de código.
- Deve ser identificada como pré-release técnica, não como release pública.
- Deve informar que o Windows pode exibir aviso de publicador desconhecido.
- Cada build deve estar vinculada a um commit, manifesto e relatório de validação.

### Release pública

Não poderá ser declarada aprovada enquanto permanecer qualquer um dos seguintes
itens:

- assinatura de código ausente nos artefatos Windows;
- texto jurídico, licença e atribuições de terceiros não aprovados;
- política de publicação e dados não aprovada;
- identidade visual e origem do ícone não confirmadas;
- critérios técnicos de instalação, atualização, desinstalação e suporte não
  reproduzidos no candidato final.

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

O proprietário do projeto deve aprovar este documento e seus anexos antes de
qualquer release pública. Nenhum campo pendente deve ser preenchido com dados
inventados ou com uma suposição sobre propriedade intelectual.

## Relação com riscos

- `R-015` permanece aberto até as decisões acima serem registradas e aprovadas.
- A assinatura de código é tratada separadamente em `R-014` e pode ser adiada
  para a primeira release pública sem transformar a build técnica em release.
