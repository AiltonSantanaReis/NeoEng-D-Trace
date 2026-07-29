# Correção 0.5.2F3 — Finalização segura do laço magnético

## Problema observado

Após a correção de leitura de imagens OpenCV, o laço passou a calcular a pré-visualização, mas alguns caminhos finais continham retornos colineares, sobreposição local ou área insuficiente. O contrato estrito de `Scene` rejeitava esses anéis e o `CommandManager` registrava `Invalid polygon`.

## Correção

- remoção determinística de duplicatas consecutivas e do ponto final repetido;
- remoção de vértices colineares e retornos locais A-B-A;
- simplificação antes da criação do objeto;
- verificação de área mínima e auto-interseção;
- normalização anti-horária;
- validação pelo mesmo contrato de `Scene` antes de executar o comando;
- preservação das âncoras quando o contorno continua inválido;
- nenhum `auto_repair` silencioso foi habilitado.

## Compatibilidade

Os modos Preciso e Legado foram preservados. O rollback restaura exatamente a 0.5.2F2.
