# Etapa 0.6O1 — observabilidade da validação manual

## Escopo

Esta etapa não altera a arquitetura, o formato de projeto nem os exportadores.
Ela acrescenta um modo opcional de validação manual com log JSONL local,
privado e imediatamente descarregado em disco.

Ativação:

```powershell
python app.py --validation-log <arquivo.jsonl>
```

Sem esse argumento, o gravador permanece desativado.

## Eventos observados

- abertura e fechamento do aplicativo;
- troca de idioma com verificação do título aplicado;
- abertura de imagem e habilitação dos controles;
- criação de polígono e seleção automática;
- sincronização entre seleção da cena e lista lateral;
- abertura e fechamento do diálogo de exportação;
- exportação de sprite, lote, atlas, metadados JSON, GLB de cena e GLB de objeto;
- avisos, erros e exceções não tratadas.

## Pós-condições

Os eventos de exportação só recebem `SUCCESS` quando o arquivo realmente existe
e possui conteúdo. JSON é reaberto e analisado. GLB exige cabeçalho `glTF` e versão
2. A seleção recebe sucesso somente quando cena e lista apontam para o mesmo
objeto.

## Privacidade

O log não grava coordenadas dos polígonos, conteúdo do projeto ou identificadores
de objeto em texto aberto. Identificadores recebem token SHA-256 truncado e
caminhos completos são sanitizados.

## Correção de logging duplicado

Os exportadores de sprite e atlas não chamam mais `logging.basicConfig`. O logger
do aplicativo não propaga para o logger raiz, enquanto loggers de módulos usam
uma única rota raiz configurada pela aplicação.
