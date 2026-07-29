# Validação da consolidação em árvore única

## Portões automáticos

1. integridade e estado anterior;
2. compilação sintática de `app.py`, `src/`, testes, benchmarks e ferramentas;
3. ausência do diretório `neoeng_d_trace/`;
4. ausência de imports para o namespace removido;
5. entrada `app.py --help` com identidade NeoEng-D-Trace;
6. testes de consolidação, identidade, JSON e GLTF/GLB;
7. suíte oficial completa no Windows/Python 3.11;
8. auditoria de privacidade e mistura de projetos.

## Validação manual necessária

- abrir por `python app.py`;
- alternar português/inglês;
- carregar imagem e projeto antigo;
- criar e selecionar um polígono;
- exportar sprite, atlas, JSON e GLB;
- fechar e reabrir confirmando preferências da raiz.

A etapa não executa Git.
