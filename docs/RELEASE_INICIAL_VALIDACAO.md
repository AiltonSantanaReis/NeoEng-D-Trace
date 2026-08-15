# Release Inicial de Validação — NeoEng-D-Trace

**Status:** modelo operacional preparado; aprovação do proprietário pendente
**Data:** 15 de agosto de 2026

## Decisão de roadmap

As primeiras disponibilizações do projeto serão tratadas como **releases de
validação**, destinadas a usuários/avaliadores identificados e claramente
rotuladas como pré-release. Elas não serão apresentadas como release pública
oficial ou distribuição comercial madura.

A assinatura de código de `R-014` fica deliberadamente para futuras
builds/releases, depois da validação com usuários e do crescimento do projeto.
Sua ausência não bloqueia uma release inicial de validação, desde que os
controles abaixo sejam cumpridos.

## Controles obrigatórios para cada release inicial

- commit-fonte, árvore limpa, versão e manifesto vinculados;
- SHA-256 dos artefatos publicado junto da release;
- testes locais e CI Linux/Windows registrados, sem transformar CI verde em
  aprovação automática;
- instalação, execução, exportação, atualização, reparo e desinstalação
  exercitados no candidato quando aplicável;
- aviso explícito de que os artefatos Windows podem não ter assinatura;
- identificação do público-alvo como avaliadores de validação;
- canal de contato e procedimento para receber relatos de falha;
- política de dados, NOTICE e atribuições anexados ao candidato;
- nenhum segredo, caminho pessoal ou evidência não reproduzível no pacote.

## Limites

Esta decisão não fecha `R-014`, não substitui revisão jurídica e não autoriza
chamar o candidato de release oficial. `R-015` permanece parcialmente aberto
até que o proprietário confirme texto jurídico, dados, atribuições, identidade
visual e contato.

## Aprovação do proprietário

- Nome/titular: __________________________________________
- Data: _________________________________________________
- Versão autorizada: _____________________________________
- Escopo: [ ] avaliadores identificados  [ ] pré-release pública rotulada
- Observações: ___________________________________________
