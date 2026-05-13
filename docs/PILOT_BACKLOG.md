# Backlog do Piloto — IA Trabalhista Robusta

Produto real para venda/comercialização. Este backlog registra pendências encontradas durante os testes da matriz trabalhista para evitar perda de contexto entre ciclos.

## Marcos já validados

- v0.1.2-editor-trabalhista-pdf — PDF jurídico A4, download real e endereçamento trabalhista.
- v0.1.3-editor-verbas-rescisorias — Template trabalhista de verbas rescisórias.
- v0.1.4-editor-horas-extras — Template trabalhista de horas extras e intervalo intrajornada.
- v0.1.5-editor-fgts — Template trabalhista de FGTS não recolhido.

## Pendências abertas

### 1. Cabeçalho do PDF usa título curto/apelido
Em alguns PDFs o cabeçalho aparece como `trab 005` ou `PILOTO-TRAB-004`, em vez do título completo do caso.

Objetivo futuro:
- Preferir título completo do documento/caso no cabeçalho do PDF.
- Manter número do caso como metadado secundário.

Prioridade: média.

### 2. Resumo Executivo conservador demais
O Resumo Executivo tem classificado muitos casos como `DADOS INSUFICIENTES`, mesmo quando existe base mínima para gerar peça inicial revisável.

Objetivo futuro:
- Diferenciar “dados insuficientes para prognóstico final” de “viabilidade inicial plausível pendente de documentos/cálculo”.
- Melhorar a classificação estratégica para casos trabalhistas comuns.

Prioridade: média.

### 3. Ruído de contexto no relatório
No caso PILOTO-TRAB-005, o relatório trouxe ruído indevido em “Elementos fáticos considerados”, mencionando “poeira de cimento”, assunto não relacionado ao caso de FGTS.

Objetivo futuro:
- Revisar geração do Resumo/Relatório Executivo.
- Impedir reaproveitamento indevido de contexto de casos anteriores.
- Criar teste de regressão para garantir que fatos de outro caso não vazem no relatório atual.

Prioridade: alta.

### 4. Resumo Fático ainda não puxa dados específicos automaticamente
Os templates estão juridicamente bons, mas ainda podem melhorar usando dados explícitos do cadastro, como:
- nome do reclamante;
- nome da reclamada;
- cidade;
- período contratual;
- função;
- salário;
- modalidade de rescisão, quando houver.

Objetivo futuro:
- Extrair dados estruturados do caso e incorporá-los no Resumo Fático de forma segura.
- Manter placeholders quando os dados estiverem ausentes.

Prioridade: média.

### 5. Token local curto para testes longos
Durante testes, o login expirou antes do fim do fluxo.

Objetivo futuro:
- Documentar configuração local recomendada para desenvolvimento.
- Exemplo local: `JWT_EXPIRES_MIN=480`.
- Não alterar padrão de produção sem decisão de segurança.

Prioridade: baixa/local.

## Próximos testes da matriz trabalhista sugeridos

1. Acidente/doença ocupacional.
2. Vínculo empregatício/pejotização.
3. Assédio moral.
4. Desvio/acúmulo de função.
5. Adicional noturno.

