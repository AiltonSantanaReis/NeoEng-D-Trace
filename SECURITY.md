# Política de Segurança

## Versão suportada

A linha `0.2.x` em desenvolvimento recebe correções de segurança. O projeto é
privado e ainda não possui release distribuível aprovada.

## Relato responsável

Use um GitHub Security Advisory privado no repositório. Não publique detalhes
exploráveis em issue, pull request ou discussão pública antes da triagem.

Inclua, quando disponível:

- versão, commit e sistema operacional;
- pré-condições e passos mínimos de reprodução;
- impacto observado e impacto potencial;
- arquivos de prova sanitizados, sem credenciais ou dados pessoais;
- sugestão de mitigação, sem exigir divulgação antecipada.

## Gates obrigatórios

O CI executa:

- `pip-audit` no ambiente resolvido pelo `poetry.lock`;
- Bandit para achados de alta severidade em `src`;
- testes Linux e Windows;
- cobertura de linhas e branches com piso incremental;
- mypy incluindo corpos de funções sem anotação.

Nenhuma execução limpa garante ausência futura de vulnerabilidades. O lock deve
ser auditado novamente antes de cada release e sempre que uma dependência mudar.

## Modelo de ameaça e fronteiras

O aplicativo é principalmente offline. Imagens, projetos, configuração, nomes,
caminhos e parâmetros de exportação são entradas não confiáveis. A aplicação não
deve interpretar conteúdo executável nem iniciar shell a partir dessas entradas.

Os controles atuais priorizam falha controlada antes de decodificação, validação
geométrica quadrática, expansão de grade, alocação de atlas e escrita final. As
saídas são limitadas e, quando o formato permite, substituídas atomicamente.

Limites centrais vigentes:

- imagens: 256 MiB em disco, 8.192 por eixo, 16.777.216 pixels e 128 MiB decodificados;
- projeto: 64 MiB, 100.000 objetos, 1.000.000 pontos e 2.000 pontos por polígono;
- atlas: 16.777.216 pixels por página, 10.000 itens e 16 páginas;
- logs: rotação, backups e sanitização de caminhos absolutos pessoais;
- configuração: 1 MiB, schema estrito e JSON sem chaves duplicadas ou números não finitos.

Esses valores são tetos de segurança, não garantias universais de desempenho.
Arquivos que ultrapassam os contratos são rejeitados; não são truncados ou
aceitos silenciosamente.

## Dados e privacidade

O projeto não requer telemetria nem rede para o fluxo principal. Logs de arquivo
e evidências estruturadas sanitizam caminhos absolutos pessoais conhecidos e
limitam mensagens. Arquivos de projeto podem conter referência de imagem escolhida
pelo usuário; portanto, não devem ser publicados sem revisão e sanitização.

Não registre credenciais, tokens, conteúdo integral de imagens ou dados pessoais.
Sanitização por expressão regular reduz exposição acidental, mas não substitui a
revisão humana antes de publicar artefatos.
