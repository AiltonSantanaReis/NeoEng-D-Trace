# Evidência — Etapa 3 / Pacote 1: persistência versionada

## Identificação

- Etapa: `3 — Persistência versionada e confiável`
- Pacote: `1 — Formato de projeto v1, round-trip, migração e escrita atômica`
- Pull request funcional: `#11`
- Base funcional: `0ff7e66767cedd0ad949a86fc8dae476d7c6594c`
- Commit funcional inicial: `349e2869623d70a23882d08135c770d30cd38fb3`
- Commit funcional aprovado: `891fbc9550b5bba9bce041272da1db1f3bc3a7b3`
- Merge commit funcional: `4a45e9c396da6cd63f44f1cf9792526c305478ec`
- Branch funcional: `feat/etapa-3-persistencia-versionada`
- Data de geração desta evidência: `2026-07-31T23:28:57.508511-03:00`
- Responsável: Ailton Santana Reis

## Objetivo e escopo

Implementar um contrato versionado e estrito para projetos NeoEng-D-Trace sem
substituir o ciclo de Abrir/Salvar da interface, que permanece destinado à
Etapa 4.

O Pacote 1 cobre:

- extensão `.ndtproj`;
- identificador `neoeng-d-trace-project`;
- versão de schema `1`;
- serialização determinística em JSON UTF-8;
- camadas, objetos, grupos, polígonos, colisões personalizadas e Béziers;
- referência externa de imagem e SHA-256 opcional;
- migração controlada do único formato legado conhecido;
- rejeição de versões futuras ou desconhecidas;
- rejeição de campos desconhecidos, tipos incorretos, chaves duplicadas,
  BOM, UTF-8 inválido e valores não finitos;
- limite de arquivo de 64 MiB testado antes e depois da leitura;
- limites de objetos e total de pontos implementados no schema, com fronteiras
  ainda não exercitadas explicitamente por testes deste pacote;
- escrita atômica com arquivo temporário, sincronização e `os.replace`;
- preservação do arquivo anterior quando a substituição atômica falha;
- rejeição de path traversal em referências relativas POSIX, Windows e mistas.

## Alterações funcionais auditadas

A comparação entre `0ff7e66767cedd0ad949a86fc8dae476d7c6594c` e `891fbc9550b5bba9bce041272da1db1f3bc3a7b3`
contém exatamente 13 caminhos e dois commits. O escopo inclui o ADR do formato,
o schema, o serviço de I/O, os erros de domínio, a integração com `Scene` e as
suítes específicas de contrato, round-trip, migração, falhas e atomicidade.

## Testes de persistência

A suíte comprova:

- round-trip de uma cena completa;
- preservação de polígonos, colisões personalizadas e segmentos Bézier;
- preservação de camadas, grupos, visibilidade, bloqueio e ordem;
- saves repetidos e save/load/save byte a byte idênticos;
- referência de imagem ausente ou alterada sem reescrever silenciosamente o
  hash originalmente carregado;
- projeto vazio válido;
- migração legada com avisos explícitos;
- rejeição de versões `0`, `2` e `999`;
- rejeição de identificador incorreto, JSON malformado, BOM, UTF-8 inválido,
  `NaN`, campos extras, tipos incorretos e referências inválidas;
- não mutação da cena quando o carregamento falha;
- rejeição de chaves JSON duplicadas;
- falha de escrita preservando o destino anterior e removendo temporários;
- sucesso de escrita sem temporários residuais;
- rejeição de arquivo acima do limite antes e depois da leitura;
- rejeição de `../`, `..\`, separadores mistos, caminho vazio e byte NUL.

## Validação da PR funcional

- Workflow: `Private validation`;
- execução: `#40`;
- Run ID: `30672383923`;
- evento: `pull_request`;
- HEAD funcional: `891fbc9550b5bba9bce041272da1db1f3bc3a7b3`;
- conclusão: `success`;
- Linux `test`: Job `91292624183`, `success`;
- Windows `test-windows`: Job `91292624143`, `success`;
- testes: `212 passed` nos dois sistemas;
- cobertura: `4617` de
  `9249` linhas, taxa
  `0.4992`, exibida como `50%`;
- baseline antes e depois: `222 arquivos`;
- Flake8 fatal: `0`;
- Black: `102 arquivos sem alteração`;
- isort: aprovado;
- mypy: `0` problemas em `62 arquivos`.

Artefatos da PR:

- Linux: `8809253261` —
  `sha256:e46e23f75bfe769f891db3e32aad13886d1559eacd0a9690fb8cdc5be1a3d598`;
- Windows: `8809264206` —
  `sha256:0ee1d59cb5628afe95b7b8532131cc317d41b614caaa28e0ee27b33223b6729b`.

## Validação da `main` depois do merge funcional

- Workflow: `Private validation`;
- execução: `#41`;
- Run ID: `30672598358`;
- evento: `push`;
- branch: `main`;
- commit: `4a45e9c396da6cd63f44f1cf9792526c305478ec`;
- conclusão: `success`;
- Linux `test`: Job `91293265047`, `success`;
- Windows `test-windows`: Job `91293265003`, `success`;
- testes e cobertura: idênticos ao contrato aprovado da PR;
- baseline antes e depois: `222 arquivos`.

Artefatos da `main`:

- Linux: `8809324964` —
  `sha256:3b3a9a45d7661231b5f08e67e582165ed84d0ee106a7484d812f0339df9a610f`;
- Windows: `8809335229` —
  `sha256:d2371050d07d0859491d57d510684710989d862f185e8426ba609fbb63c8af47`.

## Artefatos permanentes

- Pacote bruto: `NeoEng-D-Trace_Etapa3_Pacote1_Raw_Evidence_Bundle.zip`;
- tamanho do pacote bruto: `1753510 bytes`;
- SHA-256 do pacote bruto: `411981900d5f3c795e0336a4a813bfe4311d25f647cb6a878b8f7239c2311d8f`;
- pacote pós-merge: `NeoEng-D-Trace_Etapa3_Pacote1_PostMerge_Main_20260731_232857.zip`;
- tamanho do pacote pós-merge: `2542880 bytes`;
- SHA-256 do pacote pós-merge: `f8ce9be99ceae4e9859acff3e9f1f967a5c35edca85288a4b0032e6e8f4caaf0`.

Os pacotes foram reabertos, tiveram membros duplicados e path traversal
verificados e contêm checksums internos. Os quatro ZIPs originais do GitHub
foram preservados byte a byte e comparados com os digests publicados.

## Falha de segurança encontrada e corrigida

A primeira revisão da PR identificou que caminhos relativos com componente
`..` ainda eram aceitos. O merge foi bloqueado. A correção
`891fbc9550b5bba9bce041272da1db1f3bc3a7b3` passou a normalizar separadores e rejeitar traversal,
texto vazio e byte NUL. O HEAD foi revalidado integralmente antes do merge.

## Riscos

- `R-001` possui evidência suficiente para encerramento após a integração desta
  documentação e o CI final da `main`;
- `R-002` permanece aberto porque o ciclo Abrir/Salvar da interface não pertence
  a este pacote;
- `R-007` permanece parcialmente aberto: a persistência de Bézier foi resolvida,
  mas métricas e validações geométricas pertencem à Etapa 8;
- `R-012` permanece aberto: o limite de arquivo e validações de entrada foram
  testados, mas as fronteiras dos limites de objetos e pontos ainda não possuem
  testes explícitos e outras superfícies operacionais permanecem fora do pacote.

## Limitações

Esta evidência não declara:

- UI Abrir/Salvar concluída;
- autosave ou recuperação de sessão;
- compatibilidade com versões futuras desconhecidas;
- ausência total de bugs;
- produto pronto para release;
- cobertura integral de UI e ferramentas;
- encerramento integral da Etapa 3.

## Decisão

**APROVADO PARA INTEGRAÇÃO DO REGISTRO DE ENCERRAMENTO DO PACOTE 1**

O encerramento formal depende ainda da PR documental, dos jobs Linux e Windows
dessa PR, do merge pelo HEAD revisado e do workflow final da `main`.
