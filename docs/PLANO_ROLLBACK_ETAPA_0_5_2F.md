# Plano de rollback — Etapa 0.5.2F para 0.5.2E

O pacote transacional contém os bytes originais e os bytes novos dos arquivos afetados.

## Pré-condições do rollback

O restaurador aceita somente uma 0.5.2F íntegra. Se um arquivo funcional tiver sido editado depois da instalação, o rollback é bloqueado para não apagar trabalho manual.

## Arquivos restaurados

- `src/tools/base_tool.py`;
- `src/tools/magnetic_lasso.py`;
- `src/ui/canvas_view.py`;
- `src/ui/main_window.py`;
- `src/ui/tool_palette.py`.

## Arquivos exclusivos removidos

- motor preciso;
- testes da 0.5.2F;
- documentação da 0.5.2F;
- manifestos e benchmark da 0.5.2F.

## Transação

Antes de alterar o projeto, o script cria backup temporário. Depois da cópia, valida todos os hashes. Em caso de falha intermediária, restaura automaticamente o estado anterior da transação.

O rollback `0.5.2E → 0.5.2D` entregue anteriormente permanece independente e pode ser executado depois que a 0.5.2E for restaurada.
