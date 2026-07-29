# Decisão de identidade — NeoEng-D-Trace

**Status:** aprovada e consolidada em árvore única.  
**Data:** 27 de julho de 2026.

## Decisão

O produto anteriormente identificado como `PolygonTool` passa a se chamar **NeoEng-D-Trace**.

| Elemento | Valor |
|---|---|
| Nome de exibição | `NeoEng-D-Trace` |
| Distribuição Python | `neoeng-d-trace` |
| Código-fonte interno | `src/` |
| Entrada de desenvolvimento | `app.py` |
| Entrada de console | `src.launcher:main` |
| Executável futuro | `NeoEng-D-Trace.exe` |
| Identidade de commit | `NeoEng-D-Trace Maintainer` |
| Operação principal | offline |
| Modelo | proprietário e comercial |

## Decisão arquitetural vinculante

A troca de nome não migrará o código para uma segunda árvore. O diretório `neoeng_d_trace/`, aliases entre pacotes e a entrada `python -m neoeng_d_trace` não fazem parte da arquitetura final.

`APP_ID = neoeng_d_trace` é somente um identificador estável do aplicativo. Toda implementação permanece em `src/`.

## Restrições

- a decisão técnica não equivale a registro de marca;
- o repositório permanecerá privado;
- referências históricas a PolygonTool serão preservadas somente quando necessárias;
- formato de projeto, configuração em AppData, build e instalador são melhorias independentes;
- nenhuma operação Git faz parte desta consolidação.
