# LGPD MÍNIMA — IA Trabalhista Robusta

## Objetivo
Este documento define os controles mínimos de privacidade e proteção de dados pessoais para o projeto **IA Trabalhista Robusta**, em linha com a LGPD, no estágio atual do MVP vendável.

Princípios:
- coletar apenas o necessário para a finalidade do produto
- limitar exposição de dados pessoais em logs, telas, respostas e documentos
- tratar dados jurídicos e pessoais com acesso restrito por tenant e perfil
- registrar pendências de maturidade sem fingir compliance total antes da hora

---

## Escopo
Este documento cobre o mínimo necessário de governança de dados pessoais no estágio atual do produto, incluindo:
- dados de autenticação e acesso
- dados cadastrais de usuários e tenants
- dados processuais e documentos jurídicos inseridos no sistema
- dados presentes em análises, relatórios e PDFs
- dados técnicos mínimos necessários para operação, segurança e resposta a incidente

---

## Categorias de dados tratados no MVP

### 1. Dados de autenticação e conta
- nome de usuário, e-mail, senha hash, perfil e vínculo com tenant

### 2. Dados operacionais do escritório/tenant
- nome do tenant, usuários vinculados, limites, assinatura e dados administrativos mínimos

### 3. Dados jurídicos e processuais
- informações de casos, partes, documentos, análises, relatórios e peças derivadas

### 4. Dados técnicos mínimos
- logs operacionais, eventos administrativos e evidências mínimas de incidente

---

## Regras mínimas de proteção
- cada tenant deve acessar apenas seus próprios dados
- rotas administrativas globais devem ter controle restrito
- senhas não devem ser armazenadas em texto puro
- logs não devem expor segredos, tokens ou dados pessoais sem necessidade operacional
- PDFs, relatórios e exportações devem ser tratados como artefatos sensíveis quando contiverem dados pessoais ou jurídicos

---

## Controles mínimos no estágio atual

### 1. Controle de acesso
- autenticação obrigatória para rotas protegidas
- segregação por tenant como regra central de acesso
- contexto administrativo global tratado de forma excepcional e controlada

### 2. Minimização de exposição
- evitar exibir dados pessoais desnecessários em telas, logs e respostas de erro
- limitar dados retornados ao estritamente necessário para cada operação
- evitar replicação desnecessária de dados jurídicos sensíveis em múltiplos artefatos locais

### 3. Logs e auditoria
- registrar eventos operacionais e administrativos sem despejar dados sensíveis em excesso
- revisar continuamente logs para evitar vazamento de tokens, credenciais, documentos ou dados pessoais completos
- sempre que possível, preferir identificação operacional mínima em vez de conteúdo integral de documentos

### 4. Relatórios, PDFs e exportações
- considerar relatórios, PDFs e exportações como artefatos sensíveis
- evitar compartilhamento fora do fluxo autorizado do tenant
- evitar manter cópias locais exportadas sem necessidade operacional clara
- quando houver exportação/manual download, tratar o arquivo como responsabilidade operacional controlada

### 5. Retenção e descarte
- definir política formal de retenção como pendência de evolução
- até a política formal existir, evitar retenção desnecessária de cópias e exportações locais
- descartar artefatos temporários, dumps, exports e arquivos auxiliares que não precisem permanecer armazenados
- não manter backups, exports ou evidências fora do fluxo previsto sem motivo operacional claro

### 6. Exclusão e correção
- pedidos de correção, remoção ou revisão de dados devem ser tratados de forma controlada, com análise de impacto jurídico e operacional
- exclusão não deve apagar de forma irresponsável registros necessários à segurança, rastreabilidade, obrigação legal, defesa ou integridade mínima do produto
- quando a exclusão integral não for possível no estágio atual, o caso deve ser tratado com resposta operacional explícita e registro interno

### 7. Atendimento mínimo a direitos do titular
- solicitações relacionadas a acesso, correção, exportação ou exclusão devem ser recebidas por canal operacional controlado
- a análise deve identificar tenant, usuário, dados afetados, base operacional envolvida e risco de remoção indevida
- o atendimento deve ser registrado para permitir rastreabilidade mínima

### 8. Segredos, credenciais e artefatos sensíveis
- segredos, tokens, senhas, chaves administrativas e credenciais não devem aparecer em logs, respostas, screenshots, dumps compartilhados ou documentação pública
- `.env`, dumps de banco, exports e PDFs reais devem ser tratados como materiais sensíveis
- ambientes de teste devem preferir dados isolados ou controlados, evitando exposição indevida da base principal
- qualquer uso excepcional de credencial administrativa deve ser restrito, registrado e revisado

---

## Pendências assumidas nesta fase
- política formal de retenção e descarte ainda precisa ser fechada
- fluxo formal externo de atendimento a direitos do titular ainda pode ser refinado
- revisão contínua de logs sensíveis ainda precisa ser concluída
- base legal detalhada por operação ainda pode ser refinada em versão posterior
- automação mais sofisticada para exportação/exclusão ainda não é promessa desta fase

## Regra de honestidade operacional
Este documento representa a LGPD mínima do MVP vendável. Não declara conformidade total irrestrita; declara o nível real atual de proteção, controles existentes e pendências ainda abertas.

---

## Incidentes de privacidade — resposta mínima
Em caso de suspeita de exposição indevida de dados:
- interromper a ação que esteja ampliando a exposição
- registrar evidências mínimas do incidente
- identificar tenant, usuários, dados e artefatos afetados
- avaliar se logs, PDFs, exportações, respostas de erro ou acesso admin participaram do evento
- encaminhar correção técnica e registro pós-incidente no runbook correspondente

## Checklist mínimo de revisão
- há exposição indevida de token, senha, segredo ou credencial?
- há dado pessoal aparecendo em log sem necessidade?
- há relatório/PDF/export com dados além do necessário?
- há rota retornando dados de outro tenant?
- há exportação local sendo mantida sem necessidade?
- há artefato temporário sensível sem descarte adequado?
- há pedido de correção/exclusão sem trilha mínima de tratamento?

## Dono operacional
Este documento deve ser revisado sempre que houver mudança relevante em autenticação, tenant isolation, geração de relatórios/PDFs, exportação de dados, logs, auditoria, retenção, descarte, exclusão lógica/física ou incidente de privacidade.
