# Identidade Visual e Atribuições — NeoEng-D-Trace

**Status:** RASCUNHO PENDENTE DE CONFIRMAÇÃO DE DIREITOS

## Ícone proposto

O ícone fornecido para avaliação deve ser tratado como um ativo candidato, não
como ativo oficialmente publicado. Antes da integração, devem ser confirmados:

- autoria ou autorização de uso e redistribuição;
- ausência de marcas de terceiros sem autorização;
- titular que deve aparecer na atribuição;
- licença aplicável ao arquivo original e às versões derivadas.

O arquivo de origem recebido é um PNG paletizado de `878×810`. Para Windows, a
integração técnica deve gerar um `.ico` com canvas quadrado, transparência quando
aplicável e múltiplas resoluções, no mínimo `16`, `32`, `48`, `64`, `128` e
`256` pixels.

## Integração necessária

- versionar o arquivo-fonte autorizado e o `.ico` derivado;
- usar o ícone no executável GUI, no instalador e nos atalhos;
- verificar visualmente as resoluções pequenas e grandes;
- registrar SHA-256 dos ativos no manifesto de release;
- incluir a atribuição em `NOTICE` ou documento equivalente;
- repetir os testes de build, instalação e desinstalação.

## Bloqueio atual

O ícone ainda não deve ser declarado como identidade visual oficial enquanto a
origem, os direitos e a atribuição não forem confirmados. Isso mantém `R-015`
aberto sem impedir o uso do ativo em uma avaliação privada autorizada.
