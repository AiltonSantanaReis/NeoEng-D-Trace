# Identidade Visual e Atribuições — NeoEng-D-Trace

**Status:** ATIVO CANDIDATO RECEBIDO; DIREITOS E ATRIBUIÇÃO PENDENTES

## Ícone proposto

O ícone fornecido para avaliação deve ser tratado como um ativo candidato, não
como ativo oficialmente publicado. Antes da integração, devem ser confirmados:

- autoria ou autorização de uso e redistribuição;
- ausência de marcas de terceiros sem autorização;
- titular que deve aparecer na atribuição;
- licença aplicável ao arquivo original e às versões derivadas.

O arquivo recebido e versionado em `assets/branding/neoeng-d-trace-icon-source.png` é um PNG paletizado de `878×810`, modo `P`, com SHA-256
`17dde3dc0d616cef8927403cb3b2b15aa818960776605eb2a7d2b99b8e5adedc`. Para Windows, a
integração técnica deve gerar um `.ico` com canvas quadrado, transparência quando
aplicável e múltiplas resoluções, no mínimo `16`, `32`, `48`, `64`, `128` e
`256` pixels.

## Integração necessária

- o arquivo-fonte candidato já está versionado; confirmar autorização antes de tratá-lo como ativo oficial;
- gerar e versionar o `.ico` derivado somente após essa confirmação;
- usar o ícone no executável GUI, no instalador e nos atalhos;
- verificar visualmente as resoluções pequenas e grandes;
- registrar SHA-256 dos ativos no manifesto de release;
- incluir a atribuição em `NOTICE` ou documento equivalente;
- repetir os testes de build, instalação e desinstalação.

## Bloqueio atual

O ícone foi recebido e pode acompanhar uma release inicial de validação como
ativo candidato, desde que a documentação o identifique assim. Ele ainda não
deve ser declarado identidade visual oficial enquanto origem, direitos e
atribuição não forem confirmados. Isso mantém `R-015` parcialmente aberto sem
bloquear a validação inicial autorizada.
