# Plano de recriação de evidências frágeis — 2026-08-13

## Resposta objetiva

É possível produzir evidência atual, reprodutível e superior para os pontos frágeis. Não é possível recriar honestamente a mesma execução histórica, com os mesmos timestamps, identidade humana, ambiente e run IDs. Os novos pacotes devem ser chamados de evidência substitutiva atual, nunca de restauração da prova histórica original.

## Provas já recriadas

- Godot `4.7.stable.official.5b4e0cb0f`: execução real, cinco contratos aprovados e relatório bruto preservado.
- Unity `6000.5.7f1` com glTFast `6.19.0`: execução real, cinco contratos aprovados, dois processos com retorno zero e relatório bruto preservado.
- O manifesto vincula os dois relatórios ao commit-fonte e confere seus hashes SHA-256 canônicos, normalizados para LF para produzir o mesmo resultado em Windows e Linux.

## Pacotes históricos sanitizados

Os ZIPs antigos devem permanecer imutáveis, acompanhados de seus hashes e das limitações A-003. Uma evidência substitutiva v2 deve:

1. extrair recursivamente todos os arquivos;
2. sanitizar de forma determinística;
3. recalcular hashes e tamanhos das folhas para as raízes;
4. registrar o mapa de hashes antigos para novos;
5. executar verificação recursiva independente;
6. vincular o pacote ao commit-fonte atual;
7. preservar separadamente os pacotes históricos originais.

Esse processo melhora a cadeia de custódia atual, mas não altera retroativamente a execução histórica.

## Validação manual da Etapa 4

Uma evidência substitutiva deve executar novamente os fluxos atuais com fixtures relativas e determinísticas, preservar projetos produzidos, logs, JSONL, JUnit, capturas e hashes, e separar claramente:

- resultado automático;
- atestação humana;
- casos negativos esperados;
- falhas inesperadas;
- limitações do ambiente.

O `internal_summary_status: FAILURE` histórico não deve ser apagado. A nova evidência deve demonstrar de forma estruturada que cenários negativos esperados não são falhas inesperadas.

## Critério para iniciar a Etapa 14

A recriação atual pode fechar a fragilidade operacional, mas não transforma os pacotes históricos em provas autossuficientes. A Etapa 14 deve consumir somente evidências vinculadas a commit, comandos reproduzíveis, códigos de processo, hashes e artefatos verificáveis; release continua não aprovada até seus próprios gates reais.
