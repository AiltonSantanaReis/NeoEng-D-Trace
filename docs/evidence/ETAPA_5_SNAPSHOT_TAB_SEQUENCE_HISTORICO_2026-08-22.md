# Snapshot histórico da sequência de abas da Etapa 5

Este documento classifica os artefatos `panel-tab-captures` e
`tab-sequence-20260822` como evidência histórica da investigação de artefatos
visuais no painel lateral direito.

O pacote registra a sequência real de abertura das abas Objects, Layers,
Groups e Collision nas resoluções 1920x1080, 1366x768 e 1280x720. O relatório
`diff-report.json` registra que a captura inicial de Objects não era idêntica à
captura após o ciclo de abas, especialmente na resolução compacta. Esse fato
foi usado para localizar a causa no gerenciamento de visibilidade das páginas
do `QTabWidget`.

Após a correção, a validação atual é representada pelos artefatos
`page-visibility-audit` e pelo relatório de auditoria da Etapa 5. Este snapshot
não é um resultado atual, não substitui a auditoria pós-correção e não deve ser
interpretado como aprovação isolada.

Os hashes dos arquivos permanecem nos manifests de cada pacote. Nenhum arquivo
foi reescrito para transformar uma falha histórica em PASS.
