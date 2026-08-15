# Plano de Migração do Builder MSI — R-016

**Status:** VALIDADO TECNICAMENTE / GOVERNANÇA DE RELEASE PENDENTE

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

## Evidência da migração — candidato técnico

A prova local da migração foi executada em Windows com WiX 4.0.6 restaurado pelo
manifesto `.config/dotnet-tools.json`. O WiX 7.0.0 não foi usado porque a própria
ferramenta bloqueou a execução solicitando aceitação do Open Source Maintenance
Fee EULA; nenhuma aceitação foi feita implicitamente.

No bundle congelado do baseline, dois builds independentes do MSI produziram:

- 313 arquivos empacotados, 103026688 bytes por MSI;
- SHA-256 idêntico nos dois artefatos: `b7e6afa36ab393db5d171fbff69730f7aec3ab64d1df533cbf0571826427e7cd`;
- `ProductCode`, `PackageCode` e `UpgradeCode` estáveis e derivados do contrato existente;
- `PackageCode` e datas do Summary Information normalizados antes da validação final.

O candidato recompilado após as correções passou a validação real de instalação:

- instalação per-user: exit code `0`;
- CLI, projeto, JSON, GLB, perfis Godot/Unity e GUI: `SUCCESS`;
- desinstalação: exit code `0`, sem resíduos no diretório instalado;
- estado do usuário preservado fora do diretório de instalação.

Com as provas local e remota acima, o risco técnico de migração do R-016 está
**VALIDADO**: toolchain pinada, builds determinísticos, CI Linux/Windows, instalação,
upgrade, reparo, execução e remoção foram exercitados. Permanece uma pendência de
governança para a release: revisar formalmente os termos/licença da toolchain e
manter assinatura, identidade legal e aprovação pública nos gates R-014/R-015.
Os MSI de validação continuam sem assinatura digital; isso é esperado e não é
apresentado como aprovação de publicação.

## Upgrade e reparo — evidência local

O MSI oficial produzido pelo script completo no commit `828cf626b7ce382c360723b1be10c4ce718c4187` também foi exercitado contra o MSI baseline anterior:

- upgrade no mesmo diretório: MSI anterior `0`, MSI WiX novo `0`, desinstalações `0`, resíduos `0`;
- repair com `/fa`: instalação `0`, um `NeoEng-D-Trace-CLI.exe` removido deliberadamente foi restaurado, repair `0`, desinstalação `0`, resíduos `0`;
- os logs e relatórios ficam nos artefatos locais de validação e não são usados como evidência versionada sem hash/manifesto.

A validação demonstra o comportamento técnico do builder, mas não transforma o artefato em release público: assinatura, identidade legal, publicação e aprovação final permanecem gates separados.
