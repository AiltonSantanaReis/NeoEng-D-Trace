# Decisão de controle — revisão humana deferida

**Data:** 2026-09-08  
**Escopo:** E00 / build oficial `2722ac1`  
**Estado resultante:** `IN_PROGRESS / PENDING_EVIDENCE`

## Autorização

O responsável pelo projeto autorizou que a revisão humana/nativa seja realizada
somente na auditoria final, após a conclusão dos demais gates do plano. A
decisão permite continuar os gates automatizados e o trabalho preparatório
controlado sem classificar a etapa como `BLOCKED`.

## Limites preservados

- a captura automatizada continua sendo apenas `PASS_AUTOMATED_CAPTURE_ONLY`;
- a revisão humana não é convertida em `PASS` por esta decisão;
- o achado de truncamento da toolbar permanece registrado no SHA oficial;
- a revisão humana continua obrigatória antes de fechar E00 ou concluir o plano;
- E01 e qualquer etapa posterior continuam sem aceite funcional enquanto E00
  não cumprir todos os critérios;
- symlink Sandbox e skips locais permanecem gates distintos;
- não há autorização para push, merge, tag ou release.

## Critério de encerramento

Na auditoria final, a revisão humana deverá verificar os fluxos críticos,
tradução, layout, usabilidade, toolbar e aba Objetos no mesmo artefato de
proveniência ou em nova build formalmente vinculada. O estado só poderá então
ser atualizado para `PASS`, `FAIL` ou permanecer `PENDING_EVIDENCE` conforme a
evidência observada.
