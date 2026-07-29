# Política de Qualidade e Evidências

## Classificação de resultados

- **APROVADO:** requisito comprovado por procedimento reproduzível.
- **REPROVADO:** requisito executado e não atendido.
- **BLOQUEADO:** execução impedida por causa identificada.
- **NÃO TESTADO:** validação ainda não executada.
- **PARCIAL:** apenas parte do requisito foi comprovada.

## Regras de integridade

- Resultado antigo, cache, documentação ou captura sem commit não constituem prova.
- Teste instável é falha até que a causa seja identificada.
- `skip` e `xfail` exigem motivo, responsável e condição de remoção.
- Mock não substitui validação de arquivo, interface ou exportador real quando o comportamento real é o objeto do teste.
- Mensagem de sucesso só pode ocorrer depois da confirmação do efeito solicitado.
- Exceções não podem ser capturadas silenciosamente quando o resultado puder estar incorreto.

## Regra de parada

Interromper a etapa diante de perda de dados, regressão, build quebrado, divergência não explicada entre plataformas, comportamento não determinístico, queda de cobertura ou alteração fora do escopo.

## Relatório de evidência

Cada relatório em `docs/evidence/` deve conter:

1. objetivo e escopo;
2. commit e branch;
3. ambiente;
4. comandos executados;
5. entradas e respectivos hashes;
6. resultados brutos ou referência aos artefatos do CI;
7. cobertura;
8. falhas e causa raiz;
9. limitações;
10. decisão formal.

## Critério de merge

Um PR só pode ser considerado apto quando o diff estiver limitado ao escopo, todos os checks obrigatórios passarem, não houver regressão conhecida sem aprovação explícita e as evidências estiverem anexadas.
