# Adendo — integridade dos artefatos de evidência

## Identificação

- Estado: correção local em andamento; sem commit, push ou merge nesta mudança.
- Escopo: cadeia de bytes dos manifests em `docs/evidence/artifacts/`.
- Regra aplicada: UTF-8/LF para texto, bytes originais para binários, `sha256` e tamanho comparados sem normalização durante a validação.

## Problemas confirmados

A auditoria encontrou geradores que escreviam texto com o comportamento padrão do Windows, enquanto alguns digests eram calculados sobre bytes do working tree. Também havia referências a logs ignorados por `*.log`, referências sem rastreamento e dois logs históricos da etapa 6 que não existem no histórico Git consultado.

Essas divergências não foram tratadas como sucesso. Os dois logs ausentes permanecem declarados como `unavailable_artifacts` nos índices correspondentes; nenhum conteúdo foi recriado.

## Correções aplicadas

- criado `tools/evidence_integrity.py`;
- adicionada política de EOL em `.gitattributes`;
- removida a exclusão silenciosa dos logs de evidência em `.gitignore`;
- geradores auditados passaram a escrever texto com `newline="\n"`;
- manifests existentes foram reparados somente por operação explícita, com digests recalculados dos bytes efetivos;
- índices que apontavam para membros de ZIP passaram a declarar o membro arquivado verificável;
- CI Linux/Windows passou a executar `python tools/evidence_integrity.py --require-tracked`.

## Resultado verificável local

A execução do validador sem exigir rastreamento retornou `Evidence integrity passed: 16 manifests validated.` após a correção. Os testes dedicados cobrem normalização de EOL, hash obsoleto, referência não rastreada, extração de ZIP e formas de manifest.

Este resultado não substitui o gate do commit candidato: até que todos os arquivos pretendidos estejam rastreados e o CI passe, a mudança não é aprovada nem integrada.

## Limitações preservadas

- não foram inventados logs históricos ausentes;
- não foi alterado o conteúdo para transformar falha funcional em sucesso;
- não foram apresentados resultados de engine, CI remoto ou merge que ainda não ocorreram;
- a validação de conteúdo funcional continua separada da validação de integridade dos bytes.

## Decisão

PARCIAL — a regra e os bloqueios estão implementados localmente; a conclusão exige rastreamento do pacote final e execução do CI correspondente ao commit candidato.
