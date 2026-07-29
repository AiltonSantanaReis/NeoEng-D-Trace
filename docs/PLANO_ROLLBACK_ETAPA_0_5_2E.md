# Plano de rollback — Etapa 0.5.2E para 0.5.2D

## Método principal

Aplicar `polygontool_etapa_0_5_2e_rollback_para_0_5_2d.patch` sobre uma árvore 0.5.2E sem edições posteriores nos mesmos arquivos.

## Método alternativo

Extrair `polygontool_etapa_0_5_2d_arquivos_originais_preservados.zip` na raiz do projeto, substituindo somente os arquivos contidos no pacote, e remover os arquivos novos listados no manifesto.

## Verificação

Executar `polygontool_verificar_checkpoint_0_5_2d.ps1 -ProjectRoot <pasta-do-projeto>`. O script compara hashes e confirma que os arquivos exclusivos da 0.5.2E não permanecem.

## Segurança

O `git apply --check` deve ser executado antes do rollback. Se houver conflito, não usar `--reject`, `--3way` ou sobrescrita forçada; primeiro preservar as alterações locais.
