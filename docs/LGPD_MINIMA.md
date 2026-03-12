# LGPD MÍNIMA — IA Trabalhista Robusta

## Objetivo
Este documento define os controles mínimos de privacidade e proteção de dados pessoais para o projeto **IA Trabalhista Robusta**, em linha com a LGPD, no estágio atual do MVP vendável.

Princípios:
- coletar apenas o necessário para a finalidade do produto
- limitar exposição de dados pessoais em logs, telas e documentos
- tratar dados jurídicos e pessoais com acesso restrito por tenant e perfil
- registrar pendências de maturidade sem fingir compliance total antes da hora

---

## Escopo
Este documento cobre o mínimo necessário de governança de dados pessoais no estágio atual do produto, incluindo:
- dados de autenticação e acesso
- dados cadastrais de usuários e tenants
- dados processuais e documentos jurídicos inseridos no sistema
- dados presentes em análises, relatórios e PDFs

---

## Categorias de dados tratados no MVP

### 1. Dados de autenticação e conta
- nome de usuário, e-mail, senha hash, perfil e vínculo com tenant

### 2. Dados operacionais do escritório/tenant
- nome do tenant, usuários vinculados, limites e assinaturas

### 3. Dados jurídicos e processuais
- informações de casos, partes, documentos, análises e relatórios

### 4. Dados técnicos mínimos
- logs operacionais, eventos administrativos e evidências de incidente

---

## Regras mínimas de proteção
- cada tenant deve acessar apenas seus próprios dados
- rotas administrativas globais devem ter controle restrito
- senhas não devem ser armazenadas em texto puro
- logs não devem expor segredos, tokens ou dados pessoais sem necessidade operacional
- PDFs e relatórios devem ser tratados como artefatos sensíveis quando contiverem dados pessoais ou jurídicos

---

## Controles mínimos no estágio atual

### 1. Controle de acesso
- autenticação obrigatória para rotas protegidas
- segregação por tenant como regra central de acesso
- contexto administrativo global tratado de forma excepcional e controlada

### 2. Minimização de exposição
- evitar exibir dados pessoais desnecessários em telas, logs e respostas de erro
- limitar dados retornados ao estritamente necessário para cada operação

### 3. Logs e auditoria
- registrar eventos operacionais e administrativos sem despejar dados sensíveis em excesso
- revisar continuamente logs para evitar vazamento de tokens, credenciais, documentos ou dados pessoais completos

### 4. Relatórios e PDFs
- considerar relatórios e PDFs como artefatos sensíveis
- evitar compartilhamento fora do fluxo autorizado do tenant

### 5. Retenção e descarte
- definir política formal de retenção como pendência de evolução
- até a política formal existir, evitar retenção desnecessária de cópias e exportações locais

---

## Pendências assumidas nesta fase
- política formal de retenção e descarte ainda precisa ser fechada
- fluxo formal de atendimento a direitos do titular ainda precisa ser documentado
- revisão contínua de logs sensíveis ainda precisa ser concluída
- base legal detalhada por operação ainda pode ser refinada em versão posterior

## Regra de honestidade operacional
Este documento representa a LGPD mínima do MVP vendável. Não declara conformidade total irrestrita; declara o nível real atual de proteção, controles existentes e pendências ainda abertas.

---

## Incidentes de privacidade — resposta mínima
Em caso de suspeita de exposição indevida de dados:
- interromper a ação que esteja ampliando a exposição
- registrar evidências mínimas do incidente
- identificar tenant, usuários e artefatos afetados
- avaliar se logs, PDFs, respostas de erro ou acesso admin participaram do evento
- encaminhar correção técnica e registro pós-incidente no runbook correspondente

## Checklist mínimo de revisão
- há exposição indevida de token, senha, segredo ou credencial?
- há dado pessoal aparecendo em log sem necessidade?
- há relatório/PDF com dados além do necessário?
- há rota retornando dados de outro tenant?
- há exportação local sendo mantida sem necessidade?

## Dono operacional
Este documento deve ser revisado sempre que houver mudança relevante em autenticação, tenant isolation, geração de relatórios/PDFs, logs, auditoria, retenção de dados ou incidente de privacidade.
