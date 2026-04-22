# RELEASE CHECKLIST — IA Trabalhista Robusta

## Regra de ouro
Este produto só será considerado pronto para mercado quando todos os itens críticos estiverem em 100%, sem lacunas relevantes de segurança, operação, fluxo funcional, governança e experiência mínima de uso.

Legenda de status:
- [ ] Não iniciado
- [~] Parcial
- [x] Concluído

---

## 1) Base técnica e operação
- [x] API versionada em `/api/v1`
- [x] `/health` funcional
- [x] `/ready` com verificação real de banco
- [x] CI com checks principais
- [x] smoke test principal
- [x] proteção de branch + fluxo por PR
- [~] documentação operacional completa de produção
- [x] runbook de incidente/rollback
- [x] procedimento formal de backup/restore validado

## 2) Auth, tenant e segurança
- [x] autenticação funcional
- [x] isolamento multi-tenant no fluxo principal
- [x] criação de usuário vinculada ao tenant atual
- [x] activate/deactivate com restrição por tenant
- [x] admin key separada para rotas globais
- [~] revisão final de exposição de dados sensíveis em logs
- [x] revisão LGPD mínima (retenção, exportação, exclusão, segredos)
- [x] revisão formal de seed/break-glass em produção

## 3) Fluxo principal do produto
- [x] criar caso
- [x] listar caso
- [x] obter caso por id
- [x] gerar análise
- [x] persistir análise
- [x] gerar executive summary
- [x] gerar executive report HTML
- [x] gerar executive PDF
- [x] registrar uso
- [~] cobertura funcional formal ponta a ponta
- [~] validação formal dos cenários de erro principais

## 4) Relatórios e entrega executiva
- [x] resumo executivo integrado ao fluxo real
- [x] relatório HTML com resumo executivo premium
- [x] PDF executivo com fallback funcional
- [x] risco padronizado em Baixo/Médio/Alto
- [~] revisão comercial dos textos fixos
- [ ] template “cliente final”
- [ ] template “advogado/operacional”

## 5) Planos, limites e monetização
- [x] estruturas de subscription/usage presentes
- [x] enforcement inicial de limites
- [x] summary de uso
- [~] definição final dos planos comerciais
- [ ] política clara de trial
- [ ] comportamento documentado ao estourar limite
- [ ] tabela comercial pronta para venda

## 6) Admin e governança
- [x] audit logs administrativos
- [x] dashboard/summary administrativo inicial
- [x] gestão de subscription por admin
- [~] painel/admin com visão operacional suficiente
- [ ] trilha de auditoria funcional revisada para casos críticos
- [ ] export operacional mínimo para suporte/comercial

## 7) UX e prontidão comercial
- [~] experiência adequada para demo
- [~] experiência adequada para piloto assistido
- [ ] experiência adequada para autoatendimento
- [ ] onboarding de escritório/tenant claro
- [ ] posicionamento comercial fechado
- [x] documento oficial “o que faz / o que não faz / limites da IA”

## 8) Arquitetura e visão multicausa
- [x] diretriz multicausa definida
- [~] separação conceitual entre núcleo e regras trabalhistas
- [ ] fronteiras explícitas entre núcleo genérico e domínio trabalhista
- [ ] padrão replicável para futuras áreas (criminal, família, cível, etc.)

---

## Bloqueadores de mercado aberto
- [ ] checklist funcional 100% validado
- [ ] governança mínima de produção fechada
- [x] LGPD mínima revisada
- [ ] fluxo comercial/planos fechados
- [ ] onboarding minimamente utilizável
- [ ] documentação oficial do produto pronta

## Liberação para piloto controlado
Condição: somente quando todos os itens críticos de fluxo, auth, tenant, relatório, PDF, health/ready e uso estiverem validados e sem falhas abertas graves.

## Liberação para mercado
Condição: somente com 100% dos bloqueadores concluídos.

