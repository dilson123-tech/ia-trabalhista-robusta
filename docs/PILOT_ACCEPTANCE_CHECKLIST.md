# Checklist de Aceitação do Piloto — IA Trabalhista Robusta

## Objetivo

Validar se o MVP técnico está pronto para uso controlado por advogado em ambiente de piloto, com foco em segurança, coerência jurídica, fluxo funcional e qualidade das saídas.

## Escopo do piloto

Este piloto valida o fluxo principal:

1. Login do usuário autorizado.
2. Criação de caso jurídico.
3. Geração de análise.
4. Geração de relatório executivo.
5. Criação de documento no Editor Jurídico Vivo.
6. Geração assistida da peça.
7. Revisão da peça pelo advogado.
8. Aprovação da versão.
9. Exportação do PDF final.

## Critérios obrigatórios de aprovação

### 1. Autenticação e contexto

- [ ] Usuário consegue fazer login.
- [ ] O painel carrega sem erro.
- [ ] O usuário acessa apenas os próprios casos/tenant.
- [ ] Não há troca indevida de contexto entre casos.

### 2. Criação e análise do caso

- [ ] Caso é criado com área jurídica correta.
- [ ] Tipo de ação é salvo corretamente.
- [ ] A análise respeita os fatos informados.
- [ ] A análise não inventa fatos relevantes.
- [ ] A análise aponta lacunas probatórias quando necessário.

### 3. Segurança da saída jurídica

- [ ] Não há percentual público de êxito.
- [ ] Não há score público.
- [ ] Não há promessa de resultado.
- [ ] Não há tese jurídica incompatível com o caso.
- [ ] Não há pedidos inventados sem base nos fatos.
- [ ] O texto informa que a validação final é profissional.

### 4. Relatório executivo

- [ ] Relatório mostra resumo coerente.
- [ ] Relatório mostra riscos em linguagem qualitativa.
- [ ] Relatório orienta próximos passos.
- [ ] Relatório não expõe score/probabilidade.
- [ ] Relatório é legível e apresentável.

### 5. Editor Jurídico Vivo

- [ ] Documento editável é criado corretamente.
- [ ] Peça assistida é gerada com base no caso.
- [ ] Blocos da peça ficam organizados.
- [ ] A peça não mistura áreas jurídicas indevidas.
- [ ] A versão pode ser aprovada.
- [ ] O PDF final é exportado.

### 6. PDF final

- [ ] PDF abre corretamente.
- [ ] PDF não corta texto.
- [ ] PDF tem aparência formal e profissional.
- [ ] PDF contém título, área, tipo e versão.
- [ ] PDF não contém score/probabilidade.
- [ ] PDF não contém tese fora do caso.

## Resultado do piloto

- [ ] Aprovado sem ressalvas.
- [ ] Aprovado com ajustes leves.
- [ ] Reprovado para uso comercial até correção.

## Observações do advogado avaliador

Registrar abaixo pontos de melhoria, riscos, sugestões e qualquer inconsistência percebida durante o uso.

