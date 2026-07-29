# Correção 0.5.2F2 — integração do laço magnético com imagens OpenCV

## Falha observada no Windows

Após o primeiro clique, o movimento do mouse gerava repetidamente:

```text
AttributeError: 'numpy.ndarray' object has no attribute 'convertToFormat'
```

A importação real usa `cv2.imread(..., cv2.IMREAD_UNCHANGED)` e armazena a imagem
na cena como `numpy.ndarray` em BGR, BGRA ou escala de cinza. O adaptador do laço
magnético aceitava somente `QImage`, representação usada nos testes Qt iniciais.

## Correção

- aceitação explícita de `numpy.ndarray` 2D, BGR e BGRA;
- conversão correta da ordem OpenCV para escala de cinza `uint8` contígua;
- manutenção da compatibilidade com `QImage`, inclusive padding por linha;
- rejeição controlada de tipos ou formatos inválidos, sem exceção em cada movimento;
- teste de integração que usa a mesma representação produzida por `cv2.imread`;
- correção da fixture de histórico local anteriormente preparada na 0.5.2F1.

## Arquivos funcionais alterados

- `src/tools/magnetic_lasso.py`
- `src/tools/magnetic_lasso_engine.py`

Nenhum algoritmo de seleção, preset, exportador ou formato de projeto foi removido.
O rollback restaura exatamente a 0.5.2F.
