# Validação da Etapa 0.6N1A

## Estado da preparação

Verificações executadas no ambiente de preparação:

- 85 arquivos Python compilados sem erro;
- 51 testes não gráficos selecionados aprovados;
- 3 testes específicos do novo preview headless aprovados;
- benchmark sintético do preview executado em imagens de 512, 1024 e 2048 pixels: aproximadamente 0,070 s, 0,110 s e 0,160 s neste ambiente;
- aplicação transacional e rollback devem ser confirmados pelo pacote;
- nenhum arquivo do usuário foi publicado ou enviado a um remote.

## Limite do ambiente de preparação

PySide6 não está instalado no ambiente Linux usado na preparação. Por isso:

- os testes Qt foram escritos, mas não são declarados aprovados neste ambiente;
- a suíte completa encontrou quatro erros de coleta exclusivamente por ausência de PySide6;
- a validação oficial depende da `.venv` Python 3.11 do Windows do projeto.

## Critério de aprovação

A etapa somente será considerada validada quando o validador do Windows retornar `Etapa 0.6N1A: VALIDADA` e a inspeção visual confirmar:

- português e inglês completos nas superfícies modificadas;
- nenhum texto cortado na paleta;
- Visualizador de Máscara preservando zoom ao trocar idioma;
- Laço Magnético sem bloquear a janela;
- nenhuma regressão nos testes existentes.
