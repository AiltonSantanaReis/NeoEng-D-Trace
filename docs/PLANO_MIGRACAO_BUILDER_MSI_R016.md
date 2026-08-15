# Plano de Migração do Builder MSI — R-016

**Status:** ABERTO / PLANEJADO

## Situação comprovada

O builder atual em `tools/package_windows_msi.py` usa `msilib`. O build é
funcional e reproduzível no ambiente validado com Python 3.11, mas não deve ser
tratado como solução futura: `msilib` foi descontinuado no Python 3.11 e removido
no Python 3.13; Python 3.12 foi a última versão que o forneceu.

## Objetivo

Substituir o writer MSI por uma toolchain suportada, preservando o contrato
observável atual e sem alterar silenciosamente o conteúdo instalado.

## Restrições de segurança e compatibilidade

- não executar instaladores gerados antes da validação de hash e origem;
- não alterar GUID de upgrade sem decisão explícita de compatibilidade;
- preservar instalação por usuário, atalhos, arquivos, versão e desinstalação;
- manter ordenação determinística, época de build e manifesto;
- não incluir segredos, certificados ou caminhos pessoais nos artefatos;
- manter a assinatura de código fora do código-fonte e posterior ao build final.

## Fases

1. Extrair o modelo de produto, diretórios, componentes e atalhos do writer atual.
2. Selecionar uma toolchain MSI suportada pelo Python-alvo e pelo CI Windows.
3. Implementar um protótipo que gere o mesmo conjunto de arquivos e metadados.
4. Comparar dois builds independentes por manifesto, estrutura MSI e hashes.
5. Validar instalação, execução GUI/CLI, exportação, reparo, upgrade e remoção.
6. Repetir a validação em Python 3.13 ou superior, conforme o alvo definido.
7. Atualizar lockfile, CI, documentação e evidências somente após os testes.

## Critérios de aceite

O risco só poderá ser encerrado quando:

- a toolchain e suas versões estiverem fixadas e documentadas;
- dois builds independentes passarem no manifesto determinístico;
- instalação limpa e desinstalação não deixarem resíduos inesperados;
- upgrade/reparo preservarem o contrato de arquivos e atalhos;
- GUI, CLI e exportações passarem no candidato produzido;
- o CI reproduzir os mesmos gates em uma máquina Windows limpa;
- o relatório registrar falhas, limitações e hashes reais.

## Decisão de release

O R-016 é dívida de manutenção e não deve ser marcado como resolvido apenas
porque Python 3.11 ainda funciona. A migração pode ser realizada sem comprar
certificado; a assinatura de código é um gate separado do builder.
